import json
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim
from larm.stats import ci95

LISTE_SIASATHA = ["sp", "ecmp", "urm", "larm", "greedy", "sp_retry", "larm_retry"]
if os.environ.get("LARM_POLICIES"):
    LISTE_SIASATHA = [p for p in os.environ["LARM_POLICIES"].split(",") if p]
KS, HALATHAYE_KANDID, TOKHMHA, BODJE = [2, 3, 4], ["yen", "div"], 10, 1300


HAMLE = None
if os.environ.get("LARM_ATK_FIXED"):
    HAMLE = (4, "yen")


def one(args):
    siasat, k, halat, tokhm = args
    G, taghaza, f = seed_instance("fattree4", tokhm)
    s = Sim(G, taghaza, siasat, k=k, zarfiat=1000, maghyase_nerkh=24 * f, ofogh=110, garmkardan=20, tokhm=tokhm,
            hadde_aksare_keshidegi=2.5, hamlegar="adaptive", ghavanine_hamle=BODJE, halate_kandid=halat, kandidhaye_hamle=HAMLE)
    return siasat, k, halat, tokhm, s.run()["admission"]


def main():
    khoroji = sys.argv[1] if len(sys.argv) > 1 else "results_rev2/ksweep_ties.json"
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    karha = [(p, k, m, sd) for p in LISTE_SIASATHA for k in KS for m in HALATHAYE_KANDID for sd in range(TOKHMHA)]
    with Pool(farayandha) as estakhr:
        natije = estakhr.map(one, karha)
    R = {}
    for p, k, m, sd, a in natije:
        R.setdefault(p, {}).setdefault(m, {}).setdefault(str(k), {})[sd] = a
    od = {"budget": BODJE, "seeds": TOKHMHA, "attack_placement": "yen k=4" if HAMLE else "defender's candidates",
          "policies": {}}
    for p in LISTE_SIASATHA:
        od["policies"][p] = {}
        for m in HALATHAYE_KANDID:
            od["policies"][p][m] = {}
            for k in KS:
                v = [R[p][m][str(k)][sd] for sd in range(TOKHMHA)]
                od["policies"][p][m][str(k)] = {"admission": ci95(v), "adm_runs": v}
        print(p, " ".join(f"{m}:k{k}={od['policies'][p][m][str(k)]['admission'][0]:.3f}"
                          for m in HALATHAYE_KANDID for k in KS))
    json.dump(od, open(khoroji, "w"), indent=1)


if __name__ == "__main__":
    main()
