import argparse
import csv
import datetime
import gzip
import json
import os
import re
import statistics
import sys
import xml.etree.ElementTree as ET

import numpy as np

RISHE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FASELE = {"abilene": 5, "geant": 15}
TEDADE_ROOZ = 10


def _baz(masir):
    return gzip.open(masir, "rt") if masir.endswith(".gz") else open(masir)


def khandane_csv(masir):
    matrisha = {}
    with _baz(masir) as f:
        r = csv.reader(f)
        sar = next(r)
        joftha = [tuple(h.split("_")) for h in sar[1:]]
        for khat in r:
            zaman = datetime.datetime.strptime(khat[0], "%Y%m%d-%H%M")
            matrisha[zaman] = np.array([float(x) for x in khat[1:]])
    return joftha, matrisha


def _tag(e):
    return e.tag.rsplit("}", 1)[-1]


def _xml_yek(masir):
    meghdar = {}
    for e in ET.parse(masir).getroot().iter():
        if _tag(e) != "demand":
            continue
        bache = {_tag(c): (c.text or "").strip() for c in e}
        meghdar[(bache["source"], bache["target"])] = float(bache.get("demandValue") or 0.0)
    return meghdar


def khandane_xml(pooshe):
    kham = {}
    for nam in sorted(os.listdir(pooshe)):
        m = re.search(r"(\d{8})-(\d{4})\.xml$", nam)
        if m:
            kham[datetime.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M")] = _xml_yek(os.path.join(pooshe, nam))
    gereha = sorted({g for mat in kham.values() for jo in mat for g in jo})
    joftha = [(a, b) for a in gereha for b in gereha if a != b]
    matrisha = {z: np.array([mat.get(jo, 0.0) for jo in joftha]) for z, mat in kham.items()}
    return joftha, matrisha


def khandan(manba):
    return khandane_xml(manba) if os.path.isdir(manba) else khandane_csv(manba)


def entekhabe_rooz(matrisha, fasele):
    rooz = {}
    for zaman, v in matrisha.items():
        rooz.setdefault(zaman.date(), []).append((zaman, v))
    dar_rooz = 24 * 60 // fasele
    mojaz = []
    for d, lst in sorted(rooz.items()):
        if d.weekday() >= 5:
            continue
        majmooha = [float(v.sum()) for _, v in lst]
        porha = [x for x in majmooha if x > 0]
        if len(porha) < 0.9 * dar_rooz:
            continue
        if max(majmooha) > 10 * statistics.median(porha):
            continue
        mojaz.append(d)
    if len(mojaz) < TEDADE_ROOZ:
        sys.exit("too few eligible days: %d" % len(mojaz))
    entekhab = [mojaz[round(i * (len(mojaz) - 1) / (TEDADE_ROOZ - 1))] for i in range(TEDADE_ROOZ)]
    return entekhab, rooz


def aks(lst, joftha, fasele):
    dar_saat = 60 // fasele
    saatha = {}
    for zaman, v in sorted(lst, key=lambda x: x[0]):
        saatha.setdefault(zaman.hour, []).append(v)
    kamel = {h: vs for h, vs in saatha.items() if len(vs) == dar_saat}
    majmoo = {h: float(sum(v.sum() for v in vs)) for h, vs in kamel.items()}
    shoolugh = max(majmoo, key=majmoo.get)
    khalvat = min(majmoo, key=majmoo.get)

    def matris(h):
        M = np.mean(kamel[h], axis=0)
        return [[joftha[i][0], joftha[i][1], float(M[i])] for i in range(len(joftha))
                if M[i] > 0 and joftha[i][0] != joftha[i][1]]

    return {"busy_hour": shoolugh, "busy_total": majmoo[shoolugh] / dar_saat, "busy": matris(shoolugh),
            "quiet_hour": khalvat, "quiet_total": majmoo[khalvat] / dar_saat, "quiet": matris(khalvat)}


def sakhtane_aksha(shabake, manba):
    fasele = FASELE[shabake]
    joftha, matrisha = khandan(manba)
    entekhab, rooz = entekhabe_rooz(matrisha, fasele)
    roozha = []
    for d in entekhab:
        r = {"day": str(d)}
        r.update(aks(rooz[d], joftha, fasele))
        roozha.append(r)
    return {"network": shabake, "interval_minutes": fasele, "source": os.path.basename(os.path.normpath(manba)),
            "days": roozha}


def neveshtane_topo(shabake, khoroji):
    import topohub
    masir = os.path.join(os.path.dirname(topohub.__file__), "data", "sndlib", shabake + ".json")
    with open(masir) as f:
        t = json.load(f)
    namha = [g["name"] for g in t["nodes"]]
    with open(os.path.join(khoroji, shabake + ".topo"), "w") as f:
        f.write("NODES %d\n" % len(namha))
        for nam in namha:
            f.write(nam + "\n")
        f.write("LINKS %d\n" % len(t["edges"]))
        for e in t["edges"]:
            f.write("%s %s\n" % (namha[e["source"]], namha[e["target"]]))


def barresi_xml(manba, pooshe):
    joftha, matrisha = khandane_csv(manba)
    jx, mx = khandane_xml(pooshe)
    andis = {jo: i for i, jo in enumerate(joftha)}
    tedad, bishtarin = 0, 0.0
    for zaman, v in mx.items():
        if zaman not in matrisha:
            continue
        for i, jo in enumerate(jx):
            if jo in andis:
                bishtarin = max(bishtarin, abs(v[i] - matrisha[zaman][andis[jo]]))
        tedad += 1
    print("compared %d matrices, largest difference %.6g Mbit/s" % (tedad, bishtarin))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("network", choices=sorted(FASELE))
    ap.add_argument("source")
    ap.add_argument("--out", default=os.path.join(RISHE, "data", "sndlib"))
    ap.add_argument("--verify-xml", dest="verify_xml")
    ap.add_argument("--topo", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if args.verify_xml:
        barresi_xml(args.source, args.verify_xml)
        return
    if args.topo:
        neveshtane_topo(args.network, args.out)
    natije = sakhtane_aksha(args.network, args.source)
    with open(os.path.join(args.out, args.network + "_snapshots.json"), "w") as f:
        json.dump(natije, f)
    for r in natije["days"]:
        print(r["day"], "busy %02d:00" % r["busy_hour"], len(r["busy"]), "pairs")


if __name__ == "__main__":
    main()
