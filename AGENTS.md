# Repository Guidelines

## Project Structure & Module Organization

This repository contains the project plans and the Phase 1 package foundation;
application behavior is not implemented yet. Documentation stays at the
repository root:

- `README.md` introduces the project and links to its requirements.
- `PRD.md` is the source of truth for product behavior, acceptance criteria,
  and implementation decisions.
- `ROADMAP.md` tracks the delivery phases.
- `GLOSSARY.md` and `docs/adr/` record domain terms and architecture decisions.
- `../original python scripts/` contains the legacy scripts referenced by the
  PRD. Treat them as behavioral reference; do not edit them from this
  repository unless the task explicitly includes that sibling directory.

Application code lives in the `src/docbatch/` package and tests live in the
`tests/` package.

## Build, Test, and Development Commands

Create and activate the isolated environment before installing the pinned
dependencies: `python -m venv .venv`, `.\.venv\Scripts\Activate.ps1`, then
`python -m pip install -r requirements.txt`. Keep third-party packages in
`requirements.txt`; `tkinter` is standard Python and is excluded. Tests use the
standard-library `unittest` runner; run `python -m unittest discover -s tests -v`
from the repository root with `.venv` active. No linter is configured yet. For
documentation changes, review rendered Markdown and verify relative links.

## Coding Style & Naming Conventions

Use concise Markdown with sentence-style headings and wrapped paragraphs.
Preserve the PRD's existing terminology: **PDF**, **Excel inventory**, **part
folder**, and **batch name**. Examples and requirements should use the stated
folder pattern: `BOOK 53 AUGUST PART_001`.

Python code uses standard Python naming (`snake_case` functions and variables,
`PascalCase` classes); avoid introducing dependencies without a documented need.

## Testing Guidelines

Tests use the standard-library `unittest` framework in the `tests/` package;
run `python -m unittest discover -s tests -v` from the repository root with
`.venv` active. There is no coverage target yet. The PRD requires automated
tests for PDF grouping, overwrite detection, and Excel filename conversion.
Name test modules `test_<behavior>.py`, for example `tests/test_grouping.py`.
Include edge cases from the acceptance criteria, especially oversized PDFs and
invalid destination paths.

## Commit & Pull Request Guidelines

Use short imperative commit subjects, for example `Add PDF grouping tests`.
Keep each change scoped. Pull requests should explain the behavior changed,
link the relevant PRD section or issue, list validation performed, and include
screenshots for user-interface changes.

## Safety & Configuration

Never move, rename, overwrite, or modify source PDFs. The PRD requires copied
output, explicit overwrite confirmation, and a Windows-installable app without
a separate Python installation. Keep file-system behavior aligned with those
constraints.

## Agent skills

### Issue tracker

Issues and specs are tracked in this repository's GitHub Issues. See
`docs/agents/issue-tracker.md`.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md`.
