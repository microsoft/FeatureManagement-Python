# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
"""Regression tests for tagged documentation identity, redirects, and link validation."""

from pathlib import Path
import subprocess

import pytest

from scripts.build_release_docs import assemble_redirects, release_version, validate_site, verify_source


def make_site(site: Path, version: str = "2.2.0", variants: bool = True) -> list[str]:
    """Create a release site with only the API capabilities supplied by that release."""
    release = site / version
    release.mkdir()
    anchors = []
    for filename, module in (
        ("index.html", "featuremanagement"),
        ("featuremanagement.aio.html", "featuremanagement.aio"),
    ):
        methods = ["is_enabled", "get_variant"] if variants else ["is_enabled"]
        module_anchors = [f"{module}.FeatureManager"] + [f"{module}.FeatureManager.{method}" for method in methods]
        anchors.extend(module_anchors)
        (release / filename).write_text(
            f"<title>FeatureManagement {version}</title>"
            + "".join(f'<a id="{anchor}"></a>' for anchor in module_anchors),
            encoding="utf-8",
        )
    assemble_redirects(site, version)
    return anchors


def test_redirects_preserve_old_api_destinations(tmp_path: Path) -> None:
    """Route legacy synchronous API URLs to their actual location in the tagged documentation."""
    anchors = make_site(tmp_path)
    validate_site(tmp_path, "2.2.0", anchors)
    redirect = (tmp_path / "html" / "featuremanagement.html").read_text(encoding="utf-8")
    assert "../2.2.0/index.html" in redirect
    assert "+ location.search + location.hash" in redirect
    assert (tmp_path / "latest" / "featuremanagement.aio.html").is_file()


@pytest.mark.parametrize("reference", ["missing.js", "index.html#missing-anchor", "../../outside.html"])
def test_validation_rejects_broken_references(tmp_path: Path, reference: str) -> None:
    """Reject missing assets, broken API anchors, and references escaping the deployed site."""
    anchors = make_site(tmp_path)
    page = tmp_path / "2.2.0" / "index.html"
    page.write_text(page.read_text(encoding="utf-8") + f'<a href="{reference}">broken</a>', encoding="utf-8")
    with pytest.raises(ValueError, match="Broken"):
        validate_site(tmp_path, "2.2.0", anchors)


@pytest.fixture(name="tagged_source")
def tagged_source_fixture(tmp_path: Path) -> Path:
    """Create a repository with an arbitrary release commit rather than a production-specific SHA."""
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    (tmp_path / "release.txt").write_text("released", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "release.txt"], check=True)
    commit_source(tmp_path)
    subprocess.run(["git", "-C", str(tmp_path), "tag", "v2.2.0"], check=True)
    return tmp_path


def commit_source(source: Path) -> None:
    """Create an isolated test commit without relying on the user's Git identity or signing setup."""
    subprocess.run(
        [
            "git",
            "-C",
            str(source),
            "-c",
            "user.name=Documentation Test",
            "-c",
            "user.email=docs@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            "Documentation test commit",
        ],
        check=True,
    )


def test_source_rejects_non_release_checkout(tagged_source: Path) -> None:
    """Reject a newer checkout even when the requested release tag exists."""
    commit_source(tagged_source)
    with pytest.raises(ValueError, match="does not match release tag"):
        verify_source(tagged_source, "v2.2.0")


def test_source_resolves_selected_tag(tagged_source: Path) -> None:
    """Accept another release tag without a builder-specific version or commit constant."""
    subprocess.run(["git", "-C", str(tagged_source), "tag", "v3.1.0"], check=True)
    commit = subprocess.run(
        ["git", "-C", str(tagged_source), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert verify_source(tagged_source, "v3.1.0") == commit


def test_source_rejects_tracked_release_edits(tagged_source: Path) -> None:
    """Do not document local modifications as though they belonged to an immutable tag."""
    (tagged_source / "release.txt").write_text("modified", encoding="utf-8")
    with pytest.raises(ValueError, match="tracked changes"):
        verify_source(tagged_source, "v2.2.0")


def test_source_rejects_missing_tag(tagged_source: Path) -> None:
    """Report a missing release tag instead of accepting an otherwise clean checkout."""
    with pytest.raises(ValueError, match="Cannot resolve release tag"):
        verify_source(tagged_source, "v9.0.0")


def test_legacy_redirect_preserves_existing_api_page(tmp_path: Path) -> None:
    """Prefer a release's standalone synchronous API page when it exists."""
    make_site(tmp_path)
    (tmp_path / "2.2.0" / "featuremanagement.html").write_text(
        "<title>FeatureManagement 2.2.0</title>", encoding="utf-8"
    )
    assemble_redirects(tmp_path, "2.2.0")
    assert "../2.2.0/featuremanagement.html" in (tmp_path / "html" / "featuremanagement.html").read_text(
        encoding="utf-8"
    )


def test_older_api_does_not_require_variants(tmp_path: Path) -> None:
    """Validate older API capabilities without requiring methods introduced in later releases."""
    anchors = make_site(tmp_path, "1.0.0", variants=False)
    validate_site(tmp_path, "1.0.0", anchors)
    with pytest.raises(ValueError, match="Missing released API"):
        validate_site(tmp_path, "1.0.0", anchors + ["featuremanagement.FeatureManager.get_variant"])


@pytest.mark.parametrize("tag", ["main", "v2.0.0b1", "v2.3.0.dev1"])
def test_latest_rejects_non_stable_release_tags(tag: str) -> None:
    """Do not use a branch, prerelease, or development release as latest stable documentation."""
    with pytest.raises(ValueError):
        release_version(tag)
