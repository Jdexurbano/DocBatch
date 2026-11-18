import math
import os
import unittest

import tests
from docbatch.planning import PlanValidationError, build_plan

from tests.helpers import TemporaryFolders


class ValidationTestCase(unittest.TestCase):
    def assert_messages(self, operation, *fragments):
        with self.assertRaises(PlanValidationError) as caught:
            operation()
        messages = caught.exception.messages
        for fragment in fragments:
            self.assertTrue(
                any(fragment in message for message in messages),
                f"{fragment!r} not found in {messages}",
            )
        return messages


class InputValidationTests(ValidationTestCase):
    def test_nonexistent_folders_are_reported_together(self):
        folders = TemporaryFolders(self, {"alpha.pdf": 10})
        missing_source = folders.source / "missing-source"
        missing_destination = folders.destination / "missing-destination"

        messages = self.assert_messages(
            lambda: build_plan(missing_source, missing_destination, "book 53 august"),
            "Source",
            "missing-source",
            "Destination",
            "missing-destination",
        )
        self.assertEqual(len(messages), 2)

    def test_every_blocking_problem_is_reported_together(self):
        folders = TemporaryFolders(self, {"alpha.pdf": 10})

        messages = self.assert_messages(
            lambda: build_plan(folders.source / "missing", folders.destination, "", 30),
            "Source",
            "Batch name",
            "Part-size limit",
        )
        self.assertEqual(len(messages), 3)

    def test_identical_and_nested_folders_are_rejected(self):
        folders = TemporaryFolders(self, {"alpha.pdf": 10})
        nested_under_source = folders.source / "child"
        nested_under_source.mkdir()
        (nested_under_source / "nested.pdf").write_bytes(b"x")
        nested_source = folders.destination / "source-child"
        nested_source.mkdir()
        (nested_source / "nested.pdf").write_bytes(b"x")
        case_alias = folders.source.parent / folders.source.name.swapcase()

        cases = (
            (folders.source, folders.source),
            (folders.source, case_alias),
            (folders.source, nested_under_source),
            (nested_source, folders.destination),
        )
        for source, destination in cases:
            with self.subTest(source=source, destination=destination):
                self.assert_messages(
                    lambda: build_plan(source, destination, "book 53 august"),
                    "distinct",
                    "nested",
                )

    def test_file_in_place_of_either_folder_is_rejected(self):
        folders = TemporaryFolders(self, {"alpha.pdf": 10})
        source_file = folders.source / "alpha.pdf"
        destination_file = folders.destination / "report.txt"
        destination_file.write_text("not a folder")

        messages = self.assert_messages(
            lambda: build_plan(source_file, destination_file, "book 53 august"),
            "Source",
            "not a folder",
            "Destination",
        )
        self.assertEqual(len(messages), 2)


class PdfDiscoveryTests(ValidationTestCase):
    def setUp(self):
        self.folders = TemporaryFolders(self)

    def plan(self):
        return build_plan(self.folders.source, self.folders.destination, "book 53 august")

    def test_source_without_pdfs_is_reported(self):
        self.assert_messages(self.plan, "No top-level PDFs")

    def test_only_top_level_regular_pdfs_are_discovered(self):
        alpha = self.folders.pdf("alpha.pdf", 3)
        self.folders.pdf("BETA.PDF", 5)
        self.folders.pdf(".hidden.pdf", 7)
        nested = self.folders.source / "nested"
        nested.mkdir()
        (nested / "nested.pdf").write_bytes(b"x")
        (self.folders.source / "folder.pdf").mkdir()
        (self.folders.source / "notes.txt").write_text("not a pdf")
        os.symlink(alpha, self.folders.source / "link.pdf")
        os.symlink(nested, self.folders.source / "folder-link.pdf")

        plan = self.plan()

        self.assertEqual(
            [pdf.filename for pdf in plan.part_folders[0].pdfs],
            [".hidden.pdf", "alpha.pdf", "BETA.PDF", "link.pdf"],
        )

    def test_ordering_is_case_insensitive_and_repeatable(self):
        for filename in ("b.pdf", "A.pdf", "c.PDF"):
            self.folders.pdf(filename, 1)

        first = [pdf.filename for pdf in self.plan().part_folders[0].pdfs]
        second = [pdf.filename for pdf in self.plan().part_folders[0].pdfs]

        self.assertEqual(first, ["A.pdf", "b.pdf", "c.PDF"])
        self.assertEqual(second, first)

    def test_unreadable_pdfs_are_reported_with_their_filenames(self):
        self.folders.pdf("readable.pdf", 1)
        os.symlink(self.folders.source / "missing-one", self.folders.source / "broken-one.pdf")
        os.symlink(self.folders.source / "missing-two", self.folders.source / "broken-two.pdf")

        self.assert_messages(self.plan, "broken-one.pdf", "broken-two.pdf")


class PartSizeLimitValidationTests(ValidationTestCase):
    def setUp(self):
        self.folders = TemporaryFolders(self, {"alpha.pdf": 10})

    def plan_with_limit(self, limit):
        return build_plan(self.folders.source, self.folders.destination, "book 53 august", limit)

    def test_invalid_limits_are_rejected(self):
        invalid_limits = (0, -1, -0.5, math.nan, math.inf, -math.inf, 25.1, 100, "abc", "25", True, None)
        for limit in invalid_limits:
            with self.subTest(limit=limit):
                self.assert_messages(lambda: self.plan_with_limit(limit), "Part-size limit")

    def test_valid_limits_use_binary_megabytes(self):
        for limit, expected in ((1, 1024 * 1024), (25, 25 * 1024 * 1024), (0.5, 512 * 1024)):
            with self.subTest(limit=limit):
                self.assertEqual(self.plan_with_limit(limit).max_size_bytes, expected)


class BatchNameValidationTests(ValidationTestCase):
    def setUp(self):
        self.folders = TemporaryFolders(self, {"alpha.pdf": 10})

    def plan_with_name(self, batch_name):
        return build_plan(self.folders.source, self.folders.destination, batch_name)

    def test_surrounding_whitespace_is_ignored_and_internal_spacing_preserved(self):
        plan = self.plan_with_name("  book  53  august")

        self.assertEqual(plan.batch_name, "BOOK  53  AUGUST")
        self.assertEqual(plan.part_folders[0].name, "BOOK  53  AUGUST PART_001")

    def test_non_ascii_batch_name_is_accepted(self):
        self.assertEqual(self.plan_with_name("café año").batch_name, "CAFÉ AÑO")

    def test_empty_whitespace_trailing_dot_and_trailing_space_are_rejected(self):
        for batch_name in ("", "   ", "bad.", "bad ", "bad. "):
            with self.subTest(batch_name=repr(batch_name)):
                self.assert_messages(lambda: self.plan_with_name(batch_name), "Batch name")

    def test_windows_invalid_characters_are_rejected(self):
        for character in '\\/:*?"<>|':
            with self.subTest(character=character):
                self.assert_messages(
                    lambda: self.plan_with_name(f"bad{character}name"),
                    "invalid characters",
                )

    def test_control_characters_are_rejected(self):
        for batch_name in ("bad\x01name", "bad\tname", "bad\x7fname"):
            with self.subTest(batch_name=repr(batch_name)):
                self.assert_messages(lambda: self.plan_with_name(batch_name), "control characters")

    def test_reserved_device_names_are_rejected(self):
        for batch_name in ("CON", "con", "COM1", "LPT9", "NUL", "CON.txt", "CON .txt"):
            with self.subTest(batch_name=batch_name):
                self.assert_messages(lambda: self.plan_with_name(batch_name), "reserved")


if __name__ == "__main__":
    unittest.main()
