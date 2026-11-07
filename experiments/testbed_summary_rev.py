"""Summarise the second testbed series (all seven policies under attack, runs_rev/)
into results_rev/testbed_rev.json, with paired differences against shortest path.

Usage: python experiments/testbed_summary_rev.py [runs_dir] [out.json]
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testbed_summary import attack_run, ci, BINS, LATE  # noqa: E402

RUNS = sys.argv[1] if len(sys.argv) > 1 else "runs_rev"
OUT = sys.argv[2] if len(sys.argv) > 2 else "results_rev/testbed_rev.json"
POLS = ["sp", "ecmp", "urm", "larm", "greedy", "sp_retry", "larm_retry"]
KEYS = ["admission", "admission_avoidable", "admission_unavoidable", "admission_avoidable_late",
        "via_core_avoidable", "via_core_avoidable_late", "busiest"]


def main():
    per = {}
    for pol in POLS:
        for p in sorted(glob.glob(os.path.join(RUNS, f"atk_{pol}_s*.json"))):
            seed = int(re.search(r"_s(\d+)\.json$", p).group(1))
            try:
                per.setdefault(pol, {})[seed] = attack_run(p)
            except (KeyError, ValueError, json.JSONDecodeError):
                pass
    out = {"bins": BINS, "late": LATE, "attack": {}, "paired_vs_sp": {}}
    for pol, runs in per.items():
        rs = [runs[s] for s in sorted(runs)]
        agg = {"n": len(rs), "seeds": sorted(runs)}
        for key in KEYS:
            agg[key] = ci([r[key] for r in rs])
        agg["admission_avoidable_bins"] = [ci([r["admission_avoidable_bins"][i] for r in rs])
                                           for i in range(len(BINS))]
        out["attack"][pol] = agg
    if "sp" in per:
        for pol, runs in per.items():
            common = sorted(set(runs) & set(per["sp"]))
            out["paired_vs_sp"][pol] = {
                key: ci([runs[s][key] - per["sp"][s][key] for s in common
                         if runs[s][key] is not None and per["sp"][s][key] is not None])
                for key in ("admission", "admission_avoidable", "admission_unavoidable")}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    for pol in POLS:
        a = out["attack"].get(pol)
        if a:
            d = out["paired_vs_sp"].get(pol, {})
            print(f"{pol:11} n={a['n']:2} all={a['admission']} avoid={a['admission_avoidable']} "
                  f"other={a['admission_unavoidable']} via_core={a['via_core_avoidable']} "
                  f"| vs SP all={d.get('admission')}")


if __name__ == "__main__":
    main()
