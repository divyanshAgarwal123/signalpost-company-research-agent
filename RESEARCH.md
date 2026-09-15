# Signalpost challenge research

Checked 15 September 2026 (Asia/Kolkata). This document records the research stage before implementation. Builderr's current challenge page and scoring version 2 contract control if an older indexed page or starter note disagrees.

## What the owner needs

Signalpost should turn a Norwegian organisation number into a useful, up-to-date company profile. The reader needs the exact legal entity, official financials and roles, locations, a verified public website/brand, hiring, dated activity and a clear account of what changed. Every material fact must link to an allowed source, retrieval date, relevant effective or reporting period, and stored evidence. Missing, blocked and ambiguous information remains explicit. The agent must research company numbers it has never profiled before; preloading only the submitted 1,000 is insufficient.

The public sample shows the intended reader flow: search a company, inspect its profile and sources, ask a question answered only from supported facts, and browse or compare records. The sample is a dated fixture, not a production service or the final answer key. Builderr's business goal is a company intelligence product that can be launched in Norway with Håvard Liltved Dalen; the partnership is an opportunity offered to the winner, not a guaranteed job or cash equivalent.

Sources: [current challenge](https://builderr.ai/challenges/signalpost), [public sample](https://builderr.ai/signalpost), [agent playbook](https://builderr.ai/starter-briefs/signalpost-agent-playbook.md).

## What must be submitted

1. At least 1,000 completed profiles selected from Builderr's published 411,160-company universe, plus the exact organisation-number manifest. More than 1,000 profiles are allowed.
2. A repository URL and **exact commit hash**, pinned dependencies, one reproducible command that accepts a JSONL batch of organisation numbers, and code that emits exactly one terminal result envelope for each input.
3. A previous-snapshot input and material-change output. Repeated runs on the same snapshot cannot create duplicates or false changes; a failed refresh must preserve earlier supported evidence.
4. Declared models, APIs, licences, source rights, external caches, expected cost per 100-company run, server-side secrets policy and safe outbound URL policy. A machine-readable run report should include runtime, request count and third-party spend.
5. Email the exact submission details to `submit@builderr.ai` by **21 October 2026**. Version one can be followed by up to four revised exact commits, but revisions close **18 October** and affect only later daily batches. An email draft or repository upload is not proof of acceptance; wait for Builderr's acknowledgement and evaluation status.

The minimal envelope contains `organisation_number`, run and terminal status, claims, evidence, changes, errors and operations. Each claim points to evidence with a source URL/class, retrieval time, content hash and supporting span. The availability states are `available`, `not_available`, `blocked`, `not_applicable`, `ambiguous` and `failed`. A checked source with zero jobs is different from an unchecked source.

Sources: [challenge submission section](https://builderr.ai/challenges/signalpost), [evaluation contract](https://builderr.ai/docs/signalpost-evaluation-harness.md), [starter kit](https://builderr.ai/signalpost-starter-kit.zip).

## How Builderr judges it

Scoring version 2 is effective 26 August 2026. The same **100 randomly selected companies each day** are run for every frozen agent; inputs can fall outside an entrant's published 1,000. Final rank is the average of all scheduled daily batches while the frozen entry is active. An entrant-caused failure or missed batch scores zero after a clean reproduction; a shared evaluator failure is void and rerun. The reference collection is a checked union of discoveries from entrants and Builderr crawlers. As it grows, everyone's coverage is rescored against the same version. The final union freezes after eligible submissions are checked. A self-chosen local sample cannot establish final recall.

| Category | Points | What wins them |
| --- | ---: | --- |
| Coverage and source discovery | 35 | Company recall (70% of each field family) and supported fact recall (30%), weighted across information types. |
| Accuracy, exact identity and evidence | 30 | Correct legal-entity match and source-backed, dated claims. |
| Refresh and extensibility | 20 | Real changes without duplicate or invented changes, preserved history. |
| Decision-useful synthesis | 10 | Grounded account of the company, changes and unknowns. |
| UX and interaction | 5 | Easy to find, compare and verify information on desktop and mobile. |

The hard gates are independent of the 100-point score: **at least 65/100 overall, 21/35 coverage, 60% weighted external company recall and 95% exact-entity external precision**. A material wrong-company publication or fabricated financial value fails qualification. Also required: 1,000 valid profiles and manifest; exactly 100 terminal envelopes per daily batch; claim-level source/retrieval/reporting evidence; distinct availability states; idempotent refresh and history; reproducible pinned setup; declared lawful source rights, safe URL handling and server-side secrets.

Each 100-company daily run has **45 minutes, 8 vCPU, 16 GB RAM, 10 GB temporary disk, 2,000 outbound requests including redirects/retries, and $10 maximum declared third-party API spend**. Caches must be declared. Builderr provides an official registry snapshot, but external claims still need timestamps and refresh proof. Ties break on fewer wrong-company publications, then better weighted company recall, then lower external API cost.

The public contract does not enumerate every field-family weight or provide the hidden reference union. The local benchmark should therefore track external company recall by family, publication precision, evidence-span validity, refresh false positives, request/cost budget and p50/p95 runtime rather than treating a local point estimate as the award score.

Sources: [current challenge](https://builderr.ai/challenges/signalpost), [scoring version 2 contract](https://builderr.ai/docs/signalpost-evaluation-harness.md).

## Existing reviewed submissions

Builderr's board says **five submissions, four assessed, one under review**, reviewed 13 September. These are provisional scores from one shared 100-company diagnostic batch, not final averages. None is confirmed qualified.

| Entry | Published status | Revealed weakness |
| --- | --- | --- |
| Ajai | 67.46/100, provisional | Coverage below the qualification minimum. |
| Anmol | 69.57/100, provisional | One website was attached to the wrong company in revision two. |
| Karthik / AAFA | 49.03/100, provisional | Coverage and company matching need work. |
| Meet | Unscored, under review | Builderr requested confirmation of the exact code version and explanation of unsupported records. |
| Penge | 65.12/100, provisional | Coverage below the qualification minimum. |

Source: [reviewed-entry board](https://builderr.ai/challenges/signalpost).

### Public competitor code, with a separate evidence boundary

[Anmol's public repository](https://github.com/AnSa30-06/signalpost-norway) describes the same revision-two **69.57/100** wrong-site result as the board. It combines official registry/accounts/roles/subunits, NAV job postings, company sites and dated activity. Its README says the next revision tightened website acceptance to an organisation number on the site, an exact legal name plus full registered address, or a domain the company filed with the registry. It reports 1,000 generated profiles and a 100-company local budget run, but its local accuracy and revision-three repair have **not** been confirmed as qualified by Builderr's board. The revealing tradeoff is that stricter matching withdrew some websites and reduced measured local recall; precision must be protected while adding independently proved external coverage.

Other public GitHub projects self-describe as Signalpost attempts; **their presence is not proof of official submission or scoring**. [Rakesh's project](https://github.com/Rakesh-Tummala/signalpost-company-agent) extends the reference kit with optional Tavily/Exa site discovery and deeper company-site crawling. [Kildespor](https://github.com/officialarghya29/kildespor) claims 1,000 mostly registry-backed profiles, exact evidence chains and conservative site publication; its self-reported website coverage is 8.6%, suggesting an external-recall challenge if confirmed on random inputs. [Balram's project](https://github.com/Balram-1/signalpost-norway-agent) uses browser and model enrichment; its request, cost, source-rights and exact-identity behavior would need independent checks. None of those public projects is linked by Builderr to Ajai, Karthik/AAFA, Meet or Penge in the sources inspected.

Competitor pattern: many builders can produce the 1,000 registry profiles; the scarce differentiator is **allowed external facts about the exact company** without publishing group, brand, franchise or similarly named entity information as if it belonged to that legal entity. Builderr has already rejected a high score because of a single material website mismatch.

## Sources and data rights

Use [Brønnøysundregistrene open data](https://data.brreg.no/enhetsregisteret/api/dokumentasjon/en/index.html) as the organisation-number identity anchor. Its public API covers legal entities, roles, subunits and group structures; official accounts are a separate filed-financial source. The registry's NLOD licence is documented. A registry-listed website is a candidate, not proof that every page and brand on it represents exactly the legal entity. Add verified company-owned static pages, sitemaps, structured data, jobs and dated news, then official/licensed external feeds as allowed. Search results propose candidate domains but are not evidence for published claims.

The [Signalpost source policy](https://builderr.ai/starter-briefs/signalpost-sources.md) requires exact-entity verification, source URL or ID, retrieval/effective date, content hash and extraction method. It cautions against unofficial LinkedIn, Meta, Glassdoor, Indeed and Google collection merely because code is available. The [NAV job-feed terms](https://arbeidsplassen.nav.no/vilkar-api) allow use and republication, with obligations to update or remove inactive adverts and handle personal information appropriately. Those rules must be accounted for before making jobs a production connector.

The starter kit already supplies a baseline registry-to-envelope pipeline, refresh replay, tests and sample product shape. Its README explicitly says it is **not a winning submission**. Some deeper starter notes discuss an older or internal “55 external points” and an 80-point objective; those conflict with the current published five-category version-two rubric, so they are ideas for experiments rather than scoring authority.

Sources: [starter kit](https://builderr.ai/signalpost-starter-kit.zip), [playbook](https://builderr.ai/starter-briefs/signalpost-agent-playbook.md), [learning guide](https://builderr.ai/starter-briefs/signalpost-learning-harness.md), [current evaluation contract](https://builderr.ai/docs/signalpost-evaluation-harness.md).

## Prize strategy and limitations

The **$2,000 main pool** awards $1,200/$500/$300 for first/second/third among qualified entries. The **separate $500 JBOX bonus** awards $250/$150/$100 to top qualifying JBOX-built agents. Four **$100 community awards** are dated 6 September, 20 September, 4 October and 18 October; votes do not affect technical rank and only qualified entries enter the hosted gallery. September 6 has already passed. The winner also gets an opportunity to discuss a Norway launch partnership.

One entrant cannot occupy first, second and third in the same ranking. The sensible maximum target is **first in the main pool ($1,200), first in the JBOX pool ($250), and eligible community awards still ahead**. The page does not specify exactly what proof makes an agent “built with JBOX,” whether main and JBOX awards can be stacked for one entrant, or whether one entrant may win more than one fortnightly public vote. Those conditions need organizer clarification before counting a $1,450 combined technical award or multiple community awards as guaranteed. JBOX's own [product site](https://www.jboxai.com/) describes a web-product builder that exports Next.js/Supabase/GitHub work; it does not describe how its provenance is checked for this prize. Its site says 50 starting credits, with additional credits for purchase, so any paid use should be a deliberate choice.

Submission and finalist status do not guarantee a prize. Builderr verifies exact frozen artifacts and may leave prizes unawarded if no entry qualifies. The main engineering risk is that a cautious identity gate protects precision but starves external recall; the opposing risk is that looser candidate matching creates one material wrong-company publication.

Sources: [prize schedule and eligibility](https://builderr.ai/challenges/signalpost), [platform rules](https://builderr.ai/guidelines), [JBOX product](https://www.jboxai.com/).

## Build decision after this research

Pursue a deterministic legal-identity and evidence core, then improve **measured external company recall** on a hand-labelled development set and a separate no-overlap validation set. Start with official fields, exact website verification and company-owned static content; add allowed job/activity connectors only when they produce supported extra facts without increasing wrong-company publications. Preserve immutable snapshots and span-level claim proof before adding summaries or a gallery UI. Use a decision table for fallbacks: static HTTP before browser rendering, and model extraction only after direct extraction fails and every output is checked against its source.

Before freezing a submission, exercise the official output contract on 100 unseen inputs under the daily budget and produce the 1,000-profile artifact from the frozen 411,160-company universe. Verify identity and provenance failures, exact envelope count, repeat refresh, coverage by external field family, and cost/runtime in a clean run. A high local score is not a substitute for Builderr's independent evaluation.

Sources: [playbook](https://builderr.ai/starter-briefs/signalpost-agent-playbook.md), [learning guide](https://builderr.ai/starter-briefs/signalpost-learning-harness.md), [evaluation contract](https://builderr.ai/docs/signalpost-evaluation-harness.md).
