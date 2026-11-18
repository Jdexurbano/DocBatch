# Part-size limit uses binary megabytes

Status: Accepted in Phase 2.

The part-size limit is expressed in binary megabytes (1 MB = 1,048,576 bytes),
matching the legacy `split_pdf.py` configuration and preserving its grouping
results. We rejected decimal megabytes (1,000,000 bytes), the SI standard,
because switching would silently change how many PDFs fit in a part folder and
could break submission limits calibrated against the original scripts.
