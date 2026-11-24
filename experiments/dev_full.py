import json
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim
from larm.stats import ci95

TOPOS = [("fattree4", 24, [900, 1300]), ("abilene", 40, [600, 800]), ("geant", 40, [600, 800])]
TOKHMHA = list(range(100, 110))
GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 20, 110, 2.5
TANZIMAT = {"greedy": ("greedy", {}), "sp_retry": ("sp_retry", {}), "larm_retry": ("larm_retry", {}),
           "larm": ("larm", {})}
for a in (0.05, 0.1, 0.2, 0.4):
    for d0 in (0.0, 0.5):
        for siasat in ("larm", "larm_retry"):
            TANZIMAT[f"{siasat}|full|a={a}|d0={d0}"] = (siasat, {"la_full": True, "la_kw": {"a": a, "d0": d0}})
for g in (0.5, 0.7):
    for siasat in ("larm", "larm_retry"):
        TANZIMAT[f"{siasat}|full|a=0.2|d0=0.0|g={g}"] = (siasat, {"la_full": True, "la_kw": {"a": 0.2, "d0": 0.0, "forget": g}})


def _one(args):
    topolozhi, nerkh, nam, bodje, tokhm = args
    siasat, kw = TANZIMAT[nam]
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN, tokhm=tokhm,
            hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive", ghavanine_hamle=bodje, **kw)
    r = s.run()
    return args, (r["admission"], r["mean_stretch_admitted"])


def main():
    khoroji = sys.argv[1]
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    karha = [(t, nerkh, c, b, s) for t, nerkh, bs in TOPOS for c in TANZIMAT for b in bs for s in TOKHMHA]
    t0 = time.time()
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(_one, karha, chunksize=4))
    od = {"seeds": TOKHMHA, "adversary": "adaptive", "configs": {}}
    sotoonha = [(t, b) for t, nerkh, bs in TOPOS for b in bs]
    for c in TANZIMAT:
        od["configs"][c] = {}
        for t, nerkh, bs in TOPOS:
            for b in bs:
                v = [natije[(t, nerkh, c, b, s)] for s in TOKHMHA]
                od["configs"][c][f"{t}:{b}"] = {"admission": ci95([x[0] for x in v]),
                                                "stretch_admitted": ci95([x[1] for x in v])}
    od["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(od, open(khoroji, "w"), indent=1)
    print(f"{'config':40s} " + " ".join(f"{t[:7]}:{b:<5d}" for t, b in sotoonha) + "   mean")
    for c in TANZIMAT:
        meghdarha = [100 * od["configs"][c][f"{t}:{b}"]["admission"][0] for t, b in sotoonha]
        print(f"{c:40s} " + " ".join(f"{v:13.1f}" for v in meghdarha) + f"   {sum(meghdarha) / len(meghdarha):.2f}")
    print("elapsed", od["elapsed_s"])


if __name__ == "__main__":
    main()
