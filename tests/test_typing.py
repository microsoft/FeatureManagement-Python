# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Static typing regression tests for feature manager APIs."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_feature_manager_call_types(tmp_path: Path, asynchronous: bool) -> None:
    """Verify supported calls retain their exact return types."""
    module = "featuremanagement.aio" if asynchronous else "featuremanagement"
    definition = "async def" if asynchronous else "def"
    await_expression = "await " if asynchronous else ""
    calls = [
        '"Alpha"',
        'feature_flag_id="Alpha"',
        '"Alpha", custom_context=42',
        '"Alpha", "user"',
        '"Alpha", "user", custom_context=42',
        '"Alpha", context',
        '"Alpha", context, custom_context=42',
    ]
    source = (
        "from typing import Optional\n"
        "from typing_extensions import assert_type\n"
        "from featuremanagement import TargetingContext, Variant\n"
        f"from {module} import FeatureManager\n\n"
        f"{definition} check(manager: FeatureManager, context: TargetingContext) -> None:\n"
    )
    for arguments in calls:
        source += f"    assert_type({await_expression}manager.is_enabled({arguments}), bool)\n"
        source += f"    assert_type({await_expression}manager.get_variant({arguments}), Optional[Variant])\n"

    fixture = tmp_path / "feature_manager_typing.py"
    fixture.write_text(source, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", "--no-incremental", str(fixture)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
