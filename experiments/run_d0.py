import json
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim, Policy
from larm.stats import ci95

TOPOS = [("fattree4", 24, [0, 900, 1300]), ("abilene", 40, [0, 600, 800]),
         ("geant", 40, [0, 600, 800]), ("abilene_sndlib", 40, [600, 800]),
         ("geant_sndlib", 40, [600, 800])]
D0 = [0.0, 0.25, 0.5, 0.75]
SIASATHA = [Policy.LARM, Policy.LARMR]
TOKHMHA, GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 10, 20, 110, 2.5


def _one(args):
    topolozhi, nerkh, siasat, d0, bodje, tokhm = args
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN, tokhm=tokhm,
            hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive" if bodje else "none", ghavanine_hamle=bodje,
            la_kw={"d0": d0})
    r = s.run()
    return args, (r["admission"], r["peak_occ"], r["mean_stretch"], r["mean_stretch_admitted"])


def main():
    khoroji = sys.argv[1]
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    karha = [(t, nerkh, p, d0, b, s) for t, nerkh, bs in TOPOS for p in SIASATHA for d0 in D0
            for b in bs for s in range(TOKHMHA)]
    t0 = time.time()
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(_one, karha, chunksize=4))
    od = {"adversary": "adaptive", "seeds": TOKHMHA, "d0": D0, "topologies": {}}
    for t, nerkh, bs in TOPOS:
        od["topologies"][t] = {"lam": nerkh, "budgets": bs, "policies": {}}
        for p in SIASATHA:
            R = od["topologies"][t]["policies"][p] = {}
            for b in bs:
                R[str(b)] = {}
                marja = [natije[(t, nerkh, p, 0.5, b, s)][0] for s in range(TOKHMHA)]
                for d0 in D0:
                    v = [natije[(t, nerkh, p, d0, b, s)] for s in range(TOKHMHA)]
                    adm = [x[0] for x in v]
                    R[str(b)][str(d0)] = {
                        "admission": ci95(adm), "adm_runs": adm,
                        "peak": ci95([x[1] for x in v]),
                        "stretch": ci95([x[2] for x in v]),
                        "stretch_admitted": ci95([x[3] for x in v]),
                        "minus_d0_0.5": ci95([a - r for a, r in zip(adm, marja)], scale=100.0, nd=2)}
    od["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(od, open(khoroji, "w"), indent=1)
    for t, nerkh, bs in TOPOS:
        for p in SIASATHA:
            for b in bs:
                R = od["topologies"][t]["policies"][p][str(b)]
                if b:
                    radif = "  ".join(f"d0={d0}: {100 * R[str(d0)]['admission'][0]:.1f} "
                                    f"({R[str(d0)]['minus_d0_0.5'][0]:+.1f}±{R[str(d0)]['minus_d0_0.5'][1]:.1f})"
                                    for d0 in D0)
                else:
                    radif = "  ".join(f"d0={d0}: peak {R[str(d0)]['peak'][0]:.3f} stretch {R[str(d0)]['stretch'][0]:.3f}"
                                    for d0 in D0)
                print(f"{t:15s} {p:10s} {b:5d}  {radif}")
    print("elapsed", od["elapsed_s"])


if __name__ == "__main__":
    main()
