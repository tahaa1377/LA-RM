#!/bin/bash
cd "$(dirname "$0")/.."
export LARM_PROCS=${LARM_PROCS:-2}
export LARM_POLICIES=larm2,larm2_nr
R=results_rev4
mkdir -p $R
rb() { python3 experiments/run_baselines.py "$@" | tail -n +1; }
rb fattree4 $R/l2_fattree4.json 0,300,600,750,900,1300,1800,2500 10 adaptive
for adv in static aware smart; do rb fattree4 $R/l2_fattree4_$adv.json 900,1300 10 $adv; done
rb abilene $R/l2_abilene.json 0,150,300,450,600,800,1100,1500,2100 10 adaptive
for adv in static aware smart; do rb abilene $R/l2_abilene_$adv.json 600 10 $adv; done
rb abilene $R/l2_abilene_aware_1100.json 1100 10 aware
rb abilene_sndlib $R/l2_abilene_sndlib.json 0,150,300,450,600,800,1100,1500,2100 10 adaptive
rb geant_sndlib $R/l2_geant_sndlib.json 0,150,300,450,600,800,1100,1500,2100 10 adaptive
rb geant $R/l2_geant2012.json 0,150,300,450,600,800,1100,1500,2100 10 adaptive
rb geant $R/l2_geant2012_static.json 600,800,1100 10 static
rb geant $R/l2_geant2012_aware.json 600,800,1100 10 aware
rb geant $R/l2_geant2012_smart.json 600 10 smart
LARM_CANDS=div rb abilene $R/l2_div_abilene.json 0,600,800,1100 10 adaptive
LARM_CANDS=div rb abilene $R/l2_div_abilene_aware.json 1100 10 aware
LARM_CANDS=div rb geant $R/l2_div_geant2012.json 0,600,800,1100 10 adaptive
LARM_CANDS=div rb geant $R/l2_div_geant2012_aware.json 1100 10 aware
LARM_ATK_FIXED=1 python3 experiments/ksweep_cands.py $R/l2_ksweep_fixedatk.json $LARM_PROCS
python3 experiments/ksweep_cands.py $R/l2_ksweep.json $LARM_PROCS
for t in geant2009 geant2010; do
  rb $t $R/l2_$t.json 600,1100 10 adaptive
  LARM_CANDS=div rb $t $R/l2_div_$t.json 600,1100 10 adaptive
done
export LARM_MAXODS=1500
rb uscarrier $R/l2_uscarrier.json 600,1100 5 adaptive 45
LARM_CANDS=div rb uscarrier $R/l2_div_uscarrier.json 600,1100 5 adaptive 45
rb cogentco $R/l2_cogentco.json 600,1100 5 adaptive 55
LARM_CANDS=div rb cogentco $R/l2_div_cogentco.json 600,1100 5 adaptive 55
echo REVISED_DONE
