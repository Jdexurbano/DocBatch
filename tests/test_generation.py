import os
import unittest
from dataclasses import FrozenInstanceError

import tests
from docbatch.generation import (
    GeneratedPartFolder,
    GenerationResult,
    detect_conflicts,
    generate_output,
)

from tests.helpers import PART_ONE, PART_THREE, PART_TWO, PlanTestCase


class GenerateOutputTests(PlanTestCase):
    def test_conflict_free_plan_creates_part_folders_and_copies_planned_pdfs(self):
        plan = self.plan({"b.pdf": 20, "a.pdf": 10})
        source_pdf = self.folders.source / "a.pdf"
        old_mtime = 1_700_000_000_000_000_000
        os.utime(source_pdf, ns=(old_mtime, old_mtime))

        result = generate_output(plan)

        part_folder = self.folders.destination / PART_ONE
        self.assertFalse(result.cancelled)
        self.assertEqual(sorted(item.name for item in part_folder.iterdir()), ["a.pdf", "b.pdf"])
        self.assertEqual((part_folder / "a.pdf").read_bytes(), source_pdf.read_bytes())
        self.assertEqual((part_folder / "b.pdf").read_bytes(), (self.folders.source / "b.pdf").read_bytes())
        self.assertEqual((part_folder / "a.pdf").stat().st_mtime_ns, old_mtime)

    def test_source_pdfs_are_unchanged_after_generation(self):
        plan = self.plan({"b.pdf": 20, "a.pdf": 10})
        before = self.folders.snapshot(self.folders.source)

        generate_output(plan)

        self.assertEqual(self.folders.snapshot(self.folders.source), before)

    def test_result_describes_completed_run_with_paths_sizes_counts_and_oversized_flags(self):
        plan = self.plan(
            {"a.pdf": 600, "b-huge.pdf": 2000, "c.pdf": 500},
            max_size_mb=1 / 1024,
        )

        result = generate_output(plan)

        self.assertFalse(result.cancelled)
        self.assertEqual(result.generated_part_folder_count, 3)
        self.assertEqual(result.copied_pdf_count, 3)
        self.assertEqual(result.output_conflicts, ())
        self.assertEqual(
            [folder.path for folder in result.generated_part_folders],
            [part.path for part in plan.part_folders],
        )
        self.assertEqual(
            [
                (folder.name, folder.total_size_bytes, folder.has_oversized_pdf)
                for folder in result.generated_part_folders
            ],
            [
                (PART_ONE, 600, False),
                (PART_TWO, 2000, True),
                (PART_THREE, 500, False),
            ],
        )
        self.assertEqual(
            (self.folders.destination / PART_TWO / "b-huge.pdf").read_bytes(),
            b"\x00" * 2000,
        )

    def test_generation_uses_plan_instead_of_rederiving_from_source_filesystem(self):
        plan = self.plan({"a.pdf": 10, "b.pdf": 10})
        (self.folders.source / "z.pdf").write_bytes(b"z" * 10)
        (self.folders.source / "b.pdf").write_bytes(b"y" * 30)

        result = generate_output(plan)

        part_folder = self.folders.destination / PART_ONE
        self.assertEqual(sorted(item.name for item in part_folder.iterdir()), ["a.pdf", "b.pdf"])
        self.assertEqual(result.copied_pdf_count, 2)
        self.assertEqual([folder.total_size_bytes for folder in result.generated_part_folders], [20])

    def test_conflicts_cancel_generation_without_any_writes(self):
        plan = self.plan({"alpha.pdf": 10})
        part_folder = self.folders.destination / PART_ONE
        part_folder.mkdir()
        (part_folder / "notes.txt").write_text("keep me")
        source_before = self.folders.snapshot(self.folders.source)
        destination_before = self.folders.snapshot(self.folders.destination)

        result = generate_output(plan)

        self.assertTrue(result.cancelled)
        self.assertEqual(result.output_conflicts, detect_conflicts(plan))
        self.assertEqual(result.generated_part_folders, ())
        self.assertEqual(result.copied_pdf_count, 0)
        self.assertEqual(result.generated_part_folder_count, 0)
        self.assertEqual(self.folders.snapshot(self.folders.source), source_before)
        self.assertEqual(self.folders.snapshot(self.folders.destination), destination_before)

    def test_repeat_run_is_cancelled_and_preserves_the_first_output(self):
        plan = self.plan({"alpha.pdf": 10})
        first = generate_output(plan)
        self.assertFalse(first.cancelled)
        destination_before = self.folders.snapshot(self.folders.destination)

        second = generate_output(plan)

        self.assertTrue(second.cancelled)
        self.assertEqual(self.folders.snapshot(self.folders.destination), destination_before)

    def test_result_and_generated_part_folders_are_immutable_and_public(self):
        plan = self.plan({"alpha.pdf": 10})

        result = generate_output(plan)

        self.assertIsInstance(result, GenerationResult)
        self.assertIsInstance(result.generated_part_folders[0], GeneratedPartFolder)
        with self.assertRaises(FrozenInstanceError):
            result.cancelled = True
        with self.assertRaises(FrozenInstanceError):
            result.generated_part_folders[0].path = self.folders.destination


if __name__ == "__main__":
    unittest.main()
