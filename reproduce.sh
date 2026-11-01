#!/bin/bash
# Full pipeline from scratch on an Apple-silicon Mac. data/ already holds every intermediate file,
# so to recompute only the tables and figures, run the analysis steps at the end.
set -e
cd "$(dirname "$0")"
python harness/memguard.py &   # optional safety net: kills runaway experiment processes if memory runs low
GUARD=$!
trap "kill $GUARD 2>/dev/null" EXIT
# data/items.json and data/scores_*.json come from planted-cheats-vs-llm-monitors
python scripts/01_reduce.py reduce A          # unconstrained ddmin on flagged items (about 20 min)
python scripts/01_reduce.py reduce_syntax A   # ddmin where kept code must parse and define the function (about 25 min)
python scripts/01_reduce.py probes A          # word-only probes on honest correct code (about 15 min)
python scripts/01_reduce.py probes B
python scripts/02_analyze.py
