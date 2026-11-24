import glob
import json
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, ".")
from larm.instances import seed_instance
from larm import Sim

GARMKARDAN, UFOGH, HADDE_KESHIDEGI = 20, 110, 2.5
HADDE_AKSARE_OD = {"uscarrier": 1500, "cogentco": 1500}
FILEHA = ["results_rev*/*.json"]
_NEMOONEHA = {}


def _nemoone(topolozhi, tokhm):
    kelid = (topolozhi, tokhm)
    if kelid not in _NEMOONEHA:
        _NEMOONEHA[kelid] = seed_instance(topolozhi, tokhm, max_ods=HADDE_AKSARE_OD.get(topolozhi))
    return _NEMOONEHA[kelid]


def _yek(kar):
    topolozhi, harif, kandid, nerkh, zarfiat, siasat, bodje, tokhm = kar
    G, taghaza, f = _nemoone(topolozhi, tokhm)
    s = Sim(G, taghaza, siasat, zarfiat=zarfiat, maghyase_nerkh=nerkh * f, ofogh=UFOGH, garmkardan=GARMKARDAN,
            tokhm=tokhm, hadde_aksare_keshidegi=HADDE_KESHIDEGI, hamlegar=harif if bodje else "none",
            ghavanine_hamle=bodje, halate_kandid=kandid)
    return kar, round(s.run()["admission"], 4)


def main():
    tedade_tokhm = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    karha, entezar = [], {}
    for olgoo in FILEHA:
        for masir in sorted(glob.glob(olgoo)):
            d = json.load(open(masir))
            if "policies" not in d or "topo" not in d:
                continue
            topolozhi = d["topo"]
            for siasat, r in d["policies"].items():
                for bodje, v in r.items():
                    if not isinstance(v, dict) or "adm_runs" not in v:
                        continue
                    for tokhm in range(min(tedade_tokhm, len(v["adm_runs"]))):
                        kar = (topolozhi, d.get("adversary", "adaptive"), d.get("candidates", "yen"),
                               float(d.get("lam", 40)), int(d.get("cap", 1000)), siasat, int(bodje), tokhm)
                        karha.append(kar)
                        entezar.setdefault(kar, []).append((masir, v["adm_runs"][tokhm]))
    karha = sorted(set(karha), key=lambda k: (k[0], k[7]))
    with Pool(int(os.environ.get("LARM_PROCS", "2"))) as pool:
        natije = dict(pool.map(_yek, karha, chunksize=4))
    yeksan = motefavet = 0
    for kar, lst in entezar.items():
        for masir, meghdar in lst:
            if natije[kar] == meghdar:
                yeksan += 1
            else:
                motefavet += 1
                print("MISMATCH", masir, kar, natije[kar], meghdar)
    print("runs %d, stored values %d, identical %d, different %d" % (len(karha), yeksan + motefavet, yeksan, motefavet))


if __name__ == "__main__":
    main()
