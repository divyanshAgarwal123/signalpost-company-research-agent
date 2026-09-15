#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from norway_company_agent.batch import profile_complete_for_modules, profiles_from_bulk, read_organisation_inputs, terminal_envelope, validate_envelopes  # noqa: E402
from norway_company_agent.claim_history import compare_claim_envelopes  # noqa: E402
from norway_company_agent.discovery import choose_search_candidate  # noqa: E402
from norway_company_agent.evidence import evidence, utc_now  # noqa: E402
from norway_company_agent.identity import apply_website_identity_gate  # noqa: E402
from norway_company_agent.nav_jobs import experimental_public_token, scan_exact_nav_jobs  # noqa: E402
from norway_company_agent.official import fetch_official_modules  # noqa: E402
from norway_company_agent.synthesis import grounded_summary  # noqa: E402
from norway_company_agent.website import fetch_website  # noqa: E402
from scripts.run_brave_discovery import BRAVE_ENDPOINT, brave_search  # noqa: E402


def discover_exact_site(profile: dict, api_key: str, *, timeout: float = 15.0, count: int = 8) -> tuple[dict, dict]:
    results, search_operation = brave_search(profile, api_key, timeout=timeout, count=count)
    decision = choose_search_candidate(profile, results)
    selected = decision.get("selected")
    metrics = {"requests": 1, "bytes": search_operation.get("bytes") or 0, "latencies_ms": [search_operation.get("latency_ms") or 0]}
    if not selected:
        record = evidence("website_discovery", "not_found", "transient_brave_search", BRAVE_ENDPOINT,
                          note="Search candidates did not pass the crawl gate; results are discarded, not claim evidence.")
        return record, metrics
    website, crawl_metrics = fetch_website(selected["url"], timeout=timeout)
    website = apply_website_identity_gate(profile, website)["website"]
    for key in ("requests", "bytes"):
        metrics[key] += crawl_metrics.get(key) or 0
    metrics["latencies_ms"].extend(crawl_metrics.get("latencies_ms") or [])
    publishable = bool(website.get("status") == "available" and ((website.get("value") or {}).get("identity_assessment") or {}).get("publishable"))
    if publishable:
        website["source_type"] = "search_discovered_company_website"
        website["source_class"] = "search_discovered_company_website"
        profile["evidence"]["website"] = website
    record = evidence("website_discovery", "available" if publishable else "ambiguous", "transient_brave_search_then_independent_crawl", BRAVE_ENDPOINT,
                      value={"independent_page_url": website.get("source_url") if publishable else None},
                      note="Search results were discarded. Only the independently fetched exact-entity page can be published.")
    return record, metrics


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluator-owned Signalpost batch contract")
    parser.add_argument("--organisations", required=True, help="JSON, JSONL, or text organisation-number list")
    parser.add_argument("--bulk", required=True, help="Frozen Brreg entity snapshot")
    parser.add_argument("--output", required=True, help="Terminal envelope JSONL")
    parser.add_argument("--profiles-output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected-count", type=int, default=100)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--checkpoint-every", type=int, default=25)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--modules", default="registry,accounting_obligation,registry_live,financials,roles,group,locations,website")
    parser.add_argument("--brave-discovery", action="store_true", help="Use licensed Brave API for candidates, then independently verify pages")
    parser.add_argument("--brave-max-queries", type=int, help="Search cap; defaults to 40 with NAV or 80 otherwise")
    parser.add_argument("--brave-count", type=int, default=8)
    parser.add_argument("--nav-jobs", action="store_true", help="Scan NAV's official update feed once for exact active employer-org jobs")
    parser.add_argument("--nav-public-token-experiment", action="store_true", help="Use NAV's rotating public token for local experiments only")
    parser.add_argument("--nav-since", help="RFC-1123 NAV update-window start; default is 90 days before the run; older still-open ads require a declared feed index")
    parser.add_argument("--nav-max-pages", type=int, default=400)
    parser.add_argument("--previous-envelopes", help="Previous matching batch JSONL for claim-level change and evidence history")
    args = parser.parse_args()
    if args.brave_max_queries is None:
        args.brave_max_queries = 40 if args.nav_jobs else 80
    if args.brave_discovery and not os.environ.get("BRAVE_SEARCH_API_KEY", "").strip():
        parser.error("--brave-discovery requires BRAVE_SEARCH_API_KEY in the server environment")
    if not 0 <= args.brave_max_queries <= 100 or not 1 <= args.brave_count <= 20:
        parser.error("Brave discovery is limited to 0..100 queries and 1..20 results per query")
    if args.nav_jobs and not (os.environ.get("NAV_JOB_FEED_TOKEN", "").strip() or args.nav_public_token_experiment):
        parser.error("--nav-jobs requires NAV_JOB_FEED_TOKEN or the local-only --nav-public-token-experiment")
    if not 1 <= args.nav_max_pages <= 1000:
        parser.error("--nav-max-pages must be 1..1000")

    started_at = utc_now()
    organisation_inputs = read_organisation_inputs(args.organisations)
    orgs = [item["organisation_number"] for item in organisation_inputs]
    org_set = set(orgs)
    if len(orgs) != args.expected_count:
        raise SystemExit(f"Expected {args.expected_count} organisations, received {len(orgs)}")
    prior_by_org = None
    tracked_jobs: dict[str, set[str]] = {}
    if args.previous_envelopes:
        previous = [json.loads(line) for line in Path(args.previous_envelopes).read_text(encoding="utf-8").splitlines() if line.strip()]
        prior_by_org = {str(item["organisation_number"]): item for item in previous}
        if len(prior_by_org) != len(previous):
            raise SystemExit("Previous envelopes contain duplicate organisation numbers")
        for org, previous_envelope in prior_by_org.items():
            if org not in org_set:
                continue
            for claim in previous_envelope.get("claims") or []:
                if claim.get("field") == "active_job" and (uuid := (claim.get("value") or {}).get("uuid")):
                    tracked_jobs.setdefault(str(uuid), set()).add(org)
    profiles, registry_metadata = profiles_from_bulk(args.bulk, orgs)
    annotations = {item["organisation_number"]: item for item in organisation_inputs}
    for profile in profiles:
        for key in ("evaluation_split", "sample_slice"):
            if key in annotations[profile["organisation_number"]]:
                profile[key] = annotations[profile["organisation_number"]][key]
    requested_modules = [item.strip() for item in args.modules.split(",") if item.strip()]
    if args.brave_discovery and "website_discovery" not in requested_modules:
        requested_modules.append("website_discovery")
    if args.nav_jobs and "jobs" not in requested_modules:
        requested_modules.append("jobs")
    fetch_modules = set(requested_modules) - {"registry", "accounting_obligation", "website"}
    operations = {"requests": 0, "bytes": 0, "latencies_ms": []}
    discovery_lock = threading.Lock()
    discovery_queries = 0

    def enrich(profile: dict) -> tuple[dict, dict]:
        nonlocal discovery_queries
        records, metrics = fetch_official_modules(profile["organisation_number"], fetch_modules)
        profile["evidence"].update(records)
        website_metrics = {"requests": 0, "bytes": 0, "latencies_ms": []}
        if "website" in requested_modules:
            website_record, website_metrics = fetch_website(profile.get("website"))
            profile["evidence"]["website"] = apply_website_identity_gate(profile, website_record)["website"]
        discovery_metrics = {"requests": 0, "bytes": 0, "latencies_ms": []}
        if args.brave_discovery:
            current = profile["evidence"].get("website") or {}
            exact = bool(current.get("status") == "available" and ((current.get("value") or {}).get("identity_assessment") or {}).get("publishable"))
            reserved = False
            if not exact:
                with discovery_lock:
                    if discovery_queries < args.brave_max_queries:
                        discovery_queries += 1
                        reserved = True
            if reserved:
                discovery_record, discovery_metrics = discover_exact_site(profile, os.environ["BRAVE_SEARCH_API_KEY"], count=args.brave_count)
            else:
                discovery_record = evidence("website_discovery", "not_applicable", "transient_brave_search", BRAVE_ENDPOINT,
                                            note="Verified registry site present or configured search-query cap reached.")
            profile["evidence"]["website_discovery"] = discovery_record
        metric = {
            "requests": sum(item.attempted_requests for item in metrics) + website_metrics["requests"] + discovery_metrics["requests"],
            "bytes": sum(item.bytes_received for item in metrics) + website_metrics["bytes"] + discovery_metrics["bytes"],
            "latencies_ms": [item.elapsed_ms for item in metrics] + website_metrics["latencies_ms"] + discovery_metrics["latencies_ms"],
        }
        profile["run_metrics"] = metric
        return profile, metric

    state: dict[str, dict] = {}
    resumed_profiles = 0
    profiles_output = Path(args.profiles_output)
    if args.resume and profiles_output.exists():
        prior = [json.loads(line) for line in profiles_output.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not set(item["organisation_number"] for item in prior).issubset(set(orgs)):
            raise SystemExit("Resume profile membership is not a subset of this batch")
        state = {
            item["organisation_number"]: item
            for item in prior
            if profile_complete_for_modules(item, requested_modules)
        }
        resumed_profiles = len(state)
    pending_profiles = [profile for profile in profiles if profile["organisation_number"] not in state]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(enrich, profile): profile["organisation_number"] for profile in pending_profiles}
        for index, future in enumerate(as_completed(futures), 1):
            profile, metric = future.result()
            state[profile["organisation_number"]] = profile
            operations["requests"] += metric["requests"]
            operations["bytes"] += metric["bytes"]
            operations["latencies_ms"].extend(metric["latencies_ms"])
            if index % args.checkpoint_every == 0 or index == len(pending_profiles):
                checkpoint = [state[org] for org in orgs if org in state]
                write_jsonl(profiles_output, checkpoint)

    nav_operations = None
    if args.nav_jobs:
        token = os.environ.get("NAV_JOB_FEED_TOKEN", "").strip()
        token_requests = 0
        if not token:
            token, token_requests = experimental_public_token()
        since = args.nav_since or format_datetime(datetime.now(timezone.utc) - timedelta(days=90), usegmt=True)
        nav_records, nav_operations = scan_exact_nav_jobs([state[org] for org in orgs], token, since=since, max_pages=args.nav_max_pages, tracked_job_orgs=tracked_jobs)
        for org in orgs:
            state[org]["evidence"]["jobs"] = nav_records[org]
        operations["requests"] += nav_operations["requests"] + token_requests
        operations["bytes"] += nav_operations["bytes"]
        nav_operations["token_mode"] = "public_experiment" if token_requests else "registered_consumer_secret"
        nav_operations["requests"] += token_requests

    completed_at = utc_now()
    ordered_profiles = [state[org] for org in orgs]
    envelopes = [
        terminal_envelope(profile, run_id=args.run_id, modules=requested_modules, started_at=started_at, completed_at=completed_at)
        for profile in ordered_profiles
    ]
    event_counts: dict[str, int] = {}
    if prior_by_org is not None:
        for envelope in envelopes:
            if envelope["organisation_number"] not in prior_by_org:
                continue
            events, history = compare_claim_envelopes(prior_by_org[envelope["organisation_number"]], envelope)
            envelope["claim_events"] = events
            envelope["claim_history"] = history
            envelope["summary"] = grounded_summary(envelope)
            for event in events:
                kind = event["event"]
                event_counts[kind] = event_counts.get(kind, 0) + 1
    validation = validate_envelopes(envelopes, args.expected_count)
    write_jsonl(profiles_output, ordered_profiles)
    write_jsonl(Path(args.output), envelopes)
    latencies = sorted(operations.pop("latencies_ms"))
    operations["p50_ms"] = latencies[len(latencies) // 2] if latencies else None
    operations["p95_ms"] = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else None
    operations["brave_search_queries"] = discovery_queries
    operations["declared_brave_search_cost_usd"] = round(discovery_queries * 0.005, 3)
    wall_seconds = (datetime.fromisoformat(completed_at.replace("Z", "+00:00")) - datetime.fromisoformat(started_at.replace("Z", "+00:00"))).total_seconds()
    daily_budget = {
        "applicable": args.expected_count == 100,
        "reported_requests_pass": operations["requests"] <= 2000 if args.expected_count == 100 else None,
        "wall_time_pass": wall_seconds <= 2700 if args.expected_count == 100 else None,
        "declared_external_cost_pass": operations["declared_brave_search_cost_usd"] <= 10 if args.expected_count == 100 else None,
    }
    report = {
        "run_id": args.run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "expected_count": args.expected_count,
        "emitted_envelopes": len(envelopes),
        "resumed_profiles": resumed_profiles,
        "profiles_fetched_this_run": len(pending_profiles),
        "modules": requested_modules,
        "registry": registry_metadata,
        "operations": operations,
        "daily_budget": daily_budget,
        "nav_jobs": nav_operations,
        "claim_refresh_events": event_counts if args.previous_envelopes else None,
        "validation": validation,
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if validation["passed"] and (not daily_budget["applicable"] or all(daily_budget[key] for key in ("reported_requests_pass", "wall_time_pass", "declared_external_cost_pass"))) else 1)


if __name__ == "__main__":
    main()
