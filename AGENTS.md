# Repository Guidelines

## Project Structure & Module Organization

This is currently a planning workspace for **DocBacth**, not an implemented
application. Keep the repository root focused on project documentation:

- `README.md` introduces the project and links to its requirements.
- `PRD.md` is the source of truth for product behavior, acceptance criteria,
  and implementation decisions.
- `../original python scripts/` contains the legacy scripts referenced by the
  PRD. Treat them as behavioral reference; do not edit them from this
  repository unless the task explicitly includes that sibling directory.

When implementation begins, keep production code and tests in clearly named
top-level directories (for example, `src/` and `tests/`) and update this guide
with the actual layout.

## Build, Test, and Development Commands

Create and activate the isolated environment before installing dependencies:
`python -m venv .venv`, `.\.venv\Scripts\Activate.ps1`, then
`python -m pip install -r requirements.txt`. Keep third-party packages in
`requirements.txt`; `tkinter` is standard Python and is excluded. No
application build, linter, or test runner is configured yet. For documentation
changes, review rendered Markdown and verify relative links.

## Coding Style & Naming Conventions

Use concise Markdown with sentence-style headings and wrapped paragraphs.
Preserve the PRD's existing terminology: **PDF**, **Excel inventory**, **part
folder**, and **batch name**. Examples and requirements should use the stated
folder pattern: `BOOK 53 AUGUST PART_001`.

For future Python code, follow the implementation's tooling once chosen; until
then, prefer standard Python naming (`snake_case` functions and variables,
`PascalCase` classes) and avoid introducing dependencies without a documented
need.

## Testing Guidelines

There is no test framework or coverage target yet. The PRD requires automated
tests for PDF grouping, overwrite detection, and Excel filename conversion.
Place future tests under `tests/` and name them `test_<behavior>.py`, for
example `tests/test_grouping.py`. Include edge cases from the acceptance
criteria, especially oversized PDFs and invalid destination paths.

## Commit & Pull Request Guidelines

The repository has no commit history, so no local commit convention exists.
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
