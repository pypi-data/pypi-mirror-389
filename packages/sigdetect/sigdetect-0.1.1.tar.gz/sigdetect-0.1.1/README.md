# CaseWorks.Automation.CaseDocumentIntake

## sigdetect

`sigdetect` is a small Python library + CLI that detects **e-signature evidence** in PDFs and infers the **signer role** (e.g., _patient_, _attorney_, _representative_).

It looks for:

- Real signature **form fields** (`/Widget` annotations with `/FT /Sig`)
- **AcroForm** signature fields present only at the document level
- Common **vendor markers** (e.g., DocuSign, “Signature Certificate”)
- Page **labels** (like “Signature of Patient” or “Signature of Parent/Guardian”)

It returns a structured summary per file (pages, counts, roles, hints, etc.) that  can be used downstream.

---

## Contents

- [Quick start](#quick-start)
- [CLI usage](#cli-usage)
- [Library usage](#library-usage)
- [Result schema](#result-schema)
- [Configuration & rules](#configuration--rules)
- [Smoke tests](#smoke-tests)
- [Dev workflow](#dev-workflow)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Quick start

### Requirements

- Python **3.9+** (developed & tested on **3.11**)
- macOS / Linux / WSL

### Setup

~~~bash
# 1) Create and activate a virtualenv (example uses Python 3.11)
python3.11 -m venv .venv
source .venv/bin/activate

# 2) Install in editable (dev) mode
python -m pip install --upgrade pip
pip install -e .
~~~

### Sanity check

~~~bash
# Run unit & smoke tests
pytest -q
~~~

---

## CLI usage

The project ships a Typer-based CLI (exposed either as `sigdetect` or runnable via `python -m sigdetect.cli`, depending on how it is installed).

~~~bash
sigdetect --help
# or
python -m sigdetect.cli --help
~~~

### Detect (per-file summary)

~~~bash
# Execute detection according to the YAML configuration
sigdetect detect \
  --config ./sample_data/config.yml \
  --profile hipaa            # or: retainer
~~~

### Notes

- The config file controls `pdf_root`, `out_dir`, `engine`, `pseudo_signatures`, `recurse_xobjects`, etc.
- `--engine` supports **pypdf2** (default); a **pymupdf** engine placeholder exists and may be included in a future build.  
- `--pseudo-signatures` enables a vendor/Acro-only pseudo-signature when no actual `/Widget` is present (useful for DocuSign / Acrobat Sign receipts).  
- `--recurse-xobjects` allows scanning Form XObjects for vendor markers and labels embedded in page resources. 
- `--profile` selects tuned role logic:
  - `hipaa` → patient / representative / attorney
  - `retainer` → client / firm (prefers detecting two signatures)
- If the executable is not on `PATH`, you can always fall back to `python -m sigdetect.cli ...`.

### EDA (quick aggregate stats)

~~~bash
sigdetect eda \
  --config ./sample_data/config.yml

~~~

---

## Library usage

~~~python
from pathlib import Path
from sigdetect.config import DetectConfiguration
from sigdetect.detector.pypdf2_engine import PyPDF2Detector

configuration = DetectConfiguration(
    PdfRoot=Path("/path/to/pdfs"),
    OutputDirectory=Path("./out"),
    Engine="pypdf2",
    PseudoSignatures=True,
    RecurseXObjects=True,
    Profile="retainer",   # or "hipaa"
)

detector = PyPDF2Detector(configuration)
result = detector.Detect(Path("/path/to/pdfs/example.pdf"))
print(result.to_dict())
~~~

`Detect(Path)` returns a **FileResult** dataclass; call `.to_dict()` for the JSON-friendly representation (see [Result schema](#result-schema)).

---

## Library API (embed in another script)

Minimal, plug-and-play API
Import from `sigdetect.api` and get plain dicts out (JSON-ready), 
with no I/O side effects by default:

~~~python
from sigdetect.api import DetectPdf, DetectMany, ScanDirectory, ToCsvRow, Version

print("sigdetect", Version())

# 1) Single file → dict
result = DetectPdf(
    "/path/to/file.pdf",
    profileName="retainer",
    includePseudoSignatures=True,
    recurseXObjects=True,
)
print(
    result["file"],
    result["pages"],
    result["esign_found"],
    result["sig_count"],
    result["sig_pages"],
    result["roles"],
    result["hints"],
)


# 2) Directory walk (generator of dicts)
for res in ScanDirectory(
    "/path/to/pdfs",
    profileName="hipaa",
    includePseudoSignatures=True,
    recurseXObjects=True,
):
    # store in DB, print, etc.
    pass

~~~


## Result schema

High-level summary (per file):

~~~json
{
  "file": "example.pdf",
  "size_kb": 123.4,
  "pages": 3,
  "esign_found": true,
  "scanned_pdf": false,
  "mixed": false,
  "sig_count": 2,
  "sig_pages": "1,3",
  "roles": "patient;representative",
  "hints": "AcroSig:sig_patient;VendorText:DocuSign\\s+Envelope\\s+ID",
  "signatures": [
    {
      "page": 1,
      "field_name": "sig_patient",
      "role": "patient",
      "score": 5,
      "scores": { "field": 3, "page_label": 2 },
      "evidence": ["field:patient", "page_label:patient"],
      "hint": "AcroSig:sig_patient"
    },
    {
      "page": null,
      "field_name": "vendor_or_acro_detected",
      "role": "representative",
      "score": 6,
      "scores": { "page_label": 4, "general": 2 },
      "evidence": ["page_label:representative(parent/guardian)", "pseudo:true"],
      "hint": "VendorOrAcroOnly"
    }
  ]
}
~~~

### Field notes

- **`esign_found`** is `true` if any signature widget, AcroForm `/Sig` field, or vendor marker is detected.  
- **`scanned_pdf`** is a heuristic: pages with images only and no extractable text.  
- **`mixed`** means both `esign_found` and `scanned_pdf` are `true`.  
- **`roles`** summarizes unique non-`unknown` roles across signatures.
- In retainer profile, emitter prefers two signatures (client + firm), often on the same page.

---

## Configuration & rules

Built-in rules live under **`src/sigdetect/data/`**:

- **`vendor_patterns.yml`** – vendor byte/text patterns (e.g., DocuSign, Acrobat Sign).  
- **`role_rules.yml`** – signer-role logic:  
  - `labels` – strong page labels (e.g., “Signature of Patient”, including Parent/Guardian cases)  
  - `general` – weaker role hints in surrounding text  
  - `field_hints` – field-name keywords (e.g., `sig_patient`)  
  - `doc_hard` – strong document-level triggers (relationship to patient, “minor/unable to sign”, first-person consent)  
  - `weights` – scoring weights for the above  
- **`role_rules.retainer.yml`** – retainer-specific rules (labels for client/firm, general tokens, and field hints).

You can keep one config YAML per dataset, e.g.:
~~~yaml
# ./sample_data/config.yml (example)
pdf_root: ./pdfs
out_dir: ./sigdetect_out
engine: pypdf2
pseudo_signatures: true
recurse_xobjects: true
profile: retainer    # or: hipaa
~~~

YAML files can be customized or load at runtime (see CLI `--config`, if available, or import and pass patterns into engine).

### Key detection behaviors

- **Widget-first in mixed docs:** if a real `/Widget` exists, no pseudo “VendorOrAcroOnly” signature is emitted.  
- **Acro-only dedupe:** multiple `/Sig` fields at the document level collapse to a single pseudo signature.  
- **Parent/Guardian label:** “Signature of Parent/Guardian” maps to the `representative` role.  
- **Field-name fallbacks:** role hints are pulled from `/T`, `/TU`, or `/TM` (in that order).
  - Retainer heuristics:
  - Looks for client and firm labels/tokens; boosts pages with law-firm markers (LLP/LLC/PA/PC) and “By:” blocks.
  - Applies an anti-front-matter rule to reduce page-1 false positives (e.g., letterheads, firm mastheads).
  - When only vendor/Acro clues exist (no widgets), it will emit two pseudo signatures targeting likely pages.

---

## Smoke tests

Drop-in smoke tests live under **`tests/`** and cover:

- Vendor-only (multiple markers)  
- Acro-only (single pseudo with multiple `/Sig`)  
- Mixed (real widget + vendor markers → widget role, no pseudo)  
- Field-name fallbacks (`/TU`, `/TM`)  
- Parent/Guardian label → `representative`  
- Encrypted PDFs (graceful handling)

Run a subset:

~~~bash
pytest -q -k smoke
# or specific files:
pytest -q tests/test_mixed_widget_vendor_smoke.py
~~~

---

## Debugging
If you need to debug or inspect the detection logic, you can run the CLI with `--debug`:
~~~python
from pathlib import Path
from sigdetect.config import DetectConfiguration
from sigdetect.detector.pypdf2_engine import PyPDF2Detector

pdf = Path("/path/to/one.pdf")
configuration = DetectConfiguration(
    PdfRoot=pdf.parent,
    OutputDirectory=Path("."),
    Engine="pypdf2",
    Profile="retainer",
    PseudoSignatures=True,
    RecurseXObjects=True,
)
print(PyPDF2Detector(configuration).Detect(pdf).to_dict())

~~~

---

## Dev workflow

### Project layout

~~~text
src/
  sigdetect/
    detector/
      base.py
      pypdf2_engine.py
    data/
      role_rules.yml
      vendor_patterns.yml
    cli.py
tests/
pyproject.toml
.pre-commit-config.yaml
~~~

### Formatting & linting (pre-commit)

~~~bash
# one-time
pip install pre-commit
pre-commit install

# run on all files
pre-commit run --all-files
~~~

Hooks: `black`, `isort`, `ruff`, plus `pytest` (optional).  
Ensure your virtualenv folders are excluded in `.pre-commit-config.yaml` (e.g., `^\.venv`).

### Typical loop

~~~bash
# run tests
pytest -q

# run only smoke tests while iterating
pytest -q -k smoke
~~~

---

## Troubleshooting

**Using the wrong Python**

~~~bash
which python
python -V
~~~

If you see 3.8 or system Python, recreate the venv with 3.11.

**ModuleNotFoundError: typer / click / pytest**

~~~bash
pip install typer click pytest
~~~

**Pre-commit reformats files in `.venv`**

~~~yaml
exclude: |
  ^(\.venv|\.venv311|dist|build)/
~~~

**Vendor markers not detected**  
Set `--recurse-xobjects true` and enable pseudo signatures. Many providers embed markers in Form XObjects or compressed streams.

**Parent/Guardian not recognized**  
The rules already include a fallback for “Signature of Parent/Guardian”; if your variant differs, add it to `role_rules.yml → labels.representative`.

---

## License
MIT

