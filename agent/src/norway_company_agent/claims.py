from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from urllib.parse import urlparse
from typing import Any

from .identity import _tokens

NEWS_ARTICLE_PATH = re.compile(r"/(?:news|press|aktuelt|nyheter|blog)/[^/]+", re.I)


def _published_before_retrieval(value: str, retrieved_at: str | None) -> bool:
    try:
        published = datetime.fromisoformat(value.replace("Z", "+00:00"))
        retrieved = datetime.fromisoformat(str(retrieved_at or "").replace("Z", "+00:00"))
        return bool(published.tzinfo and retrieved.tzinfo and published <= retrieved)
    except ValueError:
        return False


FINANCIAL_PATHS = {
    "revenue": "resultatregnskapResultat.driftsresultat.driftsinntekter.sumDriftsinntekter",
    "operating_result": "resultatregnskapResultat.driftsresultat.driftsresultat",
    "profit_before_tax": "resultatregnskapResultat.ordinaertResultatFoerSkattekostnad",
    "annual_result": "resultatregnskapResultat.aarsresultat",
    "assets": "eiendeler.sumEiendeler",
    "equity": "egenkapitalGjeld.egenkapital.sumEgenkapital",
    "debt": "egenkapitalGjeld.gjeldOversikt.sumGjeld",
}


def _claim_id(org: str, field: str, value: Any, period: str | None) -> str:
    payload = json.dumps([org, field, value, period], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


def _claim(
    profile: dict[str, Any], field: str, value: Any, record: dict[str, Any], *,
    source_path: str, supporting_span: str, source_url: str | None = None,
    content_sha256: str | None = None, reporting_period: dict[str, str] | None = None,
    identity_proof: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if value is None or record.get("status") != "available":
        return None
    url = source_url or record.get("source_url")
    digest = content_sha256 or record.get("content_sha256")
    if not url or not digest or len(str(digest)) != 64 or not record.get("retrieved_at") or not supporting_span:
        return None
    org = str(profile["organisation_number"])
    period_end = (reporting_period or {}).get("to")
    result = {
        "id": _claim_id(org, field, value, period_end),
        "organisation_number": org,
        "field": field,
        "value": value,
        "evidence": {
            "source_url": url,
            "source_class": record.get("source_class"),
            "retrieved_at": record["retrieved_at"],
            "content_sha256": digest,
            "source_path": source_path,
            "supporting_span": supporting_span,
            "extraction_method": "deterministic_source_mapping_v1",
        },
    }
    if reporting_period:
        result["reporting_period"] = reporting_period
    if identity_proof:
        result["identity_proof"] = identity_proof
    return result


def materialise_claims(profile: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = profile.get("evidence") or {}
    claims: list[dict[str, Any]] = []

    registry = evidence.get("registry_live") or {}
    live = registry.get("value") or {}
    for field, key, path in (
        ("legal_name", "name", "navn"),
        ("legal_form", "legal_form", "organisasjonsform.kode"),
        ("registered_employees", "employees", "antallAnsatte"),
    ):
        value = live.get(key)
        item = _claim(profile, field, value, registry, source_path=path, supporting_span=str(value) if value is not None else "")
        if item:
            claims.append(item)

    accounts = evidence.get("financials") or {}
    for record in (accounts.get("value") or {}).get("records") or []:
        period = record.get("period") or {}
        reporting_period = {"from": period.get("fraDato"), "to": period.get("tilDato")}
        if not reporting_period["from"] or not reporting_period["to"]:
            continue
        record_id = record.get("record_id")
        for field, path in FINANCIAL_PATHS.items():
            value = record.get(field)
            item = _claim(
                profile, field, value, accounts,
                source_path=f"id={record_id}.{path}",
                supporting_span=str(value) if value is not None else "",
                reporting_period=reporting_period,
            )
            if item:
                item["currency"] = record.get("currency")
                claims.append(item)

    roles = evidence.get("roles") or {}
    for role in (roles.get("value") or {}).get("roles") or []:
        code = str(role.get("role_code") or "")
        if role.get("inactive") or code not in {"DAGL", "LEDE", "MEDL", "VARA", "FFØR"}:
            continue
        raw_name = role.get("name")
        name = " ".join(str(part) for part in raw_name if part) if isinstance(raw_name, list) else str(raw_name or "").strip()
        if not name:
            continue
        item = _claim(
            profile, "leadership_role", {"name": name, "role_code": code, "role": role.get("role")}, roles,
            source_path=f"rollegrupper[type.kode={role.get('group_code')}].roller[type.kode={code}].person/enhet.navn",
            supporting_span=name,
        )
        if item:
            item["last_changed_at"] = role.get("last_changed")
            claims.append(item)

    locations = evidence.get("locations") or {}
    for location in (locations.get("value") or {}).get("locations") or []:
        subunit = str(location.get("organisation_number") or "")
        name = str(location.get("name") or "").strip()
        if len(subunit) != 9 or not name:
            continue
        item = _claim(
            profile, "registered_workplace", {"subunit_organisation_number": subunit, "name": name, "address": location.get("address")}, locations,
            source_path=f"_embedded.underenheter[organisasjonsnummer={subunit}]",
            supporting_span=name,
        )
        if item:
            claims.append(item)

    website = evidence.get("website") or {}
    site = website.get("value") or {}
    assessment = site.get("identity_assessment") or {}
    if website.get("status") == "available" and assessment.get("publishable"):
        home_url = site.get("final_url") or website.get("source_url")
        title = str(site.get("title") or "").strip()
        identity_proof = {"status": assessment.get("status"), "score": assessment.get("score"), "method": assessment.get("method"), "reasons": assessment.get("reasons")}
        if assessment.get("proof_source"):
            identity_proof["proof_source"] = assessment["proof_source"]
        proof_source = assessment.get("proof_source") or {}
        site_span = title or str(proof_source.get("supporting_span") or "")
        site_path = "homepage.title" if title else str(proof_source.get("source_path") or "homepage.main_text_excerpt")
        item = _claim(
            profile, "company_website", home_url, website,
            source_path=site_path, supporting_span=site_span,
            source_url=home_url if title else proof_source.get("source_url"),
            content_sha256=site.get("content_sha256") if title else proof_source.get("content_sha256"),
            identity_proof=identity_proof,
        )
        if item:
            claims.append(item)
        description = str(site.get("description") or "").strip()
        if len(description) >= 30:
            item = _claim(
                profile, "company_site_description", description, website,
                source_path="homepage.meta.description", supporting_span=description,
                source_url=home_url, content_sha256=site.get("content_sha256"), identity_proof=identity_proof,
            )
            if item:
                claims.append(item)
        core = _tokens(profile.get("name"))
        for page in site.get("pages") or []:
            url = str(page.get("url") or "")
            title = str(page.get("title") or "").strip()
            published_at = str(page.get("published_at") or "").strip()
            if urlparse(url).hostname != urlparse(str(home_url or "")).hostname or not NEWS_ARTICLE_PATH.search(urlparse(url).path) or not _published_before_retrieval(published_at, website.get("retrieved_at")) or not title or not core:
                continue
            page_tokens = set(_tokens(title + " " + str(page.get("main_text_excerpt") or "")[:500]))
            if core[0] not in page_tokens:
                continue
            item = _claim(
                profile, "dated_company_activity", {"title": title, "url": url}, website,
                source_path="article.title", supporting_span=title,
                source_url=url, content_sha256=page.get("content_sha256"), identity_proof=identity_proof,
            )
            if item:
                item["published_at"] = published_at
                claims.append(item)
                break
    jobs = evidence.get("jobs") or {}
    if jobs.get("status") == "available" and (jobs.get("value") or {}).get("window_complete"):
        for job in (jobs.get("value") or {}).get("records") or []:
            direct = str(job.get("employer_organisation_number") or "") == str(profile["organisation_number"])
            linked_subunit = job.get("employer_relationship") == "registered_workplace_subunit" and bool((job.get("subunit_proof") or {}).get("content_sha256"))
            if not (direct or linked_subunit) or (evidence.get("registry") or {}).get("status") != "available":
                continue
            item = _claim(
                profile, "active_job", {"uuid": job.get("uuid"), "title": job.get("title")}, jobs,
                source_path="ad_content.title", supporting_span=str(job.get("title") or ""),
                source_url=job.get("detail_url"), content_sha256=job.get("content_sha256"),
                identity_proof={"method": "nav_employer_organisation_number" if direct else "nav_employer_plus_official_subunit_relation", "profile_organisation_number": profile["organisation_number"], "employer_organisation_number": job.get("employer_organisation_number"), "subunit_proof": job.get("subunit_proof") if linked_subunit else None},
            )
            if item:
                item["published_at"] = job.get("published")
                item["expires_at"] = job.get("expires")
                item["source_page_url"] = job.get("source_page_url")
                claims.append(item)
    # Two annual-account filings can report the same fact for the same period.
    # Keep one claim while preserving separate IDs for facts with different qualifiers.
    unique: list[dict[str, Any]] = []
    seen_semantics: set[str] = set()
    seen_ids: set[str] = set()
    for item in claims:
        semantic = json.dumps(
            [item["organisation_number"], item["field"], item["value"], item.get("reporting_period"), item.get("currency")],
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        )
        if semantic in seen_semantics:
            continue
        if item["id"] in seen_ids:
            item["id"] = hashlib.sha256(semantic.encode()).hexdigest()[:24]
        seen_semantics.add(semantic)
        seen_ids.add(item["id"])
        unique.append(item)
    return unique
