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

## Phase 5: Guided desktop workflow and Windows release

Add a testable orchestration service that composes planning, safe generation,
and Excel inventory creation and requires explicit confirmation before any
write. Build the `tkinter` view around it with source and destination pickers,
batch name, editable size limit, live folder-name preview, **Review summary**,
**Completion summary**, progress, errors, and a button that opens the
destination folder; run the batch on a worker thread and poll progress with Tk
`after()`. Unit-test the service and pure view helpers with `unittest`, and keep
actual UI interaction on a manual checklist.

Package the application with PyInstaller in one-folder mode and author an Inno
Setup script that installs `DocBatch` 1.0.0 per user under
`%LOCALAPPDATA%\Programs\DocBatch` with Start Menu and Desktop shortcuts and an
uninstall entry; re-installing never touches user source or destination folders.
Inno Setup is a documented build prerequisite. Deliver `OPERATOR-GUIDE.md` and
validate on a clean Windows machine without Python using generated sample PDFs,
including `54_Name of the file.pdf` and one oversized PDF, with a signed-off
checklist against every PRD acceptance criterion and completion-summary
screenshots.

**Done when:** the installed application completes the PRD workflow on a Windows
computer without a separate Python installation, without manual path entry or
the command line, and meets every PRD acceptance criterion.
