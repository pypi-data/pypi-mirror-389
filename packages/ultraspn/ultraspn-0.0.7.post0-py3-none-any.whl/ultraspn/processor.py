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
from scipy.signal import find_peaks
from tqdm import tqdm


class Config(chanfig.Config):
    input: str = "images"
    output: str = "outputs"
    table: str = "zx.csv"
    plateau_width: float = 63.
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


def _detect_plateau_bounds(
    darkness_smooth: np.ndarray,
    width: int,
    plateau_threshold: float = 0.5,
) -> Tuple[int, int]:
    high_darkness_mask = darkness_smooth > plateau_threshold

    transitions = np.diff(np.concatenate(([False], high_darkness_mask, [False])).astype(int))
    starts = np.where(transitions == 1)[0]
    ends = np.where(transitions == -1)[0]

    if len(starts) == 0 or len(ends) == 0:
        raise RuntimeError("no plateau found")

    widths = ends - starts
    widest_idx = np.argmax(widths)
    plateau_start = starts[widest_idx]
    plateau_end = ends[widest_idx]
    plateau_width = widths[widest_idx]

    if plateau_width < width * 0.20:
        raise RuntimeError("plateau is not wide enough to be considered a plateau")

    return int(plateau_start), int(plateau_end)


def _enhance_by_plateau(
    color: np.ndarray,
    enhanced_gray: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int]]:
    height, width = enhanced_gray.shape
    if height == 0 or width == 0:
        raise RuntimeError("image is empty")

    col_profile = enhanced_gray.mean(axis=0).astype(np.float64)
    max_intensity = float(col_profile.max())
    min_intensity = float(col_profile.min())
    darkness = (max_intensity - col_profile) / (max_intensity - min_intensity + 1e-9)
    sigma = max(1.0, width / 1800.0)
    darkness_smooth = cv.GaussianBlur(darkness.reshape(1, -1), (0, 0), sigma * 1.5).reshape(-1)

    left, right = _detect_plateau_bounds(darkness_smooth, width, plateau_threshold=0.5)

    src = np.float32([[left, 0], [right, 0], [right, height - 1], [left, height - 1]])
    dst_w = int(max(1, right - left))
    dst = np.float32([[0, 0], [dst_w - 1, 0], [dst_w - 1, height - 1], [0, height - 1]])
    M = cv.getPerspectiveTransform(src, dst)

    rect_color = cv.warpPerspective(color, M, (dst_w, height), flags=cv.INTER_LINEAR)
    rect_gray = cv.warpPerspective(enhanced_gray, M, (dst_w, height), flags=cv.INTER_LINEAR)

    return rect_color, rect_gray, (int(left), int(right))


def _localize_vertical_bounds(
    rect_gray: np.ndarray,
) -> Tuple[int, int]:
    h, w = rect_gray.shape
    if h == 0:
        return 0, 0

    blur_sigma = max(1.0, min(h, w) / 1500.0)
    blurred = cv.GaussianBlur(rect_gray, (0, 0), blur_sigma)

    strip_w = max(10, w // 12)
    left_strip = blurred[:, :strip_w]
    right_strip = blurred[:, w - strip_w :]

    up_l, down_l = _sobel_profiles(left_strip, axis=0)
    up_r, down_r = _sobel_profiles(right_strip, axis=0)

    smoothing = max(5, h // 200)
    up_l = _smooth_sequence(up_l, smoothing)
    down_l = _smooth_sequence(down_l, smoothing)
    up_r = _smooth_sequence(up_r, smoothing)
    down_r = _smooth_sequence(down_r, smoothing)

    bottom_l = int(np.argmax(down_l))
    bottom_r = int(np.argmax(down_r))

    peaks_l = _local_maxima(up_l)
    peaks_r = _local_maxima(up_r)

    def pick_top(peaks, up_s, bottom_idx):
        cand = [p for p in peaks if 0 < bottom_idx - p <= max(h // 4, 400)]
        if not cand and bottom_idx > 0:
            cand = [int(np.argmax(up_s[:bottom_idx]))]
        return int(max(cand, key=lambda i: up_s[i])) if cand else max(0, bottom_idx - h // 10)

    top_l = pick_top(peaks_l, up_l, bottom_l)
    top_r = pick_top(peaks_r, up_r, bottom_r)

    top = int(round((top_l + top_r) / 2.0))
    bottom = int(round((bottom_l + bottom_r) / 2.0))

    top = max(0, min(top, h - 2))
    bottom = max(top + 1, min(bottom, h))
    return top, bottom


def _localize_horizontal_bounds(
    enhanced_gray: np.ndarray,
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

    max_intensity = float(smoothed.max())
    min_intensity = float(smoothed.min())
    neg_intensity_raw = max_intensity - smoothed
    neg_intensity = neg_intensity_raw / (max_intensity - min_intensity + 1e-9)

    win_pre = max(21, int(width / 300))
    if win_pre % 2 == 0:
        win_pre += 1
    kernel_pre = np.ones(win_pre, dtype=np.float64) / win_pre
    ni_smooth = np.convolve(neg_intensity, kernel_pre, mode="same")

    win_bg = max(win_pre * 3, int(width / 40))
    if win_bg % 2 == 0:
        win_bg += 1
    kernel_bg = np.ones(win_bg, dtype=np.float64) / win_bg
    ni_mean = np.convolve(ni_smooth, kernel_bg, mode="same")
    ni_sq_mean = np.convolve(ni_smooth * ni_smooth, kernel_bg, mode="same")
    ni_var = np.maximum(0.0, ni_sq_mean - ni_mean * ni_mean)
    ni_std = np.sqrt(ni_var + 1e-9)
    k_std = 0.9
    ni_mask = ni_smooth > (ni_mean + k_std * ni_std)

    g1 = np.gradient(ni_smooth)
    center_idx = int(width // 2)
    n = width

    if g1.size >= 3:
        pos_peaks = np.where((g1[1:-1] > g1[:-2]) & (g1[1:-1] > g1[2:]))[0] + 1
        neg_peaks = np.where((g1[1:-1] < g1[:-2]) & (g1[1:-1] < g1[2:]))[0] + 1
    else:
        pos_peaks = np.array([], dtype=np.int32)
        neg_peaks = np.array([], dtype=np.int32)

    def thresholded_from_center(deriv: np.ndarray, center: int) -> tuple[int, int]:
        an_l, an_r = -1, -1
        left_idx = pos_peaks[pos_peaks < center]
        if left_idx.size:
            left_max = float(deriv[left_idx].max())
            thr_l = 0.2 * left_max
            left_set = set(int(i) for i in left_idx.tolist())
            for i in range(center - 1, 1, -1):
                if i in left_set and deriv[i] >= thr_l:
                    an_l = i
                    break

        right_idx = neg_peaks[neg_peaks > center]
        if right_idx.size:
            right_max = float((-deriv[right_idx]).max())
            thr_r = 0.2 * right_max
            right_set = set(int(i) for i in right_idx.tolist())
            for i in range(center + 1, n - 1):
                if i in right_set and (-deriv[i]) >= thr_r:
                    an_r = i
                    break
        return an_l, an_r

    an_left, an_right = thresholded_from_center(g1, center_idx)

    if an_left == -1 or an_right == -1:
        m = ni_mask.astype(np.int32)
        trans = np.diff(np.concatenate(([0], m, [0])))
        starts = np.where(trans == 1)[0]
        ends = np.where(trans == -1)[0] - 1
        run_lengths = ends - starts + 1
        min_run = max(30, int(0.04 * n))
        valid = run_lengths >= min_run
        starts = starts[valid]
        ends = ends[valid]

        if an_left == -1:
            left_runs = ends < center_idx
            if np.any(left_runs):
                le = ends[left_runs]
                ls = starts[left_runs]
                li = int(np.argmin(center_idx - le))
                rs_l = int(ls[li])
                re_l = int(le[li])
                rel = int(np.argmax(g1[rs_l : re_l + 1]))
                an_left = rs_l + rel
            else:
                lo = 1
                hi = max(2, center_idx)
                rel = int(np.argmax(g1[lo:hi])) if hi > lo else 1
                an_left = lo + rel

        if an_right == -1:
            right_runs = starts > center_idx
            if np.any(right_runs):
                rs = starts[right_runs]
                re = ends[right_runs]
                ri = int(np.argmin(rs - center_idx))
                rs_r = int(rs[ri])
                re_r = int(re[ri])
                rel = int(np.argmin(g1[rs_r : re_r + 1]))
                an_right = rs_r + rel
            else:
                lo = min(center_idx, n - 2)
                hi = n - 1
                rel = int(np.argmin(g1[lo:hi])) if hi > lo else n - 2
                an_right = lo + rel

    left = int(max(0, min(an_left, width - 2)))
    right = int(max(left + 1, min(an_right, width - 1)))
    if right <= left:
        right = min(width - 1, max(left + 1, center_idx + max(20, width // 100)))

    return left, right


def detect_bbox(work_color: np.ndarray, work_gray: np.ndarray, percentile: float) -> BoundingBox:
    top, bottom = _localize_vertical_bounds(work_gray)
    left, right = _localize_horizontal_bounds(work_gray, top, bottom)

    height, width = work_gray.shape
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
) -> Tuple[BoundingBox, str, int]:
    input_path = Path(input)
    color = cv.imread(str(input_path), cv.IMREAD_COLOR)
    if color is None:
        raise FileNotFoundError(f"unable to read image: {input_path}")

    gray = cv.cvtColor(color, cv.COLOR_BGR2GRAY)
    enhanced_gray = _preprocess(gray)
    rect_color, rect_gray, plateau_bounds = _enhance_by_plateau(color, enhanced_gray)

    bbox = detect_bbox(rect_color, rect_gray, percentile)

    plateau_left = int(plateau_bounds[0])
    global_bbox = BoundingBox(
        top=bbox.top,
        bottom=bbox.bottom,
        left=int(plateau_left + bbox.left),
        right=int(plateau_left + bbox.right),
    )

    annotated = draw_bbox(color, global_bbox, bbox_color, bbox_thickness)

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
    plateau_width = int(plateau_bounds[1] - plateau_bounds[0])
    return global_bbox, time, plateau_width


def _process_wrapper(args):
    f, input_path, output_path, cfg = args
    box, time, pwidth = process_image(input_path, output_path, cfg)
    return box, time, pwidth


def process_image_wrapper(args):
    input_path, output_path, percentile, bbox_color, bbox_thickness, f = args
    box, time, pwidth = process_image(input_path, output_path, percentile, bbox_color, bbox_thickness)
    return (box, time, pwidth), f


if __name__ == "__main__":
    cfg = Config().parse()
    ret = []
    files = sorted(os.listdir(cfg.input))
    if cfg.workers == 0:
        for f in tqdm(files, total=len(files), desc="Processing images"):
            box, time, pwidth = process_image(
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
                    "plateau_width": box.width / pwidth * cfg.plateau_width,
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
            for (box, time, pwidth), f in results:
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
                        "plateau_width": box.width / pwidth * cfg.plateau_width,
                    }
                )
    df = pd.DataFrame(ret)
    df.to_csv(cfg.table, index=False)
    print(f"saved table -> {cfg.table}")
