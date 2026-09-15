#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def read_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Check public Signalpost v2 gates without inventing a hidden score")
    parser.add_argument("--envelopes", required=True)
    parser.add_argument("--batch-report", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", help="Optional exact eligible-universe organisation-number manifest")
    args = parser.parse_args()
    envelopes = read_jsonl(args.envelopes)
    batch = json.loads(Path(args.batch_report).read_text(encoding="utf-8"))
    profiles = [row.get("profile") or {} for row in envelopes]
    claims = [claim for row in envelopes for claim in row.get("claims") or []]
    summaries_present = all(isinstance(row.get("summary"), dict) for row in envelopes)
    summary_citations_valid = summaries_present and all(
        all(sentence.get("supporting_claim_ids") and set(sentence["supporting_claim_ids"]) <= {claim.get("id") for claim in row.get("claims") or []}
            for sentence in (row.get("summary") or {}).get("sentences") or [])
        for row in envelopes
    )
    v2_envelope_fields_present = all(
        isinstance(row.get("legal_identity"), dict) and isinstance(row.get("source_snapshots"), list)
        and isinstance(row.get("refresh"), dict) and isinstance(row.get("errors"), list)
        and (row["legal_identity"] or {}).get("organisation_number") == row.get("organisation_number")
        and (row["refresh"] or {}).get("idempotence_key")
        for row in envelopes
    )
    bounded_snapshots_valid = v2_envelope_fields_present and all(
        snapshot.get("source_url") and snapshot.get("source_content_sha256") and snapshot.get("retrieved_at")
        and snapshot.get("snapshot_scope") == "bounded_claim_spans"
        and snapshot.get("bounded_spans_sha256") == hashlib.sha256(json.dumps(snapshot.get("claim_spans") or [], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        and all(span.get("claim_id") in {claim.get("id") for claim in row.get("claims") or []} for span in snapshot.get("claim_spans") or [])
        for row in envelopes for snapshot in row.get("source_snapshots") or []
    )
    site_claims = [claim for claim in claims if claim.get("field") == "company_website"]
    families = Counter(claim.get("field") for claim in claims)
    claim_metadata = all(
        all((claim.get("evidence") or {}).get(key) for key in ("source_url", "retrieved_at", "content_sha256", "source_path", "supporting_span"))
        and (not claim.get("field") in {"revenue", "operating_result", "profit_before_tax", "annual_result", "assets", "equity", "debt"} or (claim.get("reporting_period") or {}).get("to"))
        for claim in claims
    )
    started = datetime.fromisoformat(batch["started_at"].replace("Z", "+00:00"))
    completed = datetime.fromisoformat(batch["completed_at"].replace("Z", "+00:00"))
    wall_seconds = round((completed - started).total_seconds(), 1)
    states = {item.get("state") for row in envelopes for item in (row.get("modules") or {}).values()}
    valid_states = {"available", "not_available", "blocked", "not_applicable", "ambiguous", "failed"}
    website_candidates = sum(bool(profile.get("website")) for profile in profiles)
    website_published = len({claim["organisation_number"] for claim in site_claims})
    manifest_match = None
    if args.manifest:
        entries = read_jsonl(args.manifest)
        manifest_orgs = [str(row.get("organisation_number") or row.get("organisasjonsnummer") or "") for row in entries]
        output_orgs = [str(row.get("organisation_number") or "") for row in envelopes]
        manifest_match = len(manifest_orgs) == len(output_orgs) and len(set(manifest_orgs)) == len(manifest_orgs) and set(manifest_orgs) == set(output_orgs)
    report = {
        "rubric": "Builderr Signalpost scoring version 2 (26 August 2026)",
        "score_estimate": None,
        "reason_score_unavailable": "Builderr's field weights, checked reference union, exact-company labels, refresh evaluation, synthesis and UX scores are unavailable locally.",
        "sample_size": len(envelopes),
        "measured": {
            "terminal_envelopes": len(envelopes),
            "batch_structural_validation": bool(batch.get("validation", {}).get("passed")),
            "v2_module_states_valid": states <= valid_states,
            "material_claims": len(claims),
            "claim_source_date_hash_path_span_present": claim_metadata,
            "summary_claim_ids_locally_valid": summary_citations_valid if summaries_present else None,
            "v2_identity_snapshot_refresh_errors_present": bool(v2_envelope_fields_present),
            "bounded_source_snapshot_descriptors_locally_valid": bool(bounded_snapshots_valid),
            "claim_families": dict(families),
            "registered_website_candidates": website_candidates,
            "publishable_company_website_claims": website_published,
            "submitted_manifest_exact_membership": manifest_match,
            "outbound_requests_reported": batch.get("operations", {}).get("requests"),
            "wall_seconds": wall_seconds,
            "reported_daily_request_budget_pass": ((batch.get("operations", {}).get("requests") or 10**9) <= 2000) if len(envelopes) == 100 else None,
            "reported_daily_wall_budget_pass": wall_seconds <= 2700 if len(envelopes) == 100 else None,
        },
        "unmeasured_or_incomplete": [
            "21/35 coverage and 60% weighted external company recall need Builderr's checked field-family pool and weights",
            "95% exact-company precision needs independent labelled source-to-entity audit",
            "bounded claim-span descriptors are locally checked; full raw source bodies and their original content hashes remain unavailable for frozen-snapshot verification",
            "source refresh and history need a live unchanged/changed replay under the v2 envelope",
            "the eligible-universe manifest, 1000-profile content and public artifact need audit and submission" if len(envelopes) >= 1000 else "1000 completed public profiles and matching manifest have not been produced",
            "claim-linked summaries exist locally, but Builderr synthesis, gallery UX and JBOX eligibility remain unmeasured" if summaries_present else "this artifact does not yet include the latest claim-linked summary; gallery UX and JBOX eligibility are unmeasured",
            "reported network attempts still need clean redirect/retry auditing with all optional connectors enabled",
        ],
        "qualification_readiness": False,
        "interpretation": "Operational baseline passes locally. External coverage and other hard gates are not established; a good or prize-qualifying Builderr score cannot be claimed.",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
