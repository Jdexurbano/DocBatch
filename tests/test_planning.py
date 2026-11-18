import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

import tests
from docbatch.planning import PlanValidationError, build_plan


class BuildPlanTests(unittest.TestCase):
    def create_plan_fixture(self, pdf_sizes=None):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        root = Path(temporary_directory.name)
        source = root / "source"
        destination = root / "destination"
        source.mkdir()
        destination.mkdir()
        for filename, size in (pdf_sizes or {}).items():
            (source / filename).write_bytes(b"x" * size)
        return source, destination

    def snapshot(self, *folders):
        return {
            folder: sorted(item.name for item in folder.iterdir())
            for folder in folders
        }

    def test_build_plan_returns_normalized_part_folder_name(self):
        source, destination = self.create_plan_fixture({"alpha.pdf": 10})

        plan = build_plan(source, destination, "book 53 august")

        self.assertEqual(plan.batch_name, "BOOK 53 AUGUST")
        self.assertEqual(len(plan.part_folders), 1)
        self.assertEqual(plan.part_folders[0].name, "BOOK 53 AUGUST PART_001")

    def test_part_folder_exposes_ordered_pdfs_with_sizes(self):
        source, destination = self.create_plan_fixture(
            {"b.pdf": 20, "A.pdf": 5, "c.PDF": 7}
        )

        plan = build_plan(source, destination, "book 53 august")
        part = plan.part_folders[0]

        self.assertEqual(
            [(pdf.filename, pdf.size_bytes) for pdf in part.pdfs],
            [("A.pdf", 5), ("b.pdf", 20), ("c.PDF", 7)],
        )
        self.assertEqual(part.total_size_bytes, 32)
        self.assertEqual(
            part.path, destination.resolve() / "BOOK 53 AUGUST PART_001"
        )

    def test_plan_exposes_resolved_folders_and_default_part_size_limit(self):
        source, destination = self.create_plan_fixture({"alpha.pdf": 10})

        plan = build_plan(source, destination, "book 53 august")

        self.assertEqual(plan.source, source.resolve())
        self.assertEqual(plan.destination, destination.resolve())
        self.assertEqual(plan.max_size_bytes, 25 * 1024 * 1024)

    def test_plan_exposes_explicit_part_size_limit(self):
        source, destination = self.create_plan_fixture({"alpha.pdf": 10})

        plan = build_plan(source, destination, "book 53 august", 1.5)

        self.assertEqual(plan.max_size_bytes, int(1.5 * 1024 * 1024))

    def test_plan_is_immutable(self):
        source, destination = self.create_plan_fixture({"alpha.pdf": 10})
        plan = build_plan(source, destination, "book 53 august")
        part = plan.part_folders[0]
        pdf = part.pdfs[0]

        self.assertIsInstance(plan.part_folders, tuple)
        self.assertIsInstance(part.pdfs, tuple)
        with self.assertRaises(FrozenInstanceError):
            plan.batch_name = "OTHER"
        with self.assertRaises(FrozenInstanceError):
            part.name = "OTHER PART_001"
        with self.assertRaises(FrozenInstanceError):
            pdf.filename = "other.pdf"

    def test_build_plan_does_not_write_to_the_filesystem(self):
        source, destination = self.create_plan_fixture({"alpha.pdf": 10})
        before = self.snapshot(source, destination)

        plan = build_plan(source, destination, "book 53 august")

        self.assertFalse(plan.part_folders[0].path.exists())
        self.assertEqual(self.snapshot(source, destination), before)

    def test_validation_error_is_public(self):
        source, destination = self.create_plan_fixture({"alpha.pdf": 10})

        self.assertTrue(issubclass(PlanValidationError, Exception))
        self.assertIsNotNone(build_plan(source, destination, "book 53 august"))


if __name__ == "__main__":
    unittest.main()
