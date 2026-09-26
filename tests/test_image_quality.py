import numpy as np

from app.processing.image_quality import check_image_quality


def test_blank_dark_image_fails_quality():
    img = np.zeros((300, 300, 3), dtype=np.uint8)  # solid black
    report = check_image_quality(img)
    assert report.passed is False
    assert any("dark" in r for r in report.reasons)


def test_small_image_fails_resolution():
    img = np.random.randint(100, 200, (50, 50, 3), dtype=np.uint8)
    report = check_image_quality(img, min_resolution_px=224)
    assert report.passed is False
    assert any("Resolution" in r for r in report.reasons)


def test_reasonable_textured_image_can_pass():
    rng = np.random.default_rng(42)
    # Mid-brightness noisy image simulates a textured, well-lit surface.
    img = rng.integers(90, 170, (400, 400, 3), dtype=np.uint8)
    report = check_image_quality(img)
    assert report.passed is True
    assert report.width == 400 and report.height == 400
