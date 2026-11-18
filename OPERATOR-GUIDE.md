# DocBatch operator guide

DocBatch copies the top-level PDFs from a source folder into numbered, size-limited
part folders and writes one Excel inventory into each part folder. It runs on a
Windows computer without a separate Python installation.

## Install

1. Run `DocBatch-1.0.0-setup.exe`.
2. The installer places the application under
   `%LOCALAPPDATA%\Programs\DocBatch`, adds Start Menu and Desktop shortcuts, and
   registers an uninstall entry. Administrator rights are not required.
3. Re-running the installer updates only the application files. Source PDFs and
   destination folder contents are never touched by installation or reinstall.

## Launch

Select **DocBatch** from the Start Menu or double-click the **DocBatch** desktop
shortcut. There is no command line to use and no Python installation to configure.

## Run a batch

1. Select **Browse...** beside **Source folder** and choose the folder containing
   the PDFs to copy. Only top-level `.pdf` files in that folder are used.
2. Select **Browse...** beside **Destination folder** and choose a different
   folder that is not inside the source folder. Part folders are created here.
3. Enter a **Batch name**, for example `book 53 august`. The live helper shows the
   first folder name, for example `BOOK 53 AUGUST PART_001`. Enter only the batch
   name, not `PART_` or a number.
4. Set the **Part-size limit** in MB. It must be greater than zero and no more
   than 25. The limit uses binary megabytes (1 MB = 1,048,576 bytes).
5. Select **Review summary**. Check the PDF count, total size, destination
   folder, part folder names, and any overwrite or oversized-PDF warning. Nothing
   has been written yet.
6. If an existing part folder would be replaced, review its name in the warning
   and tick **Replace conflicting Part folders** only when you intend to remove
   and recreate it. Leave the box unticked to cancel without writing anything.
   A successful review turns **Process files** green; it stays disabled until
   then.
7. Select **Process files** to confirm the review. The progress bar counts part
   folders and reaches 100% when the run finishes; the screen stays responsive.
8. Read the **Completion summary**. It lists generated folders and their sizes,
   skipped files, errors, and any replacement or oversized PDF. A run with errors
   keeps the files that were copied successfully and is marked as partial output.
   After output is written, **Source folder**, **Destination folder**, and
   **Batch name** are cleared for the next batch; the part-size limit is kept.
   A cancelled run keeps those fields so the conflict can be corrected.
9. Select **Open destination folder** to inspect the results.

Source PDFs are never moved, renamed, deleted, or modified. If a PDF is larger
than the Part-size limit, it is copied as-is into its own part folder and named
in both summaries.

## Uninstall

Open **Settings > Apps > Installed apps**, select **DocBatch**, and choose
**Uninstall**. You can also use the DocBatch entry in the Start Menu's app list.
Uninstalling removes only the installed application and its shortcuts; it does
not delete your source or destination folders.
