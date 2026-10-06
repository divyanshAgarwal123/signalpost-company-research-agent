# Sources and access

Signalpost publishes facts only when they can be tied to the requested Norwegian legal entity and a permitted source. These notes describe the code's access boundaries; they are not a blanket licence to republish every source's raw content.

| Source | Use | Boundary |
| --- | --- | --- |
| [Brønnøysund Register Centre public entity data](https://data.brreg.no/enhetsregisteret/api/dokumentasjon/en/index.html) | Organisation identity, public registry fields, roles, group and workplace links. | The bulk entity file anchors input IDs. The public API is used; authorised person-number access is excluded. The entity dataset is published under [NLOD 2.0](https://data.norge.no/nlod/en/2.0). |
| [Brønnøysund annual accounts](https://data.brreg.no/regnskapsregisteret/regnskap/swagger-ui/swagger-ui/index.html?urls.primaryName=aarsregnskap) | Filed financial values and reporting periods. | An accounts record must contain the requested organisation number. Separate publication terms should be checked before archiving raw account documents. |
| Company-owned websites | Registered-site pages, descriptions and dated activity when exact-entity proof is found. | The crawler respects robots instructions, blocks private and reserved destinations and unsafe redirects, and withholds ambiguous parent, brand and franchise sites. Individual site terms still apply. |
| [Brave Search API](https://brave.com/search/api/) (optional) | Candidate site discovery only. | Requires `BRAVE_SEARCH_API_KEY` on the server. Search snippets do not become evidence; a candidate must pass an independent fetched-page identity check. Usage and cost depend on the account's current plan. |
| [NAV job feed](https://navikt.github.io/pam-stilling-feed/) (optional) | Exact employer or officially linked workplace jobs. | Requires a registered `NAV_JOB_FEED_TOKEN` and compliance with [NAV's API terms](https://arbeidsplassen.nav.no/vilkar-api). The rotating public token is for local experiments only. A bounded update window cannot prove that older active jobs do not exist. |

The default `./run_signalpost.sh` path uses no hosted model and enables neither Brave nor NAV. Its declared paid API cost is therefore $0; network use of public official services and company websites still occurs. The dependency versions are pinned in `agent/uv.lock`. Secrets belong in environment variables and are not committed.

The envelopes retain source URLs, retrieval and period dates, hashes, and bounded supporting spans. They do **not** archive complete original pages or annual accounts, so original-body hash verification needs a lawful source fetch or a separately permitted archive. Generated `profiles.jsonl` can contain page excerpts and should be reviewed before publication. The old public challenge artifact remains in the repository's historical commit, not in the maintained branch.

For a reproducible 100-company run, the repository includes a holdout input list; run statistics and validation limits are in [VALIDATION.md](VALIDATION.md). Source rights and tool use for any challenge evaluation must also satisfy the current [Signalpost rules](https://builderr.ai/challenges/signalpost) and [evaluation contract](https://builderr.ai/docs/signalpost-evaluation-harness.md).
