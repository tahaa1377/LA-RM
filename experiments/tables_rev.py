import json

P = ["sp", "ecmp", "urm", "larm", "greedy", "sp_retry", "larm_retry"]
R = "results_rev"


L2 = {"base_abilene_full": "l2_abilene", "base_geant2012_0_1100": "l2_geant2012",
      "base_geant_sndlib_full": "l2_geant_sndlib"}


def adm(f, b):
    d = json.load(open(f"{R}/{f}.json"))["policies"]
    a = {p: d[p][str(b)]["admission"] for p in P if p in d and str(b) in d[p]}
    l2 = json.load(open(f"results_rev4/{L2.get(f, f.replace('base_', 'l2_'))}.json"))["policies"]
    a["larm2"] = l2["larm2"][str(b)]["admission"]
    return a


RADIFHA = [
    ("Fat-tree ($k{=}4$)", None, None, None),
    (None, "static", "base_fattree4_static", 900),
    (None, "adaptive", "base_fattree4", 900),
    (None, "aware", "base_fattree4_aware", 900),
    (None, "smart", "base_fattree4_smart", 900),
    (None, "static", "base_fattree4_static", 1300),
    (None, "adaptive", "base_fattree4", 1300),
    (None, "aware", "base_fattree4_aware", 1300),
    (None, "smart", "base_fattree4_smart", 1300),
    ("Abilene", None, None, None),
    (None, "static", "base_abilene_static", 600),
    (None, "adaptive", "base_abilene", 600),
    (None, "aware", "base_abilene_aware", 600),
    (None, "smart", "base_abilene_smart", 600),
    (None, "adaptive", "base_abilene", 800),
    (None, "adaptive", "base_abilene_full", 1100),
    ("GEANT2012", None, None, None),
    (None, "single$^\\ast$", "base_geant2012", 600),
    (None, "smart", "base_geant2012_smart", 600),
    (None, "single$^\\ast$", "base_geant2012", 800),
    (None, "single$^\\ast$", "base_geant2012_0_1100", 1100),
    ("Abilene 2004, measured matrices", None, None, None),
    (None, "adaptive", "base_abilene_sndlib", 600),
    (None, "adaptive", "base_abilene_sndlib", 800),
    ("GEANT 2005, measured matrices", None, None, None),
    (None, "adaptive", "base_geant_sndlib", 600),
    (None, "adaptive", "base_geant_sndlib", 800),
    (None, "adaptive", "base_geant_sndlib_full", 1100),
]


def fmt(x):
    v = 100 * x
    return "100" if round(v, 1) >= 100 else f"{v:.1f}"


def main():
    maxci = {"occ_syn": 0, "other_syn": 0, "meas": 0}
    for goroh, name_mokhalef, f, b in RADIFHA:
        if goroh:
            print("\\multicolumn{10}{@{}l}{\\emph{%s}}\\\\" % goroh)
            continue
        a = adm(f, b)
        behtarin = max(round(100 * a[p][0], 1) for p in P + ["larm2"])
        selha = []
        for p in P + ["larm2"]:
            s = fmt(a[p][0])
            selha.append(f"\\textbf{{{s}}}" if round(100 * a[p][0], 1) == behtarin else s)
            ci = 100 * a[p][1]
            if "sndlib" in f:
                maxci["meas"] = max(maxci["meas"], ci)
            elif p in ("greedy", "sp_retry", "larm_retry", "larm2"):
                maxci["occ_syn"] = max(maxci["occ_syn"], ci)
            else:
                maxci["other_syn"] = max(maxci["other_syn"], ci)
        print(f"{name_mokhalef:13} & {b:<4} & " + " & ".join(selha) + " \\\\")
    print("% max 95% CI half-widths (points):", {k: round(v, 1) for k, v in maxci.items()})


if __name__ == "__main__":
    main()
