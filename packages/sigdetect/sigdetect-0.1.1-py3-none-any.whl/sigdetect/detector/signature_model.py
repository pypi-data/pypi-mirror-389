"""Signature model returned by detection engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Signature:
    """Metadata describing a detected signature field."""

    Page: int | None
    FieldName: str
    Role: str
    Score: int
    Scores: dict[str, int]
    Evidence: list[str]
    Hint: str
    RenderType: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Return the legacy snake_case representation used in JSON payloads."""

        return {
            "page": self.Page,
            "field_name": self.FieldName,
            "role": self.Role,
            "score": self.Score,
            "scores": self.Scores,
            "evidence": list(self.Evidence),
            "hint": self.Hint,
            "render_type": self.RenderType,
        }
