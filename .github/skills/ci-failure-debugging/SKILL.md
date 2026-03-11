---
name: ci-failure-debugging
description: >
  Debug and fix failing CI validation checks for this Python project.
  Use when asked to fix CI failures, debug failing PR checks, fix pylint/mypy/black/cspell/pytest errors,
  or when a PR validation workflow fails.
---

# CI Failure Debugging

This project's PR validation runs the following checks on Python 3.10–3.14. To debug failures, identify which step failed and follow the corresponding section below.

## Step 1: Identify the failing check

The validation workflow runs these steps in order:

1. **black** — code formatting
2. **pylint** — static analysis
3. **mypy** — type checking (strict mode)
4. **cspell** — spell checking
5. **pytest** — unit tests with coverage
6. **pylint (samples/tests)** — lint samples and tests with relaxed rules

## Step 2: Reproduce locally

Set up the environment first:

```bash
python -m pip install -e ".[dev,test]"
```

Then run the specific failing check:

| Check | Command | Notes |
|-------|---------|-------|
| pylint | `pylint featuremanagement` | |
| black | `black --check featuremanagement` | Use `black featuremanagement` to auto-fix |
| mypy | `mypy featuremanagement` | Uses `strict = True` from `mypy.ini` |
| cspell | `npx cspell "**"` | Config in `cspell.config.yaml`, custom words in `project-words.txt` |
| pytest | `pytest tests --doctest-modules --cov-report=xml --cov-report=html` | |
| pylint (samples) | `pylint --disable=missing-function-docstring,missing-class-docstring samples tests` | Requires `python -m pip install -r samples/requirements.txt` |

## Step 3: Fix the issue

### pylint failures

- Run `pylint featuremanagement` and fix reported issues.
- Do NOT add `# pylint: disable` comments unless absolutely necessary.
- Do NOT add new imports or dependencies to fix warnings.
- The project disables `duplicate-code` in `pyproject.toml`.
- Max line length is 120. Min public methods is 1. Max branches is 20. Max returns is 7.

### black failures

- Run `black featuremanagement` to auto-format. Line length is 120 (configured in `pyproject.toml`).
- If CI uses `black --check`, it means files need reformatting — run `black` locally to fix.

### mypy failures

- Run `mypy featuremanagement`. The project uses `strict = True` with Python 3.10 target.
- All functions must have type annotations.
- Use `Optional[X]` or `X | None` for nullable types.
- Check `mypy.ini` for the full configuration.

### cspell failures

- Misspelled words: fix the typo in your code.
- Legitimate technical terms: add the word to `project-words.txt` (one word per line, alphabetically sorted).
- Do NOT modify `cspell.config.yaml` unless adding a new ignore path.

### pytest failures

- Run `pytest tests` to reproduce.
- Sync tests: `tests/test_*.py`
- Async tests: `tests/test_*_async.py` (use `pytest-asyncio`)
- Time window filter tests: `tests/time_window_filter/`
- Telemetry tests: `tests/test_send_telemetry_appinsights.py`
- If adding new code, ensure both sync and async tests exist where applicable.

### pylint (samples/tests) failures

- This step runs with `--disable=missing-function-docstring,missing-class-docstring`.
- Requires sample dependencies: `python -m pip install -r samples/requirements.txt`.
- Fix any remaining pylint issues in `samples/` and `tests/` directories.
