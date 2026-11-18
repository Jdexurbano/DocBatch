# Src-layout tests use a bootstrap instead of an editable install

Status: Accepted in Phase 1.

Phase 1 keeps application code in `src/docbatch/` and tests in `tests/` using only
standard-library `unittest`; `tests/__init__.py` prepends `src/` to `sys.path` so
`python -m unittest discover -s tests -v` works without a `pyproject.toml` or an
editable install. We rejected adding a `pyproject.toml` and installing the package
in editable mode because that would introduce build tooling during the foundation
phase. The trade-off is a small path shim that every test relies on. The revisit during
the Windows release phase concluded that no build backend is needed; see ADR
0005.
