#!/usr/bin/env python3
"""Offline release readiness checklist for Ariadne."""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
from collections.abc import Iterable
from pathlib import Path

try:
    import tomllib as tomllib_compat  # Python >=3.11
except ModuleNotFoundError:  # pragma: no cover - fallback for Python 3.10
    try:
        import tomli as tomllib_compat  # type: ignore[no-redef]
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SystemExit("tomllib/tomli not available. Install 'tomli' or use Python 3.11+.") from exc


@dataclasses.dataclass
class CheckResult:
    name: str
    status: str  # "ok", "warning", "error"
    details: str

    def formatted(self) -> str:
        symbol = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(self.status, "•")
        return f"{symbol} {self.name}: {self.details}"


def load_pyproject(path: Path) -> dict:
    try:
        return tomllib_compat.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Could not locate pyproject.toml at {path}") from exc


def check_pyproject_metadata(root: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    data = load_pyproject(root / "pyproject.toml")
    project = data.get("project", {})

    required_fields = ["name", "description", "requires-python", "readme", "license"]
    for field in required_fields:
        value = project.get(field)
        if value:
            results.append(CheckResult(f"pyproject:{field}", "ok", f"{field!r} field is populated"))
        else:
            results.append(CheckResult(f"pyproject:{field}", "error", f"{field!r} field is missing"))

    dynamic = project.get("dynamic", [])
    if "version" in dynamic:
        results.append(CheckResult("pyproject:version", "ok", "dynamic version is managed by setuptools_scm"))
    else:
        results.append(CheckResult("pyproject:version", "error", "'version' is not declared as dynamic"))

    dependencies = project.get("dependencies", [])
    if dependencies:
        unpinned = [dep for dep in dependencies if not any(op in dep for op in ("==", ">=", "<=", "~=", "!="))]
        if unpinned:
            results.append(
                CheckResult(
                    "pyproject:dependencies", "warning", f"Found unpinned core dependencies: {', '.join(unpinned)}"
                )
            )
        else:
            results.append(
                CheckResult("pyproject:dependencies", "ok", f"All {len(dependencies)} core dependencies are pinned")
            )
    else:
        results.append(CheckResult("pyproject:dependencies", "error", "no core dependencies configured"))

    optional_deps = project.get("optional-dependencies", {})
    duplicates = find_duplicate_optional_dependencies(optional_deps)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        results.append(
            CheckResult("pyproject:optional extras", "warning", f"duplicate packages found across extras: {joined}")
        )
    else:
        results.append(
            CheckResult("pyproject:optional extras", "ok", f"{len(optional_deps)} optional dependency groups defined")
        )

    scripts = project.get("scripts", {})
    if "ariadne" in scripts:
        results.append(CheckResult("pyproject:console script", "ok", "CLI entry point 'ariadne' configured"))
    else:
        results.append(CheckResult("pyproject:console script", "warning", "CLI entry point missing"))

    scm_config = data.get("tool", {}).get("setuptools_scm", {})
    write_to = scm_config.get("write_to")
    if write_to and (root / write_to).exists():
        results.append(CheckResult("setuptools_scm", "ok", f"Version file configured at {write_to}"))
    else:
        results.append(
            CheckResult("setuptools_scm", "error", "setuptools_scm write_to path is missing or file not generated")
        )

    return results


def find_duplicate_optional_dependencies(optional_deps: dict[str, Iterable[str]]) -> set[str]:
    seen: dict[str, str] = {}
    duplicates: set[str] = set()
    for group, packages in optional_deps.items():
        for requirement in packages:
            normalized = requirement.split(";")[0].strip().lower()
            if normalized in seen and seen[normalized] != group:
                duplicates.add(normalized)
            else:
                seen.setdefault(normalized, group)
    return duplicates


def check_changelog(root: Path, version: str | None) -> list[CheckResult]:
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.exists():
        return [CheckResult("changelog", "error", "CHANGELOG.md is missing")]

    content = changelog_path.read_text(encoding="utf-8")
    headings = re.findall(r"^## \[(.+?)\]", content, flags=re.MULTILINE)
    if not headings:
        return [CheckResult("changelog", "error", "No version headings found in CHANGELOG.md")]

    latest = headings[0]
    results = [CheckResult("changelog:latest", "ok", f"Latest entry detected for version {latest}")]

    if version:
        if latest.startswith(version):
            results.append(
                CheckResult("changelog:version", "ok", f"Latest changelog entry matches requested version {version}")
            )
        else:
            results.append(
                CheckResult(
                    "changelog:version", "warning", f"Requested version {version} does not match latest entry {latest}"
                )
            )
    return results


def check_documentation(root: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    readme = root / "README.md"
    if readme.exists():
        results.append(CheckResult("docs:README", "ok", "Project README present"))
    else:
        results.append(CheckResult("docs:README", "error", "README.md is missing"))

    release_doc = root / "docs" / "project" / "RELEASE_MANAGEMENT.md"
    if release_doc.exists():
        text = release_doc.read_text(encoding="utf-8")
        if "Release Checklist" in text:
            results.append(CheckResult("docs:release management", "ok", "Release checklist documented"))
        else:
            results.append(CheckResult("docs:release management", "warning", "Release checklist section missing"))
    else:
        results.append(CheckResult("docs:release management", "error", "Release management guide missing"))

    return results


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local release readiness checks")
    parser.add_argument("--version", help="Expected release version (e.g. 0.4.1)")
    return parser.parse_args(argv)


def run_checks(root: Path, version: str | None) -> list[CheckResult]:
    results: list[CheckResult] = []
    results.extend(check_pyproject_metadata(root))
    results.extend(check_changelog(root, version))
    results.extend(check_documentation(root))
    return results


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(__file__).resolve().parent.parent
    results = run_checks(root, args.version)

    has_error = False
    for result in results:
        print(result.formatted())
        if result.status == "error":
            has_error = True

    if args.version:
        print()
        print("Next steps:")
        print("  • Run 'make test' to execute the full QA suite.")
        print("  • Build artifacts with 'python -m build' once dependencies are installed.")
        print("  • Validate metadata using 'twine check dist/*'.")
        print("  • Upload to TestPyPI before promoting to PyPI.")

    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
