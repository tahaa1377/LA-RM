import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testbed_summary import attack_run, ci, BINS, LATE

EJRAHA = sys.argv[1] if len(sys.argv) > 1 else "runs_rev"
KHOROOJI = sys.argv[2] if len(sys.argv) > 2 else "results_rev/testbed_rev.json"
LISTE_SIASATHA = ["sp", "ecmp", "urm", "larm", "greedy", "sp_retry", "larm_retry"]
KELIDHA = ["admission", "admission_avoidable", "admission_unavoidable", "admission_avoidable_late",
        "via_core_avoidable", "via_core_avoidable_late", "busiest"]


def main():
    per = {}
    for siasat in LISTE_SIASATHA:
        for p in sorted(glob.glob(os.path.join(EJRAHA, f"atk_{siasat}_s*.json"))):
            tokhm = int(re.search(r"_s(\d+)\.json$", p).group(1))
            try:
                per.setdefault(siasat, {})[tokhm] = attack_run(p)
            except (KeyError, ValueError, json.JSONDecodeError):
                pass
    khoroji = {"bins": BINS, "late": LATE, "attack": {}, "paired_vs_sp": {}}
    for siasat, runs in per.items():
        rs = [runs[s] for s in sorted(runs)]
        tajmi = {"n": len(rs), "seeds": sorted(runs)}
        for key in KELIDHA:
            tajmi[key] = ci([r[key] for r in rs])
        tajmi["admission_avoidable_bins"] = [ci([r["admission_avoidable_bins"][i] for r in rs])
                                           for i in range(len(BINS))]
        khoroji["attack"][siasat] = tajmi
    if "sp" in per:
        for siasat, runs in per.items():
            moshtarak = sorted(set(runs) & set(per["sp"]))
            khoroji["paired_vs_sp"][siasat] = {
                key: ci([runs[s][key] - per["sp"][s][key] for s in moshtarak
                         if runs[s][key] is not None and per["sp"][s][key] is not None])
                for key in ("admission", "admission_avoidable", "admission_unavoidable")}
    os.makedirs(os.path.dirname(KHOROOJI), exist_ok=True)
    json.dump(khoroji, open(KHOROOJI, "w"), indent=1)
    for siasat in LISTE_SIASATHA:
        a = khoroji["attack"].get(siasat)
        if a:
            d = khoroji["paired_vs_sp"].get(siasat, {})
            print(f"{siasat:11} n={a['n']:2} all={a['admission']} avoid={a['admission_avoidable']} "
                  f"other={a['admission_unavoidable']} via_core={a['via_core_avoidable']} "
                  f"| vs SP all={d.get('admission')}")


if __name__ == "__main__":
    main()
