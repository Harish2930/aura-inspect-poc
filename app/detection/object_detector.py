"""
Phase 1: passthrough — the whole frame is treated as the component crop.
Phase 2: replace `detect_and_crop` internals with a YOLO model call that
returns bounding boxes, then crop to the highest-confidence detection.

Kept as its own module so inspection_service.py never has to change when
YOLO is added — only this file does.
"""
from __future__ import annotations

import numpy as np


class Detection:
    def __init__(self, bbox: tuple[int, int, int, int], confidence: float, label: str = "component"):
        self.bbox = bbox  # (x, y, w, h)
        self.confidence = confidence
        self.label = label


def detect_and_crop(frame: np.ndarray) -> tuple[np.ndarray, Detection | None]:
    """
    Phase 1 behavior: no real detection, returns the full frame plus a
    synthetic full-frame Detection so downstream code has a consistent
    interface once Phase 2 (YOLO) is wired in.
    """
    h, w = frame.shape[:2]
    detection = Detection(bbox=(0, 0, w, h), confidence=1.0, label="component")
    return frame, detection


# --- Phase 2 sketch (not active) --------------------------------------------
# from ultralytics import YOLO
#
# _model = None
#
# def _get_model(weights_path: str = "yolov8n.pt"):
#     global _model
#     if _model is None:
#         _model = YOLO(weights_path)
#     return _model
#
# def detect_and_crop_yolo(frame: np.ndarray, weights_path: str = "yolov8n.pt"):
#     model = _get_model(weights_path)
#     results = model(frame, verbose=False)[0]
#     if len(results.boxes) == 0:
#         return frame, None
#     box = max(results.boxes, key=lambda b: float(b.conf))
#     x1, y1, x2, y2 = map(int, box.xyxy[0])
#     crop = frame[y1:y2, x1:x2]
#     detection = Detection(bbox=(x1, y1, x2 - x1, y2 - y1), confidence=float(box.conf), label="component")
#     return crop, detection
