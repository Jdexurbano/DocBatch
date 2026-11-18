import tempfile
import unittest
from pathlib import Path

from docbatch.planning import build_plan

BATCH_NAME = "book 53 august"
PART_ONE = "BOOK 53 AUGUST PART_001"
PART_TWO = "BOOK 53 AUGUST PART_002"
PART_THREE = "BOOK 53 AUGUST PART_003"


class TemporaryFolders:
    def __init__(self, test_case, pdf_sizes=None):
        temporary_directory = tempfile.TemporaryDirectory()
        test_case.addCleanup(temporary_directory.cleanup)
        root = Path(temporary_directory.name)
        self.source = root / "source"
        self.destination = root / "destination"
        self.source.mkdir()
        self.destination.mkdir()
        for filename, size in (pdf_sizes or {}).items():
            self.pdf(filename, size)

    def pdf(self, filename, size):
        path = self.source / filename
        with path.open("wb") as handle:
            handle.truncate(size)
        return path

    def snapshot(self, folder):
        return {
            str(item.relative_to(folder)): (
                "folder" if item.is_dir() else item.read_bytes()
            )
            for item in sorted(
                folder.rglob("*"),
                key=lambda path: str(path.relative_to(folder)),
            )
        }


class PlanTestCase(unittest.TestCase):
    def setUp(self):
        self.folders = TemporaryFolders(self)

    def plan(self, pdf_sizes, max_size_mb=25):
        for filename, size in pdf_sizes.items():
            self.folders.pdf(filename, size)
        return build_plan(
            self.folders.source,
            self.folders.destination,
            BATCH_NAME,
            max_size_mb,
        )
