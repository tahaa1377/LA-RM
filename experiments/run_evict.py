import json
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim
from larm.stats import ci95

HALATHA = [("fattree4", 24, 1300), ("abilene", 40, 800)]
RADIFHA = {"sp": ("sp", {"hamle_nasbe_mojadad": True}), "evict_static": ("sp", {"ekhraj": True}),
           "evict_refresh": ("sp", {"ekhraj": True, "hamle_nasbe_mojadad": True}),
           "larm": ("larm", {"hamle_nasbe_mojadad": True})}
TOKHMHA, GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 10, 20, 110, 2.5


def _run(args):
    topolozhi, nerkh, bodje, radif, tokhm = args
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    siasat, kw = RADIFHA[radif]
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN,
            tokhm=tokhm, hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive", ghavanine_hamle=bodje, **kw)
    r = s.run()
    return args, (r["admission"], r["churn"])


def main():
    pooshe = sys.argv[1] if len(sys.argv) > 1 else "results"
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    os.makedirs(pooshe, exist_ok=True)
    karha = [(t, nerkh, b, r, s) for t, nerkh, b in HALATHA for r in RADIFHA for s in range(TOKHMHA)]
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(_run, karha, chunksize=2))
    for t, nerkh, b in HALATHA:
        od = {"topo": t, "budget": b, "seeds": TOKHMHA, "adversary": "adaptive", "rows": {}}
        for r in RADIFHA:
            v = [natije[(t, nerkh, b, r, s)] for s in range(TOKHMHA)]
            od["rows"][r] = {"admission": ci95([x[0] for x in v]), "churn": ci95([x[1] for x in v]),
                             "adm_runs": [x[0] for x in v], "churn_runs": [x[1] for x in v]}
        with open(os.path.join(pooshe, f"evict_{t}.json"), "w") as f:
            json.dump(od, f, indent=1)
        print(t, {r: (od["rows"][r]["admission"][0], od["rows"][r]["churn"][0]) for r in RADIFHA})


if __name__ == "__main__":
    main()
