# Signalpost version 1 entry

Challenge: [Builderr Signalpost](https://builderr.ai/challenges/signalpost). Contact: Divyansh Agarwal, `divyansh104agarwal@gmail.com`.

Repository: <https://github.com/divyanshAgarwal123/signalpost-company-research-agent>. The **exact commit** is identified in the submission email; Builderr should evaluate that commit, not a later `main` revision.

## Submitted artifact

- `agent/data/entry1000.jsonl` is the exact organisation-number manifest selected from Builderr's published eligible universe.
- `submission/profiles.jsonl` contains the public company profiles.
- `submission/envelopes.jsonl` contains one terminal envelope per manifest number, with legal identity, claims, evidence references, six-state module availability, bounded claim-span source snapshot descriptors, refresh metadata, errors and a claim-linked summary.
- `submission/run-report.json` records the local artifact run and terminal validation.
- `submission/export-report.json` records output hashes and the public-export redaction. Material claims and their bounded source evidence were preserved; unclaimed company-page body excerpts and structured contact payloads were removed.

## One evaluator command

From the repository root, run:

```sh
./run_signalpost.sh INPUT_JSONL BRREG_BULK_CSV_GZ OUTPUT_DIRECTORY 100
```

`INPUT_JSONL` is the evaluator's batch of 100 organisation numbers. `BRREG_BULK_CSV_GZ` is its frozen official entity snapshot. `OUTPUT_DIRECTORY` receives `profiles.jsonl`, `envelopes.jsonl` and `run-report.json`. For a refresh of the same companies, add a fifth argument pointing to the earlier `envelopes.jsonl`. The command requires Python 3.12+, `uv`, the pinned `agent/uv.lock`, and network access to documented public sources. It does not rely on the submitted 1,000 profiles to answer unseen company numbers.

## Models, APIs, source rights, cost and data handling

The entered default uses **no hosted model**. It fetches Brønnøysundregistrene public legal-entity, roles, subunit and filed-account data, plus a bounded set of pages from a registry-listed company website only after URL, robots and exact-entity checks. Public Enhetsregisteret data is covered by [Brønnøysund's NLOD 2.0 documentation](https://data.brreg.no/enhetsregisteret/api/dokumentasjon/en/index.html). Filed-account key figures come from Brønnøysund's public Regnskapsregisteret endpoint; this artifact does not archive full annual-account copies. Company-site claims carry short supporting spans and source URLs, subject to each site's access and reuse terms. The code avoids private/local/reserved outbound hosts and unsafe redirects. The unauthorised person-number API and unofficial platform crawlers are not used. Company-site body excerpts and structured contact payloads are removed from the public artifact when they are not claim evidence.

The code has optional licensed Brave Search discovery (`BRAVE_SEARCH_API_KEY`) and registered NAV job-feed (`NAV_JOB_FEED_TOKEN`) connectors. **Neither is enabled in the version 1 evaluator command or the submitted 1,000 artifact**; no token is committed. Search results are candidate URLs only, never claim evidence. Expected declared third-party API spend for the default 100-company evaluator run is **$0**. The only local cache is the evaluator-supplied official registry snapshot and, when explicitly passed, previous terminal envelopes for refresh. The submitted artifact is an example, not a lookup cache for daily inputs.

A final live run of the exact evaluator command on 100 eligible numbers with no overlap with the submitted manifest returned 100 terminal envelopes, 1,293 material claims, 647 reported outbound requests and $0 declared API spend in 422 seconds. Its local structural, claim-metadata, bounded-source-descriptor, summary-citation and request/time/cost checks passed. The 1,000-company artifact was built in 1,268 seconds with 5,742 reported requests; the 2,000-request cap applies to the **daily 100-company** evaluation, not to artifact preparation. All 1,000 manifest numbers were independently checked against the official 411,160-company eligible-universe archive and its documented uncompressed SHA-256.

The source snapshot descriptors contain source URL, retrieval time, the original content hash and locally hashed short claim spans. They are not complete raw source bodies; independent raw-body hash verification requires a fresh allowed fetch or separately lawful archive. External-source recall, exact-company precision, hidden score, full refresh scoring, gallery UX and prize qualification remain Builderr checks. This version was not built with JBOX and makes no JBOX bonus claim.
