import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim, Policy


def ft(args):
    siasat, tokhm = args
    G, taghaza, f = seed_instance("fattree4", tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=24 * f, ofogh=110, garmkardan=20, tokhm=tokhm,
            hadde_aksare_keshidegi=2.5, hamlegar="adaptive", ghavanine_hamle=1300)
    s.run()
    seq = [t[0] for t in s.targets]
    reaims = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
    yal = np.mean([1.0 if n < 8 else 0.0 for n in seq])
    return siasat, reaims, yal


def ab(tokhm):
    G, taghaza, f = seed_instance("abilene", tokhm)
    s = Sim(G, taghaza, Policy.LARM, zarfiat=1000, maghyase_nerkh=40 * f, ofogh=110, garmkardan=20, tokhm=tokhm,
            hadde_aksare_keshidegi=2.5, hamlegar="adaptive", ghavanine_hamle=800)
    s.run()
    hub = s.targets[-1][0]
    nb = sorted(set(G.successors(hub)) | set(G.predecessors(hub)))
    return [len(s.table[n]) / 1000 for n in nb]


def main():
    siasatha = [Policy.SP, Policy.LARM, Policy.GREEDY, Policy.SPR, Policy.LARMR]
    with Pool(2) as estakhr:
        natije = estakhr.map(ft, [(p, s) for p in siasatha for s in range(10)])
        eshghal = estakhr.map(ab, range(10))
    for p in siasatha:
        r = [x for x in natije if x[0] == p]
        print(f"fat-tree 1300 {p:11} re-aims/run {np.mean([x[1] for x in r]):.1f} "
              f"edge-target share {np.mean([x[2] for x in r]):.3f}")
    allocc = np.concatenate([np.array(o) for o in eshghal])
    print(f"abilene 800 LA-RM hub-neighbor occupancy: median {np.median(allocc):.2f}, "
          f"10-90% {np.percentile(allocc, 10):.2f}-{np.percentile(allocc, 90):.2f}")


if __name__ == "__main__":
    main()
