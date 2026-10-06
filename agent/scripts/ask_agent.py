#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from norway_company_agent.research import answer_profile  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--org", required=True)
    parser.add_argument("--question", default="What do we know about this company?")
    args = parser.parse_args()
    row = None
    with Path(args.input).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            candidate = json.loads(line)
            if candidate.get("organisation_number") == args.org:
                row = candidate
                break
    if row is None:
        raise SystemExit(f"Organisation number {args.org} is not in the input profiles")
    print(json.dumps(answer_profile(row, args.question), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
