"""
Wraps calls to a vision-capable AI model. Provider-agnostic on purpose:
config/inspection.yaml -> ai.provider selects anthropic | openai | gemini,
so swapping models doesn't touch any other module.

The prompt itself is built from AppConfig (client/product/defects), NOT
hard-coded, per the "configuration-driven design" requirement (section 8).
"""
from __future__ import annotations

import json
import os
from typing import Any

from app.config import AppConfig


class AIClientError(RuntimeError):
    pass


def build_inspection_prompt(config: AppConfig) -> str:
    defects = "\n".join(f"- {d}" for d in config.defects)
    conditions = " / ".join(config.conditions)
    severities = " / ".join(config.severities)

    product_name = config.raw["product"]["name"]

    return f"""You are an AI visual quality inspection assistant for {config.client_name}'s
{product_name}.

Analyze the provided component image.

Determine whether the component appears:
{chr(10).join(f"- {c}" for c in config.conditions)}

If DEFECTIVE:
1. Identify the visible defect.
2. Identify the approximate defect location.
3. Estimate severity: {severities}.
4. Explain the visible evidence.
5. Provide confidence.

Possible defect types:
{defects}

Rules:
- Report only defects visually supported by the image.
- Do not infer internal defects (e.g. internal porosity).
- If image quality is poor, return UNCERTAIN.
- If the component is partially hidden, return UNCERTAIN.
- Return ONLY valid JSON, no markdown fences, no commentary, matching this schema:

{{
  "component": "{config.component_label}",
  "condition": "{conditions}",
  "defect": "<one of the defect types above, or null>",
  "severity": "<{severities}, or null>",
  "location": "<short location string, e.g. TOP_SURFACE, or null>",
  "reason": "<short explanation of visible evidence>",
  "confidence": <float between 0 and 1>
}}
"""


# def _call_anthropic(image_b64: str, media_type: str, prompt: str, config: AppConfig) -> str:
#     import anthropic

#     client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
#     resp = client.messages.create(
#         model=config.ai.get("model", "claude-sonnet-4-6"),
#         max_tokens=config.ai.get("max_tokens", 1000),
#         temperature=config.ai.get("temperature", 0.0),
#         messages=[
#             {
#                 "role": "user",
#                 "content": [
#                     {
#                         "type": "image",
#                         "source": {"type": "base64", "media_type": media_type, "data": image_b64},
#                     },
#                     {"type": "text", "text": prompt},
#                 ],
#             }
#         ],
#     )
#     text_blocks = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
#     return "\n".join(text_blocks)


# def _call_openai(image_b64: str, media_type: str, prompt: str, config: AppConfig) -> str:
#     from openai import OpenAI

#     client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
#     resp = client.chat.completions.create(
#         model=config.ai.get("model", "gpt-4o"),
#         temperature=config.ai.get("temperature", 0.0),
#         max_tokens=config.ai.get("max_tokens", 1000),
#         messages=[
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": prompt},
#                     {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}},
#                 ],
#             }
#         ],
#     )
#     return resp.choices[0].message.content or ""


def _call_gemini(image_b64: str, media_type: str, prompt: str, config: AppConfig) -> str:
    import google.generativeai as genai
    print(f"Calling Gemini model {config.ai.get('model', 'gemini-3.8-flash')}...")
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    model = genai.GenerativeModel(config.ai.get("model", "gemini-3.8-flash"))
    resp = model.generate_content(
        [
            {"mime_type": media_type, "data": image_b64},
            prompt,
        ]
    )
    return resp.text


_PROVIDERS = {
    # "anthropic": _call_anthropic,
    # "openai": _call_openai,
    "gemini": _call_gemini,
}


def inspect_image(image_b64: str, media_type: str, config: AppConfig) -> dict[str, Any]:
    """
    Sends the image + prompt to the configured provider and returns the
    PARSED JSON dict. Raises AIClientError on transport or parse failure —
    callers should catch this and fall back to an UNCERTAIN result rather
    than crashing the app.
    """
    print(f"Inspecting image with provider {config.ai.get('provider', 'gemini')}...")
    provider = config.ai.get("provider", "gemini")
    call_fn = _PROVIDERS.get(provider)
    if call_fn is None:
        raise AIClientError(f"Unknown ai.provider '{provider}' in config. Choose from: {list(_PROVIDERS)}")

    prompt = build_inspection_prompt(config)

    try:
        raw_text = call_fn(image_b64, media_type, prompt, config)
    except Exception as exc:  # noqa: BLE001 - surfacing as a domain error
        raise AIClientError(f"AI provider '{provider}' call failed: {exc}") from exc

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Strip accidental markdown fences even though the prompt forbids them.
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIClientError(f"Model did not return valid JSON. Raw response: {raw_text!r}") from exc
