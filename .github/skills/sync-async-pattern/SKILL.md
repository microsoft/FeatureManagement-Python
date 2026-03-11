---
name: sync-async-pattern
description: >
  Guide for implementing sync/async mirrored code in this project.
  Use when adding new classes, methods, or feature filters that need both sync and async versions,
  or when modifying existing sync code that has an async counterpart in featuremanagement/aio/.
---

# Sync/Async Mirroring Pattern

This project maintains parallel sync and async implementations. Every change to sync code in `featuremanagement/` must be mirrored in `featuremanagement/aio/`, and vice versa.

## Directory mapping

| Sync | Async |
|------|-------|
| `featuremanagement/_featuremanager.py` | `featuremanagement/aio/_featuremanager.py` |
| `featuremanagement/_featurefilters.py` | `featuremanagement/aio/_featurefilters.py` |
| `featuremanagement/_defaultfilters.py` | `featuremanagement/aio/_defaultfilters.py` |
| `featuremanagement/__init__.py` | `featuremanagement/aio/__init__.py` |

Shared code that does NOT have an async counterpart:
- `featuremanagement/_featuremanagerbase.py` — base class used by both sync and async `FeatureManager`
- `featuremanagement/_models/` — data models imported by both
- `featuremanagement/_time_window_filter/` — time window logic (no I/O, used as-is)
- `featuremanagement/azuremonitor/` — telemetry (no async version)

## Copyright header

Every source file MUST start with:

```python
# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
```

Followed by a module-level docstring.

## How to convert sync to async

### Classes

- Keep the **same class name** (e.g., both are `FeatureManager`). Users disambiguate by import path.
- Both sync and async `FeatureManager` inherit from `FeatureManagerBase`.

### Methods

- Add `async` to method definitions: `def evaluate(...)` → `async def evaluate(...)`
- Add `await` to calls that invoke filters, callbacks, or accessors.

### Default filters (composition pattern)

Async default filters do NOT duplicate logic. They wrap the sync implementation:

```python
from .._defaultfilters import TimeWindowFilter as SyncTimeWindowFilter

class TimeWindowFilter(FeatureFilter):
    def __init__(self):
        self._filter = SyncTimeWindowFilter()

    @FeatureFilter.alias("Microsoft.TimeWindow")
    async def evaluate(self, context, **kwargs):
        return self._filter.evaluate(context, **kwargs)
```

Use this pattern for any new filter whose `evaluate` does not perform I/O.

### Callbacks and accessors

The async `FeatureManager` supports BOTH sync and async callbacks. Use `inspect.iscoroutinefunction` to detect and handle both:

```python
import inspect

if inspect.iscoroutinefunction(self._on_feature_evaluated):
    await self._on_feature_evaluated(result)
else:
    self._on_feature_evaluated(result)
```

### Imports

- Sync files import from `._models`, `._featurefilters`, etc.
- Async files import from `.._models`, `.._featurefilters`, etc. (one level up from `aio/`).

## `__init__.py` exports

### Sync (`featuremanagement/__init__.py`)

Exports everything: `FeatureManager`, filters, all models, `__version__`, and defines `__all__`.

### Async (`featuremanagement/aio/__init__.py`)

Exports ONLY async-specific classes: `FeatureManager`, `FeatureFilter`, `TimeWindowFilter`, `TargetingFilter`. Does NOT re-export models or `__version__` — users import those from the sync package.

When adding a new public class:
1. Add to sync `__init__.py` with `__all__` entry.
2. If it has an async version, add to async `__init__.py` with `__all__` entry.

## Test file naming

| Sync test | Async counterpart |
|-----------|-------------------|
| `tests/test_feature_manager.py` | `tests/test_feature_manager_async.py` |
| `tests/test_feature_variants.py` | `tests/test_feature_variants_async.py` |
| `tests/test_default_feature_flags.py` | `tests/test_default_feature_flags_async.py` |

- Async test files append `_async` to the sync filename.
- Async tests use `pytest-asyncio` with `@pytest.mark.asyncio` on test functions.
- Not every sync test needs an async counterpart (e.g., refresh and telemetry tests are sync-only).

## Checklist for adding new code

1. [ ] Write the sync implementation in `featuremanagement/`.
2. [ ] Write the async mirror in `featuremanagement/aio/` following the patterns above.
3. [ ] Export from both `__init__.py` files if public.
4. [ ] Write sync tests in `tests/test_*.py`.
5. [ ] Write async tests in `tests/test_*_async.py`.
6. [ ] Run all validation: `pylint featuremanagement`, `black featuremanagement`, `mypy featuremanagement`, `pytest tests`.
