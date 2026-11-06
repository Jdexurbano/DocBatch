# Product Requirements Document: DocBacth

## 1. Product summary

Build a Windows desktop application that replaces the two existing command-line
scripts with one guided workflow:

1. Copy PDFs from a source folder into numbered, size-limited part folders.
2. Create an Excel inventory of the PDFs in every created part folder.

The application is intended for staff preparing document batches for upload or
submission. It must be distributable to another Windows computer without a
separate Python installation.

## 2. Source of truth

The initial release preserves the useful behavior documented in
[`../original python scripts/documentation.md`](../original%20python%20scripts/documentation.md):

- PDFs are copied, not moved or modified.
- Part folders use a configurable name prefix and a three-digit sequence.
- The maximum combined size per ordinary part is configurable up to 25 MB.
- One Excel file is created in each part folder.
- Excel document names are derived from known filename abbreviations.

## 3. Goals

- Replace typed folder paths and two separate scripts with one simple desktop
  workflow.
- Prevent accidental overwrites and make the destination clear before files
  are copied.
- Produce the same deliverables: numbered PDF folders and one Excel inventory
  per folder.
- Package the application as an installable Windows application.

## 4. Non-goals for the first release

- Splitting a single PDF into smaller PDFs.
- Reading, OCR-ing, editing, or merging PDF contents.
- Cloud upload, user accounts, network synchronization, or multi-user access.
- Custom Excel templates beyond the existing two-column table.

## 5. Users

### Document-processing staff

Need to prepare a folder of PDFs for a size-limited submission and receive an
Excel list for each resulting part.

### Office administrator

Needs to install the application on another Windows computer and update the
batch name or size limit without editing Python source code.

## 6. User workflow

1. The user opens the application.
2. The user selects a source folder containing PDFs.
3. The user selects an empty or approved destination folder.
4. The user enters a batch name, for example `book 53 august`.
5. The app converts the batch name to uppercase and previews the resulting
   folder structure, for example `BOOK 53 AUGUST PART_001`.
6. The user sets the maximum part size, from greater than 0 MB up to 25 MB.
7. The user reviews a summary: PDF count, total size, destination, and
   overwrite warning when applicable.
8. The user starts processing.
9. The app copies PDFs into folders such as `BOOK 53 AUGUST PART_001`.
10. The app creates `<part folder name>.xlsx` in every generated part folder.
11. The app shows a completion summary, including the generated folders,
    sizes, skipped files, and any errors.

## 7. Functional requirements

### 7.1 Input validation

- The app must require an existing source folder and destination folder.
- The source and destination must not be the same folder.
- The batch name must not be empty and must not contain Windows-invalid folder
  characters: `\\ / : * ? " < > |`.
- The app must convert the batch name to uppercase before creating folders.
- The app must display a live naming helper in the form
  `<UPPERCASE BATCH NAME> PART_001`; the user enters the batch name only, not
  `PART_` or the sequence number.
- The maximum size must be a positive number of megabytes and no greater than
  25 MB.
- Only top-level `.pdf` files in the source folder are processed.
- The app must show a clear message and stop if no PDFs are found.

### 7.2 PDF grouping and copying

- Process PDFs in alphabetical filename order for predictable results.
- Copy PDFs; never move, rename, delete, or alter source PDFs.
- Create folders using the normalized batch name followed by ` PART_001`,
  ` PART_002`, and so on.
- Keep the combined size of ordinary PDFs in each part at or below the chosen
  limit.
- Place an oversized individual PDF in its own part folder and label it in the
  final summary as exceeding the limit.
- Before copying, detect destination folders or files that would be
  overwritten. The user must explicitly choose to cancel or replace them.

### 7.3 Excel inventory

- Create one `.xlsx` file in each generated part folder.
- Use a worksheet named `Files` with columns `No.` and `Document Name`.
- Sort the PDF list alphabetically before numbering it.
- Use the existing abbreviation mapping:

  | Abbreviation | Document name |
  | --- | --- |
  | DOS | Deed of Sale |
  | DOAS | Deed of Absolute Sale |
  | SPA | Special Power of Attorney |
  | ULA | Uniform Loan Agreement |
  | Pakyaw CA | Pakyaw Contract Agreement |
  | CA | Contract Agreement |
  | AOU | Affidavit of Understanding |
  | AOC | Affidavit of Claim |
  | AOL | Affidavit of Loss |
  | AOV | Affidavit of Verification |
  | COE | Certificate of Employment |
  | COS | Contract of Service |
  | RWQ | Release, Waiver, Quitclaim |

- If no abbreviation matches, use the portion of the filename before the first
  underscore, excluding the `.pdf` extension.
- Before applying abbreviation matching or the fallback rule, remove one
  leading numeric prefix in the form `<digits>_`. For example,
  `54_Name of the file.pdf` becomes `Name of the file`; a filename that does
  not begin with digits followed by an underscore is unchanged.

### 7.4 Results and errors

- Show progress while processing large batches.
- Show the result count, generated folder paths, and each part's total size.
- Report unreadable files, copy failures, and Excel-writing failures without
  hiding the affected filename.
- Provide a button to open the destination folder after completion.

### 7.5 Distribution

- Package the app as a Windows executable that runs without Python installed.
- Provide an installer with an uninstall entry and optional Start Menu/Desktop
  shortcut.
- Include all required Python dependencies, including `openpyxl`.

## 8. UX requirements

- Use standard Windows folder-picking dialogs; users should not need to type
  paths manually.
- Keep the main screen to source-folder and destination-folder pickers, batch
  name, size limit, a live folder-name helper, and one primary `Process files`
  action.
- Do not start file operations until the user confirms the displayed summary.
- Errors and overwrite warnings must use plain language and identify the file
  or folder involved.

## 9. Technical approach

Use Python with a lightweight native desktop UI such as `tkinter` and package
it with PyInstaller. Reuse the existing script logic where correct, while
moving configuration from source code into the interface.

Developers must install third-party packages in a project-local `.venv`
virtual environment. List every third-party dependency in `requirements.txt`;
the initial list is `openpyxl` for Excel inventory creation and `PyInstaller`
for executable packaging. `tkinter` is part of the standard Python
distribution and does not belong in `requirements.txt`.

The application should be structured around two testable operations:

1. Build the part-folder plan and copy PDFs.
2. Create each Excel inventory from the resulting PDFs.

## 10. Acceptance criteria

The first release is ready when all of the following are true:

1. A user can select folders without entering a path manually.
2. Processing a source folder of PDFs produces correctly numbered part folders
   and never changes the source PDFs.
3. Ordinary part folders do not exceed the selected size limit.
4. Every generated part folder contains a correctly named Excel inventory.
5. The Excel inventory has sequential numbering, a `Files` worksheet, and
   expected abbreviation conversions.
6. The app warns before replacing an existing destination file or folder.
7. An oversized single PDF is preserved in its own part and is clearly
   reported.
8. The installed application launches and processes files on a Windows
   computer without Python installed.
9. A batch name entered as `book 53 august` produces folder names beginning
   with `BOOK 53 AUGUST PART_`.
10. The app rejects a maximum part size greater than 25 MB.
11. `54_Name of the file.pdf` is listed as `Name of the file`, while
    `Name of the file.pdf` is handled without removing any text.

## 11. Decisions needed before implementation

1. **ZIP output:** The original script says “zipping” but does not zip files.
   The first release assumes folders only. Confirm whether each part must also
   be delivered as a `.zip` archive.
2. **Oversized PDF rule:** Confirm whether a single PDF larger than the size
   limit may be submitted as-is or needs a separate manual process.
3. **Overwrite policy:** The proposed default is to stop and ask the user;
   confirm whether replacing existing output should ever be allowed.
4. **Excel naming:** Confirm whether the current abbreviation list is complete
   and whether names should be editable in the app.

## 12. Delivery artifacts

- Windows installer or distributable executable.
- This PRD and a short operator guide.
- Source code and automated tests for grouping, overwrite detection, and Excel
  filename conversion.
