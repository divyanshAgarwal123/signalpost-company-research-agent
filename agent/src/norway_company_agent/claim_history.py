from __future__ import annotations

import json
from datetime import datetime
from typing import Any


def _identity(claim: dict[str, Any]) -> str:
    field = claim["field"]
    value = claim.get("value")
    period = (claim.get("reporting_period") or {}).get("to")
    if field in {"revenue", "operating_result", "profit_before_tax", "annual_result", "assets", "equity", "debt"}:
        discriminator = period
    elif field == "active_job":
        discriminator = (value or {}).get("uuid")
    elif field == "registered_workplace":
        discriminator = (value or {}).get("subunit_organisation_number")
    elif field == "dated_company_activity":
        discriminator = (value or {}).get("url")
    elif field == "leadership_role":
        discriminator = ((value or {}).get("name"), (value or {}).get("role_code"))
    else:
        discriminator = None
    return json.dumps((field, discriminator), ensure_ascii=False, sort_keys=True)


def _module_for(field: str) -> str:
    if field in {"company_website", "company_site_description", "dated_company_activity"}:
        return "website"
    if field == "active_job":
        return "jobs"
    if field == "registered_workplace":
        return "locations"
    if field == "leadership_role":
        return "roles"
    if field in {"revenue", "operating_result", "profit_before_tax", "annual_result", "assets", "equity", "debt"}:
        return "financials"
    return "registry_live"


def _snapshot_key(claim: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    proof = ((claim.get("identity_proof") or {}).get("proof_source") or {})
    return (claim.get("id"), (claim.get("evidence") or {}).get("content_sha256"), proof.get("content_sha256"))


def _expired(claim: dict[str, Any], at: str) -> bool:
    try:
        expires = datetime.fromisoformat(str(claim.get("expires_at") or "").replace("Z", "+00:00"))
        current = datetime.fromisoformat(at.replace("Z", "+00:00"))
        return bool(expires.tzinfo and current.tzinfo and expires <= current)
    except ValueError:
        return False


def compare_claim_envelopes(previous: dict[str, Any], current: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return one-run events and retained evidence; absence is not a withdrawal by itself."""
    org = str(current.get("organisation_number") or "")
    if not org or org != str(previous.get("organisation_number") or ""):
        raise ValueError("The same exact organisation number is required for claim refresh")
    previous_claims = {_identity(c): c for c in previous.get("claims") or []}
    current_claims = {_identity(c): c for c in current.get("claims") or []}
    events: list[dict[str, Any]] = []
    earlier_history = previous.get("claim_history") or previous.get("claims") or []
    old_keys = {_identity(c) for c in earlier_history}
    retained = {_snapshot_key(c): c for c in earlier_history}
    timestamp = str(current.get("completed_at") or "")
    for key in sorted(set(previous_claims) | set(current_claims)):
        before = previous_claims.get(key)
        after = current_claims.get(key)
        if before is None:
            kind = "restored" if key in old_keys else "added"
        elif after is not None:
            kind = "unchanged" if before.get("value") == after.get("value") else "changed"
        else:
            module = _module_for(before["field"])
            source_state = ((current.get("modules") or {}).get(module) or {}).get("state")
            if before["field"] == "active_job":
                withdrawals = ((((current.get("profile") or {}).get("evidence") or {}).get("jobs") or {}).get("value") or {}).get("withdrawals") or []
                inactive = next((item for item in withdrawals if item.get("uuid") == (before.get("value") or {}).get("uuid")), None)
                kind = "removed" if inactive and source_state == "available" else "expired" if _expired(before, timestamp) else "deferred"
            elif before["field"] in {"leadership_role", "registered_workplace"} and source_state == "available":
                kind = "removed"
            else:
                # A news archive offers a selected article, not an exhaustive history.
                # A bounded NAV update feed cannot prove older vacancies absent.
                kind = "deferred"
        if kind != "unchanged":
            events.append({
                "organisation_number": org,
                "claim_key": key,
                "field": (after or before)["field"],
                "event": kind,
                "at": timestamp,
                "previous_claim": before,
                "current_claim": after,
                "source_state": ((current.get("modules") or {}).get(_module_for((after or before)["field"])) or {}).get("state"),
                "withdrawal_proof": inactive if kind == "removed" and (after or before)["field"] == "active_job" else None,
            })
        if after is not None:
            retained.setdefault(_snapshot_key(after), after)
    return events, sorted(retained.values(), key=lambda c: (c["field"], str(c.get("value")), (c.get("evidence") or {}).get("retrieved_at") or ""))
