import unittest
from unittest.mock import patch

import tests
from docbatch.inventories import InventoryFailure, InventoryResult
from docbatch.workflow import BatchWorkflow

from tests.helpers import BATCH_NAME, PART_ONE, TemporaryFolders


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.folders = TemporaryFolders(self, {"a.pdf": 600, "b.pdf": 600})
        self.workflow = BatchWorkflow()

    def test_review_previews_part_names_and_summary_without_writing(self):
        destination_before = self.folders.snapshot(self.folders.destination)

        review = self.workflow.review(
            self.folders.source, self.folders.destination, BATCH_NAME
        )

        self.assertEqual(review.errors, ())
        self.assertEqual(review.batch_name, "BOOK 53 AUGUST")
        self.assertEqual(review.preview_folder_name, "BOOK 53 AUGUST PART_001")
        self.assertEqual(review.part_names, (PART_ONE,))
        self.assertEqual(review.pdf_count, 2)
        self.assertEqual(review.total_size_bytes, 1200)
        self.assertEqual(review.output_conflicts, ())
        self.assertEqual(review.overwrite_warning, "")
        self.assertEqual(self.folders.snapshot(self.folders.destination), destination_before)

    def test_validation_problems_are_returned_as_plain_language_errors(self):
        review = self.workflow.review(
            self.folders.source, self.folders.source, "", 30
        )

        self.assertFalse(review.is_valid)
        self.assertTrue(any("Batch name" in error for error in review.errors))
        self.assertTrue(any("Part-size limit" in error for error in review.errors))
        self.assertTrue(any("distinct" in error for error in review.errors))
        self.assertEqual(review.part_names, ())
        self.assertEqual(self.folders.snapshot(self.folders.destination), {})

    def test_no_pdf_input_is_reported_without_writing(self):
        empty_source = self.folders.source / "empty"
        empty_source.mkdir()
        review = self.workflow.review(
            empty_source, self.folders.destination, BATCH_NAME
        )

        self.assertFalse(review.is_valid)
        self.assertTrue(any("No top-level PDFs" in error for error in review.errors))

    def test_review_names_conflicts_and_folders_that_replace_would_recreate(self):
        (self.folders.destination / PART_ONE).mkdir()

        review = self.workflow.review(
            self.folders.source, self.folders.destination, BATCH_NAME
        )

        self.assertTrue(review.has_conflicts)
        self.assertIn(PART_ONE, review.overwrite_warning)
        self.assertIn(PART_ONE, review.replace_notice)
        self.assertEqual([conflict.name for conflict in review.output_conflicts], [PART_ONE])

    def test_review_flags_oversized_pdf_and_accepts_exactly_25_mb(self):
        folders = TemporaryFolders(self, {"small.pdf": 1024, "huge.pdf": 25 * 1024 * 1024 + 1})

        review = self.workflow.review(
            folders.source, folders.destination, BATCH_NAME, 25
        )

        self.assertEqual(review.errors, ())
        self.assertEqual(review.max_size_bytes, 25 * 1024 * 1024)
        self.assertEqual(review.oversized_pdf_names, ("huge.pdf",))
        self.assertEqual(len(review.part_names), 2)


class ConfirmationGateTests(unittest.TestCase):
    def setUp(self):
        self.folders = TemporaryFolders(self, {"alpha.pdf": 10})
        self.workflow = BatchWorkflow()
        self.review = self.workflow.review(
            self.folders.source, self.folders.destination, BATCH_NAME
        )

    def test_run_without_approval_writes_nothing(self):
        before = self.folders.snapshot(self.folders.destination)

        result = self.workflow.run(self.review)

        self.assertTrue(result.cancelled)
        self.assertEqual(self.folders.snapshot(self.folders.destination), before)

    def test_invalid_review_cannot_be_approved_into_writing(self):
        invalid = self.workflow.review(self.folders.source, self.folders.source, "")

        result = self.workflow.run(invalid, approved=True)

        self.assertTrue(result.cancelled)
        self.assertEqual(invalid.errors, result.errors)
        self.assertEqual(self.folders.snapshot(self.folders.destination), {})

    def test_conflicts_without_replace_confirmation_write_nothing(self):
        (self.folders.destination / PART_ONE).mkdir()
        before = self.folders.snapshot(self.folders.destination)
        review = self.workflow.review(
            self.folders.source, self.folders.destination, BATCH_NAME
        )

        result = self.workflow.run(review, approved=True)

        self.assertTrue(result.cancelled)
        self.assertIn(PART_ONE, " ".join(result.errors))
        self.assertEqual(self.folders.snapshot(self.folders.destination), before)


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        self.folders = TemporaryFolders(self, {"a.pdf": 600, "b.pdf": 600})
        self.workflow = BatchWorkflow()
        self.review = self.workflow.review(
            self.folders.source, self.folders.destination, BATCH_NAME
        )

    def test_approved_run_copies_creates_inventories_and_returns_completion_data(self):
        source_before = self.folders.snapshot(self.folders.source)

        result = self.workflow.run(self.review, approved=True)

        self.assertFalse(result.cancelled)
        self.assertEqual(result.copied_pdf_count, 2)
        self.assertEqual(result.written_inventory_count, 1)
        self.assertEqual(result.skipped_files, ())
        self.assertEqual(result.errors, ())
        self.assertEqual(
            sorted(item.name for item in (self.folders.destination / PART_ONE).iterdir()),
            [PART_ONE + ".xlsx", "a.pdf", "b.pdf"],
        )
        self.assertEqual(len(result.generated_folders), 1)
        folder = result.generated_folders[0]
        self.assertEqual(folder.name, PART_ONE)
        self.assertEqual(folder.path, self.folders.destination / PART_ONE)
        self.assertEqual(folder.total_size_bytes, 1200)
        self.assertEqual(folder.pdf_count, 2)
        self.assertEqual(self.folders.snapshot(self.folders.source), source_before)

    def test_replace_confirmation_recreates_only_the_conflicting_part_folder(self):
        conflicting = self.folders.destination / PART_ONE
        conflicting.mkdir()
        (conflicting / "stale.pdf").write_bytes(b"old")
        review = self.workflow.review(
            self.folders.source, self.folders.destination, BATCH_NAME
        )

        result = self.workflow.run(review, approved=True, replace_existing=True)

        self.assertFalse(result.cancelled)
        self.assertEqual(result.replaced_folders, (PART_ONE,))
        self.assertEqual(
            sorted(item.name for item in conflicting.iterdir()),
            [PART_ONE + ".xlsx", "a.pdf", "b.pdf"],
        )

    def test_progress_events_report_copying_inventories_and_completion(self):
        events = []

        self.workflow.run(self.review, approved=True, progress=events.append)

        self.assertIn("generation", [event.stage for event in events])
        self.assertIn("copy", [event.stage for event in events])
        self.assertIn("inventory", [event.stage for event in events])
        last = events[-1]
        self.assertEqual(last.stage, "complete")
        self.assertEqual(last.completed, last.total)
        self.assertTrue(all(event.completed <= event.total for event in events))
        self.assertTrue(any(PART_ONE in event.message for event in events))

    def test_copy_failure_is_named_and_successful_files_are_not_rolled_back(self):
        (self.folders.source / "missing.pdf").write_bytes(b"x" * 10)
        review = self.workflow.review(
            self.folders.source, self.folders.destination, BATCH_NAME
        )
        (self.folders.source / "missing.pdf").unlink()

        result = self.workflow.run(review, approved=True)

        self.assertFalse(result.cancelled)
        self.assertEqual(result.skipped_files, ("missing.pdf",))
        self.assertTrue(any("missing.pdf" in error for error in result.errors))
        self.assertEqual(result.copied_pdf_count, 2)
        self.assertEqual(result.generated_folders[0].pdf_count, 2)
        self.assertEqual(result.written_inventory_count, 1)
        self.assertEqual(
            sorted(item.name for item in (self.folders.destination / PART_ONE).iterdir()),
            [PART_ONE + ".xlsx", "a.pdf", "b.pdf"],
        )

    def test_oversized_pdf_is_reported_in_the_completion_data(self):
        folders = TemporaryFolders(
            self, {"a.pdf": 600, "huge.pdf": 25 * 1024 * 1024 + 1}
        )
        review = self.workflow.review(
            folders.source, folders.destination, BATCH_NAME, 25
        )

        result = self.workflow.run(review, approved=True)

        self.assertFalse(result.cancelled)
        oversized = [
            folder for folder in result.generated_folders if folder.has_oversized_pdf
        ]
        self.assertEqual(len(oversized), 1)
        self.assertEqual(oversized[0].oversized_pdf_names, ("huge.pdf",))
        self.assertTrue((folders.destination / oversized[0].name / "huge.pdf").exists())

    def test_inventory_names_resolve_numeric_prefixes_and_abbreviations(self):
        from openpyxl import load_workbook

        folders = TemporaryFolders(
            self, {"54_Name of the file.pdf": 10, "Name of the file.pdf": 10, "DOS deed.pdf": 10}
        )
        review = self.workflow.review(
            folders.source, folders.destination, BATCH_NAME
        )

        result = self.workflow.run(review, approved=True)

        self.assertEqual(result.written_inventory_count, 1)
        sheet = load_workbook(result.destination / PART_ONE / (PART_ONE + ".xlsx"))["Files"]
        names = [cell.value for cell in sheet["B"][1:]]
        self.assertEqual(
            names, ["Name of the file", "Deed of Sale", "Name of the file"]
        )

    def test_inventory_failure_is_named_without_discarding_the_run(self):
        failure = InventoryFailure(
            PART_ONE, self.folders.destination / PART_ONE / (PART_ONE + ".xlsx"), "disk error"
        )
        def failing_writer(generation_result):
            return InventoryResult((), (failure,))

        with patch("docbatch.workflow.write_inventories", side_effect=failing_writer):
            result = self.workflow.run(self.review, approved=True)

        self.assertFalse(result.cancelled)
        self.assertEqual(result.written_inventory_count, 0)
        self.assertTrue(any(PART_ONE in error for error in result.errors))
        self.assertTrue(any("disk error" in error for error in result.errors))
        self.assertEqual(result.copied_pdf_count, 2)
        self.assertEqual(len(result.generated_folders), 1)


if __name__ == "__main__":
    unittest.main()
