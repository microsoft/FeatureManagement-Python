# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
"""Build a versioned documentation site from a verified stable release tag."""

import argparse
from collections.abc import Sequence
from html import escape
from html.parser import HTMLParser
from importlib import import_module
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit

from packaging.version import Version
from sphinx.application import Sphinx

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs" / "_build" / "site"


class HTMLPage(HTMLParser):
    """Collect the local references and anchors needed to validate a generated page."""

    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.anchors: set[str] = set()
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        anchor = attributes.get("id")
        if anchor:
            self.anchors.add(anchor)
        for attribute in ("href", "src"):
            reference = attributes.get(attribute)
            if reference:
                self.references.append(reference)
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def release_version(tag: str) -> str:
    """Derive a stable package version from the selected release tag."""
    if not tag.startswith("v"):
        raise ValueError(f"Expected a release tag named v<version>, found {tag!r}")
    version = Version(tag[1:])
    if version.is_prerelease or version.is_devrelease:
        raise ValueError(f"Only stable releases can be published as latest: {tag}")
    return str(version)


def verify_source(source: Path, tag: str) -> str:
    """Resolve the selected tag and reject a different or modified checkout."""
    commit = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    tagged = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if tagged.returncode:
        raise ValueError(f"Cannot resolve release tag {tag!r}: {tagged.stderr.strip()}")
    if commit != tagged.stdout.strip():
        raise ValueError(f"Checkout {commit} does not match release tag {tag} at {tagged.stdout.strip()}")
    changes = subprocess.run(
        ["git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if changes:
        raise ValueError(f"The release checkout has tracked changes:\n{changes}")
    return commit


def write_redirect(destination: Path, target: str) -> None:
    """Generate a relative redirect that retains search queries and API anchors."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    attribute = escape(target, quote=True)
    destination.write_text(
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">\n'
        "<title>Redirecting to FeatureManagement documentation</title>\n"
        f'<link rel="canonical" href="{attribute}">\n'
        f'<meta http-equiv="refresh" content="0; url={attribute}">\n'
        f"<script>location.replace({json.dumps(target)} + location.search + location.hash);</script>\n"
        f'</head><body><a href="{attribute}">View the documentation.</a></body></html>\n',
        encoding="utf-8",
    )


def assemble_redirects(site: Path, version: str) -> None:
    """Provide latest aliases and retain the previously published HTML page URLs."""
    pages = {page.name: page.name for page in (site / version).glob("*.html")}
    # Some releases document the synchronous API on their index page.
    pages.setdefault("featuremanagement.html", "index.html")
    write_redirect(site / "index.html", f"./{version}/index.html")
    for alias in ("latest", "html"):
        for name, target in pages.items():
            write_redirect(site / alias / name, f"../{version}/{target}")


def validate_site(site: Path, version: str, required_anchors: Sequence[str]) -> None:
    """Fail publication when generated pages have broken local links or anchors."""
    pages: dict[Path, HTMLPage] = {}
    for path in site.rglob("*.html"):
        page = HTMLPage()
        page.feed(path.read_text(encoding="utf-8"))
        pages[path.resolve()] = page
    for path, page in pages.items():
        for reference in page.references:
            url = urlsplit(reference)
            if url.scheme or url.netloc:
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if target.is_dir():
                target /= "index.html"
            if not target.is_relative_to(site.resolve()) or not target.is_file():
                raise ValueError(f"Broken local reference in {path}: {reference}")
            if url.fragment and target in pages and unquote(url.fragment) not in pages[target].anchors:
                raise ValueError(f"Broken anchor in {path}: {reference}")
    release = (site / version).resolve()
    if release / "index.html" not in pages:
        raise ValueError(f"Missing documentation index for {version}")
    anchors: set[str] = set()
    for path, page in pages.items():
        if path.is_relative_to(release):
            if version not in page.title:
                raise ValueError(f"Wrong documentation version in {path.name}: {page.title}")
            anchors.update(page.anchors)
    for anchor in required_anchors:
        if anchor not in anchors:
            raise ValueError(f"Missing released API: {anchor}")
    for alias in ("index.html", "latest/index.html", "html/index.html", "html/featuremanagement.html"):
        if not (site / alias).is_file():
            raise ValueError(f"Missing compatibility redirect: {alias}")


def release_api_anchors() -> list[str]:
    """Collect public API anchors from the imported release's feature managers."""
    anchors = []
    for module_name in ("featuremanagement", "featuremanagement.aio"):
        manager = import_module(module_name).FeatureManager
        anchors.append(f"{module_name}.FeatureManager")
        for name, member in vars(manager).items():
            if not name.startswith("_") and callable(member):
                anchors.append(f"{module_name}.FeatureManager.{name}")
    return anchors


def build_site(source: Path, tag: str) -> Path:
    """Render the tagged API and publish validated output to the ignored local build directory."""
    source = source.resolve()
    version = release_version(tag)
    commit = verify_source(source, tag)
    sys.path.insert(0, str(source))
    package = import_module("featuremanagement")
    package_file = package.__file__
    if package_file is None or not Path(package_file).resolve().is_relative_to(source):
        raise ValueError("The documentation process did not import the verified release checkout")
    if package.__version__ != version:
        raise ValueError(f"Release tag {tag} does not match package version {package.__version__}")
    required_anchors = release_api_anchors()

    with TemporaryDirectory(prefix="featuremanagement-docs-") as directory:
        temporary = Path(directory)
        documentation = temporary / "source" / "docs"
        documentation.mkdir(parents=True)
        shutil.copy2(source / "README.md", documentation.parent / "README.md")
        for path in (source / "docs").glob("*.rst"):
            shutil.copy2(path, documentation / path.name)
        site = temporary / "site"
        app = Sphinx(
            srcdir=str(documentation),
            confdir=str(ROOT / "docs" / "_sphinx"),
            outdir=str(site / version),
            doctreedir=str(temporary / "doctrees"),
            buildername="html",
            confoverrides={"release": version, "version": version},
            freshenv=True,
            warningiserror=True,
        )
        app.build(force_all=True)
        if app.statuscode:
            raise RuntimeError("The release documentation build failed; existing output was not replaced")
        assemble_redirects(site, version)
        (site / "release.json").write_text(
            json.dumps({"version": version, "tag": tag, "commit": commit}, indent=2) + "\n",
            encoding="utf-8",
        )
        validate_site(site, version, required_anchors)
        if SITE.exists():
            shutil.rmtree(SITE)
        shutil.copytree(site, SITE)
    print(f"Validated {tag} documentation: {SITE}")
    return SITE


def main() -> None:
    """Build the release checkout supplied by the workflow or a local Git worktree."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Clean checkout of the selected release tag")
    parser.add_argument("--tag", required=True, help="Stable release tag to verify and document (v<version>)")
    arguments = parser.parse_args()
    build_site(arguments.source, arguments.tag)


if __name__ == "__main__":
    main()
