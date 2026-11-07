# Changes for the revised manuscript

The revised paper compares LA-RM with three occupancy-aware policies that use the same
candidate paths and the same occupancy signal but no learning. Everything below runs
with the same seeds as the original experiments, so all comparisons are paired.

## Code

- `larm/sim.py`: three new policies.
  - `Policy.GREEDY` (`greedy`): each new flow takes the candidate with the best score
    `1 - (busiest switch occupancy) - beta*(stretch-1)` on the current tables, among
    candidates without a full switch (STAR/DIFF style).
  - `Policy.SPR` (`sp_retry`): shortest path; if it crosses a full switch, the cheapest
    candidate that does not.
  - `Policy.LARMR` (`larm_retry`): LA-RM; a draw that hits a full switch is credited 0
    and the flow is drawn again among the candidates without a full switch.
  The four original policies give exactly the same results as before.
- `experiments/run_baselines.py`: runs the seven policies for a topology, a list of
  budgets, a number of seeds and an adversary; saves per-seed admission and paired
  differences against LA-RM. Environment: `LARM_POLICIES` (subset of policies),
  `LARM_MAXODS` (OD sample on the large carriers).
- `experiments/unavoidable.py`: share of demand whose candidates all cross a switch
  (Table II of the paper).
- `experiments/diag_rev.py`: re-aims per run, time on edge switches, occupancy of the
  hub's neighbors (Section VI).
- `experiments/tables_rev.py`: rows of Table III from the result files.
- `experiments/figures_rev.py`: all figures of the paper and the supplement except
  Fig. 1 (TrueType fonts, no Type 3).
- `data/sndlib/README.md`: wording of the note on the data mirror.

## Results (`results_rev/`)

```
R=results_rev
python3 experiments/run_baselines.py fattree4 $R/base_fattree4.json 0,900,1300 10 adaptive
python3 experiments/run_baselines.py fattree4 $R/base_fattree4_aware.json 900,1300 10 aware
python3 experiments/run_baselines.py fattree4 $R/base_fattree4_static.json 900,1300 10 static
python3 experiments/run_baselines.py fattree4 $R/base_fattree4_smart.json 900,1300 10 smart
python3 experiments/run_baselines.py abilene $R/base_abilene.json 0,600,800 10 adaptive
python3 experiments/run_baselines.py abilene $R/base_abilene_full.json 1100 10 adaptive
python3 experiments/run_baselines.py abilene $R/base_abilene_static.json 600 10 static
python3 experiments/run_baselines.py abilene $R/base_abilene_aware.json 600 10 aware
python3 experiments/run_baselines.py abilene $R/base_abilene_smart.json 600 10 smart
python3 experiments/run_baselines.py geant $R/base_geant2012.json 600,800 10 adaptive
python3 experiments/run_baselines.py geant $R/base_geant2012_0_1100.json 0,1100 10 adaptive
python3 experiments/run_baselines.py geant $R/base_geant2012_static.json 600 10 static
python3 experiments/run_baselines.py geant $R/base_geant2012_aware.json 600 10 aware
python3 experiments/run_baselines.py geant $R/base_geant2012_smart.json 600 10 smart
python3 experiments/run_baselines.py abilene_sndlib $R/base_abilene_sndlib.json 0,600,800 10 adaptive
python3 experiments/run_baselines.py geant_sndlib $R/base_geant_sndlib.json 0,600,800 10 adaptive
python3 experiments/run_baselines.py geant_sndlib $R/base_geant_sndlib_full.json 1100 10 adaptive
export LARM_POLICIES=greedy,sp_retry,larm_retry
python3 experiments/run_baselines.py fattree4 $R/curve_fattree4.json 300,600,750,1800,2500 10 adaptive
python3 experiments/run_baselines.py abilene $R/curve_abilene.json 150,300,450,1500,2100 10 adaptive
python3 experiments/run_baselines.py geant $R/curve_geant2012.json 150,300,450,1500,2100 10 adaptive
python3 experiments/run_baselines.py abilene_sndlib $R/curve_abilene_sndlib.json 150,300,450,1100,1500,2100 10 adaptive
python3 experiments/run_baselines.py geant_sndlib $R/curve_geant_sndlib.json 150,300,450,1500,2100 10 adaptive
python3 experiments/run_baselines.py geant2009 $R/base_geant2009.json 600 10 adaptive
python3 experiments/run_baselines.py geant2010 $R/base_geant2010.json 600 10 adaptive
LARM_MAXODS=1500 python3 experiments/run_baselines.py uscarrier $R/base_uscarrier.json 600 5 adaptive 45
LARM_MAXODS=1500 python3 experiments/run_baselines.py cogentco $R/base_cogentco.json 600 5 adaptive 55
unset LARM_POLICIES
python3 experiments/unavoidable.py $R/unavoidable.json
python3 experiments/diag_rev.py
python3 experiments/tables_rev.py
python3 experiments/figures_rev.py paper/figs
```

On a two-core machine the whole list takes about 20 minutes.

## Testbed (second series)

`testbed/rm_controller.py` now also implements `greedy`, `sp_retry` and `larm_retry`,
using the controller's own count of live rules per switch, the count that admission
control already checks. `testbed/run_attack_rev.sh` runs all seven policies under the
attack of `run_attack.sh` (ten runs each, ordered seed by seed) into `runs_rev/`, and
`experiments/testbed_summary_rev.py` summarizes them into `results_rev/testbed_rev.json`
with paired differences against shortest path.

```
sudo testbed/run_attack_rev.sh
python3 experiments/testbed_summary_rev.py runs_rev results_rev/testbed_rev.json
```

The second series ran on a two-core Ubuntu 24.04 virtual machine with Open vSwitch 3.3
(userspace datapath), Mininet 2.3 and Ryu 4.34 under Python 3.9, ten runs per policy;
the raw runs are in `runs_rev/`. Ryu 4.34 does not build with current setuptools, so it
was run from its source tree with a small `ryu-manager` launcher; the code itself is
unchanged.
