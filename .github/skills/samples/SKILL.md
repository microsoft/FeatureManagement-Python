---
name: samples
description: >
  Guide for creating or updating sample applications in this project.
  Use when adding a new sample, modifying an existing sample, or when asked to demonstrate
  a feature management capability with example code.
---

# Sample Applications

Samples live in `samples/` and demonstrate feature management capabilities to users.

## File conventions

- Every sample must have the Microsoft copyright header:
  ```python
  # ------------------------------------------------------------------------
  # Copyright (c) Microsoft Corporation. All rights reserved.
  # Licensed under the MIT License. See License.txt in the project root for
  # license information.
  # -------------------------------------------------------------------------
  ```
- Every sample must have a module-level docstring (one-liner describing what it demonstrates).
- Filename should end with `_sample.py` and describe what is being demonstrated (e.g., `feature_flag_sample.py`, `feature_variant_sample_with_telemetry.py`).

## Structure of a sample

Samples follow this general pattern:

```python
# (copyright header)
"""Sample demonstrating <what this shows>."""

import json
import os
import sys
from featuremanagement import FeatureManager, TargetingContext

# Load feature flags from the local JSON file
file_path = os.path.dirname(os.path.abspath(sys.argv[0]))
with open(os.path.join(file_path, "formatted_feature_flags.json"), encoding="utf-8") as f:
    feature_flags = json.load(f)

# Create FeatureManager
feature_manager = FeatureManager(feature_flags)

# Demonstrate the feature
result = feature_manager.is_enabled("FlagName")
print(f"FlagName is {'enabled' if result else 'disabled'}")
```

## Feature flag definitions

Sample feature flags go in `formatted_feature_flags.json` under `feature_management.feature_flags`. Each flag needs at minimum `id` and `enabled`. Add filters, variants, allocation, or telemetry as needed for the sample.

## Custom filters

Custom filters used by samples are defined in their own file (e.g., `random_filter.py`) and imported by the samples that need them.

## Async samples

Async samples import from `featuremanagement.aio` instead of `featuremanagement`. See `quarty_sample.py` for the async pattern.

## Azure-connected samples

Samples that connect to Azure App Configuration:
- Use `azure.appconfiguration.provider.load()` to get configuration
- Authenticate using `DefaultAzureCredential` from `azure-identity`, never connection strings
- List Azure dependencies in `samples/requirements.txt`

## Telemetry samples

Two patterns exist:
1. **Callback-based**: Pass `on_feature_evaluated=publish_telemetry` to `FeatureManager` and use `track_event()` from `featuremanagement.azuremonitor`.
2. **Web app span processor**: Use `TargetingSpanProcessor` from `featuremanagement.azuremonitor` with `configure_azure_monitor(span_processors=[...])`.

## Dependencies

Any new package a sample needs must be added to `samples/requirements.txt`. CI installs these before linting samples.

## Linting

Samples are linted with relaxed rules:
```bash
pylint --disable=missing-function-docstring,missing-class-docstring samples tests
```

Function and class docstrings are NOT required in samples, but module-level docstrings ARE.

## Checklist for adding a new sample

1. [ ] Create `samples/feature_<name>_sample.py` with copyright header and module docstring.
2. [ ] Add any new feature flags to `formatted_feature_flags.json`.
3. [ ] Add any new dependencies to `samples/requirements.txt`.
4. [ ] Verify lint passes: `pylint --disable=missing-function-docstring,missing-class-docstring samples`
