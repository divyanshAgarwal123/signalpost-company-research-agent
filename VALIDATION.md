# Validation

Checked on **6 October 2026** with the maintained code, Python 3.12, and the pinned `agent/uv.lock`. The live runs used a complete official Brønnøysund bulk snapshot downloaded on 15 September 2026 (SHA-256 `4ff19012c86ecf16bd7caeaea6735b2672eea904c8d52214de76090302cdfd70`) plus live public API and website responses on the check date. The older snapshot anchors legal identity; live module results can change between runs.

| Check | Observed result | What it establishes |
| --- | --- | --- |
| Unit and saved-source tests | 124 passed | Core normalization, identity, evidence, refresh, claim uniqueness, and other local behavior pass their tests. |
| Saved-data refresh walkthrough | Two expected changes found; zero false changes; evidence complete; unchanged rerun stable | Deterministic replay works on the included fixture. This is not a live refresh reliability estimate. |
| Live ten-company batch | 10/10 terminal envelopes in 34.8 seconds; 110 reported requests; 314 claims; zero reported source errors | The documented command ran end to end with the official snapshot and live sources. Three websites passed the current identity gate; two were withheld as ambiguous; five were not available. [Run report](examples/dev10-run-report.json). |
| Live 100-company holdout | 100/100 terminal envelopes in 142.2 seconds; 637 reported requests; $0 declared paid API cost; 2,492 claims | The same command handled a separate 100-company input. The run had one website HTTP 429, explicitly marked `failed`; the other modules completed. [Run report](examples/holdout100-run-report.json). |

A separate audit of the final holdout output found 2,492 unique claim IDs, zero unresolved summary citations, and zero claims missing a source URL, retrieval time, content hash, or supporting span. Six websites passed the current identity gate, ten were marked ambiguous, 83 were unavailable, and one failed with HTTP 429. Ninety-nine financial modules were available and one was unavailable. A terminal envelope means the agent returned a result and labelled source availability; it does not mean every field was found. Structural validation checks exact count, unique organisation numbers, terminal company/module states, and zero silent drops. It does not independently verify every source claim, external-company precision, or recall.

The original 15 September challenge revision is preserved at [`ef2455b`](https://github.com/divyanshAgarwal123/signalpost-company-research-agent/tree/ef2455bc6017e0962b4681f7e2bbef41fe3dcd7b). Its historical corpus and reports remain in that commit. Those runs do not prove the behavior of later source responses or a challenge score.

## Open checks

- Independently label a held-out set of website and external-company matches to measure wrong-company publication and recall.
- Recheck the optional Brave and registered NAV paths with valid access, usage rights, redirect/request accounting, and a sufficiently long jobs index.
- Repeat live batches across dates and network conditions, and audit original source bytes against retained claim hashes where reuse rights permit.
- Deploy and monitor a service only after the local batch workflow has an operator, schedule, and source-rights plan. This repository currently provides a local command-line tool.
