# DocBatch

Terms for the document-batching workflow and its generated deliverables.

## Language

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
An existing destination file or folder that would be replaced by planned
output, requiring the user to cancel or explicitly confirm replacement.
_Avoid_: Silent overwrite
