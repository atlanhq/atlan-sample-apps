#!/usr/bin/env python3
"""Copy selected reference files from sibling repos into local mirrors.

This keeps skills portable across machines and usable when sibling repos are unavailable.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List

REQUIRED_MIRRORS: Dict[str, List[str]] = {
    "application-sdk": [
        "application_sdk/services/objectstore.py",
        "application_sdk/io/json.py",
        "application_sdk/io/parquet.py",
        "application_sdk/activities/common/utils.py",
        "application_sdk/clients/temporal.py",
        "application_sdk/server/fastapi/models.py",
        "docs/concepts/inputs.md",
        "docs/concepts/outputs.md",
        "docs/concepts/output_paths.md",
        "docs/guides/sql-application-guide.md",
        "agent-skills-docs/doc-index.md",
        "agent-skills-docs/best-practices.md",
        "agent-skills-docs/codex.md",
        "agent-skills-docs/intro.md",
        "agent-skills-docs/open-agent.md",
        "agent-skills-docs/quick-start.md",
        "agent-skills-docs/skills-for-enterprise.md",
    ],
    "atlan-cli": [
        "docs/app-command.md",
        "cmd/atlan/app.go",
        "cmd/atlan/app_run.go",
        "cmd/atlan/app_test_cmd.go",
        "cmd/atlan/app_release.go",
    ],
    "atlan-postgres-app": [
        "main.py",
        "app/clients/__init__.py",
        "tests/e2e/test_postgres_workflow/config.yaml",
        "tests/e2e/test_postgres_wwi_workflow/config.yaml",
    ],
    "atlan-redshift-app": [
        "main.py",
        "app/clients.py",
        "app/handlers/redshift.py",
        "app/workflows/metadata_extraction/redshift.py",
        "app/activities/metadata_extraction/redshift.py",
        "tests/e2e/test_redshift_workflow_mixed_filters/config.yaml",
    ],
}


def find_workspace_root(script_path: Path) -> Path:
    for candidate in [script_path.resolve(), *script_path.resolve().parents]:
        if (candidate / "atlan-sample-apps").exists() and (candidate / "application-sdk").exists():
            return candidate
    return script_path.resolve().parents[5]


def main() -> int:
    script_path = Path(__file__).resolve()
    skills_root = script_path.parents[2]
    workspace_root = find_workspace_root(script_path)
    mirror_root = skills_root / "_shared" / "references" / "source-mirror"

    copied = 0
    missing = []

    for repo, rel_paths in REQUIRED_MIRRORS.items():
        for rel in rel_paths:
            src = workspace_root / repo / rel
            dst = mirror_root / repo / rel
            if not src.exists():
                missing.append(str(src))
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1

    print(f"COPIED: {copied} files to {mirror_root}")
    if missing:
        print("MISSING:")
        for item in missing:
            print(item)

    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
