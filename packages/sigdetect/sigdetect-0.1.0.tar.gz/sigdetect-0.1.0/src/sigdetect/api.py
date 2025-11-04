"""Public helpers for programmatic use of the signature detection engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Iterator, Literal

from sigdetect.config import DetectConfiguration
from sigdetect.detector import BuildDetector

EngineName = Literal["pypdf2", "pypdf", "pymupdf"]
ProfileName = Literal["hipaa", "retainer"]


def DetectPdf(
    pdfPath: str | Path,
    *,
    profileName: ProfileName = "hipaa",
    engineName: EngineName = "pypdf2",
    includePseudoSignatures: bool = True,
    recurseXObjects: bool = True,
) -> dict[str, Any]:
    """Detect signature evidence and assign roles for a single PDF."""

    resolvedPath = Path(pdfPath)

    configuration = DetectConfiguration(
        PdfRoot=resolvedPath.parent,
        OutputDirectory=None,
        Engine=engineName,
        PseudoSignatures=includePseudoSignatures,
        RecurseXObjects=recurseXObjects,
        Profile=profileName,
    )

    detector = BuildDetector(configuration)
    result = detector.Detect(resolvedPath)
    return _ToPlainDictionary(result)


def _ToPlainDictionary(candidate: Any) -> dict[str, Any]:
    """Convert pydantic/dataclass instances to plain dictionaries."""

    if hasattr(candidate, "to_dict"):
        return candidate.to_dict()
    if hasattr(candidate, "model_dump"):
        return candidate.model_dump()  # type: ignore[attr-defined]
    if hasattr(candidate, "dict"):
        return candidate.dict()  # type: ignore[attr-defined]
    try:
        from dataclasses import asdict, is_dataclass

        if is_dataclass(candidate):
            return asdict(candidate)
    except Exception:
        pass
    if isinstance(candidate, dict):
        return {key: _ToPlainValue(candidate[key]) for key in candidate}
    raise TypeError(f"Unsupported result type: {type(candidate)!r}")


def _ToPlainValue(value: Any) -> Any:
    """Best effort conversion for nested structures."""

    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "model_dump") or hasattr(value, "dict"):
        return _ToPlainDictionary(value)
    try:
        from dataclasses import asdict, is_dataclass

        if is_dataclass(value):
            return asdict(value)
    except Exception:
        pass
    if isinstance(value, list):
        return [_ToPlainValue(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_ToPlainValue(item) for item in value)
    if isinstance(value, dict):
        return {key: _ToPlainValue(result) for key, result in value.items()}
    return value


def DetectMany(
    pdfPaths: Iterable[str | Path],
    **kwargs: Any,
) -> Iterator[dict[str, Any]]:
    """Yield :func:`DetectPdf` results for each path in ``pdfPaths``."""

    for pdfPath in pdfPaths:
        yield DetectPdf(pdfPath, **kwargs)


def ScanDirectory(
    pdfRoot: str | Path,
    *,
    globPattern: str = "**/*.pdf",
    **kwargs: Any,
) -> Iterator[dict[str, Any]]:
    """Walk ``pdfRoot`` and yield detection output for every matching PDF."""

    rootDirectory = Path(pdfRoot)
    iterator = (
        rootDirectory.rglob(globPattern.replace("**/", "", 1))
        if globPattern.startswith("**/")
        else rootDirectory.glob(globPattern)
    )
    for pdfPath in iterator:
        if pdfPath.is_file() and pdfPath.suffix.lower() == ".pdf":
            yield DetectPdf(pdfPath, **kwargs)


def ToCsvRow(result: dict[str, Any]) -> dict[str, Any]:
    """Return a curated subset of keys suitable for CSV export."""

    return {
        "file": result.get("file"),
        "size_kb": result.get("size_kb"),
        "pages": result.get("pages"),
        "esign_found": result.get("esign_found"),
        "scanned_pdf": result.get("scanned_pdf"),
        "mixed": result.get("mixed"),
        "sig_count": result.get("sig_count"),
        "sig_pages": result.get("sig_pages"),
        "roles": result.get("roles"),
        "hints": result.get("hints"),
    }


def Version() -> str:
    """Expose the installed package version without importing the CLI stack."""

    try:
        from importlib.metadata import version as resolveVersion

        return resolveVersion("sigdetect")
    except Exception:
        return "0.0.0-dev"
