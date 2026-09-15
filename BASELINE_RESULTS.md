# Signalpost baseline measurements

Measured 15 September 2026. The frozen `agent/data/dev10.jsonl` development slice has five registry-listed website cases and five without. The separate `agent/data/validation100.jsonl` contains 100 organisation numbers drawn from the same fixed candidate list, excluding those ten. These are local samples and do not reproduce Builderr's hidden reference union or final score.

The official starter runs with pinned Python 3.12 dependencies. Its saved-snapshot refresh demonstration passed, including idempotence. The starter suite passed 105 tests and five subtests after one conservative identity-rule improvement: a same-host company page can establish exact identity when the full registered legal name and registered postcode/place appear together. That rule accepted a Hallingdal and Valdres Eiendomstaksering AS contact page in the development slice; a wrong address still fails the regression test. Broad Møller Bil and Coop Extra pages stayed quarantined. The development rerun emitted 10/10 terminal envelopes in 88 outbound requests. Three fetched sites passed the site's deterministic publishability gate, but the change from the first run also reflects a previously unreachable Yatek site becoming reachable; it cannot be credited entirely to the rule change.

The no-overlap 100-company run emitted **100/100 terminal envelopes**, with zero silent drops and all module states terminal. It took 83 seconds, made **550 outbound requests**, transferred 4.4 MB, and recorded HTTP p50/p95 latencies of 715/1054 ms. That is within the 45-minute and 2,000-request daily limits. These are structural and budget checks only; they do **not** establish a 65-point score, coverage or precision qualification, claim-span acceptance, or lawful rights for new external connectors.

| Local module | Company count with available result | What the count means |
| --- | ---: | --- |
| Official registry, account-obligation and live registry | 100/100 each | Source response available, not a coverage score. |
| Official financials and roles | 100/100 each | One accounts record per company; 380 role records in total. Claims still require evaluator-grade span and reporting-date checks. |
| Official location response | 100/100 | 71 companies had at least one returned subunit; 29 had zero. |
| Official group response | 8/100 | 92 were explicitly `not_found`. |
| Registry-listed website | 13/100 | A candidate URL exists; it is not itself exact-entity proof. |
| Fetched website | 10/100 | Six ambiguous/related/review, four exact by the current deterministic gate. Two site requests errored and one was blocked. |

The four publishable fetched-site cases were Irisinfo AS, Lyseon AS, World Wide Narrative AS and Energikontroll AS. Their captured titles/domains align with the legal names, but this is **not** a blinded 95% precision estimate or independent proof of site ownership. The six fetched but nonpublishable cases included manager/umbrella sites for a housing sameie and borettslag, plus ambiguous operating-brand sites. Those abstentions protect identity precision but reduce external company recall.

The immediate work is to add permitted and documented discovery for jobs, dated public activity and company-owned pages when the registry has no usable URL. Every candidate must be resolved against the organisation number or full legal name plus matching registry address before publication. Then hand-label external-company matches on the separate validation slice, track recall and wrong-company publications by source family, and rerun the exact 100-company budget. Only after coverage and identity improve should the 1,000-profile artifact, evaluator-grade claim spans, synthesis, UI and submission freeze be attempted.

The full local run report is `agent/out/validation100-report.json`; generated profiles/envelopes and large source snapshots stay outside version control. Official constraints: [current challenge](https://builderr.ai/challenges/signalpost) and [scoring contract](https://builderr.ai/docs/signalpost-evaluation-harness.md).
