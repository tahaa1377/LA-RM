import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testbed_summary import attack_run, ci

K4 = sys.argv[1] if len(sys.argv) > 1 else "runs_k4"
K3 = sys.argv[2] if len(sys.argv) > 2 else "runs_rev"
KHOROOJI = sys.argv[3] if len(sys.argv) > 3 else "results_rev2/testbed_k4.json"
LISTE_SIASATHA = ["urm", "larm", "greedy", "sp_retry", "larm_retry"]
KELIDHA = ["admission", "admission_avoidable", "admission_unavoidable", "via_core_avoidable", "busiest"]


def runs(d, siasat):
    khoroji = {}
    for p in sorted(glob.glob(os.path.join(d, f"atk_{siasat}_s*.json"))):
        tokhm = int(re.search(r"_s(\d+)\.json$", p).group(1))
        try:
            khoroji[tokhm] = attack_run(p)
        except (KeyError, ValueError, json.JSONDecodeError):
            pass
    return khoroji


def main():
    sp = runs(K3, "sp")
    natije = {"k4": {}, "k3": {}, "k4_minus_k3": {}, "k4_minus_sp": {}}
    for siasat in LISTE_SIASATHA:
        r4, r3 = runs(K4, siasat), runs(K3, siasat)
        natije["k4"][siasat] = {"n": len(r4), **{k: ci([r4[s][k] for s in sorted(r4)]) for k in KELIDHA}}
        natije["k3"][siasat] = {"n": len(r3), **{k: ci([r3[s][k] for s in sorted(r3)]) for k in KELIDHA}}
        moshtarak = sorted(set(r4) & set(r3))
        natije["k4_minus_k3"][siasat] = {k: ci([r4[s][k] - r3[s][k] for s in moshtarak]) for k in ("admission", "admission_avoidable")}
        cs = sorted(set(r4) & set(sp))
        natije["k4_minus_sp"][siasat] = {k: ci([r4[s][k] - sp[s][k] for s in cs]) for k in ("admission", "admission_avoidable")}
        a = natije["k4"][siasat]
        print(f"{siasat:11} n={a['n']} all={a['admission']} avoid={a['admission_avoidable']} "
              f"other={a['admission_unavoidable']} via_core={a['via_core_avoidable']} | "
              f"k4-k3 all={natije['k4_minus_k3'][siasat]['admission']} | k4-sp all={natije['k4_minus_sp'][siasat]['admission']}")
    json.dump(natije, open(KHOROOJI, "w"), indent=1)
    namha = {"urm": "URM", "larm": "LA-RM", "greedy": "Greedy", "sp_retry": "SP+R", "larm_retry": "LA-RM+R"}
    print("% LaTeX rows: policy & k=3 all, avoidable, other & k=4 all, avoidable, other & k4-k3 all (points)")
    for siasat in LISTE_SIASATHA:
        a3, a4, d = natije["k3"][siasat], natije["k4"][siasat], natije["k4_minus_k3"][siasat]["admission"]
        f = lambda c: f"{c[0]:.2f}"
        print(f"{namha[siasat]} & {f(a3['admission'])} & {f(a3['admission_avoidable'])} & {f(a3['admission_unavoidable'])} & "
              f"{f(a4['admission'])} & {f(a4['admission_avoidable'])} & {f(a4['admission_unavoidable'])} & "
              f"${100 * d[0]:+.1f}\\pm{100 * d[1]:.1f}$ \\\\")


if __name__ == "__main__":
    main()
