from __future__ import annotations

import hashlib
import json
import re
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from .evidence import evidence, utc_now
from .identity import _normalised_phrase

BASE = "https://pam-stilling-feed.nav.no"
PUBLIC_TOKEN_URL = BASE + "/api/publicToken"
FEED_URL = BASE + "/api/v1/feed"
_nav_network = threading.local()


class NavRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        _safe_nav_url(newurl, "/api/v1/")
        _nav_network.redirects = getattr(_nav_network, "redirects", 0) + 1
        return super().redirect_request(req, fp, code, msg, headers, newurl)


NAV_OPENER = urllib.request.build_opener(NavRedirectHandler())


def experimental_public_token(timeout: float = 20.0) -> tuple[str, int]:
    """NAV documents this rotating token for experiments, not a frozen entry."""
    try:
        with urllib.request.urlopen(PUBLIC_TOKEN_URL, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
        attempts = 1
    except OSError:
        # The experimental endpoint has sometimes reset urllib's TLS connection
        # even when an ordinary curl request succeeds. Do not write the JWT to disk.
        fallback = subprocess.run(["curl", "--fail", "--silent", "--show-error", "--max-time", str(int(timeout)), PUBLIC_TOKEN_URL], capture_output=True, check=True, text=True)
        body = fallback.stdout
        attempts = 2
    found = re.findall(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", body)
    if len(found) != 1:
        raise ValueError("NAV public-token response did not contain exactly one JWT")
    return found[0], attempts


def _safe_nav_url(path: str, prefix: str) -> str:
    url = urllib.parse.urljoin(BASE, path)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "pam-stilling-feed.nav.no" or not parsed.path.startswith(prefix):
        raise ValueError("NAV feed supplied an unexpected follow-up URL")
    return url


def _json_get(url: str, token: str, since: str | None, timeout: float) -> tuple[dict[str, Any], str, int]:
    _nav_network.redirects = 0
    headers = {"Accept": "application/json", "Authorization": "Bearer " + token, "User-Agent": "Signalpost-development/0.1"}
    if since:
        headers["If-Modified-Since"] = since
    request = urllib.request.Request(url, headers=headers)
    with NAV_OPENER.open(request, timeout=timeout) as response:
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("NAV response exceeded the byte cap")
        return json.loads(raw), hashlib.sha256(raw).hexdigest(), len(raw)


def exact_active_job(detail: dict[str, Any], org: str, *, subunit_orgs: set[str] | None = None, now: datetime | None = None) -> dict[str, Any] | None:
    ad = detail.get("ad_content") or {}
    employer = ad.get("employer") or {}
    employer_org = str(employer.get("orgnr") or "")
    relationship = "direct_legal_entity" if employer_org == org else "registered_workplace_subunit" if employer_org in (subunit_orgs or set()) else None
    if detail.get("status") != "ACTIVE" or not relationship:
        return None
    expiry = ad.get("expires")
    title = str(ad.get("title") or "").strip()
    uuid = str(detail.get("uuid") or ad.get("uuid") or "")
    if not title or not uuid or not expiry:
        return None
    try:
        expiry_at = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
    except ValueError:
        return None
    if expiry_at < (now or datetime.now(timezone.utc)):
        return None
    return {
        "uuid": uuid,
        "title": title,
        "employer_organisation_number": employer_org,
        "profile_organisation_number": org,
        "employer_relationship": relationship,
        "employer_name": employer.get("name"),
        "published": ad.get("published"),
        "expires": expiry,
        "updated": ad.get("updated"),
        "source_page_url": ad.get("link") or ad.get("sourceurl"),
    }


def scan_exact_nav_jobs(
    profiles: list[dict[str, Any]], token: str, *, since: str, max_pages: int = 100,
    timeout: float = 20.0, min_interval: float = 0.2,
    tracked_job_orgs: dict[str, set[str]] | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Scan a bounded update window; publish only after reaching its end."""
    names: dict[str, set[str]] = {}
    subunits: dict[str, set[str]] = {}
    profile_by_org = {str(p["organisation_number"]): p for p in profiles}
    for profile in profiles:
        if (profile.get("evidence") or {}).get("registry", {}).get("status") != "available":
            continue
        org = str(profile["organisation_number"])
        name = _normalised_phrase(profile.get("name"))
        if name:
            names.setdefault(name, set()).add(org)
        locations = (profile.get("evidence") or {}).get("locations") or {}
        subunits[org] = set()
        if locations.get("status") == "available":
            for location in (locations.get("value") or {}).get("locations") or []:
                subunit_org = str(location.get("organisation_number") or "")
                if len(subunit_org) == 9:
                    subunits[org].add(subunit_org)
                    subunit_name = _normalised_phrase(location.get("name"))
                    if subunit_name:
                        names.setdefault(subunit_name, set()).add(org)
    candidates: dict[str, dict[str, Any]] = {}
    current = FEED_URL
    pages = 0
    requests = 0
    bytes_received = 0
    completed = False
    error = None
    try:
        while pages < max_pages:
            _nav_network.redirects = 0
            requests += 1
            body, page_digest, size = _json_get(current, token, since if pages == 0 else None, timeout)
            pages += 1
            requests += getattr(_nav_network, "redirects", 0)
            _nav_network.redirects = 0
            bytes_received += size
            for item in body.get("items") or []:
                header = item.get("_feed_entry") or {}
                key = _normalised_phrase(header.get("businessName"))
                uuid = str(header.get("uuid") or "")
                if not uuid or (key not in names and uuid not in (tracked_job_orgs or {})):
                    continue
                # Later entries supersede earlier ACTIVE entries before any
                # result is published, including early withdrawals.
                candidates[uuid] = {
                    "header": header, "url": item.get("url"),
                    "orgs": names.get(key, set()) | (tracked_job_orgs or {}).get(uuid, set()),
                    "feed_page_url": current, "feed_page_sha256": page_digest,
                }
            next_url = body.get("next_url")
            if not next_url:
                completed = True
                break
            current = _safe_nav_url(str(next_url), "/api/v1/feed/")
            time.sleep(min_interval)
    except Exception as exc:
        requests += getattr(_nav_network, "redirects", 0)
        error = f"{type(exc).__name__}: {str(exc)[:120]}"
    records: dict[str, list[dict[str, Any]]] = {str(p["organisation_number"]): [] for p in profiles}
    withdrawals: dict[str, list[dict[str, Any]]] = {str(p["organisation_number"]): [] for p in profiles}
    if completed:
        for candidate in candidates.values():
            if candidate["header"].get("status") == "INACTIVE":
                for org in (tracked_job_orgs or {}).get(str(candidate["header"].get("uuid") or ""), set()):
                    if org in withdrawals:
                        withdrawals[org].append({"uuid": candidate["header"]["uuid"], "event": "inactive", "source_url": candidate["feed_page_url"], "content_sha256": candidate["feed_page_sha256"], "updated_at": candidate["header"].get("sistEndret")})
                continue
            if candidate["header"].get("status") != "ACTIVE" or not candidate.get("url"):
                continue
            try:
                _nav_network.redirects = 0
                detail_url = _safe_nav_url(str(candidate["url"]), "/api/v1/feedentry/")
                requests += 1
                detail, digest, size = _json_get(detail_url, token, None, timeout)
                requests += getattr(_nav_network, "redirects", 0)
                _nav_network.redirects = 0
                bytes_received += size
                for org in candidate["orgs"]:
                    job = exact_active_job(detail, org, subunit_orgs=subunits.get(org))
                    if job:
                        location_evidence = (profile_by_org[org].get("evidence") or {}).get("locations") or {}
                        subunit_proof = {
                            "source_url": location_evidence.get("source_url"),
                            "content_sha256": location_evidence.get("content_sha256"),
                            "retrieved_at": location_evidence.get("retrieved_at"),
                            "subunit_organisation_number": job["employer_organisation_number"],
                            "source_path": "_embedded.underenheter[*].organisasjonsnummer",
                            "supporting_span": job["employer_organisation_number"],
                        } if job["employer_relationship"] == "registered_workplace_subunit" else None
                        if subunit_proof and not all(subunit_proof.get(key) for key in ("source_url", "content_sha256", "retrieved_at")):
                            continue
                        records[org].append({**job, "detail_url": detail_url, "content_sha256": digest, "subunit_proof": subunit_proof})
                time.sleep(min_interval)
            except Exception as exc:
                requests += getattr(_nav_network, "redirects", 0)
                error = f"{type(exc).__name__}: {str(exc)[:120]}"
                completed = False
                break
    fetched_at = utc_now()
    evidence_by_org = {}
    for profile in profiles:
        org = str(profile["organisation_number"])
        jobs = sorted(records[org], key=lambda job: job["uuid"]) if completed else []
        withdrawal_events = sorted(withdrawals[org], key=lambda item: item["uuid"]) if completed else []
        evidence_by_org[org] = evidence(
            "jobs", "available" if jobs or withdrawal_events else "not_found" if completed else "source_error",
            "nav_official_job_vacancy_feed", FEED_URL,
            value={"records": jobs, "withdrawals": withdrawal_events, "since_header": since, "window_complete": completed} if completed else None,
            retrieved_at=fetched_at,
            note="Exact legal employers and officially linked workplace subunits in the completed update window; absence is not proof of no older active ads." if completed else f"NAV update-window scan incomplete: {error or 'page cap reached'}",
        )
    return evidence_by_org, {
        "pages": pages, "candidate_ads": len(candidates), "requests": requests,
        "bytes": bytes_received, "window_complete": completed,
        "matched_active_jobs": sum(len(value) for value in records.values()) if completed else 0,
        "matched_inactive_job_events": sum(len(value) for value in withdrawals.values()) if completed else 0,
        "companies_with_jobs": sum(bool(value) for value in records.values()) if completed else 0,
        "error": error,
        "since_header": since,
    }
