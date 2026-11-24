import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim, Policy
from larm.stats import ci95

SIASATHA = [Policy.SP, Policy.ECMP, Policy.URM, Policy.LARM,
            Policy.GREEDY, Policy.SPR, Policy.LARMR]
if os.environ.get("LARM_POLICIES"):
    SIASATHA = [p for p in os.environ["LARM_POLICIES"].split(",") if p]
GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 20, 110, 2.5
_NAME = _HADDE_AKSARE_OD = None


def _init(nam):
    global _NAME, _HADDE_AKSARE_OD
    mo = os.environ.get("LARM_MAXODS")
    _NAME, _HADDE_AKSARE_OD = nam, int(mo) if mo else None


def _one(args):
    siasat, hamle, tokhm, nerkh, zarfiat, harif = args
    G, taghaza, f = seed_instance(_NAME, tokhm, max_ods=_HADDE_AKSARE_OD)
    s = Sim(G, taghaza, siasat, zarfiat=zarfiat, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN, tokhm=tokhm,
            hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar=harif if hamle else "none", ghavanine_hamle=hamle,
            halate_kandid=os.environ.get("LARM_CANDS", "yen"))
    r = s.run()
    return (siasat, hamle, tokhm, r["admission"], r["peak_occ"], r["mean_stretch"], r["installs_per_s"],
            r["mean_stretch_admitted"])


def main():
    topolozhi, khoroji = sys.argv[1], sys.argv[2]
    bodjeha = [int(x) for x in sys.argv[3].split(",")]
    tokhmha = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    harif = sys.argv[5] if len(sys.argv) > 5 else "adaptive"
    nerkh = 24 if topolozhi.startswith("fattree") else 40
    if len(sys.argv) > 6:
        nerkh = float(sys.argv[6])
    zarfiat = 1000
    karha = [(p, a, s, nerkh, zarfiat, harif) for p in SIASATHA for a in bodjeha for s in range(tokhmha)]
    t0 = time.time()
    with Pool(int(os.environ.get("LARM_PROCS", "2")), initializer=_init, initargs=(topolozhi,)) as estakhr:
        natije = estakhr.map(_one, karha)
    R = {}
    for siasat, hamle, tokhm, adm, pk, st, ins, sta in natije:
        R.setdefault(siasat, {}).setdefault(hamle, {})[tokhm] = (adm, pk, st, ins, sta)
    od = {"topo": topolozhi, "adversary": harif, "seeds": tokhmha, "budgets": bodjeha,
          "lam": nerkh, "cap": zarfiat, "candidates": os.environ.get("LARM_CANDS", "yen"),
          "policies": {}, "paired_vs_larm": {}}
    for siasat in SIASATHA:
        od["policies"][siasat] = {}
        for a in bodjeha:
            v = [R[siasat][a][s] for s in range(tokhmha)]
            od["policies"][siasat][str(a)] = {
                "admission": ci95([x[0] for x in v]),
                "adm_runs": [x[0] for x in v],
                "peak": ci95([x[1] for x in v]),
                "stretch": ci95([x[2] for x in v]),
                "installs_per_s": ci95([x[3] for x in v]),
                "stretch_admitted": ci95([x[4] for x in v]),
            }
    for siasat in SIASATHA:
        if siasat == Policy.LARM or Policy.LARM not in SIASATHA:
            continue
        od["paired_vs_larm"][siasat] = {}
        for a in bodjeha:
            d = [R[Policy.LARM][a][s][0] - R[siasat][a][s][0] for s in range(tokhmha)]
            od["paired_vs_larm"][siasat][str(a)] = ci95(d, scale=100.0, nd=2)
    od["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(od, open(khoroji, "w"), indent=1)
    print(f"{topolozhi} ({harif}) {od['elapsed_s']}s")
    for a in bodjeha:
        radif = "  ".join(f"{p}={od['policies'][p][str(a)]['admission'][0]:.3f}" for p in SIASATHA)
        print(f"  budget {a}: {radif}")
        if Policy.LARM in SIASATHA:
            radif = "  ".join(f"{p}:{od['paired_vs_larm'][p][str(a)][0]:+.1f}±{od['paired_vs_larm'][p][str(a)][1]:.1f}"
                            for p in SIASATHA if p != Policy.LARM)
            print(f"    LA-RM minus: {radif}")


if __name__ == "__main__":
    main()
