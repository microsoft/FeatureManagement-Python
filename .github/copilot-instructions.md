# FEATURE MANAGEMENT FOR PYTHON - COPILOT INSTRUCTIONS

---

## CORE PRINCIPLES

### RULE 1: DO NOT REPEAT INSTRUCTIONS
**NEVER repeat instructions when guiding users. Users should follow instructions independently.**

### RULE 2: REFERENCE OFFICIAL DOCUMENTATION
**ALWAYS** reference the [Azure SDK Python Design Guidelines](https://azure.github.io/azure-sdk/python_design.html)
- Link to specific pages when answering guidelines questions
- Use this as the authoritative source for SDK development guidance

### RULE 3: VERIFY ENVIRONMENT FIRST
**REQUIRED CONDITIONS:**
- Always activate the Python virtual environment before running Python commands:
  - On Windows: `.venv\Scripts\activate`
  - On Linux/macOS: `source .venv/bin/activate`
- Use `python -m pip` instead of bare `pip` when installing packages.

---

## DEV SETUP

Install all dependencies with:

```bash
python -m pip install -e ".[dev,test]"
```

This project requires **Python 3.10 or newer**.

---

## PROJECT STRUCTURE

- `featuremanagement/` — Synchronous feature management code
- `featuremanagement/aio/` — Async equivalents of feature management classes
- `featuremanagement/_models/` — Data models (feature flags, variants, telemetry)
- `featuremanagement/_time_window_filter/` — Time window filter with recurrence support
- `featuremanagement/azuremonitor/` — Optional Azure Monitor telemetry integration
- `tests/` — Unit tests (sync and async)
- `samples/` — Sample applications

---

## CODE CONVENTIONS

- All source files must include the Microsoft copyright header.
- All modules must have a module-level docstring.
- Maximum line length is 120 characters.
- Use type annotations on all functions and methods.

---

## CODE FORMATTING

### RUNNING BLACK

**COMMAND:**
```bash
black featuremanagement
```

Line length is configured to 120 in `pyproject.toml`.

**Always run black before pylint and mypy**, as formatting fixes can resolve issues those tools detect.

---

## PYLINT OPERATIONS

### RUNNING PYLINT

**COMMAND:**
```bash
pylint featuremanagement
```

### FIXING PYLINT WARNINGS

**ALLOWED ACTIONS:**
- ✅ Fix warnings with 100% confidence
- ✅ Use existing files for all solutions
- ✅ Reference official guidelines

**FORBIDDEN ACTIONS:**
- ❌ Fix warnings without complete confidence
- ❌ Create new files for solutions
- ❌ Import non-existent modules
- ❌ Add new dependencies/imports
- ❌ Make unnecessary large changes
- ❌ Change code style without reason
- ❌ Delete code without clear justification

---

## MYPY OPERATIONS

### RUNNING MYPY

**COMMAND:**
```bash
mypy featuremanagement
```

The project uses `strict = True` in `mypy.ini`.

---

## TESTING

### RUNNING TESTS

**COMMAND:**
```bash
pytest tests
```

- Sync tests are in `tests/test_*.py`
- Async tests use `pytest-asyncio` and are in files ending with `_async.py`
- Run tests with: `pytest tests`

---

## NEW FEATURES

When adding a new user-facing feature or capability:

- Create a sample in `samples/` demonstrating the feature.
- Add corresponding unit tests (sync and async where applicable).
