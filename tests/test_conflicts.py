import unittest
from dataclasses import FrozenInstanceError

import tests
from docbatch.generation import OutputConflict, detect_conflicts

from tests.helpers import PART_ONE, PART_TWO, PlanTestCase


class DetectConflictsTests(PlanTestCase):
    def describe_conflicts(self, conflicts):
        return [(conflict.kind, conflict.name) for conflict in conflicts]

    def test_existing_part_folder_is_reported_without_changing_the_destination(self):
        plan = self.plan({"alpha.pdf": 10})
        (self.folders.destination / PART_ONE).mkdir()
        before = self.folders.snapshot(self.folders.destination)

        conflicts = detect_conflicts(plan)

        self.assertEqual(self.describe_conflicts(conflicts), [("part_folder", PART_ONE)])
        self.assertEqual(conflicts[0].path, plan.destination / PART_ONE)
        self.assertIn(PART_ONE, conflicts[0].message)
        self.assertEqual(self.folders.snapshot(self.folders.destination), before)

    def test_existing_pdfs_are_reported_in_planned_pdf_order(self):
        plan = self.plan({"b.pdf": 20, "a.pdf": 10, "c.pdf": 30})
        part_folder = self.folders.destination / PART_ONE
        part_folder.mkdir()
        (part_folder / "c.pdf").write_bytes(b"old")
        (part_folder / "a.pdf").write_bytes(b"old")

        conflicts = detect_conflicts(plan)

        self.assertEqual(
            self.describe_conflicts(conflicts),
            [("part_folder", PART_ONE), ("pdf", "a.pdf"), ("pdf", "c.pdf")],
        )
        self.assertEqual(conflicts[1].path, part_folder / "a.pdf")
        self.assertIn("a.pdf", conflicts[1].message)
        self.assertIn("c.pdf", conflicts[2].message)

    def test_conflicts_are_ordered_part_folder_then_pdf_across_parts(self):
        plan = self.plan({"a.pdf": 600, "b.pdf": 600}, max_size_mb=1 / 1024)
        first = self.folders.destination / PART_ONE
        second = self.folders.destination / PART_TWO
        first.mkdir()
        second.mkdir()
        (first / "a.pdf").write_bytes(b"old")
        (second / "b.pdf").write_bytes(b"old")
        (self.folders.destination / "notes.txt").write_text("unrelated")
        (self.folders.destination / "OLD BATCH PART_001").mkdir()

        conflicts = detect_conflicts(plan)

        self.assertEqual(
            self.describe_conflicts(conflicts),
            [
                ("part_folder", PART_ONE),
                ("pdf", "a.pdf"),
                ("part_folder", PART_TWO),
                ("pdf", "b.pdf"),
            ],
        )

    def test_case_different_paths_collide_but_messages_keep_plan_spelling(self):
        plan = self.plan({"alpha.pdf": 10})
        existing_folder = self.folders.destination / PART_ONE.lower()
        existing_folder.mkdir()
        (existing_folder / "ALPHA.PDF").write_bytes(b"old")

        conflicts = detect_conflicts(plan)

        self.assertEqual(
            self.describe_conflicts(conflicts),
            [("part_folder", PART_ONE), ("pdf", "alpha.pdf")],
        )
        self.assertEqual(conflicts[0].path, plan.destination / PART_ONE)
        self.assertEqual(conflicts[1].path, plan.destination / PART_ONE / "alpha.pdf")
        self.assertIn(PART_ONE, conflicts[0].message)
        self.assertIn("alpha.pdf", conflicts[1].message)

    def test_file_at_planned_part_folder_path_is_reported(self):
        plan = self.plan({"alpha.pdf": 10})
        (self.folders.destination / PART_ONE).write_bytes(b"occupied")

        conflicts = detect_conflicts(plan)

        self.assertEqual(self.describe_conflicts(conflicts), [("part_folder", PART_ONE)])

    def test_directory_at_planned_pdf_path_is_reported(self):
        plan = self.plan({"alpha.pdf": 10})
        part_folder = self.folders.destination / PART_ONE
        part_folder.mkdir()
        (part_folder / "alpha.pdf").mkdir()

        conflicts = detect_conflicts(plan)

        self.assertEqual(
            self.describe_conflicts(conflicts),
            [("part_folder", PART_ONE), ("pdf", "alpha.pdf")],
        )

    def test_conflicts_are_immutable_and_public(self):
        plan = self.plan({"alpha.pdf": 10})
        (self.folders.destination / PART_ONE).mkdir()

        conflicts = detect_conflicts(plan)

        self.assertIsInstance(conflicts, tuple)
        self.assertIsInstance(conflicts[0], OutputConflict)
        with self.assertRaises(FrozenInstanceError):
            conflicts[0].name = "OTHER"


if __name__ == "__main__":
    unittest.main()
