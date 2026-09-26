# AuraInspect — Alubee Die-Casting Visual Inspection POC

AI-assisted visual inspection for aluminium die-cast components. Captures/uploads
a component image, runs a local image-quality gate, sends the image to a
vision-capable AI model, validates the structured response against a
config-driven defect library, and classifies the component as
**GOOD**, **DEFECTIVE**, or **UNCERTAIN**.

This is a POC for visible surface inspection only — it does not infer internal
defects (e.g. porosity) from a normal camera image.

## Status

Implemented (Phase 1–3 of the build plan):
- Image quality gate (blur / brightness / resolution) — runs before any AI call
- AI vision client (Anthropic / OpenAI / Gemini — pick one via config)
- JSON schema validation + confidence-threshold downgrade logic
- SQLite inspection history
- Streamlit demo UI (upload or webcam snapshot)
- Bare OpenCV live-capture loop (dev/debug)

Not yet implemented (Phase 2, optional per the assignment):
- YOLO-based component detection/cropping — currently a passthrough stub in
  `app/detection/object_detector.py`, ready to be swapped in.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and add the API key for whichever provider you're using
```

By default the config (`config/inspection.yaml`) is set to `ai.provider: anthropic`.
To use OpenAI or Gemini instead, change `ai.provider` and `ai.model` in that file,
and uncomment the matching package in `requirements.txt`.

## Run

**Demo UI (recommended):**
```bash
streamlit run main.py
```
Upload an image or take a webcam snapshot, click **Run Inspection**, then
**Save Inspection** to persist it to SQLite. Inspection history is shown at
the bottom of the page.

**Bare OpenCV live-capture loop** (no UI, prints results to console):
```bash
python main.py --live
```
Press **SPACE** to trigger an inspection on the current frame, **Q** to quit.
(This deliberately does *not* call the AI on every frame — see section 18 of
the assignment doc on cost control.)

**Run tests:**
```bash
pytest tests/ -v
```
The current test suite covers image quality checks, JSON validation/threshold
logic, and SQLite persistence — all without needing an API key. There is
no automated test for the live AI call itself; verify that manually against
real images (see "Building the dataset" below).

## Project structure

```
aura-inspect/
├── app/
│   ├── camera/webcam.py                  # OpenCV capture
│   ├── detection/object_detector.py      # Phase 1 passthrough / Phase 2 YOLO hook
│   ├── inspection/ai_client.py           # Vision AI call + prompt builder
│   ├── inspection/inspection_service.py  # Orchestrates the full pipeline
│   ├── inspection/defect_classifier.py   # JSON validation + threshold logic
│   ├── processing/image_processor.py     # Resize/encode helpers
│   ├── processing/image_quality.py       # Blur/brightness/resolution gate
│   ├── models/inspection_result.py       # Pydantic result model
│   ├── database/inspection_repository.py # SQLite persistence
│   └── ui/inspection_ui.py               # Streamlit UI
├── dataset/                              # Labelled images, one folder per class
├── tests/                                # pytest unit tests
├── config/inspection.yaml                # Client/product/defect config (no hard-coding)
├── .env.example
├── requirements.txt
├── main.py                               # Entry point (streamlit run main.py)
└── README.md
```

## Configuration-driven design

`config/inspection.yaml` defines the client name, product name, condition
labels, defect library, severity levels, and confidence threshold. The
inspection prompt is *built from this file* (see
`app/inspection/ai_client.py: build_inspection_prompt`), so retargeting
AuraInspect at a different client/product means editing this one YAML file —
no code changes required.

## Building the dataset

Add labelled images under `dataset/<class>/`, e.g. `dataset/scratch/`,
`dataset/good/`, etc. (folders are pre-created, matching section 10 of the
assignment). Aim for ~20–50 images per category with varied angle, lighting,
and background. Do not mix uncertain/mislabelled images into `dataset/good/`.

Use these images to manually smoke-test each test case in the assignment's
test plan (good component, scratch, dent, flash, crack, poor lighting,
blur, partial visibility, unknown defect).

## Security notes

- API keys live in `.env` (gitignored), never in source or committed to Git.
- The AI is called once per user-triggered inspection, not once per frame.
- Inspection images are written to `dataset/_inspections/` (gitignored) —
  point this elsewhere via `storage.image_dir` in the config if needed.

## Next steps

1. Add your API key to `.env` and run `streamlit run main.py` against a few
   real (or stand-in) die-cast component photos to sanity-check the prompt
   and JSON output quality.
2. Start populating `dataset/` per the labelling guidance above.
3. Once the AI responses look reliable, revisit `confidence_threshold` in
   the config based on observed behavior.
4. If time allows, implement the YOLO hook in `object_detector.py` for
   Phase 2 component cropping.
