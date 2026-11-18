import re
from dataclasses import dataclass
from pathlib import Path

from docbatch.models import GenerationResult
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

__all__ = [
    "InventoryFailure",
    "InventoryResult",
    "WrittenInventory",
    "document_name",
    "write_inventories",
]

_ABBREVIATIONS = {
    "DOS": "Deed of Sale",
    "DOAS": "Deed of Absolute Sale",
    "SPA": "Special Power of Attorney",
    "ULA": "Uniform Loan Agreement",
    "Pakyaw CA": "Pakyaw Contract Agreement",
    "CA": "Contract Agreement",
    "AOU": "Affidavit of Understanding",
    "AOC": "Affidavit of Claim",
    "AOL": "Affidavit of Loss",
    "AOV": "Affidavit of Verification",
    "COE": "Certificate of Employment",
    "COS": "Contract of Service",
    "RWQ": "Release, Waiver, Quitclaim",
}
_NUMERIC_PREFIX = re.compile(r"^\d+_")


@dataclass(frozen=True)
class WrittenInventory:
    name: str
    path: Path
    document_count: int


@dataclass(frozen=True)
class InventoryFailure:
    name: str
    path: Path
    reason: str


@dataclass(frozen=True)
class InventoryResult:
    written_inventories: tuple[WrittenInventory, ...]
    inventory_failures: tuple[InventoryFailure, ...]


def document_name(filename: str) -> str:
    stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
    prefix = _NUMERIC_PREFIX.match(stem)
    candidate = stem[prefix.end() :] if prefix else stem
    if not candidate:
        return stem

    uppercase = candidate.upper()
    for abbreviation, full_name in _ABBREVIATIONS.items():
        if abbreviation.upper() in uppercase:
            return full_name

    if "_" in candidate:
        return candidate.split("_", 1)[0].strip()
    return candidate


def write_inventories(generation_result: GenerationResult) -> InventoryResult:
    if generation_result.cancelled:
        return InventoryResult((), ())

    written = []
    failures = []
    for part in generation_result.generated_part_folders:
        inventory_path = part.path / f"{part.name}.xlsx"
        try:
            pdfs = sorted(
                (
                    item.name
                    for item in part.path.iterdir()
                    if item.suffix.lower() == ".pdf"
                    and (item.is_file() or item.is_symlink())
                ),
                key=lambda name: (name.casefold(), name),
            )
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Files"
            sheet.append(["No.", "Document Name"])
            for number, pdf in enumerate(pdfs, start=1):
                sheet.append([number, document_name(pdf)])
            table = Table(displayName="FilesTable", ref=f"A1:B{sheet.max_row}")
            table.tableStyleInfo = TableStyleInfo(
                name="TableStyleLight8",
                showFirstColumn=False,
                showLastColumn=False,
                showRowStripes=False,
                showColumnStripes=False,
            )
            sheet.add_table(table)
            workbook.save(inventory_path)
        except Exception as exc:
            failures.append(InventoryFailure(part.name, inventory_path, str(exc)))
            continue
        written.append(WrittenInventory(part.name, inventory_path, len(pdfs)))

    return InventoryResult(tuple(written), tuple(failures))
