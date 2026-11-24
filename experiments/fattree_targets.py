import json
import sys

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim
from larm.stats import ci95


def one(siasat, tokhm):
    G, taghaza, f = seed_instance("fattree4", tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=24 * f, ofogh=110, garmkardan=20, tokhm=tokhm,
            hadde_aksare_keshidegi=2.5, hamlegar="adaptive", ghavanine_hamle=1300)
    yalha = {n for od in s.ods for n in od}
    calls = []
    orig = s._benign_demand

    def hook():
        d = orig()
        calls.append(d)
        return d

    s._benign_demand = hook
    r = s.run()
    tg = [t[0] for t in s.targets if t]
    d0 = calls[0]
    nflows = sum(d0[n] for n in yalha) / 2.0
    return {"seed": tokhm, "admission": r["admission"],
            "decisions": ["edge" if tg[i] in yalha else "transit" for i in range(0, len(tg), 10)],
            "edge_share_of_attack": float(np.mean([t in yalha for t in tg])),
            "first_window_busiest_transit": max(d0[n] for n in s.nodes if n not in yalha) / nflows,
            "first_window_busiest_edge": max(d0[n] for n in yalha) / nflows}


def main():
    khoroji = {}
    for siasat in ["sp", "larm", "greedy", "sp_retry", "larm_retry"]:
        runs = [one(siasat, sd) for sd in range(10)]
        khoroji[siasat] = {"runs": runs,
                    "edge_share_of_attack": ci95([x["edge_share_of_attack"] for x in runs]),
                    "first_window_busiest_transit": ci95([x["first_window_busiest_transit"] for x in runs]),
                    "first_window_busiest_edge": ci95([x["first_window_busiest_edge"] for x in runs]),
                    "first_decision_edge": float(np.mean([x["decisions"][0] == "edge" for x in runs]))}
        v = khoroji[siasat]
        print(f"{siasat:11s} edge share of attack={v['edge_share_of_attack'][0]:.3f} "
              f"first decision on an edge switch in {v['first_decision_edge']:.0%} of seeds; "
              f"busiest transit {v['first_window_busiest_transit'][0]:.3f}, "
              f"busiest edge {v['first_window_busiest_edge'][0]:.3f}")
    json.dump(khoroji, open(sys.argv[1], "w"), indent=1)


if __name__ == "__main__":
    main()
