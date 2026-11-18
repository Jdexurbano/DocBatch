from pathlib import Path

from docbatch.models import BatchPlan, PartFolder, PlannedPDF
from docbatch.validation import (
    DEFAULT_MAX_SIZE_MB,
    MEGABYTE_BYTES,
    PlanValidationError,
    _validate_inputs,
)

__all__ = [
    "BatchPlan",
    "PartFolder",
    "PlannedPDF",
    "PlanValidationError",
    "build_plan",
]


def _discover_pdfs(source: Path):
    candidates = []
    for item in source.iterdir():
        if item.is_dir():
            continue
        if item.suffix.lower() != ".pdf":
            continue
        if not (item.is_file() or item.is_symlink()):
            continue
        candidates.append(item)
    candidates.sort(key=lambda item: (item.name.casefold(), item.name))

    pdfs = []
    errors = []
    for path in candidates:
        try:
            size = path.stat().st_size
        except OSError:
            errors.append(f"Cannot inspect PDF size: {path.name}")
        else:
            pdfs.append(PlannedPDF(path.name, size))
    return tuple(pdfs), tuple(errors), bool(candidates)


def build_plan(
    source: Path | str,
    destination: Path | str,
    batch_name: str,
    max_size_mb: float = DEFAULT_MAX_SIZE_MB,
) -> BatchPlan:
    inputs = _validate_inputs(source, destination, batch_name, max_size_mb)
    errors = list(inputs.errors)
    pdfs = ()

    if inputs.source is not None and inputs.source.is_dir():
        try:
            pdfs, discovery_errors, found_candidates = _discover_pdfs(inputs.source)
        except OSError:
            errors.append(f"Cannot read Source folder: {inputs.source}")
        else:
            errors.extend(discovery_errors)
            if not found_candidates:
                errors.append(f"No top-level PDFs found in Source folder: {inputs.source}")

    if errors:
        raise PlanValidationError(errors)

    part_name = f"{inputs.batch_name} PART_001"
    part = PartFolder(
        name=part_name,
        path=inputs.destination / part_name,
        pdfs=pdfs,
        total_size_bytes=sum(pdf.size_bytes for pdf in pdfs),
    )

    return BatchPlan(
        batch_name=inputs.batch_name,
        source=inputs.source,
        destination=inputs.destination,
        max_size_bytes=int(inputs.max_size_mb * MEGABYTE_BYTES),
        part_folders=(part,),
    )
