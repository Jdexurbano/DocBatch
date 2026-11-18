# Release validation checklist

Validate the installed application on a clean Windows computer with no Python
installation. Build the sample PDFs on a development machine, then copy the
generated folder to the clean machine:

```powershell
.\.venv\Scripts\python.exe scripts\make_sample_pdfs.py .\sample-pdfs
```

The sample folder includes `54_Name of the file.pdf`, `Name of the file.pdf`,
`DOS deed.pdf`, ordinary PDFs, and `oversized.pdf` (26 binary MB). Use a Part-size
limit of 25 MB so the last file is an oversized PDF. Copy the whole sample folder
to the clean machine and select it as the source folder; never run the validation
against originals.

Evidence: save screenshots of the Review summary and Completion summary into a
release evidence folder and record their paths below.

| PRD criterion | Result | Evidence |
| --- | --- | --- |
| 1. Folders selected with pickers, no manual path entry | [ ] | |
| 2. Numbered part folders created; source PDFs unchanged | [ ] | |
| 3. Ordinary part folders stay within the selected limit | [ ] | Review: |
| 4. Every part folder has a correctly named Excel inventory | [ ] | |
| 5. Inventory has sequential numbering, `Files` sheet, abbreviation conversions | [ ] | |
| 6. Warning shown before replacing existing output | [ ] | Review: |
| 7. Oversized PDF preserved alone and clearly reported | [ ] | Completion: |
| 8. Installed app runs without Python installed | [ ] | |
| 9. `book 53 august` produces `BOOK 53 AUGUST PART_` folders | [ ] | Review: |
| 10. Part-size limit above 25 MB is rejected | [ ] | |
| 11. `54_Name of the file.pdf` becomes `Name of the file`; unprefixed name intact | [ ] | |

Additional release checks:

- [ ] Start Menu and Desktop shortcuts launch the installed application.
- [ ] The application has an uninstall entry and uninstalls cleanly.
- [ ] Reinstalling leaves source and destination folder contents unchanged.
- [ ] Cancelling a run with output conflicts writes nothing.
- [ ] Replace confirmation names the part folders that will be removed.
- [ ] Completion summary names every skipped file and error and marks partial output.
- [ ] Progress bar reaches 100% when processing finishes.
- [ ] **Process files** has a green background only after a successful review.
- [ ] A completed run clears Source folder, Destination folder, and Batch name,
      while keeping the part-size limit; a cancelled run keeps them.
- [ ] **Open destination folder** opens the chosen destination folder.

Validated by: ______________________  Date: ______________

Review screenshot path: ______________________________________________

Completion screenshot path: __________________________________________
