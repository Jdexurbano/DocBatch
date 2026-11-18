# Replace confirmation recreates part folders

Status: Accepted in Phase 3.

When the user gives Replace confirmation, Phase 3 deletes each conflicting Part
folder and recreates it before copying, rather than merging into the existing
folder. Merging would leave PDFs from a previous batch in place, and Phase 4
builds each Excel inventory from whatever PDFs the folder actually contains, so
stale files would silently corrupt the inventory. The trade-off is that
replacement also removes unrelated files the user placed in that folder, so the
confirmation message must name the folders that will be removed.
