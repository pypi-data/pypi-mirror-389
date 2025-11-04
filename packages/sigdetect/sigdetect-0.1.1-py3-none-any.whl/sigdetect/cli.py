"""Command line interface for the signature detection tool."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

import typer

from . import __version__
from .config import LoadConfiguration
from .detector import BuildDetector
from .eda import RunExploratoryAnalysis
from .logging_setup import ConfigureLogging

Logger = ConfigureLogging()

CliApplication = typer.Typer(help="Signature detection & role attribution for PDFs")


def _JsonSerializer(candidate):
    """Ensure dataclasses and paths remain JSON serialisable."""

    if hasattr(candidate, "to_dict"):
        return candidate.to_dict()
    if is_dataclass(candidate):
        return asdict(candidate)
    if isinstance(candidate, Path):
        return str(candidate)
    return str(candidate)


@CliApplication.command(name="detect")
def Detect(
    configurationPath: Path | None = typer.Option(
        None, "--config", "-c", help="Path to YAML config"
    ),
    profileOverride: str | None = typer.Option(None, "--profile", "-p", help="hipaa or retainer"),
) -> None:
    """Run detection for the configured directory and emit ``results.json``."""

    configuration = LoadConfiguration(configurationPath)
    if profileOverride in {"hipaa", "retainer"}:
        configuration = configuration.model_copy(update={"Profile": profileOverride})

    try:
        detector = BuildDetector(configuration)
    except ValueError as exc:
        Logger.error(
            "Detector initialisation failed",
            extra={"engine": configuration.Engine, "error": str(exc)},
        )
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    pdfFiles = list(configuration.PdfRoot.glob("*.pdf"))
    if not pdfFiles:
        raise SystemExit(f"No PDFs found in {configuration.PdfRoot}")

    results = [detector.Detect(pdfPath) for pdfPath in pdfFiles]

    # Allow configuration to suppress file output entirely (out_dir: none / SIGDETECT_OUT_DIR=none)
    if configuration.OutputDirectory is None:
        payload = json.dumps(results, indent=2, ensure_ascii=False, default=_JsonSerializer)
        typer.echo(payload)
        typer.echo("Detection completed with output disabled (out_dir=none)")
        return

    outputDirectory = configuration.OutputDirectory
    outputDirectory.mkdir(parents=True, exist_ok=True)

    with open(outputDirectory / "results.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False, default=_JsonSerializer)

    typer.echo(f"Wrote {outputDirectory / 'results.json'}")


@CliApplication.command(name="eda")
def ExploratoryAnalysis(
    configurationPath: Path | None = typer.Option(
        None, "--config", "-c", help="Path to YAML config"
    ),
) -> None:
    """Generate a compact exploratory summary for the dataset."""

    configuration = LoadConfiguration(configurationPath)
    RunExploratoryAnalysis(configuration)


@CliApplication.command(name="version")
def Version() -> None:
    """Print the installed package version."""

    typer.echo(__version__)


app = CliApplication
