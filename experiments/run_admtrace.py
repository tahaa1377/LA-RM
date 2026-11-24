import json
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim

HALATHA = [("fattree4", 24, 1300), ("abilene", 40, 800)]
SIASATHA = ["sp", "ecmp", "urm", "larm"]
TOKHMHA, GARMKARDAN, EPOKHA, HADDE_KESHIDEGI = 10, 20, 120, 2.5


def _run(args):
    topolozhi, nerkh, bodje, siasat, tokhm = args
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=GARMKARDAN + EPOKHA,
            garmkardan=GARMKARDAN, tokhm=tokhm, hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive",
            ghavanine_hamle=bodje)
    s.run()
    return args, s.adm_trace[GARMKARDAN:]


def main():
    khoroji = sys.argv[1] if len(sys.argv) > 1 else "results/admtrace_heavy.json"
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    karha = [(t, nerkh, b, p, s) for t, nerkh, b in HALATHA for p in SIASATHA for s in range(TOKHMHA)]
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(_run, karha, chunksize=2))
    od = {"seeds": TOKHMHA, "adversary": "adaptive", "budgets": {t: b for t, _, b in HALATHA}}
    for t, nerkh, b in HALATHA:
        od[t] = {}
        for p in SIASATHA:
            m = np.array([natije[(t, nerkh, b, p, s)] for s in range(TOKHMHA)]).mean(axis=0)
            od[t][p] = [round(float(x), 4) for x in m]
    with open(khoroji, "w") as f:
        json.dump(od, f, indent=1)
    for t, _, _ in HALATHA:
        print(t, {p: round(float(np.mean(od[t][p])), 3) for p in SIASATHA})


if __name__ == "__main__":
    main()
