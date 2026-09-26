"""
Top-level orchestration matching the flow in section 3/5 of the assignment:
capture -> quality check -> (detect/crop) -> AI inspect -> validate -> result.

This is the function the UI (Streamlit or OpenCV overlay) and main.py call.
"""
from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np

from app.config import AppConfig, get_config
from app.inspection.ai_client import AIClientError, inspect_image
from app.inspection.defect_classifier import build_uncertain_result, validate_and_build
from app.models.inspection_result import InspectionResult
from app.processing.image_processor import encode_image_base64, resize_max_dim, save_image
from app.processing.image_quality import check_image_quality


def run_inspection(
    image: np.ndarray,
    config: AppConfig | None = None,
    save_to_disk: bool = True,
) -> InspectionResult:
    """
    image: BGR numpy array (already cropped to the component, if a detector is in use).
    Returns an InspectionResult. Never raises for expected failure modes
    (bad quality, AI error) — those become UNCERTAIN results instead.
    """
    config = config or get_config()

    image_path = None
    if save_to_disk:
        filename = f"{uuid.uuid4().hex}.jpg"
        image_path = save_image(image, config.image_dir, filename)

    # 1. Quality gate — cheap, local, no API cost.
    q = config.quality
    quality_report = check_image_quality(
        image,
        min_laplacian_variance=q["min_laplacian_variance"],
        min_mean_brightness=q["min_mean_brightness"],
        max_mean_brightness=q["max_mean_brightness"],
        min_resolution_px=q["min_resolution_px"],
    )
    if not quality_report.passed:
        reason = "Image quality insufficient for reliable inspection: " + "; ".join(quality_report.reasons)
        return build_uncertain_result(reason, config, image_path)

    # 2. Prepare + encode for the AI model.
    resized = resize_max_dim(image, max_dim=1024)
    image_b64, media_type = encode_image_base64(resized)

    # 3. AI inspection.
    try:
        raw = inspect_image(image_b64, media_type, config)
    except AIClientError as exc:
        return build_uncertain_result(f"AI inspection failed: {exc}", config, image_path)

    # 4. Validate + apply confidence-threshold / config-enum rules.
    try:
        result = validate_and_build(raw, config, image_path)
    except Exception as exc:  # noqa: BLE001
        return build_uncertain_result(f"AI response failed validation: {exc}", config, image_path)

    return result
