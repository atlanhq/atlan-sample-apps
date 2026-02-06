#!/usr/bin/env python3
"""Resolve repo:// URIs to live sibling repos or local source mirrors.

Examples:
  python resolve_source.py --print-map
  python resolve_source.py --source repo://application-sdk/application_sdk/clients/temporal.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Tuple

REPO_NAMES = [
    "application-sdk",
    "atlan-cli",
    "atlan-redshift-app",
    "atlan-postgres-app",
    "atlan-sample-apps",
]

URI_RE = re.compile(r"^repo://([a-z0-9-]+)/(.+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", help="repo:// URI to resolve")
    parser.add_argument(
        "--prefer-mirror",
        action="store_true",
        help="prefer local source-mirror even when live repo is available",
    )
    parser.add_argument(
        "--print-map",
        action="store_true",
        help="print discovered live repo paths as json",
    )
    return parser.parse_args()


def find_workspace_root(start: Path) -> Path:
    env_root = Path.cwd().anchor
    configured = Path((Path.home() / ".atlan_repo_root").as_posix())
    if configured.exists() and configured.is_dir():
        return configured

    for candidate in [start, *start.parents]:
        hits = sum((candidate / name).exists() for name in REPO_NAMES)
        if hits >= 2:
            return candidate

    # Fallback to sibling-of-repo assumption from this script path
    # .../atlan-sample-apps/.agents/skills/_shared/scripts/resolve_source.py
    # -> parent[5] should be workspace root containing sibling repos
    return start.parents[5]


def discover_live_map(workspace_root: Path) -> Dict[str, str]:
    repo_map: Dict[str, str] = {}
    for name in REPO_NAMES:
        path = workspace_root / name
        if path.exists() and path.is_dir():
            repo_map[name] = str(path)
    return repo_map


def parse_repo_uri(uri: str) -> Tuple[str, str]:
    match = URI_RE.match(uri)
    if not match:
        raise ValueError(f"invalid repo uri: {uri}")
    return match.group(1), match.group(2)


def resolve_source(uri: str, script_path: Path, prefer_mirror: bool = False) -> Dict[str, str]:
    repo_name, relative_path = parse_repo_uri(uri)
    workspace_root = find_workspace_root(script_path.resolve())
    repo_map = discover_live_map(workspace_root)
    skills_root = script_path.resolve().parents[2]
    mirror_path = (
        skills_root / "_shared" / "references" / "source-mirror" / repo_name / relative_path
    )

    if prefer_mirror and mirror_path.exists():
        return {
            "mode": "mirror",
            "repo": repo_name,
            "uri": uri,
            "path": str(mirror_path.resolve()),
        }

    if repo_name in repo_map:
        live_path = Path(repo_map[repo_name]) / relative_path
        if live_path.exists():
            return {
                "mode": "live",
                "repo": repo_name,
                "uri": uri,
                "path": str(live_path.resolve()),
            }

    if mirror_path.exists():
        return {
            "mode": "mirror",
            "repo": repo_name,
            "uri": uri,
            "path": str(mirror_path.resolve()),
        }

    raise FileNotFoundError(
        f"unable to resolve {uri}; not found in live repos or local mirrors"
    )


def main() -> int:
    args = parse_args()
    script_path = Path(__file__)

    if args.print_map:
        workspace_root = find_workspace_root(script_path.resolve())
        print(json.dumps(discover_live_map(workspace_root), indent=2))
        return 0

    if args.source:
        try:
            result = resolve_source(args.source, script_path, prefer_mirror=args.prefer_mirror)
        except Exception as exc:
            print(f"FAIL: {exc}")
            return 1
        print(json.dumps(result, indent=2))
        return 0

    print("usage: resolve_source.py --print-map OR --source repo://...")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
