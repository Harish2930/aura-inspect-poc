"""
Streamlit UI for AuraInspect. Run with:  streamlit run main.py

This is the primary demo interface — faster to iterate on than a full
OpenCV live-overlay window, and satisfies the "live inspection UI" /
"display result alongside image" requirements for the POC.
"""
from __future__ import annotations

import numpy as np
import streamlit as st
from PIL import Image

from app.config import get_config
from app.database.inspection_repository import InspectionRepository
from app.inspection.inspection_service import run_inspection

CONDITION_COLOR = {
    "GOOD": "green",
    "DEFECTIVE": "red",
    "UNCERTAIN": "orange",
}


def _pil_to_bgr(img: Image.Image) -> np.ndarray:
    import cv2
    rgb = np.array(img.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def main() -> None:
    st.set_page_config(page_title="AuraInspect — Alubee", layout="wide")
    config = get_config()
    repo = InspectionRepository(config.db_path)

    st.title(f"AuraInspect — {config.client_name}")
    st.caption(config.raw["product"]["name"] + " · Visible Surface Inspection POC")

    col_input, col_result = st.columns([1, 1])

    with col_input:
        st.subheader("Component Image")
        source = st.radio("Image source", ["Upload", "Camera"], horizontal=True)

        image = None
        if source == "Upload":
            uploaded = st.file_uploader("Upload a component image", type=["jpg", "jpeg", "png"])
            if uploaded is not None:
                image = Image.open(uploaded)
        else:
            snap = st.camera_input("Take a photo of the component")
            if snap is not None:
                image = Image.open(snap)

        if image is not None:
            st.image(image, caption="Component under inspection", width="stretch")

        run_clicked = st.button("Run Inspection", type="primary", disabled=image is None)

    with col_result:
        st.subheader("Inspection Result")

        if run_clicked and image is not None:
            with st.spinner("Inspecting..."):
                bgr = _pil_to_bgr(image)
                result = run_inspection(bgr, config=config)
            st.session_state["last_result"] = result

        result = st.session_state.get("last_result")
        if result is None:
            st.info("Run an inspection to see results here.")
        else:
            color = CONDITION_COLOR.get(result.condition, "gray")
            st.markdown(f"### :{color}[{result.condition}]")

            c1, c2 = st.columns(2)
            with c1:
                st.metric("Confidence", f"{result.confidence * 100:.0f}%")
                st.write("**Defect:**", result.defect or "—")
                st.write("**Severity:**", result.severity or "—")
            with c2:
                st.write("**Location:**", result.location or "—")
                st.write("**Component:**", result.component)

            st.write("**Reason:**", result.reason)

            if st.button("Save Inspection"):
                repo.save(result)
                st.success(f"Saved (inspection_id={result.inspection_id[:8]}...)")

    st.divider()
    st.subheader("Inspection History")
    history = repo.list_recent(limit=20)
    if history:
        st.dataframe(history, width="stretch", hide_index=True)
    else:
        st.caption("No inspections saved yet.")


if __name__ == "__main__":
    main()