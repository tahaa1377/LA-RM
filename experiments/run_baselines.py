"""Occupancy-aware baselines added in revision.

Compares LA-RM with three policies that use the same candidate paths and the same
occupancy signal but no learning:
  greedy      each new flow takes the candidate with the best score
              1 - (busiest switch) - beta*(stretch-1) on the current tables,
              in the style of STAR / DIFF;
  sp_retry    shortest path, falling back to the cheapest candidate that avoids
              full switches;
  larm_retry  LA-RM whose blocked draw is re-drawn among the candidates that
              avoid full switches.
Also reruns the four original policies, so that every comparison is paired by
seed. Saves per-seed admission and paired differences against LA-RM.

Usage: python experiments/run_baselines.py <topo> <out.json> <budgets comma-separated>
       [seeds] [adversary] [lam]
Environment: LARM_POLICIES (comma-separated subset of policies), LARM_MAXODS (sample
of OD pairs on the large carriers, as in run_main.py).
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim, Policy
from larm.stats import ci95

POLICIES = [Policy.SP, Policy.ECMP, Policy.URM, Policy.LARM,
            Policy.GREEDY, Policy.SPR, Policy.LARMR]
if os.environ.get("LARM_POLICIES"):
    POLICIES = [p for p in os.environ["LARM_POLICIES"].split(",") if p]
WU, HOR, MS = 20, 110, 2.5
_NAME = _MAXODS = None


def _init(name):
    global _NAME, _MAXODS
    mo = os.environ.get("LARM_MAXODS")
    _NAME, _MAXODS = name, int(mo) if mo else None


def _one(args):
    pol, atk, seed, lam, cap, adv = args
    G, dem, f = seed_instance(_NAME, seed, max_ods=_MAXODS)
    s = Sim(G, dem, pol, cap=cap, lam_scale=lam * f, horizon=HOR, warmup=WU, seed=seed,
            max_stretch=MS, attacker=adv if atk else "none", atk_rules=atk)
    r = s.run()
    return pol, atk, seed, r["admission"], r["peak_occ"], r["mean_stretch"], r["installs_per_s"]


def main():
    topo, out = sys.argv[1], sys.argv[2]
    budgets = [int(x) for x in sys.argv[3].split(",")]
    seeds = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    adv = sys.argv[5] if len(sys.argv) > 5 else "adaptive"
    lam = 24 if topo.startswith("fattree") else 40
    if len(sys.argv) > 6:
        lam = float(sys.argv[6])
    cap = 1000
    jobs = [(p, a, s, lam, cap, adv) for p in POLICIES for a in budgets for s in range(seeds)]
    t0 = time.time()
    with Pool(2, initializer=_init, initargs=(topo,)) as pool:
        res = pool.map(_one, jobs)
    R = {}
    for pol, atk, seed, adm, pk, st, ins in res:
        R.setdefault(pol, {}).setdefault(atk, {})[seed] = (adm, pk, st, ins)
    od = {"topo": topo, "adversary": adv, "seeds": seeds, "budgets": budgets,
          "lam": lam, "cap": cap, "policies": {}, "paired_vs_larm": {}}
    for pol in POLICIES:
        od["policies"][pol] = {}
        for a in budgets:
            v = [R[pol][a][s] for s in range(seeds)]
            od["policies"][pol][str(a)] = {
                "admission": ci95([x[0] for x in v]),
                "adm_runs": [x[0] for x in v],
                "peak": ci95([x[1] for x in v]),
                "stretch": ci95([x[2] for x in v]),
                "installs_per_s": ci95([x[3] for x in v]),
            }
    for pol in POLICIES:
        if pol == Policy.LARM or Policy.LARM not in POLICIES:
            continue
        od["paired_vs_larm"][pol] = {}
        for a in budgets:
            d = [R[Policy.LARM][a][s][0] - R[pol][a][s][0] for s in range(seeds)]
            od["paired_vs_larm"][pol][str(a)] = ci95(d, scale=100.0, nd=2)  # points
    od["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(od, open(out, "w"), indent=1)
    print(f"{topo} ({adv}) {od['elapsed_s']}s")
    for a in budgets:
        row = "  ".join(f"{p}={od['policies'][p][str(a)]['admission'][0]:.3f}" for p in POLICIES)
        print(f"  budget {a}: {row}")
        if Policy.LARM in POLICIES:
            row = "  ".join(f"{p}:{od['paired_vs_larm'][p][str(a)][0]:+.1f}±{od['paired_vs_larm'][p][str(a)][1]:.1f}"
                            for p in POLICIES if p != Policy.LARM)
            print(f"    LA-RM minus: {row}")


if __name__ == "__main__":
    main()
