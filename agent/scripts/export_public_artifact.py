#!/usr/bin/env python3
"""Publish factual profiles without copying full company-page excerpts."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def public_profile(profile: dict) -> dict:
    result = copy.deepcopy(profile)
    website = ((result.get("evidence") or {}).get("website") or {}).get("value") or {}
    for key in ("main_text_excerpt", "identity_text_excerpt", "structured_organisations", "raw_html", "html_excerpt"):
        website.pop(key, None)
    for page in website.get("pages") or []:
        for key in ("main_text_excerpt", "identity_text_excerpt", "raw_html", "html_excerpt"):
            page.pop(key, None)
    rendered = website.get("js_fallback") or {}
    for key in ("main_text_excerpt", "identity_text_excerpt", "raw_html", "html_excerpt"):
        rendered.pop(key, None)
    result["public_export"] = {
        "scope": "bounded_claim_evidence",
        "removed": "unclaimed website body excerpts and structured contact data",
        "claim_evidence_preserved": True,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--envelopes", required=True)
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--output-directory", required=True)
    args = parser.parse_args()
    envelopes = read_rows(Path(args.envelopes))
    profiles = read_rows(Path(args.profiles))
    by_org = {str(profile["organisation_number"]): public_profile(profile) for profile in profiles}
    if len(by_org) != len(profiles) or set(by_org) != {str(row["organisation_number"]) for row in envelopes}:
        raise SystemExit("Profile and envelope organisation-number sets differ")
    public_envelopes = []
    for original in envelopes:
        row = copy.deepcopy(original)
        row["profile"] = by_org[str(row["organisation_number"])]
        row["public_export"] = by_org[str(row["organisation_number"])]["public_export"]
        if row["claims"] != original["claims"] or row["source_snapshots"] != original["source_snapshots"]:
            raise SystemExit("Public export changed material claims or their bounded evidence")
        public_envelopes.append(row)
    output = Path(args.output_directory)
    profile_path = output / "profiles.jsonl"
    envelope_path = output / "envelopes.jsonl"
    write_rows(profile_path, [by_org[str(row["organisation_number"])] for row in envelopes])
    write_rows(envelope_path, public_envelopes)
    report = {
        "completed_profiles": len(profiles),
        "terminal_envelopes": len(envelopes),
        "material_claims_preserved": sum(len(row["claims"]) for row in envelopes),
        "public_envelopes_sha256": hashlib.sha256(envelope_path.read_bytes()).hexdigest(),
        "public_profiles_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
        "redaction": "Only unclaimed raw company-page excerpts and structured contact payloads were removed; claim spans remain unchanged.",
    }
    (output / "export-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
