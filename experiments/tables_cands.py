import json
import os
import sys

sys.path.insert(0, ".")
from larm.stats import ci95

R, R2, R4 = "results_rev", "results_rev2", "results_rev4"
LISTE_SIASATHA = ["sp", "ecmp", "urm", "larm", "greedy", "sp_retry", "larm_retry", "larm2"]
NAMHA = {"fattree4": "Fat-tree ($k{=}4$)", "abilene": "Abilene", "geant2009": "GEANT2009",
         "geant2010": "GEANT2010", "geant": "GEANT2012", "uscarrier": "UsCarrier",
         "cogentco": "Cogentco", "abilene_sndlib": "Abilene 2004", "geant_sndlib": "GEANT 2005"}


def load(p):
    return json.load(open(p))


def rng(meghdarha, nd=2):
    paein, bala = min(meghdarha), max(meghdarha)
    return f"{paein:.{nd}f}" if f"{paein:.{nd}f}" == f"{bala:.{nd}f}" else f"{paein:.{nd}f}--{bala:.{nd}f}"


def table_u():
    C = load(f"{R2}/candidates.json")
    print("% u table: topology & u(hub) yen & div & max u yen & div & transit avoid yen & div & cand stretch yen & div")
    for t in ["fattree4", "abilene", "geant2009", "geant2010", "geant", "uscarrier", "cogentco",
              "abilene_sndlib", "geant_sndlib"]:
        y, d = C[t]["yen"], C[t]["div"]
        tr = lambda radifha: rng([100 * r["transit_with_avoiding_candidate"] for r in radifha if r["transit_with_avoiding_candidate"] is not None], 0) \
            if any(r["transit_with_avoiding_candidate"] is not None for r in radifha) else "--"
        print(f"{NAMHA[t]} & {rng([r['u_hub'] for r in y])} & {rng([r['u_hub'] for r in d])} & "
              f"{rng([r['u_max'] for r in y])} & {rng([r['u_max'] for r in d])} & "
              f"{tr(y)} & {tr(d)} & {rng([r['mean_candidate_stretch'] for r in y])} & "
              f"{rng([r['mean_candidate_stretch'] for r in d])} \\\\")


def adm(masir, siasat, b, l2=None):
    d = load(l2 if siasat == "larm2" else masir)
    return d["policies"][siasat][str(b)]["admission"][0], d["policies"][siasat][str(b)]["adm_runs"]


def table_adm():
    yen = {"abilene": {600: f"{R}/base_abilene.json", 800: f"{R}/base_abilene.json", 1100: f"{R}/base_abilene_full.json"},
           "geant2009": {600: f"{R2}/yen_geant2009_600.json", 1100: f"{R2}/yen_geant2009_1100.json"},
           "geant2010": {600: f"{R2}/yen_geant2010_600.json", 1100: f"{R2}/yen_geant2010_1100.json"},
           "geant": {600: f"{R}/base_geant2012.json", 800: f"{R}/base_geant2012.json", 1100: f"{R}/base_geant2012_0_1100.json"},
           "uscarrier": {600: f"{R2}/yen_uscarrier_600.json", 1100: f"{R2}/yen_uscarrier_1100.json"},
           "cogentco": {600: f"{R2}/yen_cogentco_600.json", 1100: f"{R2}/yen_cogentco_1100.json"}}
    div = {t: f"{R2}/div_{'geant2012' if t == 'geant' else t}.json" for t in yen}
    l2 = {"yen": {t: f"{R4}/l2_{'geant2012' if t == 'geant' else t}.json" for t in yen},
          "div": {t: f"{R4}/l2_div_{'geant2012' if t == 'geant' else t}.json" for t in yen}}
    print("% admission table: topology & budget & candidates & 8 policies")
    summary = {}
    for t in ["abilene", "geant2009", "geant2010", "geant", "uscarrier", "cogentco"]:
        bodjeha = [600, 1100] if t not in ("abilene", "geant") else [600, 800, 1100]
        for j, b in enumerate(bodjeha):
            for halat in ("yen", "div"):
                masir = yen[t][b] if halat == "yen" else div[t]
                meghdarha = [adm(masir, p, b, l2[halat][t])[0] for p in LISTE_SIASATHA]
                summary[(t, b, halat)] = {p: adm(masir, p, b, l2[halat][t])[1] for p in LISTE_SIASATHA}
                behtarin = max(meghdarha)
                selha = [(f"\\textbf{{{100 * v:.1f}}}" if abs(v - behtarin) < 5e-4 else f"{100 * v:.1f}") for v in meghdarha]
                bargasb = NAMHA[t] if (j == 0 and halat == "yen") else ""
                bl = f"${b}$" if halat == "yen" else ""
                print(f"{bargasb} & {bl} & {'Yen' if halat == 'yen' else 'Div.'} & " + " & ".join(selha) + " \\\\")
    for t, f in (("abilene", "abilene"), ("geant", "geant2012")):
        for halat in ("yen", "div"):
            masir = f"{R2}/{halat}_{f}_aware.json"
            l2a = {("yen", "abilene"): f"{R4}/l2_abilene_aware_1100.json", ("yen", "geant2012"): f"{R4}/l2_geant2012_aware.json",
                   ("div", "abilene"): f"{R4}/l2_div_abilene_aware.json", ("div", "geant2012"): f"{R4}/l2_div_geant2012_aware.json"}
            meghdarha = [adm(masir, p, 1100, l2a[(halat, f)])[0] for p in LISTE_SIASATHA]
            behtarin = max(meghdarha)
            selha = [(f"\\textbf{{{100 * v:.1f}}}" if abs(v - behtarin) < 5e-4 else f"{100 * v:.1f}") for v in meghdarha]
            print(f"% aware {t} {halat}: " + " & ".join(selha))
    return summary


def paired(summary):
    print("% paired differences div - yen (points), and div: policy - SP")
    for (t, b, halat), d in summary.items():
        if halat != "div":
            continue
        y = summary[(t, b, "yen")]
        khoroji = []
        for p in ("urm", "larm", "greedy", "sp_retry", "larm_retry", "larm2"):
            dd = ci95([a - c for a, c in zip(d[p], y[p])], scale=100, nd=1)
            ds = ci95([a - c for a, c in zip(d[p], d["sp"])], scale=100, nd=1)
            khoroji.append(f"{p}: div-yen {dd[0]:+.1f}±{dd[1]:.1f}, div {p}-sp {ds[0]:+.1f}±{ds[1]:.1f}")
        print(f"% {t} {b}: " + "; ".join(khoroji))


def table_k():
    for f, f2, bargasb in ((f"{R2}/ksweep_div.json", f"{R4}/l2_ksweep.json", "defender's candidates"),
                       (f"{R2}/ksweep_div_fixedatk.json", f"{R4}/l2_ksweep_fixedatk.json", "fixed")):
        if not os.path.exists(f):
            continue
        d = load(f)
        d["policies"]["larm2"] = load(f2)["policies"]["larm2"]
        print(f"% fat-tree k sweep, attack placement: {bargasb}")
        for halat in ("yen", "div"):
            for k in ("2", "3", "4"):
                meghdarha = [d["policies"][p][halat][k]["admission"][0] for p in LISTE_SIASATHA]
                behtarin = max(meghdarha)
                selha = [(f"\\textbf{{{100 * v:.1f}}}" if abs(v - behtarin) < 5e-4 else f"{100 * v:.1f}") for v in meghdarha]
                print(f"{'Yen' if halat == 'yen' else 'Div.'} & ${k}$ & " + " & ".join(selha) + " \\\\")


if __name__ == "__main__":
    table_u()
    s = table_adm()
    paired(s)
    table_k()
