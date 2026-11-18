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

    def describe_parts(self, plan):
        return [
            (
                part.name,
                [(pdf.filename, pdf.size_bytes) for pdf in part.pdfs],
                part.total_size_bytes,
                part.has_oversized_pdf,
            )
            for part in plan.part_folders
        ]

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

    def test_ordinary_pdfs_are_packed_with_next_fit_in_discovery_order(self):
        source, destination = self.create_plan_fixture(
            {"c.pdf": 400, "b.pdf": 600, "a.pdf": 600}
        )

        plan = build_plan(source, destination, "book 53 august", 1 / 1024)

        self.assertEqual(
            self.describe_parts(plan),
            [
                ("BOOK 53 AUGUST PART_001", [("a.pdf", 600)], 600, False),
                (
                    "BOOK 53 AUGUST PART_002",
                    [("b.pdf", 600), ("c.pdf", 400)],
                    1000,
                    False,
                ),
            ],
        )

    def test_exact_limit_is_ordinary_and_one_byte_over_is_flagged(self):
        source, destination = self.create_plan_fixture(
            {"a-exact.pdf": 1024, "b-over.pdf": 1025}
        )

        plan = build_plan(source, destination, "book 53 august", 1 / 1024)

        self.assertEqual(
            self.describe_parts(plan),
            [
                (
                    "BOOK 53 AUGUST PART_001",
                    [("a-exact.pdf", 1024)],
                    1024,
                    False,
                ),
                (
                    "BOOK 53 AUGUST PART_002",
                    [("b-over.pdf", 1025)],
                    1025,
                    True,
                ),
            ],
        )

    def test_oversized_pdf_is_placed_inline_between_fresh_parts(self):
        source, destination = self.create_plan_fixture(
            {
                "a-small.pdf": 600,
                "b-huge.pdf": 2000,
                "c-small.pdf": 500,
                "d-small.pdf": 500,
            }
        )

        plan = build_plan(source, destination, "book 53 august", 1 / 1024)

        self.assertEqual(
            self.describe_parts(plan),
            [
                (
                    "BOOK 53 AUGUST PART_001",
                    [("a-small.pdf", 600)],
                    600,
                    False,
                ),
                (
                    "BOOK 53 AUGUST PART_002",
                    [("b-huge.pdf", 2000)],
                    2000,
                    True,
                ),
                (
                    "BOOK 53 AUGUST PART_003",
                    [("c-small.pdf", 500), ("d-small.pdf", 500)],
                    1000,
                    False,
                ),
            ],
        )

    def test_first_pdf_oversized_does_not_create_an_empty_part(self):
        source, destination = self.create_plan_fixture(
            {"a-huge.pdf": 2000, "b-small.pdf": 100}
        )

        plan = build_plan(source, destination, "book 53 august", 1 / 1024)

        self.assertEqual(
            self.describe_parts(plan),
            [
                (
                    "BOOK 53 AUGUST PART_001",
                    [("a-huge.pdf", 2000)],
                    2000,
                    True,
                ),
                (
                    "BOOK 53 AUGUST PART_002",
                    [("b-small.pdf", 100)],
                    100,
                    False,
                ),
            ],
        )

    def test_part_numbers_are_gapless_and_expand_past_999(self):
        pdf_sizes = {f"p{index:04d}.pdf": 1 for index in range(1001)}
        source, destination = self.create_plan_fixture(pdf_sizes)

        plan = build_plan(source, destination, "book 53 august", 1 / (1024 * 1024))

        self.assertEqual(
            [part.name for part in plan.part_folders],
            [
                f"BOOK 53 AUGUST PART_{index:03d}"
                for index in range(1, 1002)
            ],
        )
        self.assertTrue(all(part.pdfs for part in plan.part_folders))

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
