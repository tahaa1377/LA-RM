# New work for the revised manuscript

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
was run from its source tree with a small `ryu-manager` launcher; Ryu's own code was
not touched.

# Second round (review of November 2026)

## Code

- `larm/sim.py`
  - `Policy.GREEDY_POLL` (`greedy_poll`): greedy routing on the occupancy read once per
    epoch (the snapshot LA-RM learns from) instead of live counts; a flow sent into a
    switch that filled since the reading is lost.
  - `halate_kandid` selects the candidate sets (`yen`, the default; `div`, diverse sets;
    `ties` and `np` are intermediate variants kept for reference). `kandidhaye_hamle=(k, halat)`
    places the adversary's flows on a fixed reference table instead of the defense's
    candidates. Candidate tables are cached per process.
  - New metrics: `mean_stretch_admitted` and the per-epoch `(offered, lost)` trace
    `ol_trace`. Everything else stays as it was: every earlier result is reproduced exactly.
- `larm/paths.py`: `diverse()` builds node-disjoint paths first, then the shortest
  detours around the busiest transit switches of the shortest path, then Yen's
  paths, with pair-specific random ties; `sp_shares()` ranks the switches.
- `experiments/run_baselines.py`: `LARM_CANDS`, `LARM_PROCS`, and `stretch_admitted`
  in the output.
- `experiments/cor1_check.py`: Corollary 1 from its analytical inputs (fluid and
  Erlang forms) against simulation, static adversary.
- `experiments/candidates_rev.py`, `experiments/tables_cands.py`,
  `experiments/ksweep_cands.py`, `experiments/run_diverse_rev.sh`,
  `experiments/run_yen600_rev.sh`: the comparison of candidate sets.
- `experiments/figures_rev.py`: `fig_cor1`; `fig_bound` gains a GEANT2012 group with
  diverse candidates; Figs. 2-4 are slightly shorter.
- `testbed/net.py`, `testbed/run_attack_rev.sh`: `--k` / `K` for the number of
  candidates (default 3, as before). `experiments/testbed_summary_k4.py` summarizes
  the k=4 series next to the k=3 one.

## Results (`results_rev2/`, and `results_rev/cor1_check.json`)

```
python3 experiments/cor1_check.py results_rev/cor1_check.json
R=results_rev2
LARM_POLICIES=greedy,greedy_poll python3 experiments/run_baselines.py fattree4 $R/poll_fattree4.json 900,1300 10 adaptive
LARM_POLICIES=greedy,greedy_poll python3 experiments/run_baselines.py abilene $R/poll_abilene.json 600,800 10 adaptive
LARM_POLICIES=greedy,greedy_poll python3 experiments/run_baselines.py geant $R/poll_geant2012.json 600,800 10 adaptive
python3 experiments/run_baselines.py fattree4 $R/ovh_fattree4.json 0,900,1300 10 adaptive
python3 experiments/run_baselines.py abilene $R/ovh_abilene.json 0,600,800 10 adaptive
python3 experiments/run_baselines.py geant $R/ovh_geant2012.json 0,600,800 10 adaptive
bash experiments/run_diverse_rev.sh        # candidates.json, ksweep_div.json, div_*.json, yen_*_1100.json
bash experiments/run_yen600_rev.sh         # yen_*_600.json
LARM_ATK_FIXED=1 python3 experiments/ksweep_cands.py $R/ksweep_div_fixedatk.json
python3 experiments/tables_cands.py        # rows of Tables S7-S9
# testbed, k=4 series (as root):
K=4 OUT=runs_k4 POLICIES="urm larm greedy sp_retry larm_retry" bash testbed/run_attack_rev.sh
python3 experiments/testbed_summary_k4.py runs_k4 runs_rev $R/testbed_k4.json
```

# Third round (second review of November 2026)

This round adds only experiment scripts; the simulator and the testbed are as in the second round, and every earlier result is reproduced exactly.

## Code

- `experiments/targets_div.py`: for the five larger backbones and the three
  occupancy-aware policies, the adaptive adversary at 1100 rules with Yen's and with
  diverse candidates; records, per run, the share of attack epochs aimed at the hub
  and the share in which the hub is full, next to admission and the bound 1 - u(hub).
  With diverse sets the adversary leaves the hub for part of the attack, which is why
  admission can exceed 1 - u(hub) (Section VI-F, Section S4).
- `experiments/fattree_targets.py`: the targets of the adaptive adversary on the
  fat-tree at 1300 rules; under greedy routing its first decision, taken on benign
  counts without attack, is an edge switch in every seed (Section VI-B).
- `experiments/run_round3.sh`: runs the two scripts above and the static and
  mutation-aware adversaries on GEANT2012 at 800 and 1100 rules with Yen's candidates,
  which give the same results as the adaptive one (Table II, rows "single").
- `experiments/figures_rev.py`: Figs. 3 and 4 have a one-row legend in the order of the
  bars, with the short policy names of Table II, and a slightly larger left margin so
  that the y label is not cut.

- `experiments/tables_rev.py`: the GEANT2012 rows of Table II at 800 and 1100 rules are
  labeled "single" like the row at 600, since the three single-target adversaries give
  identical results there.

## Results (`results_rev3/`)

```
bash experiments/run_round3.sh     # targets_div.json, fattree_targets.json, yen_geant2012_static.json, yen_geant2012_aware_800.json
python3 experiments/figures_rev.py paper/figs
```

# Fourth round (third review of November 2026)

The seven earlier policies and the adversaries are used as they were, and their stored
per-seed results are reproduced exactly by the current code
(`experiments/regress_check.py`, output in `results_rev4/regress_check.txt`).

## Code

- `larm/automaton.py`: the mixed vector `p_eff` is cached and recomputed only after
  an update (same values as before); the prior is a parameter (`d0`, default 0.5 as
  before); `credit_all` credits every action at once.
- `larm/sim.py`: the revised automaton, `Policy.LARM2` (`larm2`, with retry) and
  `Policy.LARM2_NR` (`larm2_nr`, without). At the end of each epoch every candidate
  of every pair is credited with the reward of Eq. (2) at the polled occupancy
  (0 if one of its switches is full), with learning rate a = 0.4; everything else is
  as in LA-RM and LA-RM+R. `Sim(la_full=True)` gives the same credit to `larm` and
  `larm_retry` with other parameters. `nfull_trace` records the number of full
  switches at the end of every measured epoch.
- `testbed/rm_controller.py`, `testbed/net.py`, `testbed/run_attack_rev.sh`: the
  policies `larm2` and `larm2_nr`; the option `count` (`--count`, `COUNT`). With
  `poll` (default, the behaviour of the earlier series) the controller raises the count of every
  switch of a path except the last at the install and replaces all counts by the
  polled table sizes once per epoch. With `event` it raises the count of every
  switch of the path at the install and lowers it at every FlowRemoved message; the
  poll is then only compared with the counts (`count_gap` in the `.occ` file).
- `experiments/run_d0.py`: the first design for several values of its prior.
- `experiments/dev_full.py`: development runs on seeds 100-109, on which the
  learning rate of the revised automaton was chosen.
- `experiments/run_revised.sh`: the revised automaton on the paper's seeds in every
  setting of the paper (`LARM_POLICIES=larm2,larm2_nr`); `ksweep_cands.py` now
  honours `LARM_POLICIES`.
- `experiments/run_ablation.py`: credit (flows or all candidates) by learning rate,
  with and without retry; the randomization sweep; the Abilene diagnostic (stretch,
  rules per admitted flow, epochs with two or more full switches).
- `experiments/run_trace_rev4.py`: admission per epoch after the attack starts.
- `experiments/gap_summary.py`: the shortfall of every policy from the best one in
  each of the 80 settings in which all eight policies were run.
- `experiments/smart_full.py`: how often a table fills under the smart adversary.
- `experiments/time_epoch.py`: time of the once-per-epoch learning step of the two
  designs on GEANT2012 (output in `results_rev4/time_epoch.txt`).
- `experiments/tables_rev.py`, `experiments/tables_cands.py`: a column for the
  revised automaton; `experiments/tables_rev4.py`: the rows of the new tables.
- `experiments/testbed_summary_rev4.py`: the testbed series with the revised
  automaton, the calibration with exact rule counts and the k=4 series.
- `experiments/figures_rev.py`: the revised automaton in the admission, bound and
  testbed figures; the testbed figure marks the means with exact counts; new figures `fig_cor1_main`, `fig_gap`, `fig_trace2`, `fig_d0`
  and `fig_rand`.

## Results (`results_rev4/`, `runs_rev/atk_larm2_*`, `runs_evt/`, `runs_k4/atk_larm2_*`)

```
R=results_rev4
python3 experiments/run_d0.py $R/d0.json
python3 experiments/dev_full.py $R/dev_full.json
bash experiments/run_revised.sh                       # l2_*.json
python3 experiments/run_ablation.py $R/ablation.json
python3 experiments/run_trace_rev4.py $R/trace.json
python3 experiments/smart_full.py $R/smart_full.json
python3 experiments/time_epoch.py 400 > $R/time_epoch.txt
python3 experiments/gap_summary.py $R/gaps.json
python3 experiments/regress_check.py > $R/regress_check.txt
python3 experiments/tables_rev.py                     # rows of Table II
python3 experiments/tables_cands.py                   # rows of the candidate-set tables
python3 experiments/tables_rev4.py                    # rows of the tables on the revised automaton
# testbed (as root):
POLICIES="larm2" OUT=runs_rev K=3 bash testbed/run_attack_rev.sh
POLICIES="sp greedy sp_retry larm2" OUT=runs_evt K=3 COUNT=event bash testbed/run_attack_rev.sh
POLICIES="larm2" OUT=runs_k4 K=4 bash testbed/run_attack_rev.sh
python3 experiments/testbed_summary_rev4.py $R/testbed_rev.json
python3 experiments/figures_rev.py paper/figs
```
