"""
Cheap, fast, local quality checks that run BEFORE we ever call the AI model.
If the image fails here, we return UNCERTAIN without spending an API call —
this directly satisfies the "poor lighting / blur / partial visibility ->
UNCERTAIN" requirement (section 2, test cases 6-8) and the cost-control
requirement in section 18 ("do not call the AI API for every webcam frame").
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class QualityReport:
    passed: bool
    sharpness: float
    mean_brightness: float
    width: int
    height: int
    reasons: list[str]


def _laplacian_variance(gray: np.ndarray) -> float:
    """Higher variance = sharper image. Standard cheap blur detector."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def check_image_quality(
    image: np.ndarray,
    min_laplacian_variance: float = 80.0,
    min_mean_brightness: float = 40,
    max_mean_brightness: float = 235,
    min_resolution_px: int = 224,
) -> QualityReport:
    """
    image: BGR numpy array as read by OpenCV.
    Returns a QualityReport; check .passed before proceeding to AI inspection.
    """
    if image is None or image.size == 0:
        return QualityReport(False, 0.0, 0.0, 0, 0, ["Image is empty or unreadable."])

    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    sharpness = _laplacian_variance(gray)
    brightness = float(gray.mean())

    reasons: list[str] = []

    if min(width, height) < min_resolution_px:
        reasons.append(
            f"Resolution too low ({width}x{height}); need at least {min_resolution_px}px on the short side."
        )
    if sharpness < min_laplacian_variance:
        reasons.append(f"Image appears blurry (sharpness={sharpness:.1f}, min={min_laplacian_variance}).")
    if brightness < min_mean_brightness:
        reasons.append(f"Image too dark (brightness={brightness:.1f}, min={min_mean_brightness}).")
    if brightness > max_mean_brightness:
        reasons.append(f"Image too bright / blown out (brightness={brightness:.1f}, max={max_mean_brightness}).")

    return QualityReport(
        passed=len(reasons) == 0,
        sharpness=sharpness,
        mean_brightness=brightness,
        width=width,
        height=height,
        reasons=reasons,
    )
