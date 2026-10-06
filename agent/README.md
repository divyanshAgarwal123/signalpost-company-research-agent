# Signalpost implementation

The project overview, quick start, and limitations are in the [repository README](../README.md).

The implementation lives in `src/norway_company_agent/`. The main orchestration command is `scripts/run_batch.py`, called by the root `run_signalpost.sh` wrapper. It reads organisation numbers, anchors them to an official bulk snapshot, fetches the selected public modules, applies the identity gate, writes one terminal envelope per input, and records run statistics.

For a saved-source check with no live requests:

```bash
uv run --frozen python first_run.py
uv run --frozen python -m unittest discover -s tests -q
```

For a live ten-company run, download the official bulk file as shown in the root README and run the root wrapper. The optional Brave and NAV integrations are off by default and require separate credentials. See [source notes](../SOURCE_POLICY.md) and [output contract](OUTPUT_CONTRACT.md).
