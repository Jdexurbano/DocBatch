# Src-layout tests use a bootstrap instead of an editable install

Phase 1 keeps application code in `src/docbatch/` and tests in `tests/` using only
standard-library `unittest`; `tests/__init__.py` prepends `src/` to `sys.path` so
`python -m unittest discover -s tests -v` works without a `pyproject.toml` or an
editable install. This avoids adding build tooling during the foundation phase, at
the cost of a small path shim that every test relies on; revisit when packaging
begins in Phase 6.
