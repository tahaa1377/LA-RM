import json
import os
import sys

import numpy as np

R, R2, R3, R4, M = "results_rev", "results_rev2", "results_rev3", "results_rev4", "results"
P8 = ["sp", "ecmp", "urm", "larm", "greedy", "sp_retry", "larm_retry", "larm2"]

MAJMOOEHA = [
    ("fattree4", "yen", "adaptive", f"{R4}/l2_fattree4.json",
     [f"{R}/base_fattree4.json", f"{R}/curve_fattree4.json"], f"{M}/main_fattree4.json"),
    ("fattree4", "yen", "static", f"{R4}/l2_fattree4_static.json", [f"{R}/base_fattree4_static.json"], None),
    ("fattree4", "yen", "aware", f"{R4}/l2_fattree4_aware.json", [f"{R}/base_fattree4_aware.json"], None),
    ("fattree4", "yen", "smart", f"{R4}/l2_fattree4_smart.json", [f"{R}/base_fattree4_smart.json"], None),
    ("abilene", "yen", "adaptive", f"{R4}/l2_abilene.json",
     [f"{R}/base_abilene.json", f"{R}/base_abilene_full.json", f"{R}/curve_abilene.json"],
     f"{M}/main_abilene.json"),
    ("abilene", "yen", "static", f"{R4}/l2_abilene_static.json", [f"{R}/base_abilene_static.json"], None),
    ("abilene", "yen", "aware", f"{R4}/l2_abilene_aware.json", [f"{R}/base_abilene_aware.json"], None),
    ("abilene", "yen", "aware", f"{R4}/l2_abilene_aware_1100.json", [f"{R2}/yen_abilene_aware.json"], None),
    ("abilene", "yen", "smart", f"{R4}/l2_abilene_smart.json", [f"{R}/base_abilene_smart.json"], None),
    ("geant2012", "yen", "adaptive", f"{R4}/l2_geant2012.json",
     [f"{R}/base_geant2012.json", f"{R}/base_geant2012_0_1100.json", f"{R}/curve_geant2012.json"],
     f"{M}/main_geant.json"),
    ("geant2012", "yen", "static", f"{R4}/l2_geant2012_static.json",
     [f"{R}/base_geant2012_static.json", f"{R3}/yen_geant2012_static.json"], None),
    ("geant2012", "yen", "aware", f"{R4}/l2_geant2012_aware.json",
     [f"{R}/base_geant2012_aware.json", f"{R3}/yen_geant2012_aware_800.json",
      f"{R2}/yen_geant2012_aware.json"], None),
    ("geant2012", "yen", "smart", f"{R4}/l2_geant2012_smart.json", [f"{R}/base_geant2012_smart.json"], None),
    ("abilene_sndlib", "yen", "adaptive", f"{R4}/l2_abilene_sndlib.json",
     [f"{R}/base_abilene_sndlib.json", f"{R}/curve_abilene_sndlib.json"], f"{M}/main_abilene_sndlib.json"),
    ("geant_sndlib", "yen", "adaptive", f"{R4}/l2_geant_sndlib.json",
     [f"{R}/base_geant_sndlib.json", f"{R}/base_geant_sndlib_full.json", f"{R}/curve_geant_sndlib.json"],
     f"{M}/main_geant_sndlib.json"),
    ("geant2009", "yen", "adaptive", f"{R4}/l2_geant2009.json",
     [f"{R2}/yen_geant2009_600.json", f"{R2}/yen_geant2009_1100.json"], None),
    ("geant2010", "yen", "adaptive", f"{R4}/l2_geant2010.json",
     [f"{R2}/yen_geant2010_600.json", f"{R2}/yen_geant2010_1100.json"], None),
    ("uscarrier", "yen", "adaptive", f"{R4}/l2_uscarrier.json",
     [f"{R2}/yen_uscarrier_600.json", f"{R2}/yen_uscarrier_1100.json"], None),
    ("cogentco", "yen", "adaptive", f"{R4}/l2_cogentco.json",
     [f"{R2}/yen_cogentco_600.json", f"{R2}/yen_cogentco_1100.json"], None),
    ("abilene", "div", "adaptive", f"{R4}/l2_div_abilene.json", [f"{R2}/div_abilene.json"], None),
    ("abilene", "div", "aware", f"{R4}/l2_div_abilene_aware.json", [f"{R2}/div_abilene_aware.json"], None),
    ("geant2012", "div", "adaptive", f"{R4}/l2_div_geant2012.json", [f"{R2}/div_geant2012.json"], None),
    ("geant2012", "div", "aware", f"{R4}/l2_div_geant2012_aware.json",
     [f"{R2}/div_geant2012_aware.json"], None),
    ("geant2009", "div", "adaptive", f"{R4}/l2_div_geant2009.json", [f"{R2}/div_geant2009.json"], None),
    ("geant2010", "div", "adaptive", f"{R4}/l2_div_geant2010.json", [f"{R2}/div_geant2010.json"], None),
    ("uscarrier", "div", "adaptive", f"{R4}/l2_div_uscarrier.json", [f"{R2}/div_uscarrier.json"], None),
    ("cogentco", "div", "adaptive", f"{R4}/l2_div_cogentco.json", [f"{R2}/div_cogentco.json"], None),
]

JADVAL2 = (
    [("fattree4", a, b) for b in (900, 1300) for a in ("static", "adaptive", "aware", "smart")]
    + [("abilene", a, 600) for a in ("static", "adaptive", "aware", "smart")]
    + [("abilene", "adaptive", 800), ("abilene", "adaptive", 1100)]
    + [("geant2012", "adaptive", 600), ("geant2012", "smart", 600),
       ("geant2012", "adaptive", 800), ("geant2012", "adaptive", 1100)]
    + [("abilene_sndlib", "adaptive", b) for b in (600, 800)]
    + [("geant_sndlib", "adaptive", b) for b in (600, 800, 1100)])


def load(masir):
    with open(masir) as f:
        return json.load(f)


def seven(files, mainf):
    khoroji = {}
    for f in files:
        if not os.path.exists(f):
            continue
        d = load(f)["policies"]
        for p in d:
            for b, v in d[p].items():
                khoroji.setdefault(int(b), {})[p] = v["admission"][0]
    if mainf and os.path.exists(mainf):
        d = load(mainf)["policies"]
        for p in d:
            for b, v in d[p]["adm_curve"].items():
                khoroji.setdefault(int(b), {}).setdefault(p, v[0])
    return khoroji


def settings():
    radifha = []
    for topolozhi, kandidha, harif, l2f, files, mainf in MAJMOOEHA:
        s7 = seven(files, mainf)
        l2 = load(l2f)["policies"]["larm2"]
        for b in sorted(int(x) for x in l2):
            if b == 0 or b not in s7 or not all(p in s7[b] for p in P8[:-1]):
                continue
            adm = {p: 100.0 * s7[b][p] for p in P8[:-1]}
            adm["larm2"] = 100.0 * l2[str(b)]["admission"][0]
            behtarin = max(adm.values())
            radifha.append({"topology": topolozhi, "candidates": kandidha, "adversary": harif, "budget": b,
                         "admission": {p: round(v, 3) for p, v in adm.items()},
                         "gap": {p: round(v - behtarin, 3) for p, v in adm.items()},
                         "best": [p for p in P8 if adm[p] > behtarin - 0.05]})
    return radifha


def summarize(radifha):
    khoroji = {"settings": len(radifha)}
    for p in P8:
        g = np.array([r["gap"][p] for r in radifha])
        w = radifha[int(g.argmin())]
        khoroji[p] = {"mean_gap": round(float(g.mean()), 2), "worst_gap": round(float(g.min()), 2),
                  "worst_at": f"{w['topology']}/{w['candidates']}/{w['adversary']}/{w['budget']}",
                  "best_or_tied": int((g > -0.05).sum())}
    return khoroji


def main():
    khoroji = sys.argv[1] if len(sys.argv) > 1 else f"{R4}/gaps.json"
    radifha = settings()
    stress = [r for r in radifha if r["budget"] >= (900 if r["topology"] == "fattree4" else 600)]
    t2 = [r for r in radifha if r["candidates"] == "yen"
          and (r["topology"], r["adversary"], r["budget"]) in JADVAL2]
    natije = {"policies": P8, "settings": radifha,
           "summary": {"all": summarize(radifha), "stress_and_above": summarize(stress),
                       "table2": summarize(t2)}}
    for nam, s in natije["summary"].items():
        print(f"{nam}: {s['settings']} settings")
        for p in P8:
            v = s[p]
            print(f"  {p:10s} mean {v['mean_gap']:6.2f}  worst {v['worst_gap']:7.2f} ({v['worst_at']})"
                  f"  best or tied {v['best_or_tied']}")
    agah = ("greedy", "sp_retry", "larm_retry", "larm2")
    n = sum(1 for r in radifha if any(p in agah for p in r["best"]))
    print(f"settings in which an occupancy-aware policy is best or tied: {n} of {len(radifha)}")
    json.dump(natije, open(khoroji, "w"), indent=1)


if __name__ == "__main__":
    main()
