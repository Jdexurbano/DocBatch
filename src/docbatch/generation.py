import shutil
from pathlib import Path

from docbatch.models import (
    BatchPlan,
    CopyFailure,
    GeneratedPartFolder,
    GenerationResult,
    OutputConflict,
    ReplacedPartFolder,
)

__all__ = [
    "CopyFailure",
    "GeneratedPartFolder",
    "GenerationResult",
    "OutputConflict",
    "ReplacedPartFolder",
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


def _remove_entry(entry: Path) -> None:
    if entry.is_dir() and not entry.is_symlink():
        shutil.rmtree(entry)
    else:
        entry.unlink()


def generate_output(plan: BatchPlan, replace_existing: bool = False) -> GenerationResult:
    conflicts = detect_conflicts(plan)
    if conflicts and not replace_existing:
        return GenerationResult(
            cancelled=True,
            generated_part_folders=(),
            copied_pdf_count=0,
            generated_part_folder_count=0,
            output_conflicts=conflicts,
            replaced_part_folders=(),
            copy_failures=(),
        )

    replaced_part_folders = []
    if conflicts:
        destination_entries = _entries_by_casefold(plan.destination)
        conflicted_parts = {
            conflict.name for conflict in conflicts if conflict.kind == "part_folder"
        }
        for part in plan.part_folders:
            if part.name not in conflicted_parts:
                continue
            for entry in destination_entries.get(part.name.casefold(), ()):
                _remove_entry(entry)
            replaced_part_folders.append(
                ReplacedPartFolder(name=part.name, path=part.path)
            )

    generated_part_folders = []
    copy_failures = []
    copied_pdf_count = 0
    for part in plan.part_folders:
        part.path.mkdir()
        for pdf in part.pdfs:
            try:
                shutil.copy2(plan.source / pdf.filename, part.path / pdf.filename)
            except OSError as exc:
                copy_failures.append(
                    CopyFailure(filename=pdf.filename, reason=str(exc))
                )
                continue
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
        output_conflicts=conflicts,
        replaced_part_folders=tuple(replaced_part_folders),
        copy_failures=tuple(copy_failures),
    )
