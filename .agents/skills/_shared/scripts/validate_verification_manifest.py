#!/usr/bin/env python3
import json
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


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def _validate_non_empty_string_list(name: str, value) -> int:
    if not isinstance(value, list) or not value:
        return fail(f"{name} must be a non-empty list")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return fail(f"{name} must contain non-empty strings")
    return 0


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
        res = _validate_non_empty_string_list(key, data.get(key))
        if res != 0:
            return res

    resolved = data.get("resolved_facts")
    if not isinstance(resolved, list):
        return fail("resolved_facts must be a list")

    if data.get("status") not in {"ready", "blocked"}:
        return fail("status must be either 'ready' or 'blocked'")

    print("PASS: verification manifest is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
