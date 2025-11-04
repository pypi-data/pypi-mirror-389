"""Configuration loading utilities for the signature detection service."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

EngineName = Literal["pypdf2", "pypdf", "pymupdf"]
ProfileName = Literal["hipaa", "retainer"]


class DetectConfiguration(BaseModel):
    """Runtime settings governing signature detection.

    The fields use PascalCase to comply with the CaseWorks standards while aliases keep
    compatibility with the existing YAML configuration keys and environment variables.
    """

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    PdfRoot: Path = Field(default=Path("hipaa_results"), alias="pdf_root")
    OutputDirectory: Path | None = Field(default=Path("out"), alias="out_dir")
    Engine: EngineName = Field(default="pypdf2", alias="engine")
    Profile: ProfileName = Field(default="hipaa", alias="profile")
    MaxWorkers: int = Field(default=8, alias="max_workers", ge=1, le=64)
    PseudoSignatures: bool = Field(default=True, alias="pseudo_signatures")
    RecurseXObjects: bool = Field(default=True, alias="recurse_xobjects")

    @field_validator("PdfRoot", "OutputDirectory", mode="before")
    @classmethod
    def _CoercePath(cls, value: str | Path | None) -> Path | None:
        """Allow configuration values to be provided as ``str`` or ``Path``.

        :param value: The candidate value from YAML or environment variables.
        :returns: ``Path`` instances (or ``None`` for optional directories).
        """

        if value is None:
            return None
        if isinstance(value, Path):
            return value
        return Path(value)

    # Expose legacy snake_case property names for gradual migration
    @property
    def pdf_root(self) -> Path:  # pragma: no cover - simple passthrough
        return self.PdfRoot

    @property
    def out_dir(self) -> Path | None:  # pragma: no cover - simple passthrough
        return self.OutputDirectory

    @property
    def engine(self) -> EngineName:  # pragma: no cover - simple passthrough
        return self.Engine

    @property
    def profile(self) -> ProfileName:  # pragma: no cover - simple passthrough
        return self.Profile

    @property
    def max_workers(self) -> int:  # pragma: no cover - simple passthrough
        return self.MaxWorkers

    @property
    def pseudo_signatures(self) -> bool:  # pragma: no cover - simple passthrough
        return self.PseudoSignatures

    @property
    def recurse_xobjects(self) -> bool:  # pragma: no cover - simple passthrough
        return self.RecurseXObjects


def LoadConfiguration(path: Path | None) -> DetectConfiguration:
    """Load configuration from ``path`` while applying environment overrides.

    Environment variables provide the final say and follow the existing naming:

    ``SIGDETECT_ENGINE``
        Override the PDF parsing engine.
    ``SIGDETECT_PDF_ROOT``
        Directory that will be scanned for PDF files.
    ``SIGDETECT_OUT_DIR``
        Output directory for generated artefacts. Use ``"none"`` to disable writes.
    ``SIGDETECT_PROFILE``
        Runtime profile that controls which heuristics are applied.
    """

    env_engine = os.getenv("SIGDETECT_ENGINE")
    env_pdf_root = os.getenv("SIGDETECT_PDF_ROOT")
    env_out_dir = os.getenv("SIGDETECT_OUT_DIR")
    env_profile = os.getenv("SIGDETECT_PROFILE")

    raw_data: dict[str, object] = {}
    if path and Path(path).exists():
        with open(path, encoding="utf-8") as handle:
            raw_data = yaml.safe_load(handle) or {}

    if env_engine:
        raw_data["engine"] = env_engine
    if env_pdf_root:
        raw_data["pdf_root"] = env_pdf_root
    if env_out_dir:
        raw_data["out_dir"] = None if env_out_dir.lower() == "none" else env_out_dir
    if env_profile in {"hipaa", "retainer"}:
        raw_data["profile"] = env_profile

    configuration = DetectConfiguration(**raw_data)

    if configuration.OutputDirectory is not None:
        configuration.OutputDirectory.mkdir(parents=True, exist_ok=True)

    return configuration
