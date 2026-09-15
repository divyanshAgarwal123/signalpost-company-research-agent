#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from norway_company_agent.nav_jobs import experimental_public_token, scan_exact_nav_jobs  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="NAV official feed experiment: publish only exact active employer-org matches")
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--since", help="RFC-1123 start; defaults to 90 days before the run; older active jobs require a declared feed index")
    parser.add_argument("--max-pages", type=int, default=400)
    parser.add_argument("--public-token-experiment", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.max_pages <= 1000:
        parser.error("--max-pages must be between 1 and 1000")
    token = os.environ.get("NAV_JOB_FEED_TOKEN", "").strip()
    token_requests = 0
    if not token and args.public_token_experiment:
        token, token_requests = experimental_public_token()
    if not token:
        parser.error("Provide NAV_JOB_FEED_TOKEN or use the documented rotating public token for an experiment")
    profiles = [json.loads(line) for line in Path(args.profiles).read_text(encoding="utf-8").splitlines() if line.strip()]
    since = args.since or format_datetime(datetime.now(timezone.utc) - timedelta(days=90), usegmt=True)
    records, operations = scan_exact_nav_jobs(profiles, token, since=since, max_pages=args.max_pages)
    for profile in profiles:
        profile.setdefault("evidence", {})["jobs"] = records[str(profile["organisation_number"])]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in profiles), encoding="utf-8")
    operations["requests"] += token_requests
    operations["token_mode"] = "public_experiment" if token_requests else "registered_consumer_secret"
    Path(args.report).write_text(json.dumps(operations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(operations, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
