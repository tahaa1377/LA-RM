#!/bin/bash
cd "$(dirname "$0")/.."
export LARM_PROCS=${LARM_PROCS:-1}
R=results_rev2
unset LARM_POLICIES
python3 experiments/candidates_rev.py $R/candidates.json
python3 experiments/ksweep_cands.py $R/ksweep_div.json $LARM_PROCS
LARM_CANDS=div python3 experiments/run_baselines.py abilene $R/div_abilene.json 0,600,800,1100 10 adaptive
LARM_CANDS=div python3 experiments/run_baselines.py abilene $R/div_abilene_aware.json 1100 10 aware
python3 experiments/run_baselines.py abilene $R/yen_abilene_aware.json 1100 10 aware
LARM_CANDS=div python3 experiments/run_baselines.py geant $R/div_geant2012.json 0,600,800,1100 10 adaptive
LARM_CANDS=div python3 experiments/run_baselines.py geant $R/div_geant2012_aware.json 1100 10 aware
python3 experiments/run_baselines.py geant $R/yen_geant2012_aware.json 1100 10 aware
for t in geant2009 geant2010; do
  LARM_CANDS=div python3 experiments/run_baselines.py $t $R/div_$t.json 600,1100 10 adaptive
  python3 experiments/run_baselines.py $t $R/yen_${t}_1100.json 1100 10 adaptive
done
export LARM_MAXODS=1500
LARM_CANDS=div python3 experiments/run_baselines.py uscarrier $R/div_uscarrier.json 600,1100 5 adaptive 45
python3 experiments/run_baselines.py uscarrier $R/yen_uscarrier_1100.json 1100 5 adaptive 45
LARM_CANDS=div python3 experiments/run_baselines.py cogentco $R/div_cogentco.json 600,1100 5 adaptive 55
python3 experiments/run_baselines.py cogentco $R/yen_cogentco_1100.json 1100 5 adaptive 55
echo DIVERSE_DONE
