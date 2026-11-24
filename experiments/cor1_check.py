import json
import math
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim, Policy

GARMKARDAN, ZAMANE_HAMLE, SS0 = 20, 150, 60
C, HADDE_KESHIDEGI = 1000, 2.5
HALATHA = {"abilene": (40, [300, 400, 450, 500, 550, 600, 700, 800, 900, 1000]),
         "geant": (40, [300, 400, 450, 500, 550, 600, 700, 800, 900, 1000]),
         "fattree4": (24, [700, 800, 850, 900, 950, 1000])}
TOKHMHA = 10


def erlang_b(n, a):
    if n <= 0:
        return 1.0
    b = 1.0
    for i in range(1, int(n) + 1):
        b = a * b / (i + a * b)
    return b


def one(args):
    topolozhi, nerkh, A, tokhm = args
    G, taghaza, fac = seed_instance(topolozhi, tokhm)
    s = Sim(G, taghaza, Policy.SP, zarfiat=C, maghyase_nerkh=nerkh * fac, ofogh=GARMKARDAN + ZAMANE_HAMLE, garmkardan=GARMKARDAN,
            tokhm=tokhm, hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar="static", ghavanine_hamle=A)
    v = s._fixed_target()
    L = s.dur_median * math.exp(s.dur_sigma ** 2 / 2) + s.idle
    Lam = sum(s.lam.values())
    B = L * sum(s.lam[od] for od in s.ods if v in s.sp_path[od])
    share = B / (Lam * L)
    s.run()
    tr = s.ol_trace[GARMKARDAN:]
    off90, lost90 = sum(o for o, _ in tr[:90]), sum(l for _, l in tr[:90])
    offss, lostss = sum(o for o, _ in tr[SS0:]), sum(l for _, l in tr[SS0:])
    if A < C:
        fluid = 1.0 - max(0.0, A - (C - B)) / (Lam * L)
        erl = 1.0 - share * erlang_b(C - A, B)
    else:
        fluid = erl = 1.0 - share
    return {"topo": topolozhi, "A": A, "seed": tokhm, "target": str(v), "L": L, "Lambda": Lam,
            "B": B, "s": share, "fluid": fluid, "erlang": erl,
            "sim90": 1.0 - lost90 / off90, "sim_ss": 1.0 - lostss / offss}


def main():
    khoroji = sys.argv[1] if len(sys.argv) > 1 else "results_rev/cor1_check.json"
    karha = [(t, nerkh, A, sd) for t, (nerkh, bodjeha) in HALATHA.items() for A in bodjeha
            for sd in range(TOKHMHA)]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 2) as estakhr:
        radifha = estakhr.map(one, karha)
    kholase = {}
    for t, (nerkh, bodjeha) in HALATHA.items():
        kholase[t] = []
        for A in bodjeha:
            r = [x for x in radifha if x["topo"] == t and x["A"] == A]
            m = {k: float(np.mean([x[k] for x in r])) for k in ("B", "s", "fluid", "erlang", "sim90", "sim_ss")}
            m["A"] = A
            m["targets"] = sorted(set(x["target"] for x in r))
            kholase[t].append(m)
            print(f"{t:9} A={A:5} B={m['B']:6.1f} s={m['s']:.3f} fluid={m['fluid']:.3f} "
                  f"erlang={m['erlang']:.3f} sim_ss={m['sim_ss']:.3f} sim90={m['sim90']:.3f}")
    json.dump({"rows": radifha, "summary": kholase, "C": C, "warmup": GARMKARDAN, "attack_epochs": ZAMANE_HAMLE,
               "steady_from": SS0}, open(khoroji, "w"), indent=1)


if __name__ == "__main__":
    main()
