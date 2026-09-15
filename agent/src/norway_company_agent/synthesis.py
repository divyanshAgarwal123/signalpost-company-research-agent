from __future__ import annotations

from typing import Any


def grounded_summary(envelope: dict[str, Any]) -> dict[str, Any]:
    """Short user-readable statements whose cited claim IDs establish each fact."""
    claims = envelope.get("claims") or []
    by_field: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        by_field.setdefault(claim["field"], []).append(claim)
    sentences: list[dict[str, Any]] = []

    def add(statement: str, supporting: list[dict[str, Any]]) -> None:
        sentences.append({
            "text": statement,
            "supporting_claim_ids": [item["id"] for item in supporting],
            "source_urls": [item["evidence"]["source_url"] for item in supporting],
        })

    names = by_field.get("legal_name") or []
    if names:
        add(f"The registry identifies this legal company as {names[0]['value']}.", names[:1])
    descriptions = by_field.get("company_site_description") or []
    if descriptions:
        item = descriptions[0]
        add(f"Its verified company website describes its work as: {str(item['value'])[:320]}", [item])
    revenues = sorted(by_field.get("revenue") or [], key=lambda item: (item.get("reporting_period") or {}).get("to") or "", reverse=True)
    if revenues:
        item = revenues[0]
        period = (item.get("reporting_period") or {}).get("to")
        add(f"The filed record for the period ending {period} lists operating revenue as {item['value']} and currency as {item.get('currency') or 'unspecified'}.", [item])
    jobs = by_field.get("active_job") or []
    if jobs:
        selected = jobs[:2]
        add(f"NAV currently lists {len(jobs)} verified active advert(s) for this legal company or its registered workplaces: " + "; ".join(str(item["value"]["title"]) for item in selected) + ("; more are linked in the claims." if len(jobs) > 2 else "."), jobs)
    activity = sorted(by_field.get("dated_company_activity") or [], key=lambda item: item.get("published_at") or "", reverse=True)
    if activity:
        item = activity[0]
        add(f"The verified company site published “{item['value']['title']}” on {str(item['published_at'])[:10]}.", [item])

    modules = envelope.get("modules") or {}
    unknowns = []
    if not by_field.get("company_website"):
        unknowns.append(f"Exact company website is unverified ({(modules.get('website') or {}).get('state') or 'not_checked'}).")
    if not jobs:
        nav_state = (modules.get("jobs") or {}).get("state")
        if nav_state == "not_available":
            unknowns.append("No active NAV job matched this company in the checked update window; other or older still-open jobs are not ruled out.")
        elif nav_state == "available":
            unknowns.append("No currently active NAV job is verified in this profile; other job sources are not ruled out.")
        else:
            unknowns.append("Current jobs have not been verified by a completed NAV feed scan.")
    if not activity:
        unknowns.append("No dated company-owned activity is verified in this profile; this does not prove the company has not published updates.")
    for event in envelope.get("claim_events") or []:
        if event.get("event") in {"added", "changed", "restored", "expired", "removed"}:
            supporting = [item for item in (event.get("current_claim"), event.get("previous_claim")) if item]
            if supporting:
                add(f"Refresh {event['event']}: {event['field']} at {str(event.get('at') or '')[:10]}.", supporting)
    return {"sentences": sentences, "unknowns": unknowns}
