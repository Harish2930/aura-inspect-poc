"""
Simple OpenCV webcam wrapper. Deliberately NOT calling the AI on every
frame (section 18) — capture_still() is meant to be invoked on a user
trigger (keypress / button), not in a tight per-frame loop.
"""
from __future__ import annotations

import time

import cv2
import numpy as np


class Webcam:
    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self.cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        self.cap = cv2.VideoCapture(self.device_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera at index {self.device_index}")

    def read_frame(self) -> np.ndarray:
        if self.cap is None:
            self.open()
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("Failed to read frame from camera")
        return frame

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __enter__(self) -> "Webcam":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def run_live_capture_loop(
    on_trigger,
    device_index: int = 0,
    window_name: str = "AuraInspect - press SPACE to inspect, Q to quit",
) -> None:
    """
    Minimal live preview loop: shows the camera feed, calls on_trigger(frame)
    when SPACE is pressed. Intended for local/dev use; the Streamlit UI
    (app/ui/inspection_ui.py) is the primary demo interface.
    """
    with Webcam(device_index) as cam:
        while True:
            frame = cam.read_frame()
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord(" "):
                on_trigger(frame.copy())
                time.sleep(0.3)  # brief debounce
    cv2.destroyAllWindows()
