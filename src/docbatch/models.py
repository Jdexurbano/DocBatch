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


@dataclass(frozen=True)
class BatchPlan:
    batch_name: str
    source: Path
    destination: Path
    max_size_bytes: int
    part_folders: tuple[PartFolder, ...]
