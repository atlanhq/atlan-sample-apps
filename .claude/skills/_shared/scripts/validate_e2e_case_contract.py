#!/usr/bin/env python3
import sys
from pathlib import Path

REQUIRED_TOP_LEVEL_KEYS = [
    "test_workflow_args:",
    "server_config:",
    "expected_api_responses:",
    "expected_output_paths:",
    "schema_assertions:",
]


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: validate_e2e_case_contract.py <path>")

    path = Path(sys.argv[1])
    if not path.exists():
        return fail(f"file not found: {path}")

    text = path.read_text(encoding="utf-8")
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if f"\n{key}" not in f"\n{text}":
            return fail(f"missing required top-level key: {key}")

    print("PASS: e2e case contract has required sections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
