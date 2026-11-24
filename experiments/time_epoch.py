import statistics
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim


def med_ms(fn, tekrarha):
    v = []
    for _ in range(tekrarha):
        t0 = time.perf_counter()
        fn()
        v.append(1e3 * (time.perf_counter() - t0))
    return statistics.median(v), min(v), max(v)


def main():
    tekrarha = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    G, taghaza, f = seed_instance("geant", 0)
    for siasat in ("larm", "larm2"):
        s = Sim(G, taghaza, siasat, zarfiat=1000, maghyase_nerkh=40 * f, ofogh=60, garmkardan=20, tokhm=0,
                hadde_aksare_keshidegi=2.5, hamlegar="adaptive", ghavanine_hamle=600)
        s.run()
        nauto = sum(1 for od in s.ods if s.auto[od].r > 1)
        jaryanha = float(np.mean([o for o, _ in s.ol_trace]))

        def upd():
            for od in s.ods:
                s.auto[od].update()

        print(f"{siasat}: {len(s.ods)} pairs, {nauto} automata with more than one candidate, "
              f"{jaryanha:.0f} benign flows per epoch")
        print("  update of all automata: median %.1f ms (min %.1f, max %.1f)" % med_ms(upd, tekrarha))
        if siasat == "larm2":
            def both():
                s._credit_full()
                upd()
            print("  scoring of all candidates: median %.1f ms (min %.1f, max %.1f)"
                  % med_ms(s._credit_full, tekrarha))
            print("  whole step: median %.1f ms (min %.1f, max %.1f)" % med_ms(both, tekrarha))
        else:
            rng = np.random.default_rng(0)
            ods = [s.ods[i] for i in rng.integers(len(s.ods), size=int(round(jaryanha)))]

            def credit():
                load = {n: len(s.table[n]) / s.cap[n] for n in s.nodes}
                for od in ods:
                    masir = s.pt.cand[od][0]
                    st = s.pt.stretch(od, masir)
                    dagh = max(load[n] for n in masir)
                    s.auto[od].credit(0, max(0.0, 1.0 - dagh - s.stretch_pen * (st - 1.0)))

            def both():
                credit()
                upd()
            print("  credit for the epoch's flows: median %.2f ms (min %.2f, max %.2f)"
                  % med_ms(credit, tekrarha))
            print("  whole step: median %.1f ms (min %.1f, max %.1f)" % med_ms(both, tekrarha))
        state = sum(a.p.nbytes + a.S.nbytes + a.W.nbytes for a in s.auto.values())
        print(f"  state: three vectors per pair, {state / 1e3:.0f} kB in all")


if __name__ == "__main__":
    main()
