#!/bin/bash
cd "$(dirname "$0")/.."
export LARM_PROCS=2
R=results_rev3
mkdir -p $R
python3 experiments/targets_div.py $R/targets_div.json 2
python3 experiments/fattree_targets.py $R/fattree_targets.json
python3 experiments/run_baselines.py geant $R/yen_geant2012_static.json 800,1100 10 static
python3 experiments/run_baselines.py geant $R/yen_geant2012_aware_800.json 800 10 aware
echo ROUND3_DONE
