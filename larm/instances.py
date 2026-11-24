import json
import os
import random

import networkx as nx

RISHE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOSHE_REPETITA = os.environ.get("LARM_REPETITA", os.path.join(RISHE, "data", "raw"))
POOSHE_SNDLIB = os.environ.get("LARM_SNDLIB", os.path.join(RISHE, "data", "sndlib"))
NAMHAYE_REPETITA = {"abilene": "Abilene", "geant": "Geant2012", "geant2009": "Geant2009",
                    "geant2010": "Geant2010", "uscarrier": "UsCarrier", "cogentco": "Cogentco"}
SHABAKEHAYE_SNDLIB = {"abilene_sndlib": "abilene", "geant_sndlib": "geant"}
TOKHME_NAMOONE = 0


def fattree4():
    G = nx.Graph()
    for hasteh in range(16, 20):
        G.add_node(hasteh)
        G.add_nodes_from(8 + 2 * pod + (hasteh - 16) // 2 for pod in range(4))
    G.add_nodes_from(range(8))
    for pod in range(4):
        labeha = [2 * pod, 2 * pod + 1]
        tajmiha = [8 + 2 * pod, 9 + 2 * pod]
        for i, tajmi in enumerate(tajmiha):
            G.add_edge(tajmi, 16 + 2 * i, weight=1)
            for labe in labeha:
                G.add_edge(tajmi, labe, weight=1)
            G.add_edge(tajmi, 17 + 2 * i, weight=1)
    G.graph["edge_switches"] = list(range(8))
    taghaza = {(s, d): 1.0 for s in range(8) for d in range(8) if s // 2 != d // 2}
    return G.to_directed(), taghaza


def _khatha(masir):
    with open(masir) as f:
        return [khat.split() for khat in f.read().split("\n")]


def repetita(nam):
    khatha = _khatha(os.path.join(POOSHE_REPETITA, nam + ".graph"))
    G = nx.DiGraph()
    for k in range(int(khatha[0][1])):
        G.add_node(k, name=khatha[2 + k][0])
    j = next(i for i, khat in enumerate(khatha) if khat and khat[0] == "EDGES")
    for k in range(int(khatha[j][1])):
        t = khatha[j + 2 + k]
        G.add_edge(int(t[1]), int(t[2]), weight=int(t[3]))
    khatha = _khatha(os.path.join(POOSHE_REPETITA, nam + ".0000.demands"))
    taghaza = {}
    for k in range(int(khatha[0][1])):
        t = khatha[2 + k]
        s, d, w = int(t[1]), int(t[2]), float(t[3])
        if s != d and w > 0:
            taghaza[(s, d)] = w
    return G, taghaza


def namoone(taghaza, hadde_aksar):
    if hadde_aksar is None or len(taghaza) <= hadde_aksar:
        return taghaza
    joftha = list(taghaza)
    tartib = list(range(len(joftha)))
    random.Random(TOKHME_NAMOONE).shuffle(tartib)
    return {joftha[i]: taghaza[joftha[i]] for i in tartib[:hadde_aksar]}


def sndlib_topo(shabake):
    khatha = [k for k in _khatha(os.path.join(POOSHE_SNDLIB, shabake + ".topo")) if k]
    n = int(khatha[0][1])
    namha = [khatha[1 + i][0] for i in range(n)]
    shomare = {nam: i for i, nam in enumerate(namha)}
    G = nx.Graph()
    for i, nam in enumerate(namha):
        G.add_node(i, name=nam)
    m = int(khatha[1 + n][1])
    for u, v in khatha[2 + n:2 + n + m]:
        G.add_edge(shomare[u], shomare[v], weight=1)
    return G.to_directed(), shomare


def sndlib(shabake, rooz, saat="busy"):
    G, shomare = sndlib_topo(shabake)
    with open(os.path.join(POOSHE_SNDLIB, shabake + "_snapshots.json")) as f:
        aks = json.load(f)["days"][rooz]
    taghaza = {(shomare[a], shomare[b]): w for a, b, w in aks[saat]}
    zarib = 1.0 if saat == "busy" else aks["quiet_total"] / aks["busy_total"]
    return G, taghaza, zarib


def gravity(taghaza):
    khorooji, voroodi = {}, {}
    for (s, d), w in taghaza.items():
        khorooji[s] = khorooji.get(s, 0.0) + w
        voroodi[d] = voroodi.get(d, 0.0) + w
    return {(s, d): khorooji[s] * voroodi[d] for s in khorooji for d in voroodi if s != d}


def seed_instance(nam, tokhm, max_ods=None):
    if nam == "fattree4":
        G, taghaza = fattree4()
        return G, taghaza, 1.0
    if nam in SHABAKEHAYE_SNDLIB:
        G, taghaza, zarib = sndlib(SHABAKEHAYE_SNDLIB[nam], tokhm, os.environ.get("LARM_HOUR", "busy"))
        if os.environ.get("LARM_MATRIX") == "gravity":
            taghaza = gravity(taghaza)
        return G, taghaza, zarib
    G, taghaza = repetita(NAMHAYE_REPETITA[nam])
    return G, namoone(taghaza, max_ods), 1.0
