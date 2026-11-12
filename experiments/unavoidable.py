import json
import sys

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm.paths import PathTable

TOPOS = [("fattree4", 1), ("abilene", 1), ("geant2009", 1), ("geant2010", 1), ("geant", 1),
         ("uscarrier", 1), ("cogentco", 1), ("abilene_sndlib", 10), ("geant_sndlib", 10)]
HADDE_AKSARE_OD = {"uscarrier": 1500, "cogentco": 1500}


def shares(G, taghaza, k=4, hadde_aksare_keshidegi=2.5):
    ods = [od for od, w in taghaza.items() if w > 0]
    majmoo = sum(taghaza[od] for od in ods)
    pt = PathTable(G, ods, k=k, hadde_aksare_keshidegi=hadde_aksare_keshidegi)
    U = {n: 0.0 for n in G.nodes()}
    S = {n: 0.0 for n in G.nodes()}
    for od in ods:
        w = taghaza[od] / majmoo
        moshtarak = set(pt.cand[od][0])
        for p in pt.cand[od][1:]:
            moshtarak &= set(p)
        for n in moshtarak:
            U[n] += w
        eq = pt.ecmp[od]
        for p in eq:
            for n in p:
                S[n] += w / len(eq)
    return U, S


def main():
    khoroji = sys.argv[1] if len(sys.argv) > 1 else "results_rev/unavoidable.json"
    natije = {}
    for nam, roozha in TOPOS:
        radifha = []
        for rooz in range(roozha):
            G, taghaza, _ = seed_instance(nam, rooz, max_ods=HADDE_AKSARE_OD.get(nam))
            U, S = shares(G, taghaza)
            hub = max(S, key=S.get)
            umax = max(U, key=U.get)
            radifha.append({"day": rooz, "sp_hub": str(hub), "sp_share_hub": round(S[hub], 4),
                         "U_hub": round(U[hub], 4), "U_max_node": str(umax),
                         "U_max": round(U[umax], 4)})
        natije[nam] = radifha
        for r in radifha[:3]:
            print(nam, r)
    json.dump(natije, open(khoroji, "w"), indent=1)


if __name__ == "__main__":
    main()
