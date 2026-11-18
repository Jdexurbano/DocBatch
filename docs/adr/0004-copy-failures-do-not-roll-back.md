# Copy failures do not roll back the run

Status: Accepted in Phase 3.

Phase 3 continues copying after an individual PDF fails and reports every
failure with its filename in the generation result; it does not stop at the
first error or delete folders already created. This keeps the completion summary
complete for Phase 5 and preserves successfully copied work. The trade-off is
that a run with failures leaves partial output on disk, which the summary must
make explicit. This policy applies only after conflict handling: a run with
Output conflicts and no Replace confirmation writes nothing at all.
