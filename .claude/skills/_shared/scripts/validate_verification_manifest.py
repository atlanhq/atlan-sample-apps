#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

REQUIRED_KEYS = {
    "task_id",
    "timestamp_utc",
    "task_type",
    "sdk_sources",
    "docs_sources",
    "cli_sources",
    "resolved_facts",
    "unresolved_questions",
    "status",
}

URI_RE = re.compile(r"^repo://([a-z0-9-]+)/(.+)$")
ALLOWED_REPOS = {
    "application-sdk",
    "atlan-cli",
    "atlan-redshift-app",
    "atlan-postgres-app",
    "atlan-sample-apps",
}


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def validate_uri(uri: str) -> bool:
    match = URI_RE.match(uri)
    if not match:
        return False
    return match.group(1) in ALLOWED_REPOS


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: validate_verification_manifest.py <path>")

    path = Path(sys.argv[1])
    if not path.exists():
        return fail(f"file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail(f"invalid json: {exc}")

    missing = sorted(REQUIRED_KEYS - data.keys())
    if missing:
        return fail(f"missing required keys: {missing}")

    for key in ("sdk_sources", "docs_sources", "cli_sources"):
        value = data.get(key)
        if not isinstance(value, list) or not value:
            return fail(f"{key} must be a non-empty list")
        for item in value:
            if not isinstance(item, str) or not validate_uri(item):
                return fail(f"{key} contains invalid repo uri: {item}")

    resolved = data.get("resolved_facts")
    if not isinstance(resolved, list):
        return fail("resolved_facts must be a list")
    for idx, fact in enumerate(resolved):
        if isinstance(fact, dict) and "evidence" in fact:
            evidence = fact["evidence"]
            if not isinstance(evidence, str) or not validate_uri(evidence):
                return fail(f"resolved_facts[{idx}].evidence must be a valid repo uri")

    if data.get("status") not in {"ready", "blocked"}:
        return fail("status must be either 'ready' or 'blocked'")

    print("PASS: verification manifest is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
