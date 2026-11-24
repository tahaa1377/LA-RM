#!/bin/bash
set -e
cd "$(dirname "$0")"
P=${P:-2}
mkdir -p results
python3 experiments/run_extra.py results "$P"
python3 experiments/run_kfloor.py results/kfloor.json "$P"
python3 experiments/run_evict.py results "$P"
python3 experiments/run_admtrace.py results/admtrace_heavy.json "$P"
python3 experiments/run_learn.py results/learn_curve.json
python3 experiments/run_main.py results "$P"
if [ -d runs ]; then
  python3 experiments/testbed_summary_rev.py runs results/testbed.json
fi
echo "REPRODUCE_DONE"
