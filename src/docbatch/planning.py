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


def _pack_pdfs(pdfs, batch_name, destination, max_size_bytes):
    groups = []
    current_pdfs = []
    current_total_bytes = 0
    for pdf in pdfs:
        if current_pdfs and current_total_bytes + pdf.size_bytes > max_size_bytes:
            groups.append((current_pdfs, current_total_bytes))
            current_pdfs = []
            current_total_bytes = 0
        current_pdfs.append(pdf)
        current_total_bytes += pdf.size_bytes
    if current_pdfs:
        groups.append((current_pdfs, current_total_bytes))

    parts = []
    for index, (group_pdfs, group_total_bytes) in enumerate(groups, start=1):
        name = f"{batch_name} PART_{index:03d}"
        parts.append(
            PartFolder(
                name=name,
                path=destination / name,
                pdfs=tuple(group_pdfs),
                total_size_bytes=group_total_bytes,
                has_oversized_pdf=any(
                    pdf.size_bytes > max_size_bytes for pdf in group_pdfs
                ),
            )
        )
    return tuple(parts)


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

    max_size_bytes = int(inputs.max_size_mb * MEGABYTE_BYTES)

    return BatchPlan(
        batch_name=inputs.batch_name,
        source=inputs.source,
        destination=inputs.destination,
        max_size_bytes=max_size_bytes,
        part_folders=_pack_pdfs(
            pdfs, inputs.batch_name, inputs.destination, max_size_bytes
        ),
    )
