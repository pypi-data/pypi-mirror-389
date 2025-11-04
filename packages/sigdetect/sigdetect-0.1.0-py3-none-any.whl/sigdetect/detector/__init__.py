"""Detector exports and factory helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Type

from .base_detector import Detector
from .file_result_model import FileResult
from .pypdf2_engine import PyPDF2Detector
from .signature_model import Signature

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sigdetect.config import DetectConfiguration


ENGINE_REGISTRY: dict[str, Type[Detector]] = {
    PyPDF2Detector.Name: PyPDF2Detector,
}

# Accept modern engine alias alongside legacy configuration default.
ENGINE_REGISTRY.setdefault("pypdf", PyPDF2Detector)

try:  # pragma: no cover - optional dependency
    from .pymupdf_engine import PyMuPDFDetector  # type: ignore

    if getattr(PyMuPDFDetector, "Name", None):
        ENGINE_REGISTRY[PyMuPDFDetector.Name] = PyMuPDFDetector
except Exception:
    PyMuPDFDetector = None  # type: ignore


def BuildDetector(configuration: DetectConfiguration) -> Detector:
    """Instantiate the configured engine or raise a clear error."""

    engine_name = (
        getattr(configuration, "Engine", None)
        or getattr(configuration, "engine", None)
        or PyPDF2Detector.Name
    )
    normalized = engine_name.lower()

    detector_cls = ENGINE_REGISTRY.get(normalized)
    if detector_cls is None:
        available = ", ".join(sorted(ENGINE_REGISTRY)) or "<none>"
        raise ValueError(f"Unsupported engine '{engine_name}'. Available engines: {available}")
    return detector_cls(configuration)


__all__ = [
    "BuildDetector",
    "Detector",
    "ENGINE_REGISTRY",
    "FileResult",
    "Signature",
]
