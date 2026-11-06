# Issue tracker: GitHub

Issues and specs for this repository live in GitHub Issues. Use the `gh` CLI;
it infers `Jdexurbano/DocBatch` from the Git remote.

## Conventions

- Create an issue: `gh issue create --title "..." --body "..."`.
- Read an issue: `gh issue view <number> --comments`.
- List issues: `gh issue list --state open` with appropriate labels or state.
- Comment, edit labels, or close: use `gh issue comment`, `gh issue edit`, and
  `gh issue close` respectively.

When a skill says to publish to the issue tracker, create a GitHub issue. When
it says to fetch a relevant ticket, run `gh issue view <number> --comments`.

## Pull requests as a triage surface

**PRs as a request surface: no.** Set this to `yes` only if external pull
requests should be triaged as feature requests.
