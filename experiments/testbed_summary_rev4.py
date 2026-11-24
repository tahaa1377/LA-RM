import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testbed_summary import attack_run, ci, BINS, LATE

KHOROOJI = sys.argv[1] if len(sys.argv) > 1 else "results_rev4/testbed_rev.json"
LISTE_SIASATHA = ["sp", "ecmp", "urm", "larm", "greedy", "sp_retry", "larm_retry", "larm2"]
KELIDHA = ["admission", "admission_avoidable", "admission_unavoidable", "admission_avoidable_late",
        "via_core_avoidable", "via_core_avoidable_late", "busiest"]
K3 = ("admission", "admission_avoidable", "admission_unavoidable")
NAMHA = {"sp": "SP", "ecmp": "ECMP", "urm": "URM", "larm": "LA-RM", "greedy": "Greedy", "sp_retry": "SP+R",
         "larm_retry": "LA-RM+R", "larm2": "LA-RM2"}


def runs(d, siasat):
    khoroji = {}
    for p in sorted(glob.glob(os.path.join(d, f"atk_{siasat}_s*.json"))):
        tokhm = int(re.search(r"_s(\d+)\.json$", p).group(1))
        try:
            khoroji[tokhm] = attack_run(p)
            khoroji[tokhm]["_path"] = p
        except (KeyError, ValueError, json.JSONDecodeError):
            pass
    return khoroji


def f2(c):
    return f"${c[0]:.2f}\\pm{c[1]:.2f}$"


def pts(c):
    return f"${100 * c[0]:+.1f}\\pm{100 * c[1]:.1f}$"


def main():
    natije = {"bins": BINS, "late": LATE, "attack": {}, "paired_vs_sp": {}}
    per = {siasat: runs("runs_rev", siasat) for siasat in LISTE_SIASATHA}
    for siasat in LISTE_SIASATHA:
        rs = [per[siasat][s] for s in sorted(per[siasat])]
        tajmi = {"n": len(rs), "seeds": sorted(per[siasat])}
        for key in KELIDHA:
            tajmi[key] = ci([r[key] for r in rs])
        tajmi["admission_avoidable_bins"] = [ci([r["admission_avoidable_bins"][i] for r in rs]) for i in range(len(BINS))]
        tajmi["avoidable_min"] = min(r["admission_avoidable"] for r in rs)
        natije["attack"][siasat] = tajmi
        moshtarak = sorted(set(per[siasat]) & set(per["sp"]))
        natije["paired_vs_sp"][siasat] = {k: ci([per[siasat][s][k] - per["sp"][s][k] for s in moshtarak]) for k in K3}
    print("% second series, k = 3: policy & all & avoidable & other & via core (%)   | paired vs SP (all)")
    for siasat in LISTE_SIASATHA:
        a = natije["attack"][siasat]
        vc = a["via_core_avoidable"]
        print(f"{NAMHA[siasat]} & {f2(a['admission'])} & {f2(a['admission_avoidable'])} & {f2(a['admission_unavoidable'])} & "
              f"${100 * vc[0]:.0f}\\pm{100 * vc[1]:.0f}$ \\\\   % n={a['n']} vs SP {pts(natije['paired_vs_sp'][siasat]['admission'])}"
              f" min avoidable {a['avoidable_min']:.3f}")

    cal = {"event": {}, "poll": {}, "event_minus_poll": {}, "gain_vs_sp": {"event": {}, "poll": {}}, "count_gap": {}}
    KALIBRASION = [q for q in ("sp", "greedy", "sp_retry", "larm2", "larm") if len(runs("runs_evt", q)) >= 10]
    rooydad = {siasat: runs("runs_evt", siasat) for siasat in KALIBRASION}
    print("% calibration: policy & poll all, avoidable, other & event all, avoidable, other & event minus poll (all, other; points)")
    for siasat in KALIBRASION:
        moshtarak = sorted(set(rooydad[siasat]) & set(per[siasat]))
        cal["event"][siasat] = {"n": len(moshtarak), **{k: ci([rooydad[siasat][s][k] for s in moshtarak]) for k in K3}}
        cal["poll"][siasat] = {k: ci([per[siasat][s][k] for s in moshtarak]) for k in K3}
        cal["event_minus_poll"][siasat] = {k: ci([rooydad[siasat][s][k] - per[siasat][s][k] for s in moshtarak]) for k in K3}
        gaps = []
        for s in moshtarak:
            o = json.load(open(rooydad[siasat][s]["_path"] + ".occ"))
            gaps += o.get("count_gap", [])
        cal["count_gap"][siasat] = {"polls": len(gaps), "mean": round(sum(gaps) / max(1, len(gaps)), 3),
                                 "max": max(gaps) if gaps else None,
                                 "share_zero": round(sum(1 for g in gaps if g == 0) / max(1, len(gaps)), 3)}
        e, q, d = cal["event"][siasat], cal["poll"][siasat], cal["event_minus_poll"][siasat]
        print(f"{NAMHA[siasat]} & {q['admission'][0]:.2f} & {q['admission_avoidable'][0]:.2f} & {q['admission_unavoidable'][0]:.2f} & "
              f"{e['admission'][0]:.2f} & {e['admission_avoidable'][0]:.2f} & {e['admission_unavoidable'][0]:.2f} & "
              f"{pts(d['admission'])} & {pts(d['admission_unavoidable'])} \\\\   % n={e['n']} avoidable diff {pts(d['admission_avoidable'])}"
              f" gap {cal['count_gap'][siasat]}")
    for halat, src in (("event", rooydad), ("poll", per)):
        for siasat in [q for q in KALIBRASION if q != "sp"]:
            moshtarak = sorted(set(rooydad[siasat]) & set(rooydad["sp"]) & set(per[siasat]) & set(per["sp"]))
            cal["gain_vs_sp"][halat][siasat] = {k: ci([src[siasat][s][k] - src["sp"][s][k] for s in moshtarak]) for k in K3}
            print(f"% gain over SP with {halat} counts, {siasat}: all {pts(cal['gain_vs_sp'][halat][siasat]['admission'])}"
                  f" avoidable {pts(cal['gain_vs_sp'][halat][siasat]['admission_avoidable'])}")
    natije["calibration"] = cal

    k4 = {"k4": {}, "k3": {}, "k4_minus_k3": {}}
    print("% k = 4: policy & k3 all, avoid, other & k4 all, avoid, other & k4 minus k3 (all; points)")
    for siasat in ("urm", "larm", "greedy", "sp_retry", "larm_retry", "larm2"):
        r4, r3 = runs("runs_k4", siasat), per[siasat]
        if not r4:
            continue
        k4["k4"][siasat] = {"n": len(r4), **{k: ci([r4[s][k] for s in sorted(r4)]) for k in K3}}
        k4["k3"][siasat] = {k: ci([r3[s][k] for s in sorted(r3)]) for k in K3}
        moshtarak = sorted(set(r4) & set(r3))
        k4["k4_minus_k3"][siasat] = {k: ci([r4[s][k] - r3[s][k] for s in moshtarak]) for k in K3}
        a3, a4 = k4["k3"][siasat], k4["k4"][siasat]
        print(f"{NAMHA[siasat]} & {a3['admission'][0]:.2f} & {a3['admission_avoidable'][0]:.2f} & {a3['admission_unavoidable'][0]:.2f} & "
              f"{a4['admission'][0]:.2f} & {a4['admission_avoidable'][0]:.2f} & {a4['admission_unavoidable'][0]:.2f} & "
              f"{pts(k4['k4_minus_k3'][siasat]['admission'])} \\\\   % n={a4['n']} min avoidable k4 "
              f"{min(r4[s]['admission_avoidable'] for s in r4):.3f}")
    natije["k4"] = k4
    for siasat in per:
        for s in per[siasat]:
            per[siasat][s].pop("_path", None)
    os.makedirs(os.path.dirname(KHOROOJI), exist_ok=True)
    json.dump(natije, open(KHOROOJI, "w"), indent=1)


if __name__ == "__main__":
    main()
