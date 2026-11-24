import json
import sys

import networkx as nx

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm.paths import PathTable, path_cost

TOPOS = [("fattree4", 1), ("abilene", 1), ("geant2009", 1), ("geant2010", 1), ("geant", 1),
         ("uscarrier", 1), ("cogentco", 1), ("abilene_sndlib", 10), ("geant_sndlib", 10)]
HADDE_AKSARE_OD = {"uscarrier": 1500, "cogentco": 1500}
HALATHAYE_KANDID = ["yen", "ties", "np", "div"]
K, HADDE_KESHIDEGI = 4, 2.5


def analyse(G, taghaza, halat):
    ods = [od for od, w in taghaza.items() if w > 0]
    majmoo = sum(taghaza[od] for od in ods)
    nerkh = {od: taghaza[od] / majmoo for od in ods}
    pt = PathTable(G, ods, k=K, hadde_aksare_keshidegi=HADDE_KESHIDEGI, halat=halat, nerkh=nerkh)
    yen_first = {od: PathTable(G, [od], k=1).cand[od][0] for od in ods}
    U = {n: 0.0 for n in G.nodes()}
    S = {n: 0.0 for n in G.nodes()}
    for od in ods:
        moshtarak = set(pt.cand[od][0])
        for p in pt.cand[od][1:]:
            moshtarak &= set(p)
        for n in moshtarak:
            U[n] += nerkh[od]
        eq = pt.ecmp[od]
        for p in eq:
            for n in p:
                S[n] += nerkh[od] / len(eq)
    hub = max(S, key=S.get)
    umax = max(U, key=U.get)
    tr = kandide_ejtenab = any_avoid = 0.0
    H = nx.restricted_view(G, [hub], [])
    for od in ods:
        if hub in od:
            continue
        if hub not in yen_first[od]:
            continue
        w = nerkh[od]
        tr += w
        if any(hub not in p for p in pt.cand[od]):
            kandide_ejtenab += w
        try:
            p = nx.shortest_path(H, od[0], od[1], weight="weight")
            if path_cost(G, p) <= HADDE_KESHIDEGI * pt.sp_cost[od]:
                any_avoid += w
        except nx.NetworkXNoPath:
            pass
    st = [pt.stretch(od, p) for od in ods for p in pt.cand[od]]
    tedade_kandid = sum(len(pt.cand[od]) for od in ods) / len(ods)
    return {"hub": str(hub), "sp_share_hub": round(S[hub], 4), "u_hub": round(U[hub], 4),
            "u_max": round(U[umax], 4), "u_max_node": str(umax),
            "transit_share": round(tr, 4),
            "transit_with_avoiding_candidate": round(kandide_ejtenab / tr, 4) if tr else None,
            "transit_with_avoiding_path": round(any_avoid / tr, 4) if tr else None,
            "mean_candidates": round(tedade_kandid, 3), "mean_candidate_stretch": round(sum(st) / len(st), 4)}


def main():
    khoroji = sys.argv[1] if len(sys.argv) > 1 else "results_rev2/candidates.json"
    natije = {}
    for nam, roozha in TOPOS:
        natije[nam] = {}
        for halat in HALATHAYE_KANDID:
            radifha = []
            for rooz in range(roozha):
                G, taghaza, _ = seed_instance(nam, rooz, max_ods=HADDE_AKSARE_OD.get(nam))
                r = analyse(G, taghaza, halat)
                r["day"] = rooz
                radifha.append(r)
            natije[nam][halat] = radifha
            r0 = radifha[0]
            paein = min(r["u_hub"] for r in radifha), max(r["u_hub"] for r in radifha)
            print(f"{nam:15} {halat:5} u_hub={paein} u_max={min(r['u_max'] for r in radifha)}-{max(r['u_max'] for r in radifha)} "
                  f"transit={r0['transit_share']} cand_avoid={r0['transit_with_avoiding_candidate']} "
                  f"path_avoid={r0['transit_with_avoiding_path']} ncand={r0['mean_candidates']} "
                  f"cstretch={r0['mean_candidate_stretch']}", flush=True)
    json.dump(natije, open(khoroji, "w"), indent=1)


if __name__ == "__main__":
    main()
