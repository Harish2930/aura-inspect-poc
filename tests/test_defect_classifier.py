import pytest

from app.config import AppConfig
from app.inspection.defect_classifier import ValidationError, validate_and_build

CONFIG = AppConfig.load()  # uses config/inspection.yaml


def test_valid_defective_response_builds_result():
    raw = {
        "component": "ALUMINIUM_DIE_CAST_PART",
        "condition": "DEFECTIVE",
        "defect": "SCRATCH",
        "severity": "MEDIUM",
        "location": "TOP_SURFACE",
        "reason": "Visible linear mark on top surface.",
        "confidence": 0.91,
    }
    result = validate_and_build(raw, CONFIG)
    assert result.condition == "DEFECTIVE"
    assert result.defect == "SCRATCH"
    assert result.confidence == 0.91


def test_unknown_defect_falls_back_to_other():
    raw = {
        "component": "ALUMINIUM_DIE_CAST_PART",
        "condition": "DEFECTIVE",
        "defect": "WEIRD_UNLISTED_THING",
        "severity": "LOW",
        "location": "SIDE",
        "reason": "Something odd.",
        "confidence": 0.8,
    }
    result = validate_and_build(raw, CONFIG)
    assert result.defect == "OTHER"


def test_low_confidence_downgrades_to_uncertain():
    raw = {
        "component": "ALUMINIUM_DIE_CAST_PART",
        "condition": "DEFECTIVE",
        "defect": "DENT",
        "severity": "HIGH",
        "location": "EDGE",
        "reason": "Possible dent.",
        "confidence": 0.4,  # below default threshold of 0.75
    }
    result = validate_and_build(raw, CONFIG)
    assert result.condition == "UNCERTAIN"
    assert result.defect is None


def test_invalid_condition_raises():
    raw = {
        "component": "ALUMINIUM_DIE_CAST_PART",
        "condition": "BROKEN",  # not in config
        "reason": "n/a",
        "confidence": 0.9,
    }
    with pytest.raises(ValidationError):
        validate_and_build(raw, CONFIG)
