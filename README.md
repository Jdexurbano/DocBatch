# DocBacth

Planning workspace for a Windows desktop application that organizes PDF files
into upload-sized folders and creates an Excel inventory for every folder.

- [Product requirements document](PRD.md)
- [Original-script documentation](../original%20python%20scripts/documentation.md)

The source scripts remain in `../original python scripts/` and are the current
behavioral reference until the application is implemented.

## Development environment

Use a virtual environment for every local installation so project packages do
not affect the system Python installation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run `deactivate` when finished. Re-activate `.venv` before installing packages
or running project tools.

## Dependencies

| Package | Purpose |
| --- | --- |
| `openpyxl` | Creates the `.xlsx` inventory in each generated part folder. |
| `PyInstaller` | Packages the Python desktop app as a Windows executable. |

`tkinter` is the planned native UI toolkit and is included with standard
Python on Windows, so it is not listed in `requirements.txt`.
