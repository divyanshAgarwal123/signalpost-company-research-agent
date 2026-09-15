# Signalpost company research agent

This workspace is at the local baseline stage. [RESEARCH.md](RESEARCH.md) is the verified challenge brief. `agent/` contains the official Builderr starter kit as a starting point. The local runs and limitations are recorded in [BASELINE_RESULTS.md](BASELINE_RESULTS.md). Nothing has been submitted or independently scored by Builderr.

The saved-data refresh check passes with `cd agent && /opt/homebrew/bin/python3.12 first_run.py`. The fixed ten-company development slice is `agent/data/dev10.jsonl` and includes website, no-website, and ambiguous-brand cases. Official source snapshots are kept locally outside version control.

The next technical milestone is allowed external-source discovery and exact-entity publication checks on a hand-labelled slice. The existing 100-company no-overlap run satisfies the terminal-envelope and request-budget checks, but its external coverage is far below what a prize contender needs.
