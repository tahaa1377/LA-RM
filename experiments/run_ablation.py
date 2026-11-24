import json
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim
from larm.stats import ci95

TOPOS = [("fattree4", 24, [900, 1300]), ("abilene", 40, [600, 800]), ("geant", 40, [600, 800]),
         ("geant_sndlib", 40, [600, 800])]
TOKHMHA, GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 10, 20, 110, 2.5
BAZKHORD = {}
for bazkhord in ("sampled", "all"):
    for a in (0.05, 0.4):
        for siasat in ("larm", "larm_retry"):
            BAZKHORD[f"{siasat}|{bazkhord}|a={a}"] = (siasat, {"la_full": bazkhord == "all", "la_kw": {"a": a}})
TASADOF = {}
for eps, fl in ((0.1, 0.5), (0.1, 0.75), (0.1, 0.25), (0.05, 0.25), (0.0, 0.0)):
    TASADOF[f"eps={eps}|floor={fl}"] = ("larm_retry", {"la_full": True, "la_kw": {"a": 0.4, "eps": eps, "hmin_frac": fl}})
SIASATHAYE_RADYABI = ["larm", "larm_retry", "larm2_nr", "larm2", "greedy", "sp_retry"]
HALATHAYE_RADYABI = [("fattree4", 24, 1300), ("abilene", 40, 800)]
SIASATHAYE_TASHKHIS = ["sp_retry", "larm_retry", "greedy", "larm2"]


def _run(args):
    noe, topolozhi, nerkh, nam, bodje, tokhm = args
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    if noe in ("feed", "rand"):
        siasat, kw = (BAZKHORD if noe == "feed" else TASADOF)[nam]
        s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN, tokhm=tokhm,
                hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive", ghavanine_hamle=bodje, **kw)
        r = s.run()
        return args, (r["admission"], r["mean_stretch_admitted"], r["mean_stretch"])
    if noe == "trace":
        s = Sim(G, taghaza, nam, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=GARMKARDAN + 120, garmkardan=GARMKARDAN, tokhm=tokhm,
                hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive", ghavanine_hamle=bodje)
        s.run()
        return args, s.adm_trace[GARMKARDAN:]
    s = Sim(G, taghaza, nam, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN, tokhm=tokhm,
            hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive", ghavanine_hamle=bodje)
    r = s.run()
    nfull = s.nfull_trace
    jaryanhaye_paziroofte = r["benign_offered"] - r["benign_lost"]
    return args, (r["admission"], r["mean_stretch_admitted"], s.m["benign_installs"] / max(1, jaryanhaye_paziroofte),
                  float(np.mean([x >= 2 for x in nfull])), float(np.mean([x >= 1 for x in nfull])))


def main():
    khoroji = sys.argv[1]
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    karha = [("feed", t, nerkh, c, b, s) for t, nerkh, bs in TOPOS for c in BAZKHORD for b in bs for s in range(TOKHMHA)]
    karha += [("rand", t, nerkh, c, b, s) for t, nerkh, bs in TOPOS for c in TASADOF for b in bs for s in range(TOKHMHA)]
    karha += [("trace", t, nerkh, p, b, s) for t, nerkh, b in HALATHAYE_RADYABI for p in SIASATHAYE_RADYABI for s in range(TOKHMHA)]
    karha += [("diag", "abilene", 40, p, 800, s) for p in SIASATHAYE_TASHKHIS for s in range(TOKHMHA)]
    t0 = time.time()
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(_run, karha, chunksize=2))
    od = {"seeds": TOKHMHA, "adversary": "adaptive", "feedback": {}, "randomization": {}, "trace": {}, "diag_abilene_800": {}}
    for noe, jadval, key in (("feed", BAZKHORD, "feedback"), ("rand", TASADOF, "randomization")):
        for c in jadval:
            od[key][c] = {}
            for t, nerkh, bs in TOPOS:
                for b in bs:
                    v = [natije[(noe, t, nerkh, c, b, s)] for s in range(TOKHMHA)]
                    od[key][c][f"{t}:{b}"] = {"admission": ci95([x[0] for x in v]),
                                             "adm_runs": [x[0] for x in v],
                                             "stretch_admitted": ci95([x[1] for x in v]),
                                             "stretch": ci95([x[2] for x in v])}
    for t, nerkh, b in HALATHAYE_RADYABI:
        od["trace"][t] = {"budget": b}
        for p in SIASATHAYE_RADYABI:
            m = np.array([natije[("trace", t, nerkh, p, b, s)] for s in range(TOKHMHA)]).mean(axis=0)
            od["trace"][t][p] = [round(float(x), 4) for x in m]
    for p in SIASATHAYE_TASHKHIS:
        v = [natije[("diag", "abilene", 40, p, 800, s)] for s in range(TOKHMHA)]
        od["diag_abilene_800"][p] = {"admission": ci95([x[0] for x in v]),
                                     "stretch_admitted": ci95([x[1] for x in v]),
                                     "rules_per_admitted_flow": ci95([x[2] for x in v]),
                                     "epochs_two_or_more_full": ci95([x[3] for x in v]),
                                     "epochs_one_or_more_full": ci95([x[4] for x in v])}
    od["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(od, open(khoroji, "w"), indent=1)
    sotoonha = [f"{t}:{b}" for t, nerkh, bs in TOPOS for b in bs]
    for key in ("feedback", "randomization"):
        print(key)
        for c, r in od[key].items():
            print(f"  {c:28s} " + " ".join(f"{100 * r[x]['admission'][0]:6.1f}" for x in sotoonha)
                  + "   stretch " + " ".join(f"{r[x]['stretch'][0]:.2f}" for x in sotoonha))
    print("diag abilene 800")
    for p, r in od["diag_abilene_800"].items():
        print(f"  {p:11s} adm {100 * r['admission'][0]:.1f} stretch {r['stretch_admitted'][0]:.3f} "
              f"rules/flow {r['rules_per_admitted_flow'][0]:.3f} >=2 full {r['epochs_two_or_more_full'][0]:.3f} "
              f">=1 full {r['epochs_one_or_more_full'][0]:.3f}")
    print("elapsed", od["elapsed_s"])


if __name__ == "__main__":
    main()
