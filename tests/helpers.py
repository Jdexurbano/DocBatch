import tempfile
from pathlib import Path


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
