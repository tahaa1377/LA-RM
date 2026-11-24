#!/bin/bash
cd "$(dirname "$0")/.."
export LARM_PROCS=${LARM_PROCS:-1}
R=results_rev2
unset LARM_POLICIES LARM_CANDS
for t in geant2009 geant2010; do
  python3 experiments/run_baselines.py $t $R/yen_${t}_600.json 600 10 adaptive
done
LARM_MAXODS=1500 python3 experiments/run_baselines.py uscarrier $R/yen_uscarrier_600.json 600 5 adaptive 45
LARM_MAXODS=1500 python3 experiments/run_baselines.py cogentco $R/yen_cogentco_600.json 600 5 adaptive 55
echo YEN600_DONE
