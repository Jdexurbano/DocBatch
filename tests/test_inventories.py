import shutil
import unittest
from dataclasses import FrozenInstanceError

import tests
from docbatch.generation import generate_output
from docbatch.inventories import (
    InventoryFailure,
    InventoryResult,
    WrittenInventory,
    write_inventories,
)
from openpyxl import load_workbook

from tests.helpers import PART_ONE, PART_TWO, PlanTestCase


class WriteInventoriesTests(PlanTestCase):
    def rows(self, workbook_path, include_header=False):
        sheet = load_workbook(workbook_path)["Files"]
        return [
            tuple(cell.value for cell in row)
            for row in sheet.iter_rows(min_row=1 if include_header else 2)
        ]

    def test_writes_one_inventory_inside_each_generated_part_folder(self):
        plan = self.plan({"a.pdf": 600, "b.pdf": 600}, max_size_mb=1 / 1024)
        generation = generate_output(plan)
        source_before = self.folders.snapshot(self.folders.source)

        result = write_inventories(generation)

        self.assertIsInstance(result, InventoryResult)
        self.assertEqual(
            [(item.name, item.path) for item in result.written_inventories],
            [
                (PART_ONE, plan.part_folders[0].path / f"{PART_ONE}.xlsx"),
                (PART_TWO, plan.part_folders[1].path / f"{PART_TWO}.xlsx"),
            ],
        )
        self.assertEqual(
            [item.document_count for item in result.written_inventories], [1, 1]
        )
        for part in plan.part_folders:
            self.assertEqual(
                sorted(path.name for path in part.path.glob("*.xlsx")),
                [f"{part.name}.xlsx"],
            )
        self.assertEqual(result.inventory_failures, ())
        self.assertEqual(self.folders.snapshot(self.folders.source), source_before)

    def test_workbook_has_files_sheet_headers_integer_numbering_and_table_style(self):
        plan = self.plan({"alpha.pdf": 10})
        generation = generate_output(plan)

        result = write_inventories(generation)

        workbook = load_workbook(result.written_inventories[0].path)
        self.assertEqual(workbook.sheetnames, ["Files"])
        sheet = workbook["Files"]
        self.assertEqual(
            self.rows(result.written_inventories[0].path, include_header=True),
            [("No.", "Document Name"), (1, "alpha")],
        )
        self.assertIsInstance(sheet.cell(row=2, column=1).value, int)
        table = sheet.tables["FilesTable"]
        self.assertEqual(table.ref, "A1:B2")
        self.assertEqual(table.tableStyleInfo.name, "TableStyleLight8")
        self.assertFalse(table.tableStyleInfo.showFirstColumn)
        self.assertFalse(table.tableStyleInfo.showLastColumn)
        self.assertFalse(table.tableStyleInfo.showRowStripes)
        self.assertFalse(table.tableStyleInfo.showColumnStripes)

    def test_rows_use_actual_folder_pdfs_in_planning_order_with_uppercase_extension(self):
        plan = self.plan({"B.PDF": 10, "a.pdf": 10, "c.pdf": 10})
        generation = generate_output(plan)
        part_folder = generation.generated_part_folders[0].path
        (part_folder / "D.PDF").write_bytes(b"extra")
        (part_folder / "notes.txt").write_text("ignored")

        result = write_inventories(generation)

        self.assertEqual(
            self.rows(result.written_inventories[0].path),
            [(1, "a"), (2, "B"), (3, "c"), (4, "D")],
        )

    def test_pdf_that_failed_to_copy_is_not_listed_in_inventory(self):
        plan = self.plan({"a.pdf": 10, "missing.pdf": 20})
        (self.folders.source / "missing.pdf").unlink()
        generation = generate_output(plan)
        self.assertEqual(
            [failure.filename for failure in generation.copy_failures], ["missing.pdf"]
        )

        result = write_inventories(generation)

        self.assertEqual(self.rows(result.written_inventories[0].path), [(1, "a")])
        self.assertEqual(result.written_inventories[0].document_count, 1)

    def test_all_fixed_abbreviations_map_to_full_document_names(self):
        abbreviations = {
            "DOS": "Deed of Sale",
            "DOAS": "Deed of Absolute Sale",
            "SPA": "Special Power of Attorney",
            "ULA": "Uniform Loan Agreement",
            "Pakyaw CA": "Pakyaw Contract Agreement",
            "CA": "Contract Agreement",
            "AOU": "Affidavit of Understanding",
            "AOC": "Affidavit of Claim",
            "AOL": "Affidavit of Loss",
            "AOV": "Affidavit of Verification",
            "COE": "Certificate of Employment",
            "COS": "Contract of Service",
            "RWQ": "Release, Waiver, Quitclaim",
        }
        plan = self.plan({f"{abbreviation} sample.pdf": 10 for abbreviation in abbreviations})
        generation = generate_output(plan)

        result = write_inventories(generation)

        expected = [
            (number, abbreviations[abbreviation])
            for number, abbreviation in enumerate(
                [
                    "AOC",
                    "AOL",
                    "AOU",
                    "AOV",
                    "CA",
                    "COE",
                    "COS",
                    "DOAS",
                    "DOS",
                    "Pakyaw CA",
                    "RWQ",
                    "SPA",
                    "ULA",
                ],
                start=1,
            )
        ]
        self.assertEqual(self.rows(result.written_inventories[0].path), expected)

    def test_matching_ignores_case_and_pakyaw_ca_wins_over_ca(self):
        plan = self.plan({"pakyaw ca 2024.PDF": 10, "dos lower.pdf": 10})
        generation = generate_output(plan)

        result = write_inventories(generation)

        self.assertEqual(
            self.rows(result.written_inventories[0].path),
            [(1, "Deed of Sale"), (2, "Pakyaw Contract Agreement")],
        )

    def test_prefix_removal_and_fallback_rules_produce_document_names(self):
        plan = self.plan(
            {
                "54_Name of the file.pdf": 10,
                "Name of the file.pdf": 10,
                "7_54_Second group.pdf": 10,
                "12_AOU_Sworn.pdf": 10,
                "9_.pdf": 10,
                "54_.pdf": 10,
                "invoice_extra.pdf": 10,
                "plain name.pdf": 10,
            }
        )
        generation = generate_output(plan)

        result = write_inventories(generation)

        self.assertEqual(
            self.rows(result.written_inventories[0].path),
            [
                (1, "Affidavit of Understanding"),
                (2, "54_"),
                (3, "Name of the file"),
                (4, "54"),
                (5, "9_"),
                (6, "invoice"),
                (7, "Name of the file"),
                (8, "plain name"),
            ],
        )

    def test_single_pdf_and_oversized_pdf_part_folders_get_valid_inventories(self):
        plan = self.plan({"solo.pdf": 600, "huge.pdf": 2000}, max_size_mb=1 / 1024)
        generation = generate_output(plan)
        self.assertEqual(
            [part.has_oversized_pdf for part in generation.generated_part_folders],
            [True, False],
        )

        result = write_inventories(generation)

        self.assertEqual(len(result.written_inventories), 2)
        self.assertEqual(
            [self.rows(item.path) for item in result.written_inventories],
            [[(1, "huge")], [(1, "solo")]],
        )
        for item in result.written_inventories:
            workbook = load_workbook(item.path)
            self.assertEqual(workbook["Files"].tables["FilesTable"].ref, "A1:B2")

    def test_part_folder_with_no_pdfs_still_gets_header_only_inventory(self):
        plan = self.plan({"a.pdf": 10})
        (self.folders.source / "a.pdf").unlink()
        generation = generate_output(plan)

        result = write_inventories(generation)

        inventory = result.written_inventories[0]
        self.assertEqual(inventory.document_count, 0)
        self.assertEqual(
            self.rows(inventory.path, include_header=True),
            [("No.", "Document Name")],
        )
        sheet = load_workbook(inventory.path)["Files"]
        self.assertEqual(sheet.tables["FilesTable"].ref, "A1:B1")

    def test_cancelled_generation_writes_no_workbooks(self):
        plan = self.plan({"alpha.pdf": 10})
        (self.folders.destination / PART_ONE).mkdir()
        generation = generate_output(plan)
        self.assertTrue(generation.cancelled)
        destination_before = self.folders.snapshot(self.folders.destination)

        result = write_inventories(generation)

        self.assertEqual(result.written_inventories, ())
        self.assertEqual(result.inventory_failures, ())
        self.assertEqual(
            self.folders.snapshot(self.folders.destination), destination_before
        )

    def test_failure_names_its_part_folder_and_does_not_stop_other_inventories(self):
        plan = self.plan({"a.pdf": 600, "b.pdf": 600}, max_size_mb=1 / 1024)
        generation = generate_output(plan)
        broken = generation.generated_part_folders[0]
        good = generation.generated_part_folders[1]
        shutil.rmtree(broken.path)
        broken.path.write_bytes(b"occupied")

        result = write_inventories(generation)

        self.assertIsInstance(result, InventoryResult)
        self.assertEqual([item.name for item in result.written_inventories], [good.name])
        self.assertIsInstance(result.written_inventories[0], WrittenInventory)
        self.assertTrue((good.path / f"{good.name}.xlsx").exists())
        self.assertEqual(len(result.inventory_failures), 1)
        failure = result.inventory_failures[0]
        self.assertIsInstance(failure, InventoryFailure)
        self.assertEqual(failure.name, broken.name)
        self.assertEqual(failure.path, broken.path / f"{broken.name}.xlsx")
        self.assertTrue(failure.reason)
        with self.assertRaises(FrozenInstanceError):
            result.written_inventories = ()
        with self.assertRaises(FrozenInstanceError):
            result.written_inventories[0].document_count = 9
        with self.assertRaises(FrozenInstanceError):
            failure.name = "OTHER"


if __name__ == "__main__":
    unittest.main()
