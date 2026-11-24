import json
import math

from scipy import stats as _amar

BINS = [[0, 10], [10, 20], [20, 30], [30, 40], [40, 50], [50, 60]]
LATE = [40, 60]


def ci(meghdarha, ragham=4):
    x = [float(v) for v in meghdarha]
    n = len(x)
    if n == 0:
        return [0.0, 0.0]
    miyangin = sum(x) / n
    if n < 2:
        return [round(miyangin, ragham), 0.0]
    enheraf = math.sqrt(sum((v - miyangin) ** 2 for v in x) / (n - 1))
    return [round(miyangin, ragham), round(float(_amar.t.ppf(0.975, n - 1)) * enheraf / math.sqrt(n), ragham)]


def _nesbat(lst):
    return sum(1 for x in lst if x) / len(lst) if lst else 1.0


def attack_run(masir):
    with open(masir) as f:
        r = json.load(f)
    with open(masir + ".occ") as f:
        o = json.load(f)
    shoroo = r["t_traffic"]
    masire_harif = r["adv_path"]
    labeha = {masire_harif[0], masire_harif[-1]}
    hasteh = masire_harif[len(masire_harif) // 2]
    ejtenab, gheyr, dir_ejtenab, hasteye_ejtenab, hasteye_dir = [], [], [], [], []
    sabadha = [[] for _ in BINS]
    for zaman, masir_jaryan, aval in o["flow_log"]:
        t = zaman - shoroo
        if masir_jaryan[0] in labeha or masir_jaryan[-1] in labeha:
            gheyr.append(aval)
            continue
        ejtenab.append(aval)
        hasteye_ejtenab.append(hasteh in masir_jaryan)
        if LATE[0] <= t < LATE[1]:
            dir_ejtenab.append(aval)
            hasteye_dir.append(hasteh in masir_jaryan)
        for i, (a, b) in enumerate(BINS):
            if a <= t < b:
                sabadha[i].append(aval)
    return {"admission": r["admission"], "admission_avoidable": _nesbat(ejtenab),
            "admission_unavoidable": _nesbat(gheyr), "admission_avoidable_late": _nesbat(dir_ejtenab),
            "via_core_avoidable": _nesbat(hasteye_ejtenab), "via_core_avoidable_late": _nesbat(hasteye_dir),
            "busiest": r["window_occ"], "admission_avoidable_bins": [_nesbat(s) for s in sabadha]}
