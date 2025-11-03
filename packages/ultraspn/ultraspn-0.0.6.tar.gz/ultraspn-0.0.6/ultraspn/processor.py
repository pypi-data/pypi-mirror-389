from __future__ import annotations

import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence, Tuple

import chanfig
import cv2 as cv
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm


class Config(chanfig.Config):
    input: str = "images"
    output: str = "outputs"
    table: str = "zx.csv"
    percentile: float = 92.0
    bbox_color: Tuple[int, int, int] = (0, 255, 0)
    bbox_thickness: int = 5
    workers: int | None = None

    def post(self) -> None:
        if not (0.0 < self.percentile <= 100.0):
            raise ValueError("percentile must be within (0, 100]")
        if self.workers is not None and self.workers < 0:
            raise ValueError("workers must be None, 0, or positive integer")


@dataclass
class BoundingBox:
    top: int
    bottom: int
    left: int
    right: int

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)


@dataclass
class ColorCues:
    band: np.ndarray
    glare_mask: np.ndarray
    specular_map: np.ndarray


class Axis(Enum):
    VERTICAL = 0
    HORIZONTAL = 1


def _ensure_odd(value: int) -> int:
    return value if value % 2 == 1 else value + 1


def _smooth_sequence(sequence: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return sequence
    window = _ensure_odd(int(window))
    kernel = np.ones(window, dtype=np.float64) / window
    return np.convolve(sequence, kernel, mode="same")


def _clahe_parameters(gray: np.ndarray) -> Tuple[float, Tuple[int, int]]:
    h, w = gray.shape
    grid = max(2, int(round(np.sqrt(h * w) / 150)))
    clip = float(np.clip(np.var(gray) / 1024 + 1.5, 1.0, 8.0))
    return clip, (grid, grid)


def _preprocess(gray: np.ndarray) -> np.ndarray:
    clip_limit, tile_grid = _clahe_parameters(gray)
    clahe = cv.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
    enhanced = clahe.apply(gray)
    kernel = _ensure_odd(max(3, int(round(min(gray.shape) / 150))))
    return cv.GaussianBlur(enhanced, (kernel, kernel), 0)


def _band_image(gray: np.ndarray) -> np.ndarray:
    blur_size = _ensure_odd(max(21, int(round(gray.shape[1] / 20))))
    baseline = cv.GaussianBlur(gray, (blur_size, blur_size), 0)
    band = cv.subtract(gray, baseline)
    return cv.normalize(band, None, 0, 255, cv.NORM_MINMAX).astype(np.float32)


def _percentile_profile(
    primary: np.ndarray,
    axis: Axis,
    percentile: float,
    extras: Optional[Sequence[Tuple[np.ndarray, float]]] = None,
    weight_power: Optional[float] = 1.0,
) -> np.ndarray:
    def compute(sample: np.ndarray) -> np.ndarray:
        if sample.size == 0:
            length = sample.shape[0] if axis is Axis.VERTICAL else sample.shape[1]
            return np.zeros(length, dtype=np.float64)

        collapse_axis = 1 if axis is Axis.VERTICAL else 0
        weighted = sample
        if weight_power is not None:
            if axis is Axis.VERTICAL:
                weights = _column_weights(sample.shape[1]) ** float(weight_power)
                weighted = weighted * weights
            else:
                weights = (_row_weights(sample.shape[0]) ** float(weight_power))[:, None]
                weighted = weighted * weights
        return np.percentile(weighted, percentile, axis=collapse_axis).astype(np.float64)

    profile = compute(primary)
    if extras:
        for extra, blend in extras:
            if extra is None or extra.size == 0 or blend == 0.0:
                continue
            profile += float(blend) * compute(extra)
    return profile


def _extract_color_cues(image: np.ndarray) -> ColorCues:
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    processed_sat = _preprocess(saturation)
    band_sat = _band_image(processed_sat)

    red = image[:, :, 2]
    blue = image[:, :, 0]
    rb_diff = cv.absdiff(red, blue)
    processed_diff = _preprocess(rb_diff)
    band_diff = _band_image(processed_diff)
    color_band = np.maximum(band_sat, band_diff).astype(np.float32)

    value = hsv[:, :, 2].astype(np.float32)
    saturation_f = saturation.astype(np.float32)
    glare_sigma = max(1.0, min(image.shape[0], image.shape[1]) / 400.0)
    value_blur = cv.GaussianBlur(value, (0, 0), glare_sigma)
    saturation_blur = cv.GaussianBlur(saturation_f, (0, 0), glare_sigma)

    value_threshold = float(np.percentile(value_blur, 95))
    saturation_threshold = float(np.percentile(saturation_blur, 30))
    glare_mask = np.logical_and(value_blur >= value_threshold, saturation_blur <= saturation_threshold).astype(
        np.float32
    )
    glare_mask = cv.GaussianBlur(glare_mask, (0, 0), glare_sigma)
    glare_mask /= glare_mask.max() + 1e-9

    specular_map = cv.max(value_blur - saturation_blur, 0.0)
    specular_map = cv.GaussianBlur(specular_map, (0, 0), glare_sigma)
    specular_map /= specular_map.max() + 1e-9

    return ColorCues(
        band=color_band,
        glare_mask=glare_mask.astype(np.float32),
        specular_map=specular_map.astype(np.float32),
    )


def _column_weights(width: int) -> np.ndarray:
    positions = (np.arange(width) - (width - 1) / 2) / max(width / 6.0, 1.0)
    weights = np.exp(-(positions**2) / 2.0)
    return weights / weights.max()


def _row_weights(height: int) -> np.ndarray:
    positions = (np.arange(height) - (height - 1) / 2) / max(height / 6.0, 1.0)
    weights = np.exp(-(positions**2) / 2.0)
    return weights / weights.max()


def _sobel_profiles(image: np.ndarray, axis: int) -> Tuple[np.ndarray, np.ndarray]:
    if axis == 0:
        grad = cv.Sobel(image, cv.CV_32F, 0, 1, ksize=3)
        col_weights = _column_weights(image.shape[1])
        row_weights = _row_weights(image.shape[0])
        positive = (np.maximum(grad, 0.0) * col_weights).sum(axis=1) * row_weights
        negative = (np.maximum(-grad, 0.0) * col_weights).sum(axis=1) * row_weights
    elif axis == 1:
        grad = cv.Sobel(image, cv.CV_32F, 1, 0, ksize=3)
        row_weights = _row_weights(image.shape[0])
        weighted = np.maximum(grad, 0.0) * row_weights[:, None]
        col_weights = _column_weights(image.shape[1]) ** 0.5
        positive = weighted.sum(axis=0) * col_weights
        weighted_neg = np.maximum(-grad, 0.0) * row_weights[:, None]
        negative = weighted_neg.sum(axis=0) * col_weights
    else:
        raise ValueError("axis must be 0 (vertical) or 1 (horizontal)")
    return positive.astype(np.float64), negative.astype(np.float64)


def _column_energy(
    primary_slice: np.ndarray,
    extra_slice: Optional[np.ndarray],
    glare_mask: Optional[np.ndarray],
    specular_map: Optional[np.ndarray],
    smooth_sigma: float,
    blend: float = 0.35,
    glare_weight: float = 0.3,
    specular_weight: float = 0.2,
) -> np.ndarray:
    extras: Optional[Sequence[Tuple[np.ndarray, float]]] = None
    if extra_slice is not None and extra_slice.size:
        extras = [(extra_slice, blend)]
    energy = _percentile_profile(primary_slice, Axis.HORIZONTAL, 97.0, extras=extras, weight_power=None)
    energy = cv.GaussianBlur(energy.reshape(1, -1), (0, 0), smooth_sigma).reshape(-1)
    energy -= energy.min()
    if not np.any(energy):
        energy = np.ones_like(energy)
    else:
        energy /= energy.max() + 1e-9

    if glare_mask is not None and glare_mask.size:
        glare_profile = glare_mask.mean(axis=0).astype(np.float64)
        glare_profile = cv.GaussianBlur(glare_profile.reshape(1, -1), (0, 0), smooth_sigma).reshape(-1)
        glare_profile = np.clip(glare_profile, 0.0, 1.0)
        energy *= np.clip(1.0 - glare_weight * glare_profile, 0.1, 1.0)

    if specular_map is not None and specular_map.size:
        spec_profile = specular_map.mean(axis=0).astype(np.float64)
        spec_profile = cv.GaussianBlur(spec_profile.reshape(1, -1), (0, 0), smooth_sigma).reshape(-1)
        if np.any(spec_profile):
            spec_profile /= spec_profile.max() + 1e-9
            energy *= np.clip(1.0 - specular_weight * spec_profile, 0.2, 1.0)

    return energy


def _refine_bounds(profile: np.ndarray, start: int, end: int, margin: int) -> Tuple[int, int]:
    start = max(0, min(start, profile.size - 2))
    end = max(start + 1, min(end, profile.size))
    gradient = np.gradient(profile)
    top_window = gradient[max(0, start - margin) : min(profile.size, start + margin)]
    bottom_window = gradient[max(0, end - margin) : min(profile.size, end + margin)]
    top_idx = max(0, start - margin) + int(np.argmax(top_window)) if top_window.size else start
    bottom_idx = max(0, end - margin) + int(np.argmin(bottom_window)) if bottom_window.size else end
    bottom_idx = max(top_idx + 1, bottom_idx)
    return top_idx, min(profile.size, bottom_idx)


def _energy_window(values: np.ndarray, lower: float, upper: float) -> Tuple[int, int]:
    length = values.size
    if length == 0:
        return 0, 0

    weights = np.clip(values.astype(np.float64), 0.0, None)
    total = float(weights.sum())
    if total <= 0.0:
        return 0, length

    cumulative = np.cumsum(weights) / total
    start = int(np.searchsorted(cumulative, float(np.clip(lower, 0.0, 1.0)), side="left"))
    end = int(np.searchsorted(cumulative, float(np.clip(upper, 0.0, 1.0)), side="right"))
    start = max(0, min(start, length - 1))
    end = max(start + 1, min(end, length))

    if end <= start:
        peak = int(np.argmax(weights))
        start = max(0, peak - 1)
        end = min(length, peak + 2)

    return start, end


def _moment_window(values: np.ndarray, minimum: int) -> Tuple[int, int]:
    length = values.size
    if length == 0:
        return 0, 0

    weights = np.clip(values.astype(np.float64), 0.0, None)
    total = float(weights.sum())
    if total <= 0.0:
        return 0, length

    positions = (np.arange(length, dtype=np.float64) + 0.5) / float(length)
    mean = float(np.dot(weights, positions) / total)
    variance = float(np.dot(weights, (positions - mean) ** 2) / total)
    sigma = max(np.sqrt(max(variance, 0.0)), 1.0 / length)

    lower = max(0.0, mean - sigma)
    upper = min(1.0, mean + sigma)

    start = int(np.floor(lower * length))
    end = int(np.ceil(upper * length))
    if end - start < minimum:
        padding = (minimum - (end - start)) / (2.0 * length)
        lower = max(0.0, lower - padding)
        upper = min(1.0, upper + padding)
        start = int(np.floor(lower * length))
        end = int(np.ceil(upper * length))

    start = max(0, min(start, length - 1))
    end = max(start + 1, min(end, length))
    return start, end


def _local_maxima(values: np.ndarray) -> np.ndarray:
    if values.size < 3:
        return np.array([], dtype=np.int32)
    gradient = np.diff(values)
    signs = np.sign(gradient)
    turning = (np.hstack([signs, 0.0]) < 0.0) & (np.hstack([0.0, signs]) > 0.0)
    return np.where(turning)[0].astype(np.int32)


def _localize_vertical_bounds(
    enhanced_gray: np.ndarray,
    band: np.ndarray,
    color_cues: ColorCues,
    percentile: float,
) -> Tuple[int, int]:
    height = enhanced_gray.shape[0]
    if height == 0:
        return 0, 0

    blur_sigma = max(1.0, min(enhanced_gray.shape) / 1500.0)
    blurred = cv.GaussianBlur(enhanced_gray, (0, 0), blur_sigma)
    upward_edges, downward_edges = _sobel_profiles(blurred, axis=0)

    smoothing = max(5, height // 200)
    upward_smooth = _smooth_sequence(upward_edges, smoothing)
    downward_smooth = _smooth_sequence(downward_edges, smoothing)

    bottom_peak = int(np.argmax(downward_smooth))
    peaks = _local_maxima(upward_smooth)
    max_gap = max(height // 4, 400)
    candidates = [idx for idx in peaks if 0 < bottom_peak - idx <= max_gap]
    if not candidates and bottom_peak > 0:
        candidates = [int(np.argmax(upward_smooth[:bottom_peak]))]
    top_estimate = (
        max(candidates, key=lambda idx: upward_smooth[idx]) if candidates else max(0, bottom_peak - height // 10)
    )
    top_estimate = int(top_estimate)
    bottom_estimate = max(top_estimate + 1, bottom_peak)

    percentile_energy = min(99.0, 95.0 + height / 8000.0)
    base_margin = max(smoothing * 3, height // 100, 40)
    min_height = max(40, height // 100)
    margin = max(base_margin, (bottom_estimate - top_estimate) // 2 + min_height)
    lower = max(0, min(top_estimate, bottom_estimate) - margin)
    upper = min(height, max(top_estimate, bottom_estimate) + margin)
    if upper - lower <= min_height:
        extra = min_height - (upper - lower)
        lower = max(0, lower - extra // 2)
        upper = min(height, upper + extra - extra // 2)

    band_segment = band[lower:upper]
    energy = _percentile_profile(band_segment, Axis.VERTICAL, percentile_energy)
    smooth_window = max(3, band_segment.shape[0] // 120)
    energy = _smooth_sequence(energy, smooth_window)
    energy = np.clip(energy, 0.0, None)

    if color_cues.glare_mask.size:
        glare_profile = color_cues.glare_mask[lower:upper].mean(axis=1)
        glare_profile = _smooth_sequence(glare_profile, smooth_window)
        energy *= np.clip(1.0 - 0.45 * glare_profile, 0.1, 1.0)
    if color_cues.specular_map.size:
        spec_profile = color_cues.specular_map[lower:upper].mean(axis=1)
        spec_profile = _smooth_sequence(spec_profile, smooth_window)
        if np.any(spec_profile):
            spec_profile /= spec_profile.max() + 1e-9
            energy *= np.clip(1.0 - 0.25 * spec_profile, 0.2, 1.0)

    segment_length = max(upper - lower, 1)
    desired_span = max(min_height, bottom_estimate - top_estimate)
    span_fraction = np.clip(desired_span / segment_length, 0.2, 0.85)
    center_fraction = np.clip(((top_estimate + bottom_estimate) / 2 - lower) / segment_length, 0.0, 1.0)
    lower_frac = max(0.0, center_fraction - span_fraction / 2.0)
    upper_frac = min(1.0, center_fraction + span_fraction / 2.0)
    span_frac = max(upper_frac - lower_frac, 1e-3)
    if span_frac < span_fraction:
        deficit = span_fraction - span_frac
        lower_frac = max(0.0, lower_frac - deficit / 2.0)
        upper_frac = min(1.0, upper_frac + deficit / 2.0)

    rel_top, rel_bottom = _energy_window(energy, lower_frac, upper_frac)
    candidate_top = lower + rel_top
    candidate_bottom = lower + rel_bottom
    if candidate_bottom <= candidate_top:
        candidate_bottom = min(height, candidate_top + max(2, int(np.ceil(segment_length * span_fraction))))
    span = candidate_bottom - candidate_top
    if span < min_height:
        pad = (min_height - span) // 2
        candidate_top = max(0, candidate_top - pad)
        candidate_bottom = min(height, candidate_bottom + (min_height - span - pad))

    row_profile = _percentile_profile(band, Axis.VERTICAL, percentile)
    refinement_margin = max(10, min((candidate_bottom - candidate_top) // 2, 60))
    top_final, bottom_final = _refine_bounds(row_profile, candidate_top, candidate_bottom, refinement_margin)
    top_final = max(0, min(top_final, height - 2))
    bottom_final = max(top_final + 1, min(bottom_final, height))
    return top_final, bottom_final


def _find_plate_boundaries_simple(intensity_profile: np.ndarray, center_idx: int, sigma: float) -> Tuple[int, int]:
    """Find plate boundaries by detecting where dark plate transitions to bright background."""
    width = len(intensity_profile)
    smoothed = cv.GaussianBlur(intensity_profile.reshape(1, -1), (0, 0), sigma).reshape(-1)

    center_window = min(200, width // 6)
    center_start = max(0, center_idx - center_window // 2)
    center_end = min(width, center_idx + center_window // 2)
    if center_end <= center_start:
        return 0, width - 1
    plate_intensity = smoothed[center_start:center_end].min()

    intensity_range = smoothed.max() - smoothed.min()

    right_boundary = width - 1
    window_size = max(50, width // 60)
    for i in range(center_idx + center_window // 2, width - window_size):
        if smoothed[i] > plate_intensity + 0.25 * intensity_range:
            ahead_min = smoothed[i : i + window_size].min()
            if ahead_min > plate_intensity + 0.20 * intensity_range:
                right_boundary = i
                break

    left_boundary = 0
    for i in range(center_idx - center_window // 2, window_size, -1):
        if smoothed[i] > plate_intensity + 0.25 * intensity_range:
            behind_min = smoothed[max(0, i - window_size) : i].min()
            if behind_min > plate_intensity + 0.20 * intensity_range:
                left_boundary = i
                break

    return left_boundary, right_boundary


def _localize_horizontal_bounds(
    enhanced_gray: np.ndarray,
    band: np.ndarray,
    color_cues: ColorCues,
    top: int,
    bottom: int,
) -> Tuple[int, int]:
    height, width = enhanced_gray.shape
    top = max(0, min(top, height - 1))
    bottom = max(top + 1, min(bottom, height))
    strip_proc = enhanced_gray[top:bottom]
    if strip_proc.size == 0:
        return 0, width

    profile = strip_proc.mean(axis=0).astype(np.float64)
    sigma = max(1.0, width / 1800.0)
    smoothed = cv.GaussianBlur(profile.reshape(1, -1), (0, 0), sigma).reshape(-1)

    gradient = np.gradient(smoothed)

    band_slice = band[top:bottom]
    smooth_cols = max(1.0, width / 2000.0)
    extra_slice = color_cues.band[top:bottom]
    glare_slice = color_cues.glare_mask[top:bottom]
    spec_slice = color_cues.specular_map[top:bottom]
    col_norm = _column_energy(band_slice, extra_slice, glare_slice, spec_slice, smooth_cols)

    max_intensity = smoothed.max()
    min_intensity = smoothed.min()
    darkness_score = (max_intensity - smoothed) / (max_intensity - min_intensity + 1e-9)
    specimen_score = darkness_score * (0.3 + 0.7 * col_norm)
    specimen_score_smooth = cv.GaussianBlur(specimen_score.reshape(1, -1), (0, 0), sigma * 2.0).reshape(-1)
    
    peak_idx = int(np.argmax(specimen_score_smooth))
    peak_value = specimen_score_smooth[peak_idx]

    for threshold_pct in [0.7, 0.6, 0.5, 0.4]:
        threshold = threshold_pct * peak_value
        mask = specimen_score_smooth >= threshold

        if np.any(mask):
            left_edge = peak_idx
            while left_edge > 0 and mask[left_edge - 1]:
                left_edge -= 1
            right_edge = peak_idx
            while right_edge < width - 1 and mask[right_edge + 1]:
                right_edge += 1

            if right_edge - left_edge >= width * 0.1:
                center = float((left_edge + right_edge) / 2.0)
                break
    else:
        center = float(peak_idx)

    sigma_weight = max(width / 4.0, 1.0)
    weights = np.exp(-((np.arange(width) - center) ** 2) / (2.0 * sigma_weight**2))

    col_boost = 0.5 + 0.5 * np.clip(col_norm, 0.0, 1.0)
    center_idx = int(round(center))
    gradient = np.gradient(smoothed)
    weighted = gradient * weights
    sobel_pos, sobel_neg = _sobel_profiles(strip_proc, axis=1)

    negative = (np.clip(-weighted, 0.0, None) + sobel_neg) * col_boost
    positive = (np.clip(weighted, 0.0, None) + sobel_pos) * col_boost

    sobel_neg_weighted = sobel_neg * col_boost
    sobel_pos_weighted = sobel_pos * col_boost

    specimen_intensity = np.percentile(smoothed, 5)
    intensity_range = smoothed.max() - smoothed.min()
    dark_threshold = specimen_intensity + 0.30 * intensity_range
    search_window = max(50, width // 60)

    extent_left = 0
    for i in range(center_idx, search_window, -1):
        if smoothed[i] > dark_threshold:
            check_start = max(0, i - search_window)
            check_end = i
            if check_end > check_start:
                region_min = smoothed[check_start:check_end].min()
                if region_min > dark_threshold * 0.9:
                    extent_left = i
                    break

    extent_right = width - 1
    for i in range(center_idx, width - search_window):
        if smoothed[i] > dark_threshold:
            check_start = i
            check_end = min(width, i + search_window)
            if check_end > check_start:
                region_min = smoothed[check_start:check_end].min()
                if region_min > dark_threshold * 0.9:
                    extent_right = i
                    break

    min_extent = max(width // 20, 100)
    max_extent = int(width * 0.63)
    use_fallback = False

    if (extent_right - extent_left < min_extent) or (extent_right - extent_left > max_extent):
        use_fallback = True
        extent_threshold = 0.60 * specimen_score_smooth.max()
        extent_mask = specimen_score_smooth >= extent_threshold
        extent_indices = np.where(extent_mask)[0]

        if len(extent_indices) > 0:
            extent_left = extent_indices[0]
            extent_right = extent_indices[-1]
        else:
            half_width = int(width * 0.3)
            extent_left = max(0, center_idx - half_width)
            extent_right = min(width - 1, center_idx + half_width)

    extent_width_ratio = (extent_right - extent_left) / float(width)
    if extent_width_ratio > 0.58 and not use_fallback:
        left_adjustment = int(width * 0.008)
        right_adjustment = int(width * 0.018)
        left = extent_left + left_adjustment
        right = extent_right - right_adjustment
    else:
        margin = 0 if use_fallback else int(width * 0.03)
        inset = int(width * 0.05)
        search_left_start = max(0, extent_left - margin)
        search_left_end = min(center_idx, extent_left + inset + int(width * 0.10))
        search_right_start = max(center_idx, extent_right - inset - int(width * 0.10))
        search_right_end = min(width, extent_right + margin)

        left_scan_region = sobel_neg_weighted[search_left_start:search_left_end]
        if left_scan_region.size == 0 or search_left_end <= search_left_start:
            left = extent_left
        else:
            left = search_left_start + int(np.argmax(left_scan_region))

        right_scan_region = sobel_pos_weighted[search_right_start:search_right_end]
        if right_scan_region.size == 0 or search_right_end <= search_right_start:
            right = extent_right
        else:
            right = search_right_start + int(np.argmax(right_scan_region))

        if use_fallback:
            left = left + int(width * 0.01)
            right = right - int(width * 0.01)

    if right <= left:
        right = min(width - 1, left + max(width // 40, 10))
    left = max(0, min(left, width - 2))
    right = max(left + 1, min(right, width - 1))

    right = max(left + 1, min(right, width - 1))
    left = max(0, min(left, right - 1))

    detected_width = right - left
    max_reasonable_width = int(width * 0.75)
    if detected_width > max_reasonable_width:
        excess = detected_width - max_reasonable_width
        left_edge_strength = negative[left] if left < len(negative) else 0.0
        right_edge_strength = positive[right] if right < len(positive) else 0.0

        if left_edge_strength < right_edge_strength:
            left = min(left + excess, right - max_reasonable_width // 2)
        else:
            right = max(right - excess, left + max_reasonable_width // 2)

    return left, right


def detect_bbox(image: np.ndarray, percentile: float) -> BoundingBox:
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    enhanced_gray = _preprocess(gray)
    gray_band = _band_image(enhanced_gray)
    color_cues = _extract_color_cues(image)
    combined_band = np.maximum(gray_band, color_cues.band)

    top, bottom = _localize_vertical_bounds(enhanced_gray, combined_band, color_cues, percentile)
    left, right = _localize_horizontal_bounds(enhanced_gray, combined_band, color_cues, top, bottom)

    height, width = enhanced_gray.shape
    top = max(0, min(top, height - 2))
    bottom = max(top + 1, min(bottom, height))
    left = max(0, min(left, width - 2))
    right = max(left + 1, min(right, width))

    return BoundingBox(top=top, bottom=bottom, left=left, right=right)


def draw_bbox(image: np.ndarray, box: BoundingBox, bbox_color: Tuple[int, int, int], bbox_thickness: int) -> np.ndarray:
    annotated = image.copy()
    cv.rectangle(
        annotated,
        (int(box.left), int(box.top)),
        (int(box.right), int(box.bottom)),
        tuple(int(v) for v in bbox_color),
        int(bbox_thickness),
    )
    return annotated


def process_image(
    input: str, output: str, percentile: float, bbox_color: Tuple[int, int, int], bbox_thickness: int
) -> Tuple[BoundingBox, str]:
    input_path = Path(input)
    color = cv.imread(str(input_path), cv.IMREAD_COLOR)
    if color is None:
        raise FileNotFoundError(f"unable to read image: {input_path}")

    bbox = detect_bbox(color, percentile)
    annotated = draw_bbox(color, bbox, bbox_color, bbox_thickness)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(input_path)
    try:
        exif = img.getexif()
        time = exif[306]
    except Exception:
        time = ""
    if not cv.imwrite(str(output_path), annotated):
        raise RuntimeError(f"failed to save {output_path}")
    return bbox, time


def _process_wrapper(args):
    f, input_path, output_path, cfg = args
    box, time = process_image(input_path, output_path, cfg)
    return box, time


def process_image_wrapper(args):
    input_path, output_path, percentile, bbox_color, bbox_thickness, f = args
    box, time = process_image(input_path, output_path, percentile, bbox_color, bbox_thickness)
    return (box, time), f


if __name__ == "__main__":
    cfg = Config().parse()
    ret = []
    files = sorted(os.listdir(cfg.input))
    if cfg.workers == 0:
        for f in tqdm(files, total=len(files), desc="Processing images"):
            box, time = process_image(
                os.path.join(cfg.input, f),
                os.path.join(cfg.output, f),
                cfg.percentile,
                cfg.bbox_color,
                cfg.bbox_thickness,
            )
            ret.append(
                {
                    "id": f,
                    "time": time,
                    "height": box.height,
                    "width": box.width,
                    "top": box.top,
                    "left": box.left,
                    "bottom": box.bottom,
                    "right": box.right,
                }
            )
    else:
        num_workers = cfg.workers if cfg.workers is not None else multiprocessing.cpu_count()
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            results = list(
                tqdm(
                    executor.map(
                        process_image_wrapper,
                        [
                            (
                                os.path.join(cfg.input, f),
                                os.path.join(cfg.output, f),
                                cfg.percentile,
                                cfg.bbox_color,
                                cfg.bbox_thickness,
                                f,
                            )
                            for f in files
                        ],
                    ),
                    total=len(files),
                    desc="Processing images",
                )
            )
            ret = []
            for (box, time), f in results:
                ret.append(
                    {
                        "id": f,
                        "time": time,
                        "height": box.height,
                        "width": box.width,
                        "top": box.top,
                        "left": box.left,
                        "bottom": box.bottom,
                        "right": box.right,
                    }
                )
    df = pd.DataFrame(ret)
    df.to_csv(cfg.table, index=False)
    print(f"saved table -> {cfg.table}")
