from pathlib import Path

from docbatch.models import BatchPlan, PartFolder, PlannedPDF
from docbatch.validation import PlanValidationError, normalize_batch_name

__all__ = [
    "BatchPlan",
    "PartFolder",
    "PlannedPDF",
    "PlanValidationError",
    "build_plan",
]

MEGABYTE_BYTES = 1024 * 1024
DEFAULT_MAX_SIZE_MB = 25.0
PART_NAME_TEMPLATE = "{batch_name} PART_{number:03d}"


def build_plan(
    source: Path | str,
    destination: Path | str,
    batch_name: str,
    max_size_mb: float = DEFAULT_MAX_SIZE_MB,
) -> BatchPlan:
    normalized_name = normalize_batch_name(batch_name)
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()

    pdf_paths = sorted(
        (
            item
            for item in source_path.iterdir()
            if item.is_file() and item.suffix.lower() == ".pdf"
        ),
        key=lambda item: (item.name.lower(), item.name),
    )
    pdfs = tuple(
        PlannedPDF(path.name, path.stat().st_size) for path in pdf_paths
    )

    part_name = PART_NAME_TEMPLATE.format(batch_name=normalized_name, number=1)
    part = PartFolder(
        name=part_name,
        path=destination_path / part_name,
        pdfs=pdfs,
        total_size_bytes=sum(pdf.size_bytes for pdf in pdfs),
    )

    return BatchPlan(
        batch_name=normalized_name,
        source=source_path,
        destination=destination_path,
        max_size_bytes=int(max_size_mb * MEGABYTE_BYTES),
        part_folders=(part,),
    )
