import json
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim
from larm.stats import ci95

BODJEHA = [0, 150, 300, 450, 600, 800, 1100, 1500, 2100]
TOPOS = [("fattree4", 24, [0, 300, 600, 750, 900, 1300, 1800, 2500]), ("abilene", 40, BODJEHA),
         ("geant", 40, BODJEHA), ("abilene_sndlib", 40, BODJEHA), ("geant_sndlib", 40, BODJEHA)]
SIASATHA = ["sp", "ecmp", "urm", "larm"]
TOKHMHA, GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 10, 20, 110, 2.5


def _run(args):
    topolozhi, nerkh, siasat, bodje, tokhm = args
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN,
            tokhm=tokhm, hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive" if bodje else "none",
            ghavanine_hamle=bodje)
    r = s.run()
    return args, (r["admission"], r["peak_occ"], r["mean_stretch_admitted"])


def main():
    pooshe = sys.argv[1] if len(sys.argv) > 1 else "results"
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    entekhab = sys.argv[3].split(",") if len(sys.argv) > 3 else [t for t, _, _ in TOPOS]
    os.makedirs(pooshe, exist_ok=True)
    for topolozhi, nerkh, bodjeha in TOPOS:
        if topolozhi not in entekhab:
            continue
        karha = [(topolozhi, nerkh, p, b, s) for p in SIASATHA for b in bodjeha for s in range(TOKHMHA)]
        t0 = time.time()
        with Pool(farayandha) as estakhr:
            natije = dict(estakhr.map(_run, karha, chunksize=2))
        od = {"topo": topolozhi, "lam": nerkh, "cap": 1000, "seeds": TOKHMHA, "adversary": "adaptive",
              "budgets": bodjeha, "policies": {}}
        for p in SIASATHA:
            R = {"adm_curve": {}, "adm_runs": {}, "peak": {}, "stretch_admitted": {}}
            for b in bodjeha:
                v = [natije[(topolozhi, nerkh, p, b, s)] for s in range(TOKHMHA)]
                R["adm_curve"][str(b)] = ci95([x[0] for x in v])
                R["adm_runs"][str(b)] = [x[0] for x in v]
                R["peak"][str(b)] = ci95([x[1] for x in v])
                R["stretch_admitted"][str(b)] = ci95([x[2] for x in v])
            od["policies"][p] = R
        od["elapsed_s"] = round(time.time() - t0, 1)
        with open(os.path.join(pooshe, f"main_{topolozhi}.json"), "w") as f:
            json.dump(od, f, indent=1)
        print(topolozhi, {p: [od["policies"][p]["adm_curve"][str(b)][0] for b in bodjeha] for p in SIASATHA})


if __name__ == "__main__":
    main()
