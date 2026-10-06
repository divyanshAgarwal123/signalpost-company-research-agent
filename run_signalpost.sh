#!/bin/sh
set -eu

if [ "$#" -lt 3 ] || [ "$#" -gt 5 ]; then
  echo "Usage: run_signalpost.sh INPUT_JSONL BRREG_BULK_CSV_GZ OUTPUT_DIRECTORY [EXPECTED_COUNT] [PREVIOUS_ENVELOPES_JSONL]" >&2
  exit 2
fi

organisations=$1
bulk=$2
output_dir=$3
expected_count=${4:-100}
previous_envelopes=${5:-}
start_dir=$(pwd)
case "$organisations" in /*) ;; *) organisations="$start_dir/$organisations" ;; esac
case "$bulk" in /*) ;; *) bulk="$start_dir/$bulk" ;; esac
case "$output_dir" in /*) ;; *) output_dir="$start_dir/$output_dir" ;; esac
if [ -n "$previous_envelopes" ]; then
  case "$previous_envelopes" in /*) ;; *) previous_envelopes="$start_dir/$previous_envelopes" ;; esac
fi
mkdir -p "$output_dir"
agent_dir=$(CDPATH= cd -- "$(dirname -- "$0")/agent" && pwd)
cd "$agent_dir"

uv_command=$(command -v uv || true)
if [ -z "$uv_command" ] && [ -x /opt/homebrew/bin/uv ]; then
  uv_command=/opt/homebrew/bin/uv
fi
if [ -z "$uv_command" ]; then
  echo "Install uv before running this pinned entry point." >&2
  exit 2
fi

set -- --organisations "$organisations" --bulk "$bulk" \
  --profiles-output "$output_dir/profiles.jsonl" \
  --output "$output_dir/envelopes.jsonl" \
  --report "$output_dir/run-report.json" \
  --run-id "signalpost-$(date -u +%Y%m%dT%H%M%SZ)" \
  --expected-count "$expected_count"
if [ -n "$previous_envelopes" ]; then
  set -- "$@" --previous-envelopes "$previous_envelopes"
fi
"$uv_command" run --frozen python scripts/run_batch.py "$@"
