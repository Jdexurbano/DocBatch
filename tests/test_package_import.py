import unittest
from pathlib import Path

import tests


class DocbatchPackageImportTests(unittest.TestCase):
    def test_imports_package_from_source_tree(self):
        import docbatch

        package_init = Path(docbatch.__file__).resolve()
        expected_init = (
            Path(__file__).resolve().parent.parent
            / "src"
            / "docbatch"
            / "__init__.py"
        )
        self.assertEqual(package_init, expected_init.resolve())
