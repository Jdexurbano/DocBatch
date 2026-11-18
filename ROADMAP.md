# DocBatch Roadmap

## Release scope

The first release creates numbered PDF part folders and one Excel inventory per
folder. It does not create ZIP archives, edit PDFs, or allow editable document
name mappings. An oversized PDF is copied into its own part folder and clearly
reported. Existing output requires an explicit replacement confirmation.

## Phase 1: Project foundation

Create the Python project layout, keep third-party packages in `.venv`, and
install from `requirements.txt`. Use standard-library `unittest`; place tests
under `tests/` and application code under `src/`.

**Done when:** a clean environment can install dependencies and run the test
suite.

## Phase 2: Batch planning and validation

Implement a testable operation that validates source and destination folders,
normalizes the batch name, sorts top-level PDFs, and produces a part-folder
plan. Default the editable part-size limit to 25 MB. Detect no-PDF input,
invalid names, same-folder input/output, and oversized PDFs.

**Done when:** unit tests cover normal grouping, the 25 MB boundary, oversized
files, invalid inputs, and deterministic folder names such as
`BOOK 53 AUGUST PART_001`.

## Phase 3: Safe output generation

Implement the planned folder creation and PDF copying without changing source
files. Detect every output conflict before writing; cancel by default and only
replace after explicit confirmation. Report unreadable files and copy failures
with their filenames.

**Done when:** tests prove source PDFs are unchanged and conflicts cannot be
silently overwritten.

## Phase 4: Excel inventories

Create one `Files` worksheet per part folder using `openpyxl`. Apply the fixed
abbreviation mapping and numeric-prefix removal rules, then save the inventory
as `<part folder name>.xlsx`.

**Done when:** tests verify worksheet names, numbering, mapping behavior,
fallback names, and one workbook per generated folder.

## Phase 5: Guided desktop workflow

Build the `tkinter` screen: source and destination pickers, batch name,
editable size limit, live folder-name preview, review summary, confirmation,
progress, errors, and an option to open the destination folder.

**Done when:** a user can complete the PRD workflow without entering file
paths manually or using the command line.

## Phase 6: Windows release

Build the application with PyInstaller and package it in an Inno Setup
installer with an uninstall entry. Validate installation and processing on a
Windows computer without a separate Python installation.

**Done when:** the installed application meets every PRD acceptance criterion.
