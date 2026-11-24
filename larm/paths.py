import random
import zlib
from itertools import islice

import networkx as nx


def path_cost(G, masir, weight="weight"):
    return sum(G[u][v][weight] for u, v in zip(masir[:-1], masir[1:]))


def k_shortest(G, s, d, k, weight="weight"):
    return [list(p) for p in islice(nx.shortest_simple_paths(G, s, d, weight=weight), k)]


def ecmp_paths(G, s, d, weight="weight", zarfiat=16):
    return [list(p) for p in islice(nx.all_shortest_paths(G, s, d, weight=weight), zarfiat)]


def _tie_weight(G, od, weight="weight", scale=1e-6):
    rng = random.Random(zlib.crc32(repr(od).encode()))
    xi = {e: rng.random() for e in sorted(G.edges(), key=repr)}
    return lambda u, v, d: d[weight] * (1.0 + scale * xi[(u, v)])


def node_protecting(G, s, d, k, hadde_aksare_keshidegi=None, olaviyat=None, weight="weight"):
    wf = _tie_weight(G, (s, d), weight)
    p1 = list(nx.shortest_path(G, s, d, weight=wf))
    paye = path_cost(G, p1, weight)
    hadd = None if hadde_aksare_keshidegi is None else hadde_aksare_keshidegi * paye
    entekhab_shode = [p1]
    olaviyat = olaviyat or {}
    obour = sorted(p1[1:-1], key=lambda n: (-olaviyat.get(n, 0.0), repr(n)))
    for t in obour:
        if len(entekhab_shode) >= k:
            break
        if any(t not in p for p in entekhab_shode):
            continue
        H = nx.restricted_view(G, [t], [])
        try:
            p = list(nx.shortest_path(H, s, d, weight=wf))
        except nx.NetworkXNoPath:
            continue
        if (hadd is None or path_cost(G, p, weight) <= hadd) and p not in entekhab_shode:
            entekhab_shode.append(p)
    if len(entekhab_shode) < k:
        for p in nx.shortest_simple_paths(G, s, d, weight=wf):
            p = list(p)
            if hadd is not None and path_cost(G, p, weight) > hadd:
                break
            if p not in entekhab_shode:
                entekhab_shode.append(p)
            if len(entekhab_shode) >= k:
                break
    return sorted(entekhab_shode, key=lambda p: path_cost(G, p, weight))


def diverse(G, s, d, k, hadde_aksare_keshidegi=None, olaviyat=None, weight="weight"):
    wf = _tie_weight(G, (s, d), weight)
    p1 = list(nx.shortest_path(G, s, d, weight=wf))
    paye = path_cost(G, p1, weight)
    hadd = None if hadde_aksare_keshidegi is None else hadde_aksare_keshidegi * paye
    movafagh = lambda p: hadd is None or path_cost(G, p, weight) <= hadd
    entekhab_shode = [p1]
    estefade_shode = set(p1[1:-1])
    while len(entekhab_shode) < k and estefade_shode:
        H = nx.restricted_view(G, list(estefade_shode), [])
        try:
            p = list(nx.shortest_path(H, s, d, weight=wf))
        except nx.NetworkXNoPath:
            break
        if not movafagh(p) or p in entekhab_shode:
            break
        entekhab_shode.append(p)
        estefade_shode |= set(p[1:-1])
    olaviyat = olaviyat or {}
    for t in sorted(p1[1:-1], key=lambda n: (-olaviyat.get(n, 0.0), repr(n))):
        if len(entekhab_shode) >= k:
            break
        if any(t not in p for p in entekhab_shode):
            continue
        H = nx.restricted_view(G, [t], [])
        try:
            p = list(nx.shortest_path(H, s, d, weight=wf))
        except nx.NetworkXNoPath:
            continue
        if movafagh(p) and p not in entekhab_shode:
            entekhab_shode.append(p)
    if len(entekhab_shode) < k:
        for p in nx.shortest_simple_paths(G, s, d, weight=wf):
            p = list(p)
            if not movafagh(p):
                break
            if p not in entekhab_shode:
                entekhab_shode.append(p)
            if len(entekhab_shode) >= k:
                break
    return sorted(entekhab_shode, key=lambda p: path_cost(G, p, weight))


def random_ties(G, s, d, k, hadde_aksare_keshidegi=None, weight="weight"):
    wf = _tie_weight(G, (s, d), weight)
    khoroji = []
    paye = None
    for p in nx.shortest_simple_paths(G, s, d, weight=wf):
        p = list(p)
        c = path_cost(G, p, weight)
        paye = c if paye is None else paye
        if hadde_aksare_keshidegi is not None and c > hadde_aksare_keshidegi * paye:
            break
        khoroji.append(p)
        if len(khoroji) >= k:
            break
    return sorted(khoroji, key=lambda p: path_cost(G, p, weight))


def sp_shares(G, ods, nerkh, weight="weight"):
    S = {n: 0.0 for n in G.nodes()}
    majmoo = sum(nerkh[od] for od in ods) or 1.0
    for od in ods:
        eq = ecmp_paths(G, od[0], od[1], weight)
        for p in eq:
            for n in p:
                S[n] += nerkh[od] / majmoo / len(eq)
    return S


class PathTable:

    def __init__(self, G, ods, k=4, weight="weight", hadde_aksare_keshidegi=None, halat="yen", nerkh=None):
        self.G = G
        self.k = k
        self.mode = halat
        self.cand = {}
        self.ecmp = {}
        self.sp_cost = {}
        self.cost = {}
        olaviyat = sp_shares(G, ods, nerkh, weight) if halat in ("np", "div") else None
        for od in ods:
            s, d = od
            if halat == "div":
                kandidha = diverse(G, s, d, k, hadde_aksare_keshidegi, olaviyat, weight)
            elif halat == "np":
                kandidha = node_protecting(G, s, d, k, hadde_aksare_keshidegi, olaviyat, weight)
            elif halat == "ties":
                kandidha = random_ties(G, s, d, k, hadde_aksare_keshidegi, weight)
            else:
                kandidha = k_shortest(G, s, d, k, weight)
            paye = path_cost(G, kandidha[0], weight)
            if hadde_aksare_keshidegi is not None:
                kandidha = [p for p in kandidha if path_cost(G, p, weight) <= hadde_aksare_keshidegi * paye] or kandidha[:1]
            self.cand[od] = kandidha
            self.cost[od] = [path_cost(G, p, weight) for p in kandidha]
            self.sp_cost[od] = paye
            self.ecmp[od] = ecmp_paths(G, s, d, weight)

    def stretch(self, od, masir):
        return path_cost(self.G, masir) / self.sp_cost[od]
