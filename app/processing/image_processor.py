"""
Small helpers for preparing an image before it's sent to the vision model
or written to disk. Kept separate from image_quality.py so the "is this
image good enough" logic and the "reshape/encode this image" logic don't
get tangled together.
"""
from __future__ import annotations

import base64
from pathlib import Path

import cv2
import numpy as np


def resize_max_dim(image: np.ndarray, max_dim: int = 1024) -> np.ndarray:
    """Downscale large images before sending to the AI model (keeps payloads small/cheap)."""
    h, w = image.shape[:2]
    scale = max_dim / max(h, w)
    if scale >= 1.0:
        return image
    return cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def encode_image_base64(image: np.ndarray, ext: str = ".jpg") -> tuple[str, str]:
    """Returns (base64_string, media_type) for the given BGR image."""
    ok, buf = cv2.imencode(ext, image)
    if not ok:
        raise ValueError(f"Failed to encode image as {ext}")
    media_type = "image/jpeg" if ext.lower() in (".jpg", ".jpeg") else "image/png"
    return base64.b64encode(buf.tobytes()).decode("utf-8"), media_type


def save_image(image: np.ndarray, directory: str | Path, filename: str) -> str:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    cv2.imwrite(str(path), image)
    return str(path)
