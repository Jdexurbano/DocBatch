# DocBatch

Terms for the document-batching workflow and its generated deliverables.

## Language

**Source folder**:
The existing folder whose top-level PDFs are read into a batch plan; its PDFs are
never moved, renamed, or modified.
_Avoid_: Input folder, origin folder

**Destination folder**:
The existing folder under which part folders are created; it must be distinct
from, and not nested with, the source folder.
_Avoid_: Output folder, target folder

**Batch name**:
The user-supplied label normalized to uppercase and used as the prefix of all
generated part folders.
_Avoid_: Folder name, file name

**Part folder**:
One numbered output folder containing copied PDFs whose combined size is within
the selected limit, except when it contains a single oversized PDF.
_Avoid_: ZIP, archive, batch folder

**Oversized PDF**:
A single PDF whose size exceeds the selected part-size limit; it occupies its
own part folder and is reported as exceeding the limit.
_Avoid_: Split PDF, rejected PDF

**Part-size limit**:
The maximum combined PDF size for an ordinary part folder. It defaults to 25
MB and must be greater than zero and no more than 25 MB.
_Avoid_: Upload limit, file-size limit

**Excel inventory**:
The `.xlsx` file in a part folder that lists that folder's PDFs and their
document names.
_Avoid_: Spreadsheet, Excel list

**Output conflict**:
An existing file or folder at a path the plan will write, requiring the user to
cancel or give Replace confirmation before anything is written.
_Avoid_: Silent overwrite, collision

**Replace confirmation**:
The explicit approval that lets generation replace Output conflicts; without
it, a run with conflicts is cancelled and writes nothing.
_Avoid_: Overwrite flag, force option
