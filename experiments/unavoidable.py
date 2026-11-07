"""Unavoidable demand per switch (revision).

For every switch v, U(v) is the share of benign demand whose candidate paths
(k=4, stretch <= 2.5) all cross v, including the pairs that start or end at v.
No policy that routes on the candidate sets can keep these flows off v, so an
adversary that keeps v full blocks at least U(v) of the benign flows whatever the
policy, and a policy that retries among the candidates blocks no more than that
while no other switch fills. Also prints the share of demand that crosses v under
shortest-path routing (equal-cost ties split evenly), for comparison.

Usage: python experiments/unavoidable.py [out.json]
"""
import json
import sys

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm.paths import PathTable

TOPOS = [("fattree4", 1), ("abilene", 1), ("geant2009", 1), ("geant2010", 1), ("geant", 1),
         ("uscarrier", 1), ("cogentco", 1), ("abilene_sndlib", 10), ("geant_sndlib", 10)]
MAXODS = {"uscarrier": 1500, "cogentco": 1500}   # the OD sample used in the experiments


def shares(G, dem, k=4, max_stretch=2.5):
    ods = [od for od, w in dem.items() if w > 0]
    tot = sum(dem[od] for od in ods)
    pt = PathTable(G, ods, k=k, max_stretch=max_stretch)
    U = {n: 0.0 for n in G.nodes()}
    S = {n: 0.0 for n in G.nodes()}
    for od in ods:
        w = dem[od] / tot
        common = set(pt.cand[od][0])
        for p in pt.cand[od][1:]:
            common &= set(p)
        for n in common:
            U[n] += w
        eq = pt.ecmp[od]
        for p in eq:
            for n in p:
                S[n] += w / len(eq)
    return U, S


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "results_rev/unavoidable.json"
    res = {}
    for name, days in TOPOS:
        rows = []
        for day in range(days):
            G, dem, _ = seed_instance(name, day, max_ods=MAXODS.get(name))
            U, S = shares(G, dem)
            hub = max(S, key=S.get)
            umax = max(U, key=U.get)
            rows.append({"day": day, "sp_hub": str(hub), "sp_share_hub": round(S[hub], 4),
                         "U_hub": round(U[hub], 4), "U_max_node": str(umax),
                         "U_max": round(U[umax], 4)})
        res[name] = rows
        for r in rows[:3]:
            print(name, r)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
