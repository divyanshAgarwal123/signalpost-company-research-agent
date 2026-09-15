# Signalpost company research agent

This workspace is at the local baseline stage. [RESEARCH.md](RESEARCH.md) is the verified challenge brief. `agent/` contains the official Builderr starter kit as a starting point; it has not been submitted, independently scored, or improved for coverage yet.

The saved-data refresh check passes with `cd agent && /opt/homebrew/bin/python3.12 first_run.py`. The fixed ten-company development slice is `agent/data/dev10.jsonl` and includes website, no-website, and ambiguous-brand cases. Official source snapshots are kept locally outside version control.

The next technical milestone is a 10-company live batch with a report of verified external coverage and identity abstentions. Subsequent work must improve supported external recall while preserving zero material wrong-company publications on a separate hand-labelled validation set.
