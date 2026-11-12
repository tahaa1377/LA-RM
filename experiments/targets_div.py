import json
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim, Policy
from larm.stats import ci95

TOPOS = [("geant2009", 10, 40, None), ("geant2010", 10, 40, None), ("geant", 10, 40, None),
         ("uscarrier", 5, 45, 1500), ("cogentco", 5, 55, 1500)]
SIASATHA = [Policy.GREEDY, Policy.SPR, Policy.LARMR]
KANDIDHA = ["yen", "div"]
BODJE, GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 1100, 20, 110, 2.5
HABHA = json.load(open("results_rev2/candidates.json"))


def _one(args):
    topolozhi, maxods, nerkh, siasat, kandidha, tokhm = args
    hub = HABHA[topolozhi]["div"][0]["hub"]
    G, taghaza, f = seed_instance(topolozhi, tokhm, max_ods=maxods)
    s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN, tokhm=tokhm,
            hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="adaptive", ghavanine_hamle=BODJE, halate_kandid=kandidha)
    gereye_hab = next(n for n in s.nodes if str(n) == hub)
    por = []
    orig = s._adversary_refresh

    def refresh(now):
        orig(now)
        por.append(len(s.table[gereye_hab]) >= s.cap[gereye_hab])

    s._adversary_refresh = refresh
    r = s.run()
    tg = [t[0] if t else None for t in s.targets]
    on_hub = float(np.mean([t == gereye_hab for t in tg])) if tg else float("nan")
    return (topolozhi, siasat, kandidha, tokhm, r["admission"], on_hub,
            float(np.mean(por)) if por else float("nan"))


def main():
    khoroji = sys.argv[1]
    farayandha = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    karha = [(t, mo, nerkh, p, c, sd) for t, ns, nerkh, mo in TOPOS for p in SIASATHA
            for c in KANDIDHA for sd in range(ns)]
    with Pool(farayandha) as estakhr:
        radifha = estakhr.map(_one, karha, chunksize=1)
    natije = {}
    for topolozhi, siasat, kandidha, tokhm, adm, on_hub, por in radifha:
        natije.setdefault(topolozhi, {}).setdefault(kandidha, {}).setdefault(siasat, []).append(
            {"seed": tokhm, "admission": adm, "aim_hub": on_hub, "hub_full": por})
    kholase = {}
    for topolozhi, byc in natije.items():
        u = {c: HABHA[topolozhi][c][0]["u_hub"] for c in KANDIDHA}
        for kandidha, byp in byc.items():
            for siasat, runs in byp.items():
                runs.sort(key=lambda x: x["seed"])
                kholase.setdefault(topolozhi, {}).setdefault(kandidha, {})[siasat] = {
                    "admission": ci95([x["admission"] for x in runs]),
                    "aim_hub": ci95([x["aim_hub"] for x in runs]),
                    "hub_full": ci95([x["hub_full"] for x in runs]),
                    "bound_1_minus_u": 1.0 - u[kandidha]}
    json.dump({"budget": BODJE, "adversary": "adaptive", "summary": kholase, "runs": natije},
              open(khoroji, "w"), indent=1)
    for topolozhi in kholase:
        for c in KANDIDHA:
            for siasat, v in kholase[topolozhi][c].items():
                print(f"{topolozhi:10s} {c:4s} {siasat:11s} adm={v['admission'][0]:.3f} "
                      f"aim_hub={v['aim_hub'][0]:.2f} hub_full={v['hub_full'][0]:.2f} "
                      f"bound={v['bound_1_minus_u']:.3f}")


if __name__ == "__main__":
    main()
