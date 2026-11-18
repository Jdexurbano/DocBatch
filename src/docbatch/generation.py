import shutil
from pathlib import Path

from docbatch.models import (
    BatchPlan,
    GeneratedPartFolder,
    GenerationResult,
    OutputConflict,
)

__all__ = [
    "GeneratedPartFolder",
    "GenerationResult",
    "OutputConflict",
    "detect_conflicts",
    "generate_output",
]


def _entries_by_casefold(directory: Path):
    try:
        entries = tuple(directory.iterdir())
    except OSError:
        return {}
    grouped = {}
    for entry in entries:
        grouped.setdefault(entry.name.casefold(), []).append(entry)
    for matches in grouped.values():
        matches.sort(key=lambda item: item.name)
    return grouped


def detect_conflicts(plan: BatchPlan) -> tuple[OutputConflict, ...]:
    conflicts = []
    destination_entries = _entries_by_casefold(plan.destination)

    for part in plan.part_folders:
        folder_key = part.name.casefold()
        if folder_key in destination_entries:
            conflicts.append(
                OutputConflict(
                    kind="part_folder",
                    path=part.path,
                    name=part.name,
                    message=f"Part folder already exists: {part.name}",
                )
            )

        matching_folders = [
            entry
            for entry in destination_entries.get(folder_key, ())
            if entry.is_dir()
        ]
        if not matching_folders:
            continue

        existing_pdf_names = set()
        for folder in matching_folders:
            existing_pdf_names.update(_entries_by_casefold(folder))

        for pdf in part.pdfs:
            if pdf.filename.casefold() not in existing_pdf_names:
                continue
            conflicts.append(
                OutputConflict(
                    kind="pdf",
                    path=part.path / pdf.filename,
                    name=pdf.filename,
                    message=f"PDF already exists: {pdf.filename} in {part.name}",
                )
            )

    return tuple(conflicts)


def generate_output(plan: BatchPlan, replace_existing: bool = False) -> GenerationResult:
    conflicts = detect_conflicts(plan)
    if conflicts:
        if replace_existing:
            raise NotImplementedError("Replace confirmation is not available yet")
        return GenerationResult(
            cancelled=True,
            generated_part_folders=(),
            copied_pdf_count=0,
            generated_part_folder_count=0,
            output_conflicts=conflicts,
        )

    generated_part_folders = []
    copied_pdf_count = 0
    for part in plan.part_folders:
        part.path.mkdir()
        for pdf in part.pdfs:
            shutil.copy2(plan.source / pdf.filename, part.path / pdf.filename)
            copied_pdf_count += 1
        generated_part_folders.append(
            GeneratedPartFolder(
                name=part.name,
                path=part.path,
                total_size_bytes=part.total_size_bytes,
                has_oversized_pdf=part.has_oversized_pdf,
            )
        )

    return GenerationResult(
        cancelled=False,
        generated_part_folders=tuple(generated_part_folders),
        copied_pdf_count=copied_pdf_count,
        generated_part_folder_count=len(generated_part_folders),
        output_conflicts=(),
    )
