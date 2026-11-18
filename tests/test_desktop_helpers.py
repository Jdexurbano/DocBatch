import unittest
from dataclasses import replace
from types import SimpleNamespace

import tests
from docbatch.desktop import (
    folder_name_preview,
    format_completion_summary,
    format_progress,
    format_review_summary,
    format_size,
    parse_size_limit,
    progress_maximum,
    should_clear_inputs,
)
from docbatch.workflow import (
    BatchWorkflow,
    GeneratedFolderSummary,
    ProgressEvent,
    WorkflowResult,
)

from tests.helpers import BATCH_NAME, PART_ONE, PART_TWO, TemporaryFolders


class NamingAndSizeHelperTests(unittest.TestCase):
    def test_folder_name_preview_normalizes_the_batch_name(self):
        self.assertEqual(folder_name_preview("book 53 august"), "BOOK 53 AUGUST PART_001")
        self.assertEqual(folder_name_preview("  café año "), "CAFÉ AÑO PART_001")

    def test_format_size_shows_binary_units_and_exact_bytes(self):
        self.assertEqual(format_size(10), "10 bytes")
        self.assertEqual(format_size(1200), "1.17 KB (1,200 bytes)")
        self.assertEqual(
            format_size(25 * 1024 * 1024), "25.00 MB (26,214,400 bytes)"
        )

    def test_parse_size_limit_accepts_plain_or_mb_suffixed_numbers(self):
        self.assertEqual(parse_size_limit("25"), 25.0)
        self.assertEqual(parse_size_limit(" 1.5 MB "), 1.5)

    def test_parse_size_limit_rejects_text_with_plain_language(self):
        for value in ("", "abc", "MB", "1,5"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as caught:
                    parse_size_limit(value)
                self.assertIn("number", str(caught.exception))


class SummaryFormattingTests(unittest.TestCase):
    def setUp(self):
        self.folders = TemporaryFolders(self, {"a.pdf": 600, "b.pdf": 600})
        self.workflow = BatchWorkflow()

    def test_review_summary_shows_count_size_destination_parts_and_warnings(self):
        review = self.workflow.review(
            self.folders.source, self.folders.destination, BATCH_NAME, 1 / 1024
        )

        text = format_review_summary(review)

        self.assertIn("PDFs: 2", text)
        self.assertIn("1.17 KB (1,200 bytes)", text)
        self.assertIn(str(self.folders.destination), text)
        self.assertIn(PART_ONE, text)
        self.assertIn(PART_TWO, text)
        self.assertNotIn("overwrite", text.lower())

    def test_review_summary_names_conflicts_and_oversized_pdfs(self):
        (self.folders.destination / PART_ONE).mkdir()
        folders = TemporaryFolders(self, {"huge.pdf": 25 * 1024 * 1024 + 1})
        review = self.workflow.review(
            folders.source, folders.destination, BATCH_NAME, 25
        )

        text = format_review_summary(review)

        self.assertIn(PART_ONE, text)
        self.assertIn("huge.pdf", text)
        self.assertIn("exceed", text.lower())

    def test_completion_summary_lists_folders_sizes_skipped_files_and_errors(self):
        folder = GeneratedFolderSummary(
            name=PART_ONE,
            path=self.folders.destination / PART_ONE,
            total_size_bytes=1200,
            pdf_count=1,
            has_oversized_pdf=True,
            oversized_pdf_names=("huge.pdf",),
        )
        result = WorkflowResult(
            cancelled=False,
            destination=self.folders.destination,
            generated_folders=(folder,),
            replaced_folders=(PART_ONE,),
            skipped_files=("missing.pdf",),
            errors=("Could not copy missing.pdf: file not found",),
            copied_pdf_count=1,
            written_inventory_count=1,
        )

        text = format_completion_summary(result)

        self.assertIn(PART_ONE, text)
        self.assertIn("1.17 KB (1,200 bytes)", text)
        self.assertIn("huge.pdf", text)
        self.assertIn("Replaced", text)
        self.assertIn("missing.pdf", text)
        self.assertIn("partial", text.lower())

    def test_cancelled_completion_summary_explains_that_nothing_was_written(self):
        result = WorkflowResult(
            cancelled=True,
            destination=self.folders.destination,
            generated_folders=(),
            replaced_folders=(),
            skipped_files=(),
            errors=("Output conflicts were found; nothing was written: " + PART_ONE,),
            copied_pdf_count=0,
            written_inventory_count=0,
        )

        text = format_completion_summary(result)

        self.assertIn("nothing was written", text.lower())
        self.assertIn(PART_ONE, text)

    def test_progress_text_includes_message_and_position(self):
        event = ProgressEvent("copy", f"Copied part 1 of 2: {PART_ONE}", 1, 2)

        self.assertEqual(
            format_progress(event), f"Copied part 1 of 2: {PART_ONE} (1/2)"
        )


class RunStateHelperTests(unittest.TestCase):
    def test_progress_maximum_uses_part_folders_not_pdfs(self):
        review = SimpleNamespace(part_names=(PART_ONE, PART_TWO), pdf_count=7)

        self.assertEqual(progress_maximum(review), 2)

    def test_progress_maximum_never_returns_zero(self):
        review = SimpleNamespace(part_names=(), pdf_count=0)

        self.assertEqual(progress_maximum(review), 1)

    def test_should_clear_inputs_only_after_output_was_written(self):
        result = WorkflowResult(
            cancelled=False,
            destination=None,
            generated_folders=(),
            replaced_folders=(),
            skipped_files=(),
            errors=(),
            copied_pdf_count=0,
            written_inventory_count=0,
        )

        self.assertTrue(should_clear_inputs(result))
        self.assertFalse(should_clear_inputs(replace(result, cancelled=True)))
        self.assertFalse(should_clear_inputs(None))


if __name__ == "__main__":
    unittest.main()
