"""
Loads config/inspection.yaml once and exposes it as a simple object.
This is the single source of truth for client/product/defect config,
so the inspection engine never hard-codes Alubee-specific logic.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "inspection.yaml"


@dataclass
class AppConfig:
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path = DEFAULT_CONFIG_PATH) -> "AppConfig":
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(raw=data)

    # --- convenience accessors -------------------------------------------------
    @property
    def client_name(self) -> str:
        return self.raw["client"]["name"]

    @property
    def component_label(self) -> str:
        return self.raw["product"]["component_label"]

    @property
    def conditions(self) -> list[str]:
        return self.raw["inspection"]["conditions"]

    @property
    def defects(self) -> list[str]:
        return self.raw["defects"]

    @property
    def severities(self) -> list[str]:
        return self.raw["severity"]

    @property
    def confidence_threshold(self) -> float:
        return float(self.raw["confidence_threshold"])

    @property
    def quality(self) -> dict[str, Any]:
        return self.raw["quality"]

    @property
    def camera(self) -> dict[str, Any]:
        return self.raw["camera"]

    @property
    def ai(self) -> dict[str, Any]:
        return self.raw["ai"]

    @property
    def db_path(self) -> str:
        return self.raw["database"]["path"]

    @property
    def image_dir(self) -> str:
        return self.raw["storage"]["image_dir"]


def get_config() -> AppConfig:
    """Load config once per process call site. Cheap enough to not bother caching globally."""
    return AppConfig.load()
