import json
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim

HALATHA = [("fattree4", 24, 1300), ("abilene", 40, 600), ("abilene", 40, 800), ("geant", 40, 600)]
LISTE_SIASATHA = ["larm", "larm_retry", "larm2_nr", "larm2", "greedy", "sp_retry"]
TOKHMHA, GARMKARDAN, DOREHA, HADDE_KESHIDEGI = 10, 20, 120, 2.5


def _run(args):
    topolozhi, nerkh, bodje, siasat, tokhm = args
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=GARMKARDAN + DOREHA, garmkardan=GARMKARDAN, tokhm=tokhm,
            hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive", ghavanine_hamle=bodje)
    s.run()
    return args, s.adm_trace[GARMKARDAN:]


def main():
    khoroji = sys.argv[1]
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    karha = [(t, nerkh, b, p, s) for t, nerkh, b in HALATHA for p in LISTE_SIASATHA for s in range(TOKHMHA)]
    t0 = time.time()
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(_run, karha))
    od = {"seeds": TOKHMHA, "adversary": "adaptive", "epochs": DOREHA, "cases": {}}
    for t, nerkh, b in HALATHA:
        c = od["cases"][f"{t}:{b}"] = {}
        for p in LISTE_SIASATHA:
            m = np.array([natije[(t, nerkh, b, p, s)] for s in range(TOKHMHA)]).mean(axis=0)
            c[p] = [round(float(x), 4) for x in m]
    od["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(od, open(khoroji, "w"), indent=1)
    print("done", od["elapsed_s"])


if __name__ == "__main__":
    main()
