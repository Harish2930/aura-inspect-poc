"""
Entry point.

Demo UI (primary):      streamlit run main.py
Bare OpenCV live loop:  python main.py --live   (dev/debug, prints results to console)
"""
from __future__ import annotations

import sys


def run_live() -> None:
    from app.camera.webcam import run_live_capture_loop
    from app.config import get_config
    from app.inspection.inspection_service import run_inspection

    config = get_config()

    def on_trigger(frame):
        result = run_inspection(frame, config=config)
        print(
            f"[{result.condition}] defect={result.defect} severity={result.severity} "
            f"confidence={result.confidence:.2f} reason={result.reason}"
        )

    run_live_capture_loop(on_trigger, device_index=config.camera["device_index"])


if "--live" in sys.argv:
    run_live()
else:
    # streamlit run main.py executes this module top-to-bottom, so the UI
    # entry point is called directly here rather than gated in a
    # `if __name__ == "__main__"` block (Streamlit doesn't set __name__
    # to "__main__" the way a plain `python main.py` invocation does).
    from app.ui.inspection_ui import main as run_ui

    run_ui()
