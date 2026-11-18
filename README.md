# DocBatch

A guided Windows desktop application that organizes PDF files into upload-sized
folders and creates an Excel inventory for every folder.

- [Product requirements document](PRD.md)
- [Operator guide](OPERATOR-GUIDE.md)
- [Release validation checklist](docs/release/validation-checklist.md)
- [Original-script documentation](../original%20python%20scripts/documentation.md)

The source scripts remain in `../original python scripts/` and are the behavioral
reference for the legacy scripts replaced by this application.

## Development environment

The foundation is verified with Python 3.14.2 (3.14.x); no other Python versions
are claimed as supported.

Use a virtual environment for every local installation so project packages do
not affect the system Python installation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run `deactivate` when finished. Re-activate `.venv` before installing packages
or running project tools.

## Tests

With the virtual environment active, run the single test command from the
repository root:

```powershell
python -m unittest discover -s tests -v
```

## Dependencies

| Package | Purpose |
| --- | --- |
| `openpyxl` | Creates the `.xlsx` inventory in each generated part folder. |
| `PyInstaller` | Packages the Python desktop app as a Windows executable. |

`tkinter` is the native UI toolkit and is included with standard Python on
Windows, so it is not listed in `requirements.txt`.

## Windows release

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

The build produces a one-folder PyInstaller bundle in `dist\DocBatch`. When
Inno Setup 6 is installed and `iscc` is on `PATH`, it also produces
`dist\installer\DocBatch-1.0.0-setup.exe`. Inno Setup is a build prerequisite;
the build script does not install it. The installer writes only to
`%LOCALAPPDATA%\Programs\DocBatch` and never touches Source or Destination
folders.

Generate sample PDFs for release validation with
`.\.venv\Scripts\python.exe scripts\make_sample_pdfs.py .\sample-pdfs`, then
follow [the release validation checklist](docs/release/validation-checklist.md).
