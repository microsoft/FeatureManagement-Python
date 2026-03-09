# Copilot Instructions

## Python Environment

Always activate and use the Python virtual environment when running Python commands:

- On Windows: `.venv\Scripts\activate`
- On Linux/macOS: `source .venv/bin/activate`

Use `python -m pip` instead of bare `pip` when installing packages.

## Dev Setup

Install all dependencies with:

```
python -m pip install -e ".[dev,test]"
```

## Python Version

This project requires Python 3.10 or newer.

## Project Structure

- `featuremanagement/` — Synchronous feature management code
- `featuremanagement/aio/` — Async equivalents of feature management classes
- `featuremanagement/_models/` — Data models (feature flags, variants, telemetry)
- `featuremanagement/_time_window_filter/` — Time window filter with recurrence support
- `featuremanagement/azuremonitor/` — Optional Azure Monitor telemetry integration
- `tests/` — Unit tests (sync and async)
- `samples/` — Sample applications

## Code Conventions

- All source files must include the Microsoft copyright header.
- All modules must have a module-level docstring.
- Maximum line length is 120 characters.
- Use type annotations on all functions and methods.

## Code Quality

Run these before submitting changes:

```
black featuremanagement
pylint featuremanagement
mypy featuremanagement
pytest tests
```

## Testing

- Sync tests are in `tests/test_*.py`
- Async tests use `pytest-asyncio` and are in files ending with `_async.py`
- Run tests with: `pytest tests`
