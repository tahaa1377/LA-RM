import argparse
import json
import os
import subprocess
import time

from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel

import sys
sys.path.insert(0, os.environ.get("LARM_ROOT", "."))
from testbed.topo import TOPOS


def build(name_topolozhi):
    G = TOPOS[name_topolozhi]()
    net = Mininet(controller=None, switch=OVSSwitch, link=TCLink, autoSetMacs=False)
    ctrl = net.addController("c0", controller=RemoteController, ip="127.0.0.1", port=6653)
    sw = {n: net.addSwitch(f"s{n+1}", dpid=format(n + 1, "016x"),
                           datapath="user", protocols="OpenFlow13") for n in G.nodes()}
    yalha = sorted(G.nodes())
    host_edge, host_port, miyazbanha = {}, {}, {}
    ports = {}
    pcount = {n: 0 for n in G.nodes()}
    seen = set()
    for u, v in G.edges():
        if (v, u) in seen:
            continue
        seen.add((u, v))
        l = net.addLink(sw[u], sw[v])
        pu = sw[u].ports[l.intf1]
        pv = sw[v].ports[l.intf2]
        ports[(u, v)] = pu
        ports[(v, u)] = pv
    host_nodes = G.graph.get("edge_switches", yalha)
    for n in host_nodes:
        h = net.addHost(f"h{n+1}", ip=f"10.0.0.{n+1}/24",
                        mac="00:00:00:00:00:%02x" % (n + 1))
        l = net.addLink(h, sw[n])
        host_port[n] = sw[n].ports[l.intf2]
        host_edge[n] = n
        miyazbanha[n] = h
    return net, G, sw, miyazbanha, host_edge, host_port, ports


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topo", default="grid3")
    ap.add_argument("--policy", default="larm")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--cap", type=int, default=60)
    ap.add_argument("--idle", type=int, default=8)
    ap.add_argument("--flows", type=int, default=600, help="benign flows over the run")
    ap.add_argument("--bg", type=int, default=40, help="background long-lived flows to the center")
    ap.add_argument("--dur", type=int, default=40, help="run seconds")
    ap.add_argument("--attack", action="store_true",
                    help="run an occupancy-level adversary that holds long-lived flows on a bottleneck")
    ap.add_argument("--adv_src", type=int, default=0, help="adversary source host (edge switch id)")
    ap.add_argument("--adv_dst", type=int, default=5, help="adversary destination host (edge switch id)")
    ap.add_argument("--adv_n", type=int, default=90, help="long-lived adversary flows")
    ap.add_argument("--adv_port", type=int, default=9999, help="UDP port the controller treats as adversary")
    ap.add_argument("--k", type=int, default=3, help="candidate paths per pair")
    ap.add_argument("--count", default="poll", choices=["poll", "event"],
                    help="how the controller keeps its rule counts (see rm_controller.py)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    setLogLevel("warning")

    net, G, sw, miyazbanha, host_edge, host_port, ports = build(args.topo)
    log = os.path.abspath(args.out + ".occ")
    tanzim = {"policy": args.policy, "topo": args.topo, "seed": args.seed, "k": args.k, "idle": args.idle,
           "epoch": 1.0, "cap": args.cap, "max_stretch": 2.5, "log": log,
           "adv_port": args.adv_port, "count": args.count,
           "host_edge": {str(k): v for k, v in host_edge.items()},
           "host_port": {str(k): v for k, v in host_port.items()},
           "ports": {f"{a}-{b}": p for (a, b), p in ports.items()}}
    masire_tanzim = os.path.abspath(args.out + ".cfg")
    json.dump(tanzim, open(masire_tanzim, "w"))

    env = dict(os.environ, RM_CONFIG=masire_tanzim, LARM_ROOT=os.environ.get("LARM_ROOT", "."),
               PYTHONPATH=os.environ.get("LARM_ROOT", "."))
    ryu = subprocess.Popen([os.environ.get("RYU", "ryu-manager"), "--ofp-tcp-listen-port", "6653",
                            os.path.join(os.environ.get("LARM_ROOT", "."), "testbed/rm_controller.py")],
                           env=env, stdout=open(args.out + ".ryu", "w"), stderr=subprocess.STDOUT)
    t_traffic = None
    try:
        net.start()
        time.sleep(4)
        allh = sorted(miyazbanha)
        for n in allh:
            for m in allh:
                if n != m:
                    miyazbanha[n].cmd(f"arp -s 10.0.0.{m+1} 00:00:00:00:00:{m+1:02x}")
        for n in allh:
            mac = miyazbanha[n].cmd(f"cat /sys/class/net/{miyazbanha[n].name}-eth0/address").strip()
            if mac != "00:00:00:00:00:%02x" % (n + 1):
                raise RuntimeError(f"host {n} has MAC {mac}, expected n+1 encoding")
        tolid = os.path.join(os.environ.get("LARM_ROOT", "."), "testbed/flowgen.py")
        hlist = ",".join(str(h) for h in sorted(miyazbanha))
        if args.attack and args.adv_src in miyazbanha and args.adv_dst in miyazbanha:
            dst_ip = f"10.0.0.{args.adv_dst + 1}"
            miyazbanha[args.adv_src].cmd(
                f"python3 {tolid} --mode adv --dst {dst_ip} --port {args.adv_port} "
                f"--n {args.adv_n} --dur {args.dur} --seed {args.seed} >/dev/null 2>&1 &")
            time.sleep(6)
        t_traffic = time.time()
        for n in sorted(miyazbanha):
            miyazbanha[n].cmd(f"python3 {tolid} --mode alltoall --me {n} --hosts {hlist} "
                         f"--port 9100 --n {args.flows} --dur {args.dur} "
                         f"--seed {args.seed*100+n} >/dev/null 2>&1 &")
        time.sleep(args.dur + 6)
    finally:
        try:
            net.stop()
        except Exception:
            pass
        ryu.terminate()
        time.sleep(1)
    eshghal = {"occ": []}
    if os.path.exists(log):
        try:
            eshghal = json.load(open(log))
        except Exception:
            pass
    summary = summarize(eshghal, args, t_traffic)
    json.dump(summary, open(args.out, "w"), indent=1)
    print(json.dumps({k: summary[k] for k in ("policy", "peak_occ", "window_occ", "epochs", "admission")}))


def _adv_path(args):
    from larm.paths import PathTable
    G = TOPOS[args.topo]()
    od = (args.adv_src, args.adv_dst)
    pt = PathTable(G, [od], k=args.k, hadde_aksare_keshidegi=2.5)
    return list(pt.cand[od][0])


def _gini(meghdarha):
    v = sorted(x for x in meghdarha)
    n = len(v)
    s = sum(v)
    if n == 0 or s == 0:
        return 0.0
    tajammoei = sum((i + 1) * x for i, x in enumerate(v))
    return (2 * tajammoei) / (n * s) - (n + 1) / n


def summarize(eshghal, args, t_traffic=None):
    series = eshghal.get("occ", [])
    zamanha = eshghal.get("t", [])
    peaks = [max(e.values()) for e in series if e]
    peak = max(peaks) if peaks else 0.0
    garm = [max(e.values()) for e in series[5:] if e]
    sust = sum(garm) / len(garm) if garm else 0.0
    garme_dore = [e for e in series[5:] if e]
    gini = sum(_gini(list(e.values())) for e in garme_dore) / len(garme_dore) if garme_dore else 0.0
    total = [sum(e.values()) for e in garme_dore]
    mean_total = sum(total) / len(total) if total else 0.0
    panjere, win_e = [], []
    if t_traffic is not None and len(zamanha) == len(series):
        paein, bala = t_traffic + 0.25 * args.dur, t_traffic + args.dur
        win_e = [e for e, t in zip(series, zamanha) if e and paein <= t <= bala]
        panjere = [max(e.values()) for e in win_e]
    per_switch = ({k: round(sum(e[k] for e in win_e) / len(win_e), 4) for k in win_e[0]}
                  if win_e else {})
    win_gini = (sum(_gini(list(e.values())) for e in win_e) / len(win_e)) if win_e else None
    masire_mokhalef = _adv_path(args) if args.attack else []
    obour = set(masire_mokhalef[1:-1])
    hasteh = masire_mokhalef[len(masire_mokhalef) // 2] if masire_mokhalef else None
    fl = eshghal.get("flow_log", [])
    def share(radifha, test):
        return round(sum(1 for r in radifha if test(r[1])) / len(radifha), 4) if radifha else None
    late = [r for r in fl if t_traffic is not None and r[0] >= t_traffic + 0.25 * args.dur]
    early = [r for r in fl if t_traffic is not None and r[0] < t_traffic + 0.25 * args.dur]
    return {"policy": args.policy, "topo": args.topo, "seed": args.seed,
            "k": args.k, "cap": args.cap, "attack": bool(args.attack),
            "adv_n": args.adv_n if args.attack else 0, "dur": args.dur,
            "peak_occ": round(peak, 4),
            "sustained_occ": round(sust, 4), "epochs": len(series),
            "window_epochs": len(panjere),
            "window_occ": round(sum(panjere) / len(panjere), 4) if panjere else None,
            "window_full": round(sum(1 for x in panjere if x >= 1.0) / len(panjere), 4) if panjere else None,
            "flows_offered": eshghal.get("flows_offered", 0),
            "flows_admitted_first": eshghal.get("flows_admitted_first", 0),
            "flows_admitted_any": eshghal.get("flows_admitted_any", 0),
            "admission": round(eshghal.get("admission", 1.0), 4),
            "admission_any": round(eshghal.get("flows_admitted_any", 0) / eshghal["flows_offered"], 4)
            if eshghal.get("flows_offered") else 1.0,
            "req_offered": eshghal.get("req_offered", 0), "req_admitted": eshghal.get("req_admitted", 0),
            "req_admission": round(eshghal.get("req_admission", 1.0), 4),
            "load_gini": round(gini, 4), "mean_total_occ": round(mean_total, 2),
            "window_gini": round(win_gini, 4) if win_gini is not None else None,
            "window_switch_occ": per_switch,
            "adv_path": masire_mokhalef,
            "via_core": share(fl, lambda p: hasteh in p) if hasteh is not None else None,
            "via_core_early": share(early, lambda p: hasteh in p) if hasteh is not None else None,
            "via_core_late": share(late, lambda p: hasteh in p) if hasteh is not None else None,
            "via_transit": share(fl, lambda p: bool(obour & set(p))) if obour else None,
            "admission_late": round(sum(1 for r in late if r[2]) / len(late), 4) if late else None,
            "t_traffic": round(t_traffic, 3) if t_traffic else None,
            "series_t": [round(t - t_traffic, 2) for t in zamanha] if t_traffic and zamanha else [],
            "series_max": [round(max(e.values()), 4) for e in series if e]}


if __name__ == "__main__":
    main()
