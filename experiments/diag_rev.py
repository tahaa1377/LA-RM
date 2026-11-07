"""Diagnostics quoted in the revised text (Section VI-B and VI-C).

1) Fat-tree, adaptive adversary, 1300 rules: re-aims per run and the share of
   targeting epochs spent on edge switches, per policy (10 seeds).
2) Abilene, adaptive adversary, 800 rules, LA-RM: occupancy of the hub's
   neighbors at the end of the run (10 seeds).
Usage: python experiments/diag_rev.py
"""
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim, Policy


def ft(args):
    pol, seed = args
    G, dem, f = seed_instance("fattree4", seed)
    s = Sim(G, dem, pol, cap=1000, lam_scale=24 * f, horizon=110, warmup=20, seed=seed,
            max_stretch=2.5, attacker="adaptive", atk_rules=1300)
    s.run()
    seq = [t[0] for t in s.targets]
    reaims = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
    edge = np.mean([1.0 if n < 8 else 0.0 for n in seq])   # switches 0-7 are edge switches
    return pol, reaims, edge


def ab(seed):
    G, dem, f = seed_instance("abilene", seed)
    s = Sim(G, dem, Policy.LARM, cap=1000, lam_scale=40 * f, horizon=110, warmup=20, seed=seed,
            max_stretch=2.5, attacker="adaptive", atk_rules=800)
    s.run()
    hub = s.targets[-1][0]
    nb = sorted(set(G.successors(hub)) | set(G.predecessors(hub)))
    return [len(s.table[n]) / 1000 for n in nb]


def main():
    pols = [Policy.SP, Policy.LARM, Policy.GREEDY, Policy.SPR, Policy.LARMR]
    with Pool(2) as pool:
        res = pool.map(ft, [(p, s) for p in pols for s in range(10)])
        occ = pool.map(ab, range(10))
    for p in pols:
        r = [x for x in res if x[0] == p]
        print(f"fat-tree 1300 {p:11} re-aims/run {np.mean([x[1] for x in r]):.1f} "
              f"edge-target share {np.mean([x[2] for x in r]):.3f}")
    allocc = np.concatenate([np.array(o) for o in occ])
    print(f"abilene 800 LA-RM hub-neighbor occupancy: median {np.median(allocc):.2f}, "
          f"10-90% {np.percentile(allocc, 10):.2f}-{np.percentile(allocc, 90):.2f}")


if __name__ == "__main__":
    main()
