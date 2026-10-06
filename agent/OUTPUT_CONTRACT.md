# Batch output contract

`run_signalpost.sh` writes one JSON object per input organisation number to `envelopes.jsonl`, in input order. The core fields are:

| Field | Meaning |
| --- | --- |
| `organisation_number`, `legal_identity` | Requested ID and verified registry identity. |
| `run_id`, `started_at`, `completed_at`, `state` | Run and terminal status. |
| `modules` | Each requested module's availability state, retry count, and final timestamp. |
| `claims` | Material facts with IDs, values, and source evidence. |
| `source_snapshots` | Bounded claim spans tied to source URLs, hashes, and retrieval times. |
| `refresh` | Deterministic comparison key and material changes when earlier envelopes are provided. |
| `summary` | Sentences linked to supporting claim IDs and a list of unknowns. |
| `errors` | Source or processing failures. |

The six module states are `available`, `not_available`, `blocked`, `not_applicable`, `ambiguous`, and `failed`. Missing or unverified information is not silently converted into a negative fact.

The companion `run-report.json` records input and output counts, total runtime, request and byte counts, API cost declaration, and structural validation. `profiles.jsonl` is the working observation record and may contain fetched source excerpts. See the [root README](../README.md) for the one-command run and [source notes](../SOURCE_POLICY.md) before sharing outputs.
