from dataclasses import dataclass, field
from pathlib import Path

from docbatch.generation import OutputConflict, detect_conflicts, generate_output
from docbatch.inventories import write_inventories
from docbatch.models import BatchPlan
from docbatch.planning import PlanValidationError, build_plan
from docbatch.validation import DEFAULT_MAX_SIZE_MB, normalize_batch_name

__all__ = [
    "FIRST_PART_SUFFIX",
    "BatchWorkflow",
    "GeneratedFolderSummary",
    "ProgressEvent",
    "WorkflowReview",
    "WorkflowResult",
]

FIRST_PART_SUFFIX = " PART_001"


@dataclass(frozen=True)
class ProgressEvent:
    stage: str
    message: str
    completed: int
    total: int


@dataclass(frozen=True)
class WorkflowReview:
    errors: tuple[str, ...]
    batch_name: str
    source: Path | None
    destination: Path | None
    max_size_mb: float | None
    max_size_bytes: int
    pdf_count: int
    total_size_bytes: int
    part_names: tuple[str, ...]
    preview_folder_name: str
    oversized_pdf_names: tuple[str, ...]
    output_conflicts: tuple[OutputConflict, ...]
    overwrite_warning: str
    replace_notice: str
    _plan: BatchPlan | None = field(repr=False, compare=False, default=None)

    @property
    def is_valid(self):
        return not self.errors

    @property
    def has_conflicts(self):
        return bool(self.output_conflicts)


@dataclass(frozen=True)
class GeneratedFolderSummary:
    name: str
    path: Path
    total_size_bytes: int
    pdf_count: int
    has_oversized_pdf: bool
    oversized_pdf_names: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowResult:
    cancelled: bool
    destination: Path | None
    generated_folders: tuple[GeneratedFolderSummary, ...]
    replaced_folders: tuple[str, ...]
    skipped_files: tuple[str, ...]
    errors: tuple[str, ...]
    copied_pdf_count: int
    written_inventory_count: int


def _iter_pdfs(plan):
    return (pdf for part in plan.part_folders for pdf in part.pdfs)


def _oversized_names(pdfs, max_size_bytes):
    return tuple(pdf.filename for pdf in pdfs if pdf.size_bytes > max_size_bytes)


def _empty_review(errors, batch_name=""):
    return WorkflowReview(
        errors=tuple(errors),
        batch_name=normalize_batch_name(batch_name) if isinstance(batch_name, str) else "",
        source=None,
        destination=None,
        max_size_mb=None,
        max_size_bytes=0,
        pdf_count=0,
        total_size_bytes=0,
        part_names=(),
        preview_folder_name=f"{normalize_batch_name(batch_name)}{FIRST_PART_SUFFIX}"
        if isinstance(batch_name, str)
        else "",
        oversized_pdf_names=(),
        output_conflicts=(),
        overwrite_warning="",
        replace_notice="",
    )


class BatchWorkflow:
    def review(
        self,
        source,
        destination,
        batch_name,
        max_size_mb: float = DEFAULT_MAX_SIZE_MB,
    ) -> WorkflowReview:
        try:
            plan = build_plan(source, destination, batch_name, max_size_mb)
        except PlanValidationError as exc:
            return _empty_review(exc.messages, batch_name)

        conflicts = detect_conflicts(plan)
        conflicted_parts = tuple(
            dict.fromkeys(conflict.name for conflict in conflicts if conflict.kind == "part_folder")
        )
        conflict_names = ", ".join(conflict.name for conflict in conflicts)
        warning = (
            "Existing output will be replaced: " + conflict_names if conflicts else ""
        )
        replace_notice = (
            "Replace confirmation will remove and recreate: " + ", ".join(conflicted_parts)
            if conflicted_parts
            else ""
        )
        pdfs = tuple(_iter_pdfs(plan))
        oversized = _oversized_names(pdfs, plan.max_size_bytes)
        total_size = sum(pdf.size_bytes for pdf in pdfs)

        return WorkflowReview(
            errors=(),
            batch_name=plan.batch_name,
            source=plan.source,
            destination=plan.destination,
            max_size_mb=max_size_mb if isinstance(max_size_mb, (int, float)) else None,
            max_size_bytes=plan.max_size_bytes,
            pdf_count=sum(len(part.pdfs) for part in plan.part_folders),
            total_size_bytes=total_size,
            part_names=tuple(part.name for part in plan.part_folders),
            preview_folder_name=f"{plan.batch_name}{FIRST_PART_SUFFIX}",
            oversized_pdf_names=oversized,
            output_conflicts=conflicts,
            overwrite_warning=warning,
            replace_notice=replace_notice,
            _plan=plan,
        )

    def run(
        self,
        review: WorkflowReview,
        *,
        approved: bool = False,
        replace_existing: bool = False,
        progress=None,
    ) -> WorkflowResult:
        def cancel(errors):
            self._emit(progress, "cancelled", "; ".join(errors), 0, 0)
            return self._cancelled(review, errors)

        if not review.is_valid:
            return cancel(review.errors)
        if not approved:
            return cancel(("Processing was not confirmed; nothing was written.",))
        if review.has_conflicts and not replace_existing:
            names = ", ".join(conflict.name for conflict in review.output_conflicts)
            return cancel(
                (
                    "Output conflicts were found and Replace confirmation was not "
                    f"given; nothing was written: {names}",
                )
            )
        if review._plan is None:
            return cancel(("The review has expired; please review the batch again.",))

        plan = review._plan
        part_count = len(plan.part_folders)
        self._emit(
            progress,
            "generation",
            f"Copying {review.pdf_count} PDF(s) into {part_count} part folder(s)",
            0,
            part_count,
        )
        generation = generate_output(plan, replace_existing=replace_existing)

        if generation.cancelled:
            names = ", ".join(conflict.name for conflict in generation.output_conflicts)
            return cancel((f"Output conflicts were found; nothing was written: {names}",))

        for index, folder in enumerate(generation.generated_part_folders, start=1):
            self._emit(
                progress,
                "copy",
                f"Copied part {index} of {part_count}: {folder.name}",
                index,
                part_count,
            )

        self._emit(
            progress,
            "inventory",
            f"Creating {part_count} Excel inventory file(s)",
            0,
            part_count,
        )
        inventories = write_inventories(generation)
        for index, inventory in enumerate(inventories.written_inventories, start=1):
            self._emit(
                progress,
                "inventory",
                f"Created inventory {index} of {part_count}: {inventory.name}",
                index,
                part_count,
            )

        errors = [
            f"Could not copy {failure.filename}: {failure.reason}"
            for failure in generation.copy_failures
        ]
        errors.extend(
            f"Could not create Excel inventory {failure.path.name} for "
            f"{failure.name}: {failure.reason}"
            for failure in inventories.inventory_failures
        )
        failed_filenames = {failure.filename for failure in generation.copy_failures}
        generated_names = {folder.name for folder in generation.generated_part_folders}
        generated_folders = tuple(
            GeneratedFolderSummary(
                name=part.name,
                path=part.path,
                total_size_bytes=part.total_size_bytes,
                pdf_count=sum(
                    1 for pdf in part.pdfs if pdf.filename not in failed_filenames
                ),
                has_oversized_pdf=part.has_oversized_pdf,
                oversized_pdf_names=_oversized_names(part.pdfs, plan.max_size_bytes),
            )
            for part in plan.part_folders
            if part.name in generated_names
        )
        self._emit(
            progress,
            "complete",
            f"Processed {part_count} part folder(s); copied {generation.copied_pdf_count} PDF(s)",
            part_count,
            part_count,
        )

        return WorkflowResult(
            cancelled=False,
            destination=review.destination,
            generated_folders=generated_folders,
            replaced_folders=tuple(
                folder.name for folder in generation.replaced_part_folders
            ),
            skipped_files=tuple(
                failure.filename for failure in generation.copy_failures
            ),
            errors=tuple(errors),
            copied_pdf_count=generation.copied_pdf_count,
            written_inventory_count=len(inventories.written_inventories),
        )

    @staticmethod
    def _emit(progress, stage, message, completed, total):
        if progress is not None:
            progress(ProgressEvent(stage, message, completed, total))

    @staticmethod
    def _cancelled(review, errors):
        return WorkflowResult(
            cancelled=True,
            destination=review.destination,
            generated_folders=(),
            replaced_folders=(),
            skipped_files=(),
            errors=tuple(errors),
            copied_pdf_count=0,
            written_inventory_count=0,
        )
