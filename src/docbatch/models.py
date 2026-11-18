from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlannedPDF:
    filename: str
    size_bytes: int


@dataclass(frozen=True)
class PartFolder:
    name: str
    path: Path
    pdfs: tuple[PlannedPDF, ...]
    total_size_bytes: int
    has_oversized_pdf: bool


@dataclass(frozen=True)
class BatchPlan:
    batch_name: str
    source: Path
    destination: Path
    max_size_bytes: int
    part_folders: tuple[PartFolder, ...]


@dataclass(frozen=True)
class OutputConflict:
    kind: str
    path: Path
    name: str
    message: str


@dataclass(frozen=True)
class GeneratedPartFolder:
    name: str
    path: Path
    total_size_bytes: int
    has_oversized_pdf: bool


@dataclass(frozen=True)
class CopyFailure:
    filename: str
    reason: str


@dataclass(frozen=True)
class ReplacedPartFolder:
    name: str
    path: Path


@dataclass(frozen=True)
class GenerationResult:
    cancelled: bool
    generated_part_folders: tuple[GeneratedPartFolder, ...]
    copied_pdf_count: int
    generated_part_folder_count: int
    output_conflicts: tuple[OutputConflict, ...]
    replaced_part_folders: tuple[ReplacedPartFolder, ...]
    copy_failures: tuple[CopyFailure, ...]
