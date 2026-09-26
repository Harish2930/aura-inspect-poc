"""
Structured inspection result. Mirrors the JSON contract in the assignment
doc (section 9) plus the SQLite history schema (section 15).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class InspectionResult(BaseModel):
    inspection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    component: str
    condition: str          # GOOD | DEFECTIVE | UNCERTAIN
    defect: Optional[str] = None
    severity: Optional[str] = None
    location: Optional[str] = None
    reason: str
    confidence: float

    image_path: Optional[str] = None

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"confidence must be between 0 and 1, got {v}")
        return v

    def to_row(self) -> dict:
        """Flat dict for SQLite insertion."""
        return {
            "inspection_id": self.inspection_id,
            "timestamp": self.timestamp,
            "component": self.component,
            "condition": self.condition,
            "defect": self.defect,
            "severity": self.severity,
            "location": self.location,
            "confidence": self.confidence,
            "reason": self.reason,
            "image_path": self.image_path,
        }
