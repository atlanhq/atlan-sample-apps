#!/usr/bin/env python3

import argparse
import dataclasses
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclasses.dataclass(frozen=True)
class Finding:
    project_dir: str
    target: str
    vulnerability_id: str
    pkg_name: str
    severity: str
    installed_version: str
    fixed_version: str
    title: str


def _sha256(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _next_major_upper_bound(version: str) -> str:
    match = re.match(r"^\s*(\d+)", version)
    if not match:
        return ""
    major = int(match.group(1))
    return f",<{major + 1}.0.0"


def infer_project_dir(repo_root: Path, target: str) -> Optional[Path]:
    if not target:
        return None

    target_path = Path(target)
    if not target_path.is_absolute():
        target_path = (repo_root / target_path).resolve()

    candidate: Optional[Path] = None
    if target_path.is_file():
        candidate = target_path.parent
    elif target_path.exists() and target_path.is_dir():
        candidate = target_path
    else:
        # Best-effort: treat target as a relative file path and use its parent.
        candidate = (repo_root / Path(target).parent).resolve()

    current = candidate
    while current is not None:
        if not (current == repo_root or repo_root in current.parents):
            break
        if (current / "pyproject.toml").exists():
            return current
        if current == repo_root:
            break
        current = current.parent

    return None


def parse_trivy_findings(
    repo_root: Path, trivy_json: Dict[str, Any], severities: Set[str]
) -> Tuple[List[Finding], List[Finding]]:
    fixable: List[Finding] = []
    unfixable: List[Finding] = []

    results = trivy_json.get("Results") or []
    if not isinstance(results, list):
        return fixable, unfixable

    for result in results:
        if not isinstance(result, dict):
            continue

        target = str(result.get("Target") or "")
        project_dir = infer_project_dir(repo_root, target)
        if project_dir is None:
            continue

        vulnerabilities = result.get("Vulnerabilities") or []
        if not isinstance(vulnerabilities, list):
            continue

        for vuln in vulnerabilities:
            if not isinstance(vuln, dict):
                continue

            severity = str(vuln.get("Severity") or "").upper()
            if severity not in severities:
                continue

            pkg_name = str(vuln.get("PkgName") or "")
            if not pkg_name:
                continue

            installed_version = str(vuln.get("InstalledVersion") or "")
            fixed_version = str(vuln.get("FixedVersion") or "")
            vulnerability_id = str(vuln.get("VulnerabilityID") or vuln.get("VulnID") or "")
            title = str(vuln.get("Title") or vuln.get("Description") or "")

            finding = Finding(
                project_dir=str(project_dir.relative_to(repo_root)),
                target=target,
                vulnerability_id=vulnerability_id,
                pkg_name=pkg_name,
                severity=severity,
                installed_version=installed_version,
                fixed_version=fixed_version,
                title=title,
            )

            if fixed_version.strip():
                fixable.append(finding)
            else:
                unfixable.append(finding)

    return fixable, unfixable


def write_unfixable_issue(
    issue_path: Path, severities: Sequence[str], findings: Sequence[Finding]
) -> None:
    by_project: Dict[str, List[Finding]] = defaultdict(list)
    for finding in findings:
        by_project[finding.project_dir].append(finding)

    lines: List[str] = []
    lines.append("## Unfixable Trivy findings\n")
    lines.append(
        f"Trivy detected {', '.join(severities)} vulnerabilities with **no fixed version available**.\n"
    )
    lines.append("This workflow did **not** open an autofix PR.\n")

    for project_dir in sorted(by_project.keys()):
        lines.append(f"\n### `{project_dir}`\n")
        lines.append("| Severity | Package | Installed | Fixed | Vulnerability | Title |\n")
        lines.append("| --- | --- | --- | --- | --- | --- |\n")
        for finding in sorted(
            by_project[project_dir],
            key=lambda f: (f.severity, f.pkg_name, f.vulnerability_id),
        ):
            vuln = finding.vulnerability_id or "N/A"
            title = (finding.title or "").replace("\n", " ").strip()
            lines.append(
                f"| {finding.severity} | `{finding.pkg_name}` | `{finding.installed_version or 'N/A'}` | "
                f"`{finding.fixed_version or 'N/A'}` | `{vuln}` | {title or 'N/A'} |\n"
            )

    issue_path.write_text("".join(lines), encoding="utf-8")


def relax_pins(pyproject_path: Path, findings: Sequence[Finding]) -> List[str]:
    text = pyproject_path.read_text(encoding="utf-8")
    updated: List[str] = []
    new_text = text

    for finding in findings:
        if not finding.installed_version or not finding.fixed_version:
            continue

        old_spec = f"{finding.pkg_name}=={finding.installed_version}"
        upper = _next_major_upper_bound(finding.fixed_version)
        new_spec = f"{finding.pkg_name}>={finding.fixed_version}{upper}"

        for quote in ('"', "'"):
            old_token = f"{quote}{old_spec}{quote}"
            new_token = f"{quote}{new_spec}{quote}"
            if old_token in new_text:
                new_text = new_text.replace(old_token, new_token)
                updated.append(f"{old_spec} -> {new_spec}")

    if new_text != text:
        pyproject_path.write_text(new_text, encoding="utf-8")

    return sorted(set(updated))


def run_uv_lock(project_dir: Path, packages: Sequence[str]) -> subprocess.CompletedProcess[str]:
    cmd: List[str] = ["uv", "lock"]
    for pkg in packages:
        cmd.extend(["-P", pkg])

    return subprocess.run(
        cmd,
        cwd=str(project_dir),
        text=True,
        capture_output=True,
        check=False,
    )


def project_test_info(project_dir: Path) -> Tuple[bool, bool]:
    return (project_dir / "tests" / "unit").is_dir(), (project_dir / "tests" / "e2e").is_dir()


def write_summary(
    summary_path: Path,
    severities: Sequence[str],
    fixable_findings: Sequence[Finding],
    per_project_updates: Dict[str, Dict[str, Any]],
) -> None:
    by_project: Dict[str, List[Finding]] = defaultdict(list)
    for finding in fixable_findings:
        by_project[finding.project_dir].append(finding)

    lines: List[str] = []
    lines.append("## Security Autofix Summary\n\n")
    lines.append(f"- Severity threshold: `{','.join(severities)}`\n")
    lines.append(f"- Projects with fixable findings: `{len(by_project)}`\n\n")

    if not by_project:
        lines.append("No fixable HIGH/CRITICAL vulnerabilities detected.\n")
        summary_path.write_text("".join(lines), encoding="utf-8")
        return

    lines.append("| Project | Packages (fixable) | Unit tests | E2E tests | Actions |\n")
    lines.append("| --- | --- | --- | --- | --- |\n")

    for project_dir in sorted(by_project.keys()):
        updates = per_project_updates.get(project_dir) or {}
        unit_tests = "✅" if updates.get("has_unit_tests") else "—"
        e2e_tests = "✅" if updates.get("has_e2e_tests") else "—"
        packages = sorted({f.pkg_name for f in by_project[project_dir]})
        actions: List[str] = []
        if updates.get("pyproject_updates"):
            actions.append("relaxed pins")
        if updates.get("uv_lock_ran"):
            actions.append("uv lock")
        if updates.get("uv_lock_failed"):
            actions.append("uv lock failed")
        if not actions:
            actions.append("none")

        lines.append(
            f"| `{project_dir}` | {', '.join(f'`{p}`' for p in packages)} | {unit_tests} | {e2e_tests} | "
            f"{', '.join(actions)} |\n"
        )

    lines.append("\n### Notes\n")
    lines.append("- This PR is intended to only touch `pyproject.toml` and `uv.lock`.\n")
    lines.append("- E2E tests are not run by the autofix workflow (unit tests only).\n")

    summary_path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministically remediate fixable Trivy HIGH/CRITICAL vulnerabilities for uv projects."
    )
    parser.add_argument("--trivy-json", required=True, help="Path to Trivy vulnerability JSON output.")
    parser.add_argument(
        "--severity",
        default="CRITICAL,HIGH",
        help="Comma-separated severity levels to consider (default: CRITICAL,HIGH).",
    )
    parser.add_argument(
        "--summary-path",
        default="security-autofix-summary.md",
        help="Where to write the PR summary markdown.",
    )
    parser.add_argument(
        "--issue-path",
        default="security-unfixable-issue.md",
        help="Where to write the unfixable-issue markdown (created only when needed).",
    )
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    trivy_path = Path(args.trivy_json).resolve()
    if not trivy_path.exists():
        print(f"Trivy JSON not found: {trivy_path}", file=sys.stderr)
        return 1

    severities = [s.strip().upper() for s in str(args.severity).split(",") if s.strip()]
    severity_set = set(severities)

    trivy_data = json.loads(trivy_path.read_text(encoding="utf-8"))
    fixable, unfixable = parse_trivy_findings(repo_root, trivy_data, severity_set)

    summary_path = Path(args.summary_path).resolve()
    issue_path = Path(args.issue_path).resolve()

    if unfixable:
        write_unfixable_issue(issue_path, severities, unfixable)
        write_summary(summary_path, severities, fixable, per_project_updates={})
        return 0

    if not fixable:
        write_summary(summary_path, severities, fixable, per_project_updates={})
        return 0

    by_project: Dict[str, List[Finding]] = defaultdict(list)
    for finding in fixable:
        by_project[finding.project_dir].append(finding)

    per_project_updates: Dict[str, Dict[str, Any]] = {}
    any_changes = False

    for project_dir_str in sorted(by_project.keys()):
        project_dir = (repo_root / project_dir_str).resolve()
        pyproject_path = project_dir / "pyproject.toml"
        lock_path = project_dir / "uv.lock"
        if not pyproject_path.exists() or not lock_path.exists():
            continue

        before_hashes = {
            "pyproject.toml": _sha256(pyproject_path),
            "uv.lock": _sha256(lock_path),
        }

        unit_tests, e2e_tests = project_test_info(project_dir)
        per_project_updates[project_dir_str] = {
            "has_unit_tests": unit_tests,
            "has_e2e_tests": e2e_tests,
            "pyproject_updates": [],
            "uv_lock_ran": False,
            "uv_lock_failed": False,
        }

        packages = sorted({f.pkg_name for f in by_project[project_dir_str]})
        result = run_uv_lock(project_dir, packages)
        per_project_updates[project_dir_str]["uv_lock_ran"] = True

        if result.returncode != 0:
            updates = relax_pins(pyproject_path, by_project[project_dir_str])
            per_project_updates[project_dir_str]["pyproject_updates"] = updates

            result2 = run_uv_lock(project_dir, packages)
            per_project_updates[project_dir_str]["uv_lock_ran"] = True
            if result2.returncode != 0:
                per_project_updates[project_dir_str]["uv_lock_failed"] = True
                print(
                    f"uv lock failed in {project_dir_str}:\n{result2.stdout}\n{result2.stderr}",
                    file=sys.stderr,
                )
                return 1

        after_hashes = {
            "pyproject.toml": _sha256(pyproject_path),
            "uv.lock": _sha256(lock_path),
        }

        if before_hashes != after_hashes:
            any_changes = True

    write_summary(summary_path, severities, fixable, per_project_updates)
    return 2 if any_changes else 0


if __name__ == "__main__":
    sys.exit(main())
