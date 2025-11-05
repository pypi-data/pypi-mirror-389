# Repository Guidelines

## Project Structure & Module Organization
- `src/satellitecenter/` hosts runtime code; `main.py` exposes the CLI entry `satellitecenter.main:main`.
- `src/satellitecenter/config/` stores Python indicator mappings packaged with releases; update schema docs before modifying.
- `src/satellitecenter/utils/` groups reusable helpers (encryption, config loading, standardization); keep new helpers pure and well tested.
- `tests/` mirrors runtime modules via `test_*.py`; shared fixtures belong in `tests/conftest.py`.
- CLI adapters reside in `interface.py`; packaging metadata is tracked through `pyproject.toml` and `satellitecenter.egg-info/`.
- `scripts/` contains automation such as Nuitka compilation; `build/` and `dist/` are generated outputs and should stay untracked.

## Build, Test, and Development Commands
- `uv pip install -e ".[dev]"` sets up an editable install with full tooling.
- `uv run python -m build` creates source and wheel artifacts inside `dist/`.
- `uv run python scripts/compile_to_executable.py` produces a standalone binary under `dist_executable/`.
- `uv run python interface.py --help` verifies CLI wiring after refactors.
- `uv run pytest` executes the suite with coverage gates (`--cov-fail-under=60` via pyproject).

## Coding Style & Naming Conventions
- Format with Black (88-char lines, 4-space indents) using `uv run black src/ tests/`.
- Lint with Ruff (`E,F,I,N,W,B,C90`); autofix using `uv run ruff check src/ tests/ --fix`.
- Keep snake_case for functions/modules, PascalCase for classes, and UPPER_SNAKE_CASE for constants.
- Add type hints to new public APIs; validate through `uv run mypy src/`.
- Configuration modules (e.g., `indicator_mapping.py`) should stay Black-formatted; any JSON overrides keep two-space indents and trailing newline.

## Testing Guidelines
- Place unit tests alongside related modules using the `test_<module>.py` pattern.
- Raise coverage above the 60% gate when touching core logic; add regression cases for new utilities.
- Centralize fixtures in `tests/conftest.py` and avoid stateful globals in tests.
- Recreate key CLI flows with sample CSVs to ensure interface parity.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`); keep subjects ≤72 characters.
- Squash WIP commits locally and ensure each commit leaves the project runnable.
- Pull requests should summarize motivation, list major changes, and attach test evidence (`uv run pytest`).
- Link issues when relevant and include CLI output or screenshots for user-visible updates.

## Release & Versioning Notes
- `setuptools_scm` manages versions; never edit `src/satellitecenter/_version.py` manually.
- Tag releases as `vX.Y.Z` so builds pick up the correct version and update `RELEASE.md` with highlights.
