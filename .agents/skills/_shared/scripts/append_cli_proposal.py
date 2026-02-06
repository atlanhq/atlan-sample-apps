#!/usr/bin/env python3
import argparse
from datetime import date
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--workflow-step", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--why", required=True)
    parser.add_argument("--cli-evidence", action="append", required=True)
    parser.add_argument("--sdk-doc-evidence", action="append", required=True)
    parser.add_argument("--suggested-fix", required=True)
    parser.add_argument("--priority", default="P2")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out = Path(args.file)
    out.parent.mkdir(parents=True, exist_ok=True)

    proposal_id = f"{date.today().isoformat()}-auto"

    lines = []
    lines.append("\n## Proposal " + proposal_id)
    lines.append(f"- `date`: {date.today().isoformat()}")
    lines.append(f"- `workflow_step`: {args.workflow_step}")
    lines.append(f"- `current_cli_behavior`: {args.current}")
    lines.append(f"- `expected_cli_behavior`: {args.expected}")
    lines.append(f"- `why_it_matters`: {args.why}")
    lines.append("- `source_evidence`:")
    for item in args.cli_evidence:
        lines.append(f"  - `{item}`")
    for item in args.sdk_doc_evidence:
        lines.append(f"  - `{item}`")
    lines.append(f"- `suggested_fix`: {args.suggested_fix}")
    lines.append(f"- `priority`: {args.priority}")

    with out.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    print(f"APPENDED: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
