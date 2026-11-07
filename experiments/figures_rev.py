"""Figures of the revised paper and its supplement, drawn from the result files.

Usage: python experiments/figures_rev.py <out_dir>

Fonts are embedded as TrueType (Liberation Sans, metrically equal to Arial), so the
PDFs contain no Type 3 fonts. Colors follow one fixed categorical order, and every
series also has its own marker and line style, so the figures read in grayscale.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

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
MAINT_INFO = {"Creator": "", "Producer": "", "Title": "", "Author": "",
              "Subject": "", "Keywords": ""}

# policy -> (label, color, marker, linestyle); colors in fixed categorical order
POL = {
    "sp": ("Shortest path", "#2a78d6", "o", (0, (4, 2))),
    "ecmp": ("ECMP", "#eb6834", "s", (0, (4, 2))),
    "urm": ("Uniform mutation", "#1baf7a", "^", (0, (4, 2))),
    "larm": ("LA-RM", "#eda100", "D", (0, (6, 2, 1.5, 2))),
    "greedy": ("Greedy", "#e87ba4", "v", "-"),
    "sp_retry": ("SP + retry", "#008300", "P", "-"),
    "larm_retry": ("LA-RM + retry", "#6250d6", "X", "-"),
}
ORDER = ["sp", "ecmp", "urm", "larm", "greedy", "sp_retry", "larm_retry"]
GRID_COLOR = "#e4e3df"


def load(path):
    with open(path) as f:
        return json.load(f)


def curve_new(paths, pol):
    """Merge budget -> (mean, ci) of one policy from several run_baselines files."""
    pts = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        d = load(p)
        if pol not in d["policies"]:
            continue
        for b, v in d["policies"][pol].items():
            pts[int(b)] = tuple(v["admission"])
    return pts


def curve_main(path, pol):
    d = load(path)
    return {int(b): tuple(v) for b, v in d["policies"][pol]["adm_curve"].items()}


def style_axes(ax):
    ax.grid(True, axis="y", color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)


def plot_series(ax, pts, pol, cap=1000.0, ms=3.6):
    lab, col, mk, ls = POL[pol]
    xs = sorted(pts)
    x = [b / cap for b in xs]
    y = [pts[b][0] for b in xs]
    e = [pts[b][1] for b in xs]
    ax.errorbar(x, y, yerr=e, color=col, marker=mk, ms=ms, lw=1.1, ls=ls,
                elinewidth=0.6, capsize=1.5, markeredgewidth=0.5,
                markeredgecolor="white", label=lab, zorder=3 if ls == "-" else 2)


def legend_handles(pols):
    hs = []
    for p in pols:
        lab, col, mk, ls = POL[p]
        hs.append(Line2D([0], [0], color=col, marker=mk, ls=ls, lw=1.1, ms=4,
                         markeredgecolor="white", markeredgewidth=0.5, label=lab))
    return hs


def fig_admission(root, out):
    R, M = f"{root}/results_rev", f"{root}/results"
    panels = [
        ("Fat-tree ($k$=4)", f"{M}/main_fattree4.json",
         [f"{R}/base_fattree4.json", f"{R}/curve_fattree4.json"]),
        ("Abilene", f"{M}/main_abilene.json",
         [f"{R}/base_abilene.json", f"{R}/base_abilene_full.json", f"{R}/curve_abilene.json"]),
        ("GEANT2012", f"{M}/main_geant.json",
         [f"{R}/base_geant2012.json", f"{R}/base_geant2012_0_1100.json",
          f"{R}/curve_geant2012.json"]),
    ]
    fig, axs = plt.subplots(1, 3, figsize=(7.16, 2.15), sharey=True)
    for ax, (title, mainf, newfs) in zip(axs, panels):
        for pol in ORDER:
            pts = curve_main(mainf, pol) if pol in ("sp", "ecmp", "urm", "larm") \
                else curve_new(newfs, pol)
            plot_series(ax, pts, pol)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Adversary budget (tables)")
        ax.set_ylim(0.3, 1.02)
        style_axes(ax)
    axs[0].set_ylabel("Benign admission")
    fig.legend(handles=legend_handles(ORDER), loc="upper center", ncol=7, frameon=False,
               bbox_to_anchor=(0.5, 1.02), handlelength=2.6, columnspacing=1.1)
    fig.tight_layout(rect=(0, 0, 1, 0.9), w_pad=0.8)
    fig.savefig(f"{out}/fig_admission.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def fig_admtrace(root, out):
    """Admission over time at the heavy budget (original four policies). The series
    start when the attack starts (run_admtrace.py stores the epochs after warm-up)."""
    d = load(f"{root}/results/admtrace_heavy.json")
    fig, axs = plt.subplots(1, 2, figsize=(3.5, 1.9), sharey=True)
    for ax, topo, title in zip(axs, ("fattree4", "abilene"), ("Fat-tree, 1300 rules", "Abilene, 800 rules")):
        for pol in ("sp", "ecmp", "urm", "larm"):
            y = d[topo][pol]
            lab, col, mk, ls = POL[pol]
            ax.plot(range(len(y)), y, color=col, lw=0.9, ls=ls, label=lab)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Epochs since attack start")
        ax.set_ylim(0.3, 1.02)
        style_axes(ax)
    axs[0].set_ylabel("Benign admission")
    fig.legend(handles=[Line2D([0], [0], color=POL[p][1], ls=POL[p][3], lw=1.0, label=POL[p][0])
                        for p in ("sp", "ecmp", "urm", "larm")],
               loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.03),
               handlelength=2.2, columnspacing=0.8, fontsize=6.8)
    fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=0.6)
    fig.savefig(f"{out}/fig_admtrace.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def fig_evict(root, out):
    rows = [("sp", "Shortest path\n(re-install)"), ("evict_static", "Evict oldest\n(aging)"),
            ("evict_refresh", "Evict oldest\n(re-install)"), ("larm", "LA-RM\n(re-install)")]
    fig, axs = plt.subplots(1, 2, figsize=(7.16, 1.9))
    cols = ["#2a78d6", "#eb6834"]
    for ax, key, ylab in zip(axs, ("admission", "churn"),
                             ("Benign admission", "Benign rules evicted per flow")):
        for j, topo in enumerate(("fattree4", "abilene")):
            d = load(f"{root}/results/evict_{topo}.json")["rows"]
            xs = [i + (j - 0.5) * 0.36 for i in range(len(rows))]
            ys = [d[r][key][0] for r, _ in rows]
            es = [d[r][key][1] for r, _ in rows]
            ax.bar(xs, ys, width=0.34, yerr=es, color=cols[j], edgecolor="white", linewidth=0.8,
                   error_kw={"elinewidth": 0.6, "capsize": 1.5},
                   label="Fat-tree, 1300 rules" if topo == "fattree4" else "Abilene, 800 rules")
        ax.set_xticks(range(len(rows)))
        ax.set_xticklabels([lab for _, lab in rows], fontsize=7)
        ax.set_ylabel(ylab)
        style_axes(ax)
    axs[0].set_ylim(0, 1.15)
    axs[0].legend(frameon=False, fontsize=7, loc="upper left", ncol=2)
    fig.tight_layout(w_pad=1.2)
    fig.savefig(f"{out}/fig_evict.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def fig_attack(root, out):
    """Testbed under attack: admission of the avoidable benign flows in 10 s bins.
    Left: the original series (four policies). Right: the second series, all seven
    policies on another host (results_rev/testbed_rev.json), if present."""
    series = [("First series", f"{root}/results/testbed.json", ("sp", "ecmp", "urm", "larm"))]
    rev = f"{root}/results_rev/testbed_rev.json"
    if os.path.exists(rev):
        series.append(("Second series", rev, ORDER))
    fig, axs = plt.subplots(1, len(series), figsize=(3.5 * len(series), 2.0), sharey=True,
                            squeeze=False)
    for ax, (title, path, pols) in zip(axs[0], series):
        d = load(path)
        x = [(a + b) / 2 for a, b in d["bins"]]
        for pol in pols:
            if pol not in d["attack"]:
                continue
            v = d["attack"][pol]["admission_avoidable_bins"]
            lab, col, mk, ls = POL[pol]
            ax.errorbar(x, [p[0] for p in v], yerr=[p[1] for p in v], color=col, marker=mk, ms=3.4,
                        lw=1.0, ls=ls, elinewidth=0.6, capsize=1.5, markeredgecolor="white",
                        markeredgewidth=0.5, label=lab)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Time since benign workload start (s)")
        ax.set_ylim(0.6, 1.02)
        style_axes(ax)
    axs[0][0].set_ylabel("Admission, avoidable flows")
    if len(series) > 1:
        fig.legend(handles=legend_handles(ORDER), loc="upper center", ncol=7, frameon=False,
                   bbox_to_anchor=(0.5, 1.03), handlelength=2.4, columnspacing=1.0, fontsize=7)
        fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=0.8)
    else:
        axs[0][0].legend(frameon=False, ncol=2, fontsize=6.8, loc="lower right")
        fig.tight_layout()
    fig.savefig(f"{out}/fig_attack.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def fig_learn(root, out):
    d = load(f"{root}/results/learn_curve.json")
    P = d["p"]
    tgt_idx = d["cross"][0]
    fig, ax = plt.subplots(figsize=(3.5, 1.8))
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
    lss = ["-", (0, (4, 2)), (0, (1.5, 1.5)), (0, (6, 2, 1.5, 2))]
    for i in range(len(P[0])):
        lab = "path through the attacked core" if i == tgt_idx else f"clear path {i + 1 - (i > tgt_idx)}"
        ax.plot(range(len(P)), [p[i] for p in P], color=cols[i], ls=lss[i], lw=1.1, label=lab)
    ax.set_xlabel("Epoch (attack from epoch 0)")
    ax.set_ylabel("Probability before mixing")
    ax.set_ylim(0, 1.0)
    style_axes(ax)
    ax.legend(frameon=False, fontsize=6.5, loc="center right")
    fig.tight_layout()
    fig.savefig(f"{out}/fig_learn.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def fig_kfloor(root, out):
    d = load(f"{root}/results/kfloor.json")
    fig, ax = plt.subplots(figsize=(3.5, 1.8))
    cols = ["#2a78d6", "#eb6834", "#1baf7a"]
    mks = ["o", "s", "^"]
    for c, mk, fl in zip(cols, mks, d["floors"]):
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
    fig.savefig(f"{out}/fig_kfloor.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def fig_measured(root, out):
    R, M = f"{root}/results_rev", f"{root}/results"
    panels = [
        ("Abilene 2004, measured", f"{M}/main_abilene_sndlib.json",
         [f"{R}/base_abilene_sndlib.json", f"{R}/curve_abilene_sndlib.json"]),
        ("GEANT 2005, measured", f"{M}/main_geant_sndlib.json",
         [f"{R}/base_geant_sndlib.json", f"{R}/base_geant_sndlib_full.json",
          f"{R}/curve_geant_sndlib.json"]),
    ]
    fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.15), sharey=True)
    for ax, (title, mainf, newfs) in zip(axs, panels):
        for pol in ORDER:
            pts = curve_main(mainf, pol) if pol in ("sp", "ecmp", "urm", "larm") \
                else curve_new(newfs, pol)
            plot_series(ax, pts, pol)
        ax.set_title(title, pad=3)
        ax.set_xlabel("Adversary budget (tables)")
        ax.set_ylim(0.3, 1.02)
        style_axes(ax)
    axs[0].set_ylabel("Benign admission")
    fig.legend(handles=legend_handles(ORDER), loc="upper center", ncol=7, frameon=False,
               bbox_to_anchor=(0.5, 1.02), handlelength=2.6, columnspacing=1.1)
    fig.tight_layout(rect=(0, 0, 1, 0.9), w_pad=0.8)
    fig.savefig(f"{out}/fig_measured.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def fig_control(root, out):
    sets = [("fattree4", "Fat-tree\n1300"), ("abilene", "Abilene\n800"),
            ("abilene_sndlib", "Abilene 2004\n800"), ("geant_sndlib", "GEANT 2005\n800")]
    keys = [("larm", "LA-RM", "#eda100"), ("noise", "LA-RM, random rewards", "#8a8984"),
            ("urm", "Uniform mutation", "#1baf7a")]
    fig, ax = plt.subplots(figsize=(3.5, 1.9))
    for j, (key, lab, col) in enumerate(keys):
        xs, ys, es = [], [], []
        for i, (topo, _) in enumerate(sets):
            p = f"{root}/results/extra_{topo}.json"
            if not os.path.exists(p):
                continue
            c = load(p)["control"][key]["admission"]
            xs.append(i + (j - 1) * 0.27)
            ys.append(c[0])
            es.append(c[1])
        ax.bar(xs, ys, width=0.25, yerr=es, color=col, edgecolor="white", linewidth=0.8,
               error_kw={"elinewidth": 0.6, "capsize": 1.5}, label=lab)
    ax.set_xticks(range(len(sets)))
    ax.set_xticklabels([s for _, s in sets], fontsize=6.5)
    ax.set_ylabel("Benign admission")
    ax.set_ylim(0.4, 0.85)
    style_axes(ax)
    ax.legend(frameon=False, fontsize=6.3, loc="upper right", ncol=1)
    fig.tight_layout()
    fig.savefig(f"{out}/fig_control.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def fig_topo(root, out):
    """Testbed fat-tree with the attacker's pinned path."""
    fig, ax = plt.subplots(figsize=(3.5, 1.75))
    core = [(1.5 + 2.0 * i, 3.0) for i in range(4)]
    agg = [(0.75 * 0 + i * 1.0 + (i // 2) * 0.6, 2.0) for i in range(8)]
    edge = [(x, 1.0) for x, _ in agg]
    host = [(x, 0.25) for x, _ in edge]
    # center the rows
    off = (core[-1][0] + core[0][0]) / 2 - (agg[-1][0] + agg[0][0]) / 2
    agg = [(x + off, y) for x, y in agg]
    edge = [(x + off, y) for x, y in edge]
    host = [(x + off, y) for x, y in host]
    links = []
    for p in range(4):
        a0, a1 = 2 * p, 2 * p + 1
        for e in (a0, a1):
            for a in (a0, a1):
                links.append((edge[e], agg[a]))
        for a_local, a in enumerate((a0, a1)):
            for j in range(2):
                links.append((agg[a], core[2 * a_local + j]))
    for e in range(8):
        links.append((host[e], edge[e]))
    for (x0, y0), (x1, y1) in links:
        ax.plot([x0, x1], [y0, y1], color="#c3c2b7", lw=0.6, zorder=1)
    # attacker: host on edge switch 0 -> host on edge switch 5, pinned to its shortest
    # path through the first core (testbed/net.py defaults: adv_src=0, adv_dst=5)
    path = [host[0], edge[0], agg[0], core[0], agg[4], edge[5], host[5]]
    for (x0, y0), (x1, y1) in zip(path[:-1], path[1:]):
        ax.plot([x0, x1], [y0, y1], color="#e34948", lw=1.8, zorder=2)
    def boxes(pts, col, w, h, label=None):
        for x, y in pts:
            ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h, facecolor=col,
                                       edgecolor="#52514e", lw=0.5, zorder=3))
    boxes(core, "#cde2fb", 0.62, 0.32)
    boxes(agg, "#cde2fb", 0.56, 0.3)
    boxes(edge, "#cde2fb", 0.56, 0.3)
    for x, y in host:
        ax.add_patch(plt.Circle((x, y), 0.11, facecolor="#ffffff", edgecolor="#52514e",
                                lw=0.5, zorder=3))
    for x, y in [path[1], path[2], path[3], path[4], path[5]]:
        ax.text(x, y, "85", ha="center", va="center", fontsize=6.2, zorder=4, color="#0b0b0b")
    for name, y in (("core", 3.0), ("aggregation", 2.0), ("edge", 1.0), ("hosts", 0.25)):
        ax.text(-0.55, y, name, ha="right", va="center", fontsize=6.5, color="#52514e")
    ax.text(path[0][0], path[0][1] - 0.32, "attacker", ha="center", va="top", fontsize=6.2)
    ax.text(path[-1][0], path[-1][1] - 0.32, "sink", ha="center", va="top", fontsize=6.2)
    ax.set_xlim(-2.4, agg[-1][0] + 0.6)
    ax.set_ylim(-0.35, 3.35)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout(pad=0.2)
    fig.savefig(f"{out}/fig_topo.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def rowmajor(handles, labels, ncol):
    """Reorder legend entries so that they read row by row (matplotlib fills columns)."""
    nrow = -(-len(handles) // ncol)
    order = []
    for c in range(ncol):
        for r in range(nrow):
            k = r * ncol + c
            if k < len(handles):
                order.append(k)
    return [handles[k] for k in order], [labels[k] for k in order]


def fig_bound(root, out):
    """What rerouting can save (Proposition 3): admission with one switch held full,
    against the bound 1 - u(target)."""
    R = f"{root}/results_rev"
    un = load(f"{R}/unavoidable.json")
    u_ab = un["abilene"][0]["U_hub"]
    u_ge = un["geant"][0]["U_hub"]
    groups = [
        ("Fat-tree\ncore or aggr.", f"{R}/base_fattree4.json", "1300", 0.0),
        ("Fat-tree\nedge", f"{R}/base_fattree4_aware.json", "1300", 0.25),
        ("Abilene\nhub", f"{R}/base_abilene_full.json", "1100", u_ab),
        ("GEANT2012\nhub", f"{R}/base_geant2012_0_1100.json", "1100", u_ge),
    ]
    pols = ["sp", "larm", "greedy", "sp_retry", "larm_retry"]
    fig, ax = plt.subplots(figsize=(3.5, 2.05))
    wbar = 0.15
    for gi, (lab, path, b, u) in enumerate(groups):
        d = load(path)["policies"]
        for j, pol in enumerate(pols):
            m, e = d[pol][b]["admission"]
            x = gi + (j - 2) * wbar
            ax.bar(x, m, width=wbar * 0.92, yerr=e, color=POL[pol][1], edgecolor="white",
                   linewidth=0.5, error_kw={"elinewidth": 0.5, "capsize": 1.2},
                   label=POL[pol][0] if gi == 0 else None, zorder=2)
        ax.plot([gi - 2.6 * wbar, gi + 2.6 * wbar], [1 - u, 1 - u], color="#0b0b0b", lw=1.1,
                ls=(0, (3, 1.5)), zorder=3, label="bound $1-u$" if gi == 0 else None)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([g[0] for g in groups], fontsize=7)
    ax.set_ylabel("Benign admission")
    ax.set_ylim(0, 1.08)
    style_axes(ax)
    h, l = ax.get_legend_handles_labels()
    h = h[1:] + h[:1]          # policies first, the bound last
    l = l[1:] + l[:1]
    h, l = rowmajor(h, l, 3)
    ax.legend(h, l, frameon=False, fontsize=6.3, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.30),
              handlelength=1.6, columnspacing=0.8)
    fig.tight_layout(pad=0.3)
    fig.savefig(f"{out}/fig_bound.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def fig_testbed2(root, out):
    """Second testbed series: admission of all, avoidable and other benign flows."""
    path = f"{root}/results_rev/testbed_rev.json"
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    d = load(path)["attack"]
    keys = [("admission", "All flows"), ("admission_avoidable", "Avoidable"),
            ("admission_unavoidable", "Other")]
    pols = [p for p in ORDER if p in d]
    fig, ax = plt.subplots(figsize=(3.5, 2.0))
    wbar = 0.115
    for gi, (key, lab) in enumerate(keys):
        for j, pol in enumerate(pols):
            m, e = d[pol][key]
            x = gi + (j - (len(pols) - 1) / 2) * wbar
            ax.bar(x, m, width=wbar * 0.92, yerr=e, color=POL[pol][1], edgecolor="white",
                   linewidth=0.5, error_kw={"elinewidth": 0.5, "capsize": 1.0},
                   label=POL[pol][0] if gi == 0 else None, zorder=2)
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([k[1] for k in keys], fontsize=7.5)
    ax.set_ylabel("Benign admission")
    ax.set_ylim(0, 1.08)
    style_axes(ax)
    h, l = ax.get_legend_handles_labels()
    h, l = rowmajor(h, l, 4)
    ax.legend(h, l, frameon=False, fontsize=6.2, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.32),
              handlelength=1.4, columnspacing=0.7)
    fig.tight_layout(pad=0.3)
    fig.savefig(f"{out}/fig_testbed2.pdf", metadata=MAINT_INFO)
    plt.close(fig)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "paper/figs"
    os.makedirs(out, exist_ok=True)
    root = "."
    for f in (fig_admission, fig_admtrace, fig_evict, fig_attack, fig_learn, fig_kfloor,
              fig_measured, fig_control, fig_topo, fig_bound, fig_testbed2):
        try:
            f(root, out)
            print("ok", f.__name__)
        except FileNotFoundError as e:
            print("skip", f.__name__, e)


if __name__ == "__main__":
    main()
