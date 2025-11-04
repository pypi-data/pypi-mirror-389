# Agent Platform

This project utilizes `uv` for all Python package management and virtual environment handling. All code
should be written using `asyncio`.

## Dev environment tips

- Run `uv sync` after updating dependencies to update the local environment.
- Do not use `pip`, `pip-tools`, `poetry`, or `conda` directly for dependency management in this project.
- We use ruff for linting and ruff for formatting.
- Make sure the `pre-commit.py` script passes after all changes are good and the user has indicated happiness with changes.
  This file automatically runs linting, formatting, and unit tests.
- Code style/linting changes should only be made after the core functional changes have been made and approved.

## Testing instructions

- **Execute scripts:** Use `uv run python <script_name>.py` to run Python scripts within the project's virtual environment.
- **Interactive Python:** Use `uv run python` to launch an interactive Python shell within the project's environment.
- **Testing instructions:** Run all tests using `uv run pytest`"

