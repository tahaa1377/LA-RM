import json
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim
from larm.stats import ci95

TOPOS = [("fattree4", 24, [900, 1300]), ("abilene", 40, [600, 800]), ("geant", 40, [600, 800]),
         ("geant_sndlib", 40, [600, 800])]
TOKHMHA, GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 10, 20, 110, 2.5
HALATHA = {f"{siasat}|sampled|a=0.4|d0=0": (siasat, {"la_full": False, "la_kw": {"a": 0.4, "d0": 0.0}})
           for siasat in ("larm", "larm_retry")}
ABLATION = "results_rev4/ablation.json"
LARM2 = {f"{siasat}|sampled|a=0.4|d0=0": f"{siasat}|all|a=0.4" for siasat in ("larm", "larm_retry")}


def _run(args):
    topolozhi, nerkh, nam, bodje, tokhm = args
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    siasat, kw = HALATHA[nam]
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN, tokhm=tokhm,
            hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive", ghavanine_hamle=bodje, **kw)
    r = s.run()
    return args, (r["admission"], r["mean_stretch_admitted"], r["mean_stretch"])


def main():
    khoroji = sys.argv[1] if len(sys.argv) > 1 else "results_rev4/larmr_tuned.json"
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    karha = [(t, nerkh, c, b, s) for t, nerkh, bs in TOPOS for c in HALATHA for b in bs for s in range(TOKHMHA)]
    t0 = time.time()
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(_run, karha, chunksize=2))
    with open(ABLATION) as f:
        larm2 = json.load(f)["feedback"]
    od = {"seeds": TOKHMHA, "adversary": "adaptive", "reference": LARM2, "feedback": {}, "larm2_minus": {}}
    for c in HALATHA:
        od["feedback"][c] = {}
        od["larm2_minus"][c] = {}
        for t, nerkh, bs in TOPOS:
            for b in bs:
                v = [natije[(t, nerkh, c, b, s)] for s in range(TOKHMHA)]
                adm = [x[0] for x in v]
                od["feedback"][c][f"{t}:{b}"] = {"admission": ci95(adm), "adm_runs": adm,
                                                 "stretch_admitted": ci95([x[1] for x in v]),
                                                 "stretch": ci95([x[2] for x in v])}
                marja = larm2[LARM2[c]][f"{t}:{b}"]["adm_runs"]
                od["larm2_minus"][c][f"{t}:{b}"] = ci95([a - r for a, r in zip(marja, adm)], scale=100.0, nd=1)
    od["elapsed_s"] = round(time.time() - t0, 1)
    with open(khoroji, "w") as f:
        json.dump(od, f, indent=1)
    for c in HALATHA:
        radif = "  ".join(f"{k} {100 * od['feedback'][c][k]['admission'][0]:.1f} "
                          f"({od['larm2_minus'][c][k][0]:+.1f}±{od['larm2_minus'][c][k][1]:.1f})"
                          for k in od["feedback"][c])
        print(f"{c}: {radif}")


if __name__ == "__main__":
    main()
