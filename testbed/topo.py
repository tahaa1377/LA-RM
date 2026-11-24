import networkx as nx


def _fattree4():
    G = nx.Graph()
    G.add_nodes_from(range(8, 16))
    for pod in range(4):
        labeha = [2 * pod, 2 * pod + 1]
        for i, tajmi in enumerate([8 + 2 * pod, 9 + 2 * pod]):
            G.add_edge(tajmi, 16 + 2 * i, weight=1)
            for labe in labeha:
                G.add_edge(tajmi, labe, weight=1)
            G.add_edge(tajmi, 17 + 2 * i, weight=1)
    G.graph["edge_switches"] = list(range(8))
    return G.to_directed()


def _grid3():
    G = nx.Graph()
    for satr in range(3):
        for sotoon in range(3):
            n = 3 * satr + sotoon
            G.add_node(n)
            if sotoon < 2:
                G.add_edge(n, n + 1, weight=1)
            if satr < 2:
                G.add_edge(n, n + 3, weight=1)
    return G.to_directed()


TOPOS = {"fattree4": _fattree4, "grid3": _grid3}
