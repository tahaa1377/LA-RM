import json
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim

LISTE_SIASATHA = ["sp", "ecmp", "urm", "larm", "greedy", "sp_retry", "larm_retry"]
HALATHA = [("abilene", "results_rev/base_abilene.json", [600, 800], 40, "adaptive"),
         ("fattree4", "results_rev/base_fattree4.json", [900, 1300], 24, "adaptive"),
         ("geant", "results_rev/base_geant2012.json", [600], 40, "adaptive"),
         ("geant_sndlib", "results_rev/base_geant_sndlib.json", [800], 40, "adaptive"),
         ("fattree4", "results_rev/base_fattree4_aware.json", [1300], 24, "aware"),
         ("abilene", "results_rev/base_abilene_smart.json", [600], 40, "smart")]


def one(a):
    topolozhi, siasat, b, tokhm, nerkh, harif = a
    G, taghaza, f = seed_instance(topolozhi, tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=110, garmkardan=20, tokhm=tokhm,
            hadde_aksare_keshidegi=2.5, hamlegar=harif, ghavanine_hamle=b)
    return a, s.run()["admission"]


def main():
    farayandha = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    karha = [(t, p, b, s, nerkh, harif) for t, f, bs, nerkh, harif in HALATHA for p in LISTE_SIASATHA for b in bs for s in range(10)]
    t0 = time.time()
    with Pool(farayandha) as estakhr:
        natije = dict(estakhr.map(one, karha))
    bad = n = 0
    for t, f, bs, nerkh, harif in HALATHA:
        d = json.load(open(f))["policies"]
        for p in LISTE_SIASATHA:
            for b in bs:
                marja = d[p][str(b)]["adm_runs"]
                got = [natije[(t, p, b, s, nerkh, harif)] for s in range(10)]
                movafagh = all(abs(x - y) < 1e-12 for x, y in zip(marja, got))
                bad += not movafagh
                n += 1
                print(f"{t:13s} {harif:9s} {p:10s} {b:5d} {'identical' if movafagh else 'DIFFERENT'}  mean={sum(got) / 10:.4f}")
    print(f"{n - bad} of {n} configurations identical in every seed; elapsed {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
