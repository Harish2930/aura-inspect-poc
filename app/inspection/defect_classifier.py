"""
Takes the raw dict returned by ai_client.inspect_image() and turns it into
a validated InspectionResult. This is where config-driven enum checking and
the confidence_threshold rule live — NOT in ai_client, so the AI wrapper
stays a dumb transport layer and this module stays swappable/testable.
"""
from __future__ import annotations

from app.config import AppConfig
from app.models.inspection_result import InspectionResult


class ValidationError(ValueError):
    pass


def validate_and_build(raw: dict, config: AppConfig, image_path: str | None = None) -> InspectionResult:
    condition = raw.get("condition")
    if condition not in config.conditions:
        raise ValidationError(f"Unknown condition '{condition}', expected one of {config.conditions}")

    defect = raw.get("defect")
    if defect is not None and defect not in config.defects:
        # Model hallucinated a defect type outside our library -> fall back to OTHER
        # rather than hard-failing, since "OTHER" exists precisely for this case.
        defect = "OTHER"

    severity = raw.get("severity")
    if severity is not None and severity not in config.severities:
        severity = None

    confidence = float(raw.get("confidence", 0.0))

    # Enforce the confidence_threshold rule (section 8 / success criteria):
    # a low-confidence DEFECTIVE/GOOD call should be downgraded to UNCERTAIN
    # rather than reported as a confident classification.
    if condition != "UNCERTAIN" and confidence < config.confidence_threshold:
        condition = "UNCERTAIN"
        reason = (
            f"{raw.get('reason', '').strip()} "
            f"[Downgraded to UNCERTAIN: confidence {confidence:.2f} below threshold "
            f"{config.confidence_threshold:.2f}]"
        ).strip()
        defect, severity, location = None, None, None
    else:
        reason = raw.get("reason", "")
        location = raw.get("location")

    return InspectionResult(
        component=raw.get("component", config.component_label),
        condition=condition,
        defect=defect,
        severity=severity,
        location=location,
        reason=reason,
        confidence=confidence,
        image_path=image_path,
    )


def build_uncertain_result(reason: str, config: AppConfig, image_path: str | None = None) -> InspectionResult:
    """Used when image quality fails or the AI call itself errors out — never crash the app."""
    return InspectionResult(
        component=config.component_label,
        condition="UNCERTAIN",
        defect=None,
        severity=None,
        location=None,
        reason=reason,
        confidence=0.0,
        image_path=image_path,
    )
