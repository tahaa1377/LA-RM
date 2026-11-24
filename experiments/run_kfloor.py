import json
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim
from larm.stats import ci95

TOPOLOZHI, NERKH, BODJE = "fattree4", 24, 1300
KHA = [2, 3, 4, 6, 8, 12]
KAFHA = [0.25, 0.5, 0.75]
TOKHMHA, GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 10, 20, 110, 2.5


def _run(args):
    k, kaf, tokhm = args
    G, taghaza, f = seed_instance(TOPOLOZHI, tokhm)
    s = Sim(G, taghaza, "larm", k=k, zarfiat=1000, maghyase_nerkh=NERKH * f, ofogh=UFOGH, garmkardan=GARMKARDAN,
            tokhm=tokhm, hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive", ghavanine_hamle=BODJE,
            la_kw={"hmin_frac": kaf})
    return args, s.run()["admission"]


def main():
    khoroji = sys.argv[1] if len(sys.argv) > 1 else "results/kfloor.json"
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    karha = [(k, kaf, s) for kaf in KAFHA for k in KHA for s in range(TOKHMHA)]
    t0 = time.time()
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(_run, karha, chunksize=2))
    od = {"topo": TOPOLOZHI, "budget": BODJE, "policy": "larm", "seeds": TOKHMHA, "floors": KAFHA, "ks": KHA,
          "grid": {}, "adm_runs": {}}
    for kaf in KAFHA:
        od["grid"][str(kaf)], od["adm_runs"][str(kaf)] = {}, {}
        for k in KHA:
            v = [natije[(k, kaf, s)] for s in range(TOKHMHA)]
            od["grid"][str(kaf)][str(k)] = ci95(v, scale=100.0, nd=1)
            od["adm_runs"][str(kaf)][str(k)] = v
    od["elapsed_s"] = round(time.time() - t0, 1)
    with open(khoroji, "w") as f:
        json.dump(od, f, indent=1)
    for kaf in KAFHA:
        print(kaf, {k: od["grid"][str(kaf)][str(k)][0] for k in KHA})


if __name__ == "__main__":
    main()
