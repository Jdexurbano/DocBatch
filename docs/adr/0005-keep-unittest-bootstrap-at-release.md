# Keep the unittest bootstrap in the Windows release

Status: Accepted in Phase 5.

Phase 1's `tests/__init__.py` path shim was flagged for revisit when packaging
tooling arrived. The combined desktop-and-release phase introduces PyInstaller,
but neither a build backend nor an editable install is needed to build the
application, so we keep the shim and leave `pyproject.toml` out. The trade-off
remains that every test depends on a small path shim; adding build tooling would
only duplicate what `unittest discover` already does here.
