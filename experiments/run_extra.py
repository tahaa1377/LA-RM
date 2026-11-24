import json
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim
from larm.stats import ci95

KONTROL = [("fattree4", 24, 1300), ("abilene", 40, 800), ("abilene_sndlib", 40, 800), ("geant_sndlib", 40, 800)]
HALATHAYE_KONTROL = {"larm": ("larm", {}), "noise": ("larm", {"reward_mode": "noise"}), "urm": ("urm", {})}
SNDLIB = [("abilene_sndlib", 40), ("geant_sndlib", 40)]
MATRISHA = {"quiet": (800, {"LARM_HOUR": "quiet", "LARM_MATRIX": "measured"}),
            "gravity": (600, {"LARM_HOUR": "busy", "LARM_MATRIX": "gravity"})}
SIASATHA = ["sp", "ecmp", "urm", "larm"]
TOKHMHA, GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 10, 20, 110, 2.5


def _run(args):
    topolozhi, nerkh, noe, nam, bodje, tokhm = args
    if noe == "control":
        siasat, kw = HALATHAYE_KONTROL[nam]
        os.environ["LARM_HOUR"], os.environ["LARM_MATRIX"] = "busy", "measured"
    else:
        siasat, kw = nam, {}
        os.environ.update(MATRISHA[noe][1])
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN,
            tokhm=tokhm, hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive", ghavanine_hamle=bodje, **kw)
    return args, s.run()["admission"]


def main():
    pooshe = sys.argv[1] if len(sys.argv) > 1 else "results"
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    os.makedirs(pooshe, exist_ok=True)
    karha = [(t, nerkh, "control", c, b, s) for t, nerkh, b in KONTROL for c in HALATHAYE_KONTROL for s in range(TOKHMHA)]
    karha += [(t, nerkh, m, p, MATRISHA[m][0], s) for t, nerkh in SNDLIB for m in MATRISHA for p in SIASATHA
              for s in range(TOKHMHA)]
    t0 = time.time()
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(_run, karha, chunksize=2))
    for t, nerkh, b in KONTROL:
        od = {"topo": t, "lam": nerkh, "seeds": TOKHMHA, "adversary": "adaptive", "budget": b, "control": {}}
        for c in HALATHAYE_KONTROL:
            v = [natije[(t, nerkh, "control", c, b, s)] for s in range(TOKHMHA)]
            od["control"][c] = {"admission": ci95(v), "adm_runs": v}
        for t2, nerkh2 in SNDLIB:
            if t2 != t:
                continue
            for m, (bm, _) in MATRISHA.items():
                od[m] = {"budget": bm, "policies": {}}
                for p in SIASATHA:
                    v = [natije[(t, nerkh, m, p, bm, s)] for s in range(TOKHMHA)]
                    od[m]["policies"][p] = {"admission": ci95(v), "adm_runs": v}
        od["elapsed_s"] = round(time.time() - t0, 1)
        with open(os.path.join(pooshe, f"extra_{t}.json"), "w") as f:
            json.dump(od, f, indent=1)
        radif = {c: od["control"][c]["admission"] for c in HALATHAYE_KONTROL}
        for m in MATRISHA:
            if m in od:
                radif[m] = [round(od[m]["policies"][p]["admission"][0], 3) for p in SIASATHA]
        print(t, radif)


if __name__ == "__main__":
    main()
