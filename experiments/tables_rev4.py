import json
import os
import sys

import numpy as np

sys.path.insert(0, ".")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from larm.stats import ci95

R4 = "results_rev4"
KELIDHA6 = ["fattree4:900", "fattree4:1300", "abilene:600", "abilene:800", "geant:600", "geant:800"]
KELIDHA8 = KELIDHA6 + ["geant_sndlib:600", "geant_sndlib:800"]


def load(p):
    return json.load(open(p))


def pd(x, y):
    m, h = ci95([a - b for a, b in zip(x, y)], scale=100.0, nd=6)
    return f"${m:+.1f}\\pm{h:.1f}$"


def dev():
    d = load(f"{R4}/dev_full.json")["configs"]
    print("% development seeds 100-109: configuration & six settings & mean")
    radifha = [("Greedy", "greedy"), ("SP+R", "sp_retry"), ("LA-RM+R", "larm_retry"), ("LA-RM", "larm")]
    radifha += [(f"all, $a={a}$, retry", f"larm_retry|full|a={a}|d0=0.5") for a in (0.05, 0.1, 0.2, 0.4)]
    radifha += [(f"all, $a={a}$, no retry", f"larm|full|a={a}|d0=0.5") for a in (0.05, 0.1, 0.2, 0.4)]
    radifha += [(f"all, $a=0.2$, $\\gamma={g}$, retry", f"larm_retry|full|a=0.2|d0=0.0|g={g}") for g in (0.5, 0.7)]
    for bargasb, key in radifha:
        v = [100 * d[key][k]["admission"][0] for k in KELIDHA6]
        print(f"{bargasb} & " + " & ".join(f"{x:.1f}" for x in v) + f" & {np.mean(v):.2f} \\\\")
    same = all(d[f"larm_retry|full|a={a}|d0=0.0"][k]["admission"] == d[f"larm_retry|full|a={a}|d0=0.5"][k]["admission"]
               for a in (0.05, 0.1, 0.2, 0.4) for k in KELIDHA6)
    print(f"% d0 = 0 and d0 = 0.5 give identical results with credit for every candidate: {same}")


def ablation():
    A = load(f"{R4}/ablation.json")
    F = A["feedback"]
    print("% ablation, paper seeds: credit & a & retry & eight settings")
    for bazkhord, bargasb in (("sampled", "flows"), ("all", "all")):
        for a in (0.05, 0.4):
            for siasat, rt in (("larm", "no"), ("larm_retry", "yes")):
                c = F[f"{siasat}|{bazkhord}|a={a}"]
                print(f"{bargasb} & ${a}$ & {rt} & " + " & ".join(f"{100 * c[k]['admission'][0]:.1f}" for k in KELIDHA8) + " \\\\")
    paye = F["larm|sampled|a=0.05"]
    print("% paired differences against the first design without retry (points)")
    for key, bargasb in (("larm|sampled|a=0.4", "rate alone"), ("larm|all|a=0.05", "credit alone"), ("larm|all|a=0.4", "both")):
        print(f"{bargasb} & " + " & ".join(pd(F[key][k]["adm_runs"], paye[k]["adm_runs"]) for k in KELIDHA8) + " \\\\")
    print("retry, on top of both & " + " & ".join(
        pd(F["larm_retry|all|a=0.4"][k]["adm_runs"], F["larm|all|a=0.4"][k]["adm_runs"]) for k in KELIDHA8) + " \\\\")
    print("LA-RM2 minus LA-RM+R & " + " & ".join(
        pd(F["larm_retry|all|a=0.4"][k]["adm_runs"], F["larm_retry|sampled|a=0.05"][k]["adm_runs"]) for k in KELIDHA8) + " \\\\")
    print("% randomization: eps & floor & largest share (k=4) & admission in eight settings; then stretch on the backbones")
    R = A["randomization"]

    def pstar(eps, fl, k=4):
        if eps == 0 and fl == 0:
            return 1.0
        u = np.full(k, 1.0 / k)
        pe = (1 - eps) * np.eye(k)[0] + eps * u
        H = lambda q: float(-(q[q > 0] * np.log(q[q > 0])).sum())
        while H(pe) < fl * np.log(k):
            pe = 0.9 * pe + 0.1 * u
        return float(pe[0])
    for eps, fl in ((0.1, 0.75), (0.1, 0.5), (0.05, 0.25), (0.1, 0.25), (0.0, 0.0)):
        c = R[f"eps={eps}|floor={fl}"]
        print(f"${eps}$ & ${fl}$ & ${pstar(eps, fl):.2f}$ & " + " & ".join(f"{100 * c[k]['admission'][0]:.1f}" for k in KELIDHA8)
              + " & " + "/".join(f"{c[k]['stretch_admitted'][0]:.2f}" for k in ("abilene:600", "geant:600")) + " \\\\")
    d0 = R["eps=0.1|floor=0.5"]
    print("no randomization minus default & " + " & ".join(pd(R["eps=0.0|floor=0.0"][k]["adm_runs"], d0[k]["adm_runs"]) for k in KELIDHA8) + " \\\\")
    print("% Abilene at 800 rules: policy & admission & stretch & rules per admitted flow & epochs with >=2 full & >=1 full")
    D = A["diag_abilene_800"]
    for siasat, bargasb in (("sp_retry", "SP+R"), ("greedy", "Greedy"), ("larm_retry", "LA-RM+R"), ("larm2", "LA-RM2")):
        v = D[siasat]
        print(f"{bargasb} & ${100 * v['admission'][0]:.1f}\\pm{100 * v['admission'][1]:.1f}$ & ${v['stretch_admitted'][0]:.2f}$ & "
              f"${v['rules_per_admitted_flow'][0]:.2f}$ & ${100 * v['epochs_two_or_more_full'][0]:.0f}$ & "
              f"${100 * v['epochs_one_or_more_full'][0]:.0f}$ \\\\")


def gaps():
    G = load(f"{R4}/gaps.json")["summary"]
    namha = {"sp": "SP", "ecmp": "ECMP", "urm": "URM", "larm": "LA-RM", "greedy": "Greedy", "sp_retry": "SP+R",
             "larm_retry": "LA-RM+R", "larm2": "LA-RM2"}
    print("% shortfall from the best policy: policy & (mean, worst, best or tied) for all settings, stress and above, Table II")
    print("% settings:", {k: v["settings"] for k, v in G.items()})
    for p, bargasb in namha.items():
        selha = []
        for s in ("all", "stress_and_above", "table2"):
            v = G[s][p]
            selha += [f"{-v['mean_gap']:.2f}", f"{-v['worst_gap']:.2f}", str(v["best_or_tied"])]
        print(f"{bargasb} & " + " & ".join(selha) + " \\\\")
    for s in ("all", "stress_and_above", "table2"):
        print(f"% worst cases ({s}):", {p: G[s][p]["worst_at"] for p in ("greedy", "sp_retry", "larm_retry", "larm2")})


def nr():
    print("% LA-RM2 without retry (larm2_nr) next to LA-RM2, admission in %")
    for f, bargasb, bs in (("l2_fattree4", "Fat-tree", ("900", "1300")), ("l2_abilene", "Abilene", ("600", "800", "1100")),
                       ("l2_geant2012", "GEANT2012", ("600", "800", "1100")), ("l2_abilene_sndlib", "Abilene 2004", ("600", "800")),
                       ("l2_geant_sndlib", "GEANT 2005", ("600", "800", "1100"))):
        P = load(f"{R4}/{f}.json")["policies"]
        for b in bs:
            a, n = P["larm2"][b], P["larm2_nr"][b]
            print(f"{bargasb} & ${b}$ & {100 * n['admission'][0]:.1f} & {100 * a['admission'][0]:.1f} & "
                  f"{pd(a['adm_runs'], n['adm_runs'])} \\\\")


if __name__ == "__main__":
    dev()
    ablation()
    gaps()
    nr()
