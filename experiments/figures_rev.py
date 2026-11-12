import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

plt.rcParams.update({
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "DejaVu Sans"],
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.edgecolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e",
    "axes.labelcolor": "#0b0b0b", "text.color": "#0b0b0b",
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 300, "pdf.compression": 9,
    "mathtext.fontset": "custom", "mathtext.rm": "Liberation Sans",
    "mathtext.it": "Liberation Sans:italic", "mathtext.bf": "Liberation Sans:bold",
    "mathtext.cal": "Liberation Sans:italic", "mathtext.sf": "Liberation Sans",
})
FARADADE_KHALI = {"Creator": "", "Producer": "", "Title": "", "Author": "",
              "Subject": "", "Keywords": ""}

MOSHAKHASATE_SIASAT = {
    "sp": ("Shortest path", "#2a78d6", "o", (0, (4, 2))),
    "ecmp": ("ECMP", "#eb6834", "s", (0, (4, 2))),
    "urm": ("Uniform mutation", "#1baf7a", "^", (0, (4, 2))),
    "larm": ("LA-RM", "#eda100", "D", (0, (6, 2, 1.5, 2))),
    "greedy": ("Greedy", "#e87ba4", "v", "-"),
    "sp_retry": ("SP + retry", "#008300", "P", "-"),
    "larm_retry": ("LA-RM + retry", "#6250d6", "X", "-"),
    "larm2": ("LA-RM2", "#b3261e", "*", "-"),
    "larm2_nr": ("LA-RM2, no retry", "#b3261e", "*", (0, (4, 2))),
}
TARTIB = ["sp", "ecmp", "urm", "larm", "greedy", "sp_retry", "larm_retry"]
TARTIB8 = TARTIB + ["larm2"]
KOTAH = {"sp": "SP", "ecmp": "ECMP", "urm": "URM", "larm": "LA-RM", "greedy": "Greedy",
         "sp_retry": "SP+R", "larm_retry": "LA-RM+R", "larm2": "LA-RM2",
         "larm2_nr": "LA-RM2, no retry"}
R4 = "results_rev4"
RANGE_SHABAKE = "#e4e3df"


def load(masir):
    with open(masir) as f:
        return json.load(f)


def curve_new(masirha, siasat):
    pts = {}
    for p in masirha:
        if not os.path.exists(p):
            continue
        d = load(p)
        if siasat not in d["policies"]:
            continue
        for b, v in d["policies"][siasat].items():
            pts[int(b)] = tuple(v["admission"])
    return pts


def curve_main(masir, siasat):
    d = load(masir)
    return {int(b): tuple(v) for b, v in d["policies"][siasat]["adm_curve"].items()}


def style_axes(ax):
    ax.grid(True, axis="y", color=RANGE_SHABAKE, linewidth=0.5)
    ax.set_axisbelow(True)


def plot_series(ax, pts, siasat, zarfiat=1000.0, ms=3.6):
    bargasb, sotoon, mk, ls = MOSHAKHASATE_SIASAT[siasat]
    xs = sorted(pts)
    x = [b / zarfiat for b in xs]
    y = [pts[b][0] for b in xs]
    e = [pts[b][1] for b in xs]
    ax.errorbar(x, y, yerr=e, color=sotoon, marker=mk, ms=ms + 1.6 if mk == "*" else ms, lw=1.1, ls=ls,
                elinewidth=0.6, capsize=1.5, markeredgewidth=0.5,
                markeredgecolor="white", label=bargasb, zorder=4 if siasat == "larm2" else 3 if ls == "-" else 2)


def legend_handles(siasatha, short=False):
    hs = []
    for p in siasatha:
        bargasb, sotoon, mk, ls = MOSHAKHASATE_SIASAT[p]
        hs.append(Line2D([0], [0], color=sotoon, marker=mk, ls=ls, lw=1.1, ms=5 if mk == "*" else 4,
                         markeredgecolor="white", markeredgewidth=0.5,
                         label=KOTAH[p] if short else bargasb))
    return hs


def fig_admission(risheh, khoroji):
    R, M = f"{risheh}/results_rev", f"{risheh}/results"
    panels = [
        ("Fat-tree ($k$=4)", f"{M}/main_fattree4.json",
         [f"{R}/base_fattree4.json", f"{R}/curve_fattree4.json"], f"{risheh}/{R4}/l2_fattree4.json"),
        ("Abilene", f"{M}/main_abilene.json",
         [f"{R}/base_abilene.json", f"{R}/base_abilene_full.json", f"{R}/curve_abilene.json"],
         f"{risheh}/{R4}/l2_abilene.json"),
        ("GEANT2012", f"{M}/main_geant.json",
         [f"{R}/base_geant2012.json", f"{R}/base_geant2012_0_1100.json",
          f"{R}/curve_geant2012.json"], f"{risheh}/{R4}/l2_geant2012.json"),
    ]
    fig, axs = plt.subplots(1, 3, figsize=(7.16, 1.95), sharey=True)
    for ax, (title, mainf, newfs, l2f) in zip(axs, panels):
        for siasat in TARTIB8:
            if siasat == "larm2":
                pts = curve_new([l2f], siasat)
            else:
                pts = curve_main(mainf, siasat) if siasat in ("sp", "ecmp", "urm", "larm") \
                    else curve_new(newfs, siasat)
            plot_series(ax, pts, siasat)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Adversary budget (tables)")
        ax.set_ylim(0.3, 1.02)
        style_axes(ax)
    axs[0].set_ylabel("Benign admission")
    fig.legend(handles=legend_handles(TARTIB8, short=True), loc="upper center", ncol=8, frameon=False,
               bbox_to_anchor=(0.5, 1.02), handlelength=2.6, columnspacing=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.9), w_pad=0.8)
    fig.savefig(f"{khoroji}/fig_admission.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_admtrace(risheh, khoroji):
    d = load(f"{risheh}/results/admtrace_heavy.json")
    fig, axs = plt.subplots(1, 2, figsize=(3.5, 1.9), sharey=True)
    for ax, topolozhi, title in zip(axs, ("fattree4", "abilene"), ("Fat-tree, 1300 rules", "Abilene, 800 rules")):
        for siasat in ("sp", "ecmp", "urm", "larm"):
            y = d[topolozhi][siasat]
            bargasb, sotoon, mk, ls = MOSHAKHASATE_SIASAT[siasat]
            ax.plot(range(len(y)), y, color=sotoon, lw=0.9, ls=ls, label=bargasb)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Epochs since attack start")
        ax.set_ylim(0.3, 1.02)
        style_axes(ax)
    axs[0].set_ylabel("Benign admission")
    fig.legend(handles=[Line2D([0], [0], color=MOSHAKHASATE_SIASAT[p][1], ls=MOSHAKHASATE_SIASAT[p][3], lw=1.0, label=MOSHAKHASATE_SIASAT[p][0])
                        for p in ("sp", "ecmp", "urm", "larm")],
               loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.03),
               handlelength=2.2, columnspacing=0.8, fontsize=6.8)
    fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=0.6)
    fig.savefig(f"{khoroji}/fig_admtrace.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_evict(risheh, khoroji):
    radifha = [("sp", "Shortest path\n(re-install)"), ("evict_static", "Evict oldest\n(aging)"),
            ("evict_refresh", "Evict oldest\n(re-install)"), ("larm", "LA-RM\n(re-install)")]
    fig, axs = plt.subplots(1, 2, figsize=(7.16, 1.9))
    sotoonha = ["#2a78d6", "#eb6834"]
    for ax, key, ylab in zip(axs, ("admission", "churn"),
                             ("Benign admission", "Benign rules evicted per flow")):
        for j, topolozhi in enumerate(("fattree4", "abilene")):
            d = load(f"{risheh}/results/evict_{topolozhi}.json")["rows"]
            xs = [i + (j - 0.5) * 0.36 for i in range(len(radifha))]
            ys = [d[r][key][0] for r, _ in radifha]
            es = [d[r][key][1] for r, _ in radifha]
            ax.bar(xs, ys, width=0.34, yerr=es, color=sotoonha[j], edgecolor="white", linewidth=0.8,
                   error_kw={"elinewidth": 0.6, "capsize": 1.5},
                   label="Fat-tree, 1300 rules" if topolozhi == "fattree4" else "Abilene, 800 rules")
        ax.set_xticks(range(len(radifha)))
        ax.set_xticklabels([bargasb for _, bargasb in radifha], fontsize=7)
        ax.set_ylabel(ylab)
        style_axes(ax)
    axs[0].set_ylim(0, 1.15)
    axs[0].legend(frameon=False, fontsize=7, loc="upper left", ncol=2)
    fig.tight_layout(w_pad=1.2)
    fig.savefig(f"{khoroji}/fig_evict.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_attack(risheh, khoroji):
    series = [("First series", f"{risheh}/results/testbed.json", ("sp", "ecmp", "urm", "larm"))]
    rev = f"{risheh}/{R4}/testbed_rev.json"
    if not os.path.exists(rev):
        rev = f"{risheh}/results_rev/testbed_rev.json"
    if os.path.exists(rev):
        series.append(("Second series", rev, TARTIB8))
    fig, axs = plt.subplots(1, len(series), figsize=(3.5 * len(series), 2.0), sharey=True,
                            squeeze=False)
    for ax, (title, masir, siasatha) in zip(axs[0], series):
        d = load(masir)
        x = [(a + b) / 2 for a, b in d["bins"]]
        for siasat in siasatha:
            if siasat not in d["attack"]:
                continue
            v = d["attack"][siasat]["admission_avoidable_bins"]
            bargasb, sotoon, mk, ls = MOSHAKHASATE_SIASAT[siasat]
            ax.errorbar(x, [p[0] for p in v], yerr=[p[1] for p in v], color=sotoon, marker=mk,
                        ms=5.0 if mk == "*" else 3.4, lw=1.0, ls=ls, elinewidth=0.6, capsize=1.5,
                        markeredgecolor="white", markeredgewidth=0.5, label=bargasb)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Time since benign workload start (s)")
        ax.set_ylim(0.6, 1.02)
        style_axes(ax)
    axs[0][0].set_ylabel("Admission, avoidable flows")
    if len(series) > 1:
        fig.legend(handles=legend_handles(TARTIB8, short=True), loc="upper center", ncol=8, frameon=False,
                   bbox_to_anchor=(0.5, 1.03), handlelength=2.4, columnspacing=1.0, fontsize=7)
        fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=0.8)
    else:
        axs[0][0].legend(frameon=False, ncol=2, fontsize=6.8, loc="lower right")
        fig.tight_layout()
    fig.savefig(f"{khoroji}/fig_attack.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_learn(risheh, khoroji):
    d = load(f"{risheh}/results/learn_curve.json")
    P = d["p"]
    tgt_idx = d["cross"][0]
    fig, ax = plt.subplots(figsize=(3.5, 1.8))
    sotoonha = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
    lss = ["-", (0, (4, 2)), (0, (1.5, 1.5)), (0, (6, 2, 1.5, 2))]
    for i in range(len(P[0])):
        bargasb = "path through the attacked core" if i == tgt_idx else f"clear path {i + 1 - (i > tgt_idx)}"
        ax.plot(range(len(P)), [p[i] for p in P], color=sotoonha[i], ls=lss[i], lw=1.1, label=bargasb)
    ax.set_xlabel("Epoch (attack from epoch 0)")
    ax.set_ylabel("Probability before mixing")
    ax.set_ylim(0, 1.0)
    style_axes(ax)
    ax.legend(frameon=False, fontsize=6.5, loc="center right")
    fig.tight_layout()
    fig.savefig(f"{khoroji}/fig_learn.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_kfloor(risheh, khoroji):
    d = load(f"{risheh}/results/kfloor.json")
    fig, ax = plt.subplots(figsize=(3.5, 1.8))
    sotoonha = ["#2a78d6", "#eb6834", "#1baf7a"]
    mks = ["o", "s", "^"]
    for c, mk, fl in zip(sotoonha, mks, d["floors"]):
        g = d["grid"][str(fl)]
        ks = sorted(int(k) for k in g)
        ax.errorbar(ks, [g[str(k)][0] for k in ks], yerr=[g[str(k)][1] for k in ks], color=c,
                    marker=mk, ms=3.6, lw=1.1, elinewidth=0.6, capsize=1.5,
                    markeredgecolor="white", markeredgewidth=0.5,
                    label=f"floor {fl:g} of ln $k$")
    ax.axhline(62.8, color="#52514e", lw=0.7, ls=":", label="shortest path")
    ax.set_xlabel("Candidate paths $k$")
    ax.set_ylabel("Benign admission (%)")
    ax.set_xticks([2, 3, 4, 6, 8, 12])
    ax.set_ylim(40, 84)
    style_axes(ax)
    ax.legend(frameon=False, fontsize=6.5, loc="lower right", ncol=2)
    fig.tight_layout()
    fig.savefig(f"{khoroji}/fig_kfloor.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_measured(risheh, khoroji):
    R, M = f"{risheh}/results_rev", f"{risheh}/results"
    panels = [
        ("Abilene 2004, measured", f"{M}/main_abilene_sndlib.json",
         [f"{R}/base_abilene_sndlib.json", f"{R}/curve_abilene_sndlib.json"],
         f"{risheh}/{R4}/l2_abilene_sndlib.json"),
        ("GEANT 2005, measured", f"{M}/main_geant_sndlib.json",
         [f"{R}/base_geant_sndlib.json", f"{R}/base_geant_sndlib_full.json",
          f"{R}/curve_geant_sndlib.json"], f"{risheh}/{R4}/l2_geant_sndlib.json"),
    ]
    fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.15), sharey=True)
    for ax, (title, mainf, newfs, l2f) in zip(axs, panels):
        for siasat in TARTIB8:
            if siasat == "larm2":
                pts = curve_new([l2f], siasat)
            else:
                pts = curve_main(mainf, siasat) if siasat in ("sp", "ecmp", "urm", "larm") \
                    else curve_new(newfs, siasat)
            plot_series(ax, pts, siasat)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Adversary budget (tables)")
        ax.set_ylim(0.3, 1.02)
        style_axes(ax)
    axs[0].set_ylabel("Benign admission")
    fig.legend(handles=legend_handles(TARTIB8, short=True), loc="upper center", ncol=8, frameon=False,
               bbox_to_anchor=(0.5, 1.02), handlelength=2.6, columnspacing=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.9), w_pad=0.8)
    fig.savefig(f"{khoroji}/fig_measured.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_control(risheh, khoroji):
    majmooeha = [("fattree4", "Fat-tree\n1300"), ("abilene", "Abilene\n800"),
            ("abilene_sndlib", "Abilene 2004\n800"), ("geant_sndlib", "GEANT 2005\n800")]
    kelidha = [("larm", "LA-RM", "#eda100"), ("noise", "LA-RM, random rewards", "#8a8984"),
            ("urm", "Uniform mutation", "#1baf7a")]
    fig, ax = plt.subplots(figsize=(3.5, 1.9))
    for j, (key, bargasb, sotoon) in enumerate(kelidha):
        xs, ys, es = [], [], []
        for i, (topolozhi, _) in enumerate(majmooeha):
            p = f"{risheh}/results/extra_{topolozhi}.json"
            if not os.path.exists(p):
                continue
            c = load(p)["control"][key]["admission"]
            xs.append(i + (j - 1) * 0.27)
            ys.append(c[0])
            es.append(c[1])
        ax.bar(xs, ys, width=0.25, yerr=es, color=sotoon, edgecolor="white", linewidth=0.8,
               error_kw={"elinewidth": 0.6, "capsize": 1.5}, label=bargasb)
    ax.set_xticks(range(len(majmooeha)))
    ax.set_xticklabels([s for _, s in majmooeha], fontsize=6.5)
    ax.set_ylabel("Benign admission")
    ax.set_ylim(0.4, 0.85)
    style_axes(ax)
    ax.legend(frameon=False, fontsize=6.3, loc="upper right", ncol=1)
    fig.tight_layout()
    fig.savefig(f"{khoroji}/fig_control.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_topo(risheh, khoroji):
    fig, ax = plt.subplots(figsize=(3.5, 1.75))
    hasteh = [(1.5 + 2.0 * i, 3.0) for i in range(4)]
    tajmi = [(0.75 * 0 + i * 1.0 + (i // 2) * 0.6, 2.0) for i in range(8)]
    yal = [(x, 1.0) for x, _ in tajmi]
    miyazban = [(x, 0.25) for x, _ in yal]
    off = (hasteh[-1][0] + hasteh[0][0]) / 2 - (tajmi[-1][0] + tajmi[0][0]) / 2
    tajmi = [(x + off, y) for x, y in tajmi]
    yal = [(x + off, y) for x, y in yal]
    miyazban = [(x + off, y) for x, y in miyazban]
    links = []
    for p in range(4):
        a0, a1 = 2 * p, 2 * p + 1
        for e in (a0, a1):
            for a in (a0, a1):
                links.append((yal[e], tajmi[a]))
        for a_local, a in enumerate((a0, a1)):
            for j in range(2):
                links.append((tajmi[a], hasteh[2 * a_local + j]))
    for e in range(8):
        links.append((miyazban[e], yal[e]))
    for (x0, y0), (x1, y1) in links:
        ax.plot([x0, x1], [y0, y1], color="#c3c2b7", lw=0.6, zorder=1)
    masir = [miyazban[0], yal[0], tajmi[0], hasteh[0], tajmi[4], yal[5], miyazban[5]]
    for (x0, y0), (x1, y1) in zip(masir[:-1], masir[1:]):
        ax.plot([x0, x1], [y0, y1], color="#e34948", lw=1.8, zorder=2)
    def boxes(pts, sotoon, w, h, label=None):
        for x, y in pts:
            ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h, facecolor=sotoon,
                                       edgecolor="#52514e", lw=0.5, zorder=3))
    boxes(hasteh, "#cde2fb", 0.62, 0.32)
    boxes(tajmi, "#cde2fb", 0.56, 0.3)
    boxes(yal, "#cde2fb", 0.56, 0.3)
    for x, y in miyazban:
        ax.add_patch(plt.Circle((x, y), 0.11, facecolor="#ffffff", edgecolor="#52514e",
                                lw=0.5, zorder=3))
    for x, y in [masir[1], masir[2], masir[3], masir[4], masir[5]]:
        ax.text(x, y, "85", ha="center", va="center", fontsize=6.2, zorder=4, color="#0b0b0b")
    for nam, y in (("core", 3.0), ("aggregation", 2.0), ("edge", 1.0), ("hosts", 0.25)):
        ax.text(-0.55, y, nam, ha="right", va="center", fontsize=6.5, color="#52514e")
    ax.text(masir[0][0], masir[0][1] - 0.32, "attacker", ha="center", va="top", fontsize=6.2)
    ax.text(masir[-1][0], masir[-1][1] - 0.32, "sink", ha="center", va="top", fontsize=6.2)
    ax.set_xlim(-2.4, tajmi[-1][0] + 0.6)
    ax.set_ylim(-0.35, 3.35)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout(pad=0.2)
    fig.savefig(f"{khoroji}/fig_topo.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def rowmajor(handles, labels, ncol):
    nrow = -(-len(handles) // ncol)
    tartib = []
    for c in range(ncol):
        for r in range(nrow):
            k = r * ncol + c
            if k < len(handles):
                tartib.append(k)
    return [handles[k] for k in tartib], [labels[k] for k in tartib]


def fig_bound(risheh, khoroji):
    R = f"{risheh}/results_rev"
    un = load(f"{R}/unavoidable.json")
    u_ab = un["abilene"][0]["U_hub"]
    u_ge = un["geant"][0]["U_hub"]
    L2 = f"{risheh}/{R4}"
    gorohha = [
        ("Fat-tree\ncore/aggr.", f"{R}/base_fattree4.json", "1300", 0.0, f"{L2}/l2_fattree4.json"),
        ("Fat-tree\nedge", f"{R}/base_fattree4_aware.json", "1300", 0.25, f"{L2}/l2_fattree4_aware.json"),
        ("Abilene\nhub", f"{R}/base_abilene_full.json", "1100", u_ab, f"{L2}/l2_abilene.json"),
        ("GEANT\nhub", f"{R}/base_geant2012_0_1100.json", "1100", u_ge, f"{L2}/l2_geant2012.json"),
    ]
    div = f"{risheh}/results_rev2/div_geant2012_aware.json"
    if os.path.exists(div):
        u_div = load(f"{risheh}/results_rev2/candidates.json")["geant"]["div"][0]["u_hub"]
        gorohha.append(("GEANT hub,\ndiverse", div, "1100", u_div, f"{L2}/l2_div_geant2012_aware.json"))
    siasatha = ["sp", "larm", "greedy", "sp_retry", "larm_retry", "larm2"]
    fig, ax = plt.subplots(figsize=(3.5, 1.6))
    wbar = 0.13
    for gi, (bargasb, masir, b, u, l2f) in enumerate(gorohha):
        d = dict(load(masir)["policies"])
        d["larm2"] = load(l2f)["policies"]["larm2"]
        for j, siasat in enumerate(siasatha):
            m, e = d[siasat][b]["admission"]
            x = gi + (j - 2.5) * wbar
            ax.bar(x, m, width=wbar * 0.92, yerr=e, color=MOSHAKHASATE_SIASAT[siasat][1], edgecolor="white",
                   linewidth=0.5, error_kw={"elinewidth": 0.5, "capsize": 1.2},
                   label=KOTAH[siasat] if gi == 0 else None, zorder=2)
        ax.plot([gi - 3.1 * wbar, gi + 3.1 * wbar], [1 - u, 1 - u], color="#0b0b0b", lw=1.1,
                ls=(0, (3, 1.5)), zorder=3, label="bound $1-u$" if gi == 0 else None)
    ax.set_xticks(range(len(gorohha)))
    ax.set_xticklabels([g[0] for g in gorohha], fontsize=6.8)
    ax.set_ylabel("Benign admission")
    ax.set_ylim(0, 1.08)
    style_axes(ax)
    h, l = ax.get_legend_handles_labels()
    h = h[1:] + h[:1]
    l = l[1:] + l[:1]
    ax.legend(h, l, frameon=False, fontsize=6.0, ncol=len(h), loc="lower center",
              bbox_to_anchor=(0.47, 1.0), handlelength=1.0, columnspacing=0.6, handletextpad=0.4,
              borderaxespad=0.2)
    fig.tight_layout(pad=0.3)
    fig.subplots_adjust(left=fig.subplotpars.left + 0.025)
    fig.savefig(f"{khoroji}/fig_bound.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_testbed2(risheh, khoroji):
    masir = f"{risheh}/{R4}/testbed_rev.json"
    if not os.path.exists(masir):
        masir = f"{risheh}/results_rev/testbed_rev.json"
    if not os.path.exists(masir):
        raise FileNotFoundError(masir)
    por = load(masir)
    d = por["attack"]
    daghigh = por.get("calibration", {}).get("event", {})
    kelidha = [("admission", "All flows"), ("admission_avoidable", "Avoidable"),
            ("admission_unavoidable", "Other")]
    siasatha = [p for p in TARTIB8 if p in d]
    fig, ax = plt.subplots(figsize=(3.5, 1.62))
    wbar = 0.92 / len(siasatha) * 0.875
    for gi, (key, bargasb) in enumerate(kelidha):
        for j, siasat in enumerate(siasatha):
            m, e = d[siasat][key]
            x = gi + (j - (len(siasatha) - 1) / 2) * wbar
            ax.bar(x, m, width=wbar * 0.92, yerr=e, color=MOSHAKHASATE_SIASAT[siasat][1], edgecolor="white",
                   linewidth=0.5, error_kw={"elinewidth": 0.5, "capsize": 1.0},
                   label=KOTAH[siasat] if gi == 0 else None, zorder=2)
            if siasat in daghigh:
                ax.plot([x], [daghigh[siasat][key][0]], ls="none", marker="D", ms=2.7, mfc="white",
                        mec="black", mew=0.6, zorder=4)
    if daghigh:
        ax.plot([1.66], [0.91], ls="none", marker="D", ms=2.7, mfc="white", mec="black",
                mew=0.6, zorder=4)
        ax.text(1.73, 0.91, "exact counts", fontsize=6.2, va="center", ha="left")
    ax.set_xticks(range(len(kelidha)))
    ax.set_xticklabels([k[1] for k in kelidha], fontsize=7.5)
    ax.set_ylabel("Benign admission")
    ax.set_ylim(0, 1.08)
    style_axes(ax)
    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, frameon=False, fontsize=5.9, ncol=len(h), loc="lower center",
              bbox_to_anchor=(0.47, 1.0), handlelength=0.9, columnspacing=0.5, handletextpad=0.35,
              borderaxespad=0.2)
    fig.tight_layout(pad=0.3)
    fig.subplots_adjust(left=fig.subplotpars.left + 0.025)
    fig.savefig(f"{khoroji}/fig_testbed2.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_cor1(risheh, khoroji):
    d = load(f"{risheh}/results_rev/cor1_check.json")["summary"]
    panels = [("abilene", "Abilene"), ("geant", "GEANT2012"), ("fattree4", "Fat-tree ($k$=4)")]
    fig, axs = plt.subplots(1, 3, figsize=(7.16, 1.95), sharey=True)
    for ax, (key, title) in zip(axs, panels):
        radifha = d[key]
        A = [r["A"] for r in radifha]
        ax.plot(A, [r["fluid"] for r in radifha], color="#2a78d6", ls=(0, (4, 2)), lw=1.0)
        ax.plot(A, [r["erlang"] for r in radifha], color="#eb6834", ls="-", lw=1.0)
        ax.plot(A, [r["sim_ss"] for r in radifha], ls="none", marker="o", ms=3.4, color="#0b0b0b")
        ax.plot(A, [r["sim90"] for r in radifha], ls="none", marker="o", ms=3.4, mfc="white",
                mec="#52514e", mew=0.8)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Adversary rules on the target")
        ax.set_ylim(0.38, 1.02)
        style_axes(ax)
    axs[0].set_ylabel("Benign admission")
    handles = [Line2D([0], [0], color="#2a78d6", ls=(0, (4, 2)), lw=1.0, label="Fluid (Corollary 1)"),
               Line2D([0], [0], color="#eb6834", ls="-", lw=1.0, label="Erlang loss formula"),
               Line2D([0], [0], ls="none", marker="o", ms=3.4, color="#0b0b0b",
                      label="Simulated, after the transition"),
               Line2D([0], [0], ls="none", marker="o", ms=3.4, mfc="white", mec="#52514e", mew=0.8,
                      label="Simulated, first 90 epochs")]
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, 1.02), handlelength=2.6, columnspacing=1.4)
    fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=0.8)
    fig.savefig(f"{khoroji}/fig_cor1.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_cor1_main(risheh, khoroji):
    d = load(f"{risheh}/results_rev/cor1_check.json")["summary"]
    majmooeha = [("fattree4", "Fat-tree ($k$=4)", "#1baf7a", "^"), ("abilene", "Abilene", "#2a78d6", "o"),
            ("geant", "GEANT2012", "#eb6834", "s")]
    fig, ax = plt.subplots(figsize=(3.5, 1.36))
    for key, bargasb, sotoon, mk in majmooeha:
        radifha = d[key]
        A = [r["A"] for r in radifha]
        ax.plot(A, [r["erlang"] for r in radifha], color=sotoon, lw=1.1, zorder=2)
        ax.plot(A, [r["sim_ss"] for r in radifha], ls="none", marker=mk, ms=3.8, color=sotoon,
                markeredgecolor="white", markeredgewidth=0.5, zorder=3)
    ax.set_xlabel("Adversary rules on the target")
    ax.set_ylabel("Benign admission")
    ax.set_ylim(0.36, 1.03)
    ax.set_xlim(280, 1020)
    style_axes(ax)
    handles = [Line2D([0], [0], color=sotoon, marker=mk, lw=1.1, ms=3.8, markeredgecolor="white",
                      markeredgewidth=0.5, label=bargasb) for _, bargasb, sotoon, mk in majmooeha]
    ax.legend(handles=handles, frameon=False, fontsize=6.8, loc="lower left", handlelength=2.2)
    fig.tight_layout(pad=0.3)
    fig.subplots_adjust(left=fig.subplotpars.left + 0.025)
    fig.savefig(f"{khoroji}/fig_cor1_main.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_trace2(risheh, khoroji):
    d = load(f"{risheh}/{R4}/trace.json")["cases"]
    siasatha = ["larm", "larm2_nr", "larm2", "greedy", "sp_retry"]
    fig, axs = plt.subplots(1, 2, figsize=(3.5, 1.58), sharey=True)
    for ax, key, title in zip(axs, ("fattree4:1300", "abilene:600"),
                              ("Fat-tree, 1300 rules", "Abilene, 600 rules")):
        for siasat in siasatha:
            y = d[key][siasat]
            bargasb, sotoon, mk, ls = MOSHAKHASATE_SIASAT[siasat]
            ax.plot(range(len(y)), y, color=sotoon, lw=1.1 if siasat.startswith("larm") else 0.9, ls=ls,
                    zorder=4 if siasat == "larm2" else 3)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Epochs since attack start")
        ax.set_ylim(0.4, 1.02)
        ax.set_xlim(0, 90)
        ax.set_xticks([0, 30, 60, 90])
        style_axes(ax)
    axs[0].set_ylabel("Benign admission")
    fig.legend(handles=[Line2D([0], [0], color=MOSHAKHASATE_SIASAT[p][1], ls=MOSHAKHASATE_SIASAT[p][3], lw=1.1, label=KOTAH[p]) for p in siasatha],
               loc="upper center", ncol=5, frameon=False, bbox_to_anchor=(0.5, 1.03),
               handlelength=1.5, columnspacing=0.7, handletextpad=0.4, fontsize=6.0)
    fig.tight_layout(rect=(0, 0, 1, 0.9), w_pad=0.5, pad=0.3)
    fig.subplots_adjust(left=fig.subplotpars.left + 0.02)
    fig.savefig(f"{khoroji}/fig_trace2.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_d0(risheh, khoroji):
    d = load(f"{risheh}/{R4}/d0.json")
    majmooeha = [("fattree4", "Fat-tree", ("900", "1300")), ("abilene", "Abilene", ("600", "800")),
            ("geant", "GEANT2012", ("600", "800")), ("abilene_sndlib", "Abilene 2004", ("600", "800")),
            ("geant_sndlib", "GEANT 2005", ("600", "800"))]
    xs = d["d0"]
    fig, axs = plt.subplots(1, 5, figsize=(7.16, 1.75), sharey=True)
    for ax, (key, title, (b1, b2)) in zip(axs, majmooeha):
        P = d["topologies"][key]["policies"]
        for siasat, sotoon, mk in (("larm", MOSHAKHASATE_SIASAT["larm"][1], "D"), ("larm_retry", MOSHAKHASATE_SIASAT["larm_retry"][1], "X")):
            for b, ls, fill in ((b1, "-", True), (b2, (0, (4, 2)), False)):
                y = [P[siasat][b][str(x)]["admission"][0] for x in xs]
                e = [P[siasat][b][str(x)]["admission"][1] for x in xs]
                ax.errorbar(xs, y, yerr=e, color=sotoon, marker=mk, ms=3.6, lw=1.0, ls=ls, elinewidth=0.6,
                            capsize=1.5, mfc=sotoon if fill else "white", markeredgecolor=sotoon if not fill else "white",
                            markeredgewidth=0.6)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Prior $d_0$")
        ax.set_xticks(xs)
        ax.set_xticklabels(["0", "0.25", "0.5", "0.75"])
        ax.set_ylim(0.55, 1.02)
        style_axes(ax)
    axs[0].set_ylabel("Benign admission")
    handles = [Line2D([0], [0], color=MOSHAKHASATE_SIASAT["larm"][1], marker="D", ms=3.6, lw=1.0, label="LA-RM"),
               Line2D([0], [0], color=MOSHAKHASATE_SIASAT["larm_retry"][1], marker="X", ms=3.6, lw=1.0, label="LA-RM+R"),
               Line2D([0], [0], color="#52514e", lw=1.0, ls="-", label="stress budget"),
               Line2D([0], [0], color="#52514e", lw=1.0, ls=(0, (4, 2)), label="heavy budget")]
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.03),
               handlelength=2.4, columnspacing=1.4)
    fig.tight_layout(rect=(0, 0, 1, 0.9), w_pad=0.6)
    fig.savefig(f"{khoroji}/fig_d0.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_rand(risheh, khoroji):
    d = load(f"{risheh}/{R4}/ablation.json")["randomization"]
    import numpy as np

    def pstar(eps, fl, k=4):
        if eps == 0 and fl == 0:
            return 1.0
        u = np.full(k, 1.0 / k)
        p = np.zeros(k); p[0] = 1.0
        pe = (1 - eps) * p + eps * u
        H = lambda q: float(-(q[q > 0] * np.log(q[q > 0])).sum())
        while H(pe) < fl * np.log(k):
            pe = 0.9 * pe + 0.1 * u
        return float(pe[0])

    tanzimha = sorted(((pstar(float(c.split("|")[0][4:]), float(c.split("|")[1][6:])), c) for c in d))
    majmooeha = [("fattree4:1300", "Fat-tree, 1300", "#1baf7a", "^"), ("abilene:600", "Abilene, 600", "#2a78d6", "o"),
            ("abilene:800", "Abilene, 800", "#2a78d6", "s"), ("geant:600", "GEANT2012, 600", "#eb6834", "o"),
            ("geant:800", "GEANT2012, 800", "#eb6834", "s")]
    fig, ax = plt.subplots(figsize=(3.5, 1.9))
    for key, bargasb, sotoon, mk in majmooeha:
        x = [c[0] for c in tanzimha]
        y = [d[c[1]][key]["admission"][0] for c in tanzimha]
        e = [d[c[1]][key]["admission"][1] for c in tanzimha]
        ax.errorbar(x, y, yerr=e, color=sotoon, marker=mk, ms=3.6, lw=1.0, ls="-" if mk != "s" else (0, (4, 2)),
                    elinewidth=0.6, capsize=1.5, markeredgecolor="white", markeredgewidth=0.5, label=bargasb)
    ax.set_xlabel("Largest share of a pair's flows on one path ($k$ = 4)")
    ax.set_ylabel("Benign admission")
    style_axes(ax)
    ax.legend(frameon=False, fontsize=6.2, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0),
              handlelength=2.2, columnspacing=1.0, borderaxespad=0.2)
    fig.tight_layout(pad=0.3)
    fig.subplots_adjust(left=fig.subplotpars.left + 0.025)
    fig.savefig(f"{khoroji}/fig_rand.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def fig_gap(risheh, khoroji):
    import numpy as np
    radifha = load(f"{risheh}/{R4}/gaps.json")["settings"]
    siasatha = ["greedy", "sp_retry", "larm_retry", "larm2"]
    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(3.5, 1.22))
    for y, siasat in enumerate(reversed(siasatha)):
        g = np.array([-r["gap"][siasat] for r in radifha])
        sotoon = MOSHAKHASATE_SIASAT[siasat][1]
        ax.scatter(g, y + rng.uniform(-0.24, 0.24, len(g)), s=7, color=sotoon, alpha=0.6, linewidths=0, zorder=3)
        ax.plot([g.mean(), g.mean()], [y - 0.36, y + 0.36], color="#0b0b0b", lw=1.3, zorder=4)
        ax.annotate(f"{g.max():.2f}", (g.max(), y), xytext=(4, 0), textcoords="offset points",
                    va="center", ha="left", fontsize=7, color=sotoon)
    ax.set_yticks(range(len(siasatha)))
    ax.set_yticklabels([KOTAH[p] for p in reversed(siasatha)])
    ax.set_ylim(-0.6, len(siasatha) - 0.4)
    ax.set_xlim(-0.25, 10.8)
    ax.set_xlabel("Shortfall from the best policy (points of admission)")
    ax.grid(axis="x", color=RANGE_SHABAKE, lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout(pad=0.3)
    fig.savefig(f"{khoroji}/fig_gap.pdf", metadata=FARADADE_KHALI)
    plt.close(fig)


def main():
    khoroji = sys.argv[1] if len(sys.argv) > 1 else "paper/figs"
    os.makedirs(khoroji, exist_ok=True)
    risheh = "."
    for f in (fig_admission, fig_admtrace, fig_evict, fig_attack, fig_learn, fig_kfloor,
              fig_measured, fig_control, fig_topo, fig_bound, fig_testbed2, fig_cor1,
              fig_cor1_main, fig_trace2, fig_d0, fig_rand, fig_gap):
        try:
            f(risheh, khoroji)
            print("ok", f.__name__)
        except FileNotFoundError as e:
            print("skip", f.__name__, e)


if __name__ == "__main__":
    main()
