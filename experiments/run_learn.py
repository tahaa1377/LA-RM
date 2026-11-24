import json
import sys

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim

TOPOLOZHI, NERKH, BODJE, TOKHM, EPOKHA, HADDE_KESHIDEGI = "fattree4", 24, 900, 0, 120, 2.5


def main():
    khoroji = sys.argv[1] if len(sys.argv) > 1 else "results/learn_curve.json"
    G, taghaza, f = seed_instance(TOPOLOZHI, TOKHM)
    s = Sim(G, taghaza, "larm", zarfiat=1000, maghyase_nerkh=NERKH * f, ofogh=EPOKHA, garmkardan=0, tokhm=TOKHM,
            hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="static", ghavanine_hamle=BODJE)
    hadaf = s._fixed_target()
    od = next(od for od in s.ods if sum(hadaf in p for p in s.pt.cand[od]) == 1)
    s.watch_od = od
    s.run()
    od_json = {"topo": TOPOLOZHI, "adversary": "static", "budget": BODJE, "seed": TOKHM, "od": list(od),
               "target": hadaf, "cross": [i for i, p in enumerate(s.pt.cand[od]) if hadaf in p],
               "candidates": s.pt.cand[od], "p": [[round(float(x), 6) for x in p] for p in s.p_trace]}
    with open(khoroji, "w") as f:
        json.dump(od_json, f, indent=1)
    print(od, hadaf, od_json["cross"], od_json["p"][-1])


if __name__ == "__main__":
    main()
