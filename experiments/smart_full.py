import json
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim
from larm.stats import ci95

HALATHA = [("fattree4", 24, 900), ("fattree4", 24, 1300), ("abilene", 40, 600), ("geant", 40, 600)]
LISTE_SIASATHA = ["sp", "greedy"]


def one(a):
    topolozhi, nerkh, b, siasat, tokhm = a
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=110, garmkardan=20, tokhm=tokhm,
            hadde_aksare_keshidegi=2.5, hamlegar="smart", ghavanine_hamle=b)
    r = s.run()
    return a, (r["admission"], float(np.mean([x > 0 for x in s.nfull_trace])))


def main():
    khoroji = sys.argv[1]
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    karha = [(t, nerkh, b, p, s) for t, nerkh, b in HALATHA for p in LISTE_SIASATHA for s in range(10)]
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(one, karha))
    od = {"seeds": 10, "adversary": "smart", "cases": {}}
    for t, nerkh, b in HALATHA:
        for p in LISTE_SIASATHA:
            v = [natije[(t, nerkh, b, p, s)] for s in range(10)]
            od["cases"][f"{t}:{b}:{p}"] = {"share": b // 3, "admission": ci95([x[0] for x in v]),
                                           "epochs_with_full_switch": ci95([x[1] for x in v])}
            print(t, b, p, od["cases"][f"{t}:{b}:{p}"])
    json.dump(od, open(khoroji, "w"), indent=1)


if __name__ == "__main__":
    main()
