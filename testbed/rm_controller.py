"""Route-mutation controller for OpenFlow 1.3 (Ryu).

On the first packet of a flow (packet-in at the ingress switch) the controller
picks one of the candidate paths from the ingress to the egress edge switch and
installs a forwarding rule on every switch along that path, with an idle
timeout. The path is chosen by the configured policy:

  sp    one shortest path per ingress-egress pair, ties between equal-cost
        paths broken at random (seeded) when the controller starts
  ecmp  a fixed hash of the 5-tuple over the equal-cost shortest paths
  urm   a uniform random candidate path (mutation without learning)
  larm  a candidate path drawn from a per-ingress-egress learning automaton
        whose reward is 1 - (busiest switch on the path), so it learns to
        route around whichever switch is filling up (this work)

Occupancy-aware policies added in revision (same candidates, no learning except
larm_retry). They use the controller's own count of live rules per switch, the
same count that admission control checks:

  greedy      the candidate with the best score 1 - (busiest switch on the
              path) - 0.3*(stretch-1) on the current counts, among candidates
              without a full switch; ties broken at random
  sp_retry    the shortest path unless it crosses a full switch, else the
              cheapest candidate that does not
  larm_retry  as larm, but a draw that crosses a full switch is credited 0 and
              the flow is drawn again among the candidates without a full switch

An epoch thread polls per-switch flow statistics, records occupancy, and (for
larm) credits and updates the automata. The controller never reads any host's
role or address beyond what it needs to forward; occupancy is the only signal.

Benign admission is scored per flow, at its first setup request, as in the
simulator. A packet that overtakes its own FlowMod to a downstream switch is
sent back along the flow's existing path, never re-routed. Hosts use static
ARP, so nothing is ever flooded (flooding in a fabric with loops would storm).

It imports the same automaton and path code as the offline simulator.
"""
import json
import os
import random
import sys
import time
import zlib

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.lib import hub
from ryu.lib.packet import ethernet, ipv4, packet, udp
from ryu.ofproto import ofproto_v1_3

sys.path.insert(0, os.environ.get("LARM_ROOT", "."))
from larm.automaton import PathAutomaton
from larm.paths import PathTable
from testbed.topo import TOPOS

LEARNING = ("larm", "larm_retry")


class RouteMutation(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = json.load(open(os.environ["RM_CONFIG"]))
        self.policy = cfg["policy"]
        self.k = cfg.get("k", 3)
        self.idle = cfg.get("idle", 10)
        self.epoch = cfg.get("epoch", 1.0)
        self.cap = cfg.get("cap", 1000)
        self.max_stretch = cfg.get("max_stretch", 2.5)
        self.logpath = cfg["log"]
        self.G = TOPOS[cfg["topo"]]()
        self.host_edge = {int(k): int(v) for k, v in cfg["host_edge"].items()}  # host id -> edge switch dpid
        # candidate paths between every pair of edge switches
        edges = sorted(set(self.host_edge.values()))
        self.ods = [(a, b) for a in edges for b in edges if a != b]
        self.pt = PathTable(self.G, self.ods, k=self.k, max_stretch=self.max_stretch)
        self.auto = {od: PathAutomaton(len(self.pt.cand[od])) for od in self.ods} \
            if self.policy in LEARNING else {}
        self._retry_fail = None
        self._tie = random.Random(cfg.get("seed", 0) + 7)
        tie = random.Random(cfg.get("seed", 0))
        self.sp_path = {od: self.pt.ecmp[od][tie.randrange(len(self.pt.ecmp[od]))] for od in self.ods}
        self.dp = {}            # dpid -> datapath
        self.port = {}          # (dpid, next_dpid) -> out_port, learned from LLDP-free static map
        self.port = cfg["ports"]  # {"dpid-nextdpid": port}
        self.port = {tuple(int(x) for x in k.split("-")): v for k, v in cfg["ports"].items()}
        self.host_port = {int(k): int(v) for k, v in cfg["host_port"].items()}  # dpid -> access port
        self.installed = {}     # node -> set(cookie) currently believed live
        self.live = {}          # node -> last known rule count (from stats)
        self.occ_log = []
        self.t_log = []         # wall-clock time of each completed poll round
        self.cookie = 0
        self.pending = []       # (od, idx, path) awaiting reward this epoch
        self.offered = 0        # benign setup requests (packet-ins), retries included
        self.admitted = 0       # benign setup requests that were installed
        # per-flow bookkeeping, keyed by the 5-tuple: admission is scored per
        # flow at its first setup request, as in the simulator
        self.flows = {}         # key -> {"first": admitted at first request, "ok": ever installed, "path": live path}
        self.cookie_key = {}    # path cookie -> flow key, to forget a path when its rules expire
        self.adv_paths = {}     # adversary key -> live path
        self._round_open = 0.0  # time the outstanding stats round was sent (0 = none)
        self.adv_port = cfg.get("adv_port", 9999)  # flows to this UDP port are adversary (routed SP, can't mutate)
        hub.spawn(self._epoch_loop)

    # ---- switch bring-up ------------------------------------------------
    @staticmethod
    def _node(dpid):
        # switches are created with dpid = node_id + 1
        return dpid - 1

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _features(self, ev):
        dp = ev.msg.datapath
        self.dp[self._node(dp.id)] = dp
        self.installed.setdefault(self._node(dp.id), set())
        ofp, psr = dp.ofproto, dp.ofproto_parser
        # table-miss -> controller
        self._add_flow(dp, 0, psr.OFPMatch(), [psr.OFPActionOutput(ofp.OFPP_CONTROLLER,
                       ofp.OFPCML_NO_BUFFER)], idle=0, prio=0)

    def _add_flow(self, dp, cookie, match, actions, idle, prio=10):
        ofp, psr = dp.ofproto, dp.ofproto_parser
        inst = [psr.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        dp.send_msg(psr.OFPFlowMod(datapath=dp, cookie=cookie, priority=prio,
                    match=match, instructions=inst, idle_timeout=idle,
                    flags=ofp.OFPFF_SEND_FLOW_REM))

    # ---- reactive routing ----------------------------------------------
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in(self, ev):
        msg = ev.msg
        dp = msg.datapath
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None:
            return
        ip = pkt.get_protocol(ipv4.ipv4)
        u = pkt.get_protocol(udp.udp)
        if ip is None or u is None:
            # hosts use static ARP; flooding in a fabric with loops would storm,
            # so anything that is not routable UDP is dropped
            self.n_other = getattr(self, "n_other", 0) + 1
            return
        self.n_udp = getattr(self, "n_udp", 0) + 1
        dst_h = self._host_of_mac(eth.dst)
        src_h = self._host_of_mac(eth.src)
        if dst_h is None or src_h is None:
            self.n_other = getattr(self, "n_other", 0) + 1
            return
        flow = dict(ipv4_src=ip.src, ipv4_dst=ip.dst, udp_src=u.src_port, udp_dst=u.dst_port)
        ing, egr = self.host_edge[src_h], self.host_edge[dst_h]
        adversary = (u.dst_port == self.adv_port)
        if ing == egr:
            self._install_flow(egr, flow, self.host_port[egr])
            self._resend(dp, msg)
            return
        od = (ing, egr)
        key = (ip.src, ip.dst, u.src_port, u.dst_port)
        if adversary and key in self.adv_paths:
            # rules already sent; this packet overtook a FlowMod downstream
            self._resend(dp, msg)
            return
        rec = None if adversary else self.flows.get(key)
        if rec is not None and rec["path"] is not None:
            # same race for a benign flow: keep its path, do not draw a new one
            self._resend(dp, msg)
            return
        if adversary:
            idx, path = 0, self.pt.cand[od][0]   # the adversary routes on the shortest path
        else:
            self._retry_fail = None
            idx, path = self._choose(od, key)
            self.offered += 1
            if self._retry_fail is not None and self.policy in LEARNING:
                # the first draw met a full switch: credit it 0, like a blocked flow
                self.pending.append((od, self._retry_fail[0], self._retry_fail[1], False))
        # admission control: drop the flow if any switch on the path is at capacity
        blocked = any(self.live.get(n, 0) >= self.cap for n in path)
        if not adversary and self.policy in LEARNING:
            # credit the automaton for every benign request: a blocked path is the
            # signal to route elsewhere (reward 0), an admitted one is rewarded
            # by how clear its busiest switch is.
            self.pending.append((od, idx, path, not blocked))
        if not adversary and rec is None:
            rec = self.flows[key] = {"first": not blocked, "ok": False, "path": None,
                                     "t0": time.time(), "p0": path}
        if blocked:
            return
        cookie = self._install_path_flow(path, egr, flow)
        self.cookie_key[cookie] = (adversary, key)
        if adversary:
            self.adv_paths[key] = path
        else:
            self.admitted += 1
            rec["ok"] = True
            rec["path"] = path
        self._resend(dp, msg)

    def _flow_match(self, dp, flow):
        return dp.ofproto_parser.OFPMatch(
            eth_type=0x0800, ip_proto=17,
            ipv4_src=flow["ipv4_src"], ipv4_dst=flow["ipv4_dst"],
            udp_src=flow["udp_src"], udp_dst=flow["udp_dst"])

    def _install_path_flow(self, path, egr, flow):
        self.cookie += 1
        cookie = self.cookie
        for a, b in zip(path[:-1], path[1:]):
            dp = self.dp.get(a)
            if dp is None:
                continue
            out = self.port[(a, b)]
            self._add_flow(dp, cookie, self._flow_match(dp, flow),
                           [dp.ofproto_parser.OFPActionOutput(out)], self.idle)
            self.installed[a].add(cookie)
            self.live[a] = self.live.get(a, 0) + 1   # optimistic; reconciled from stats each epoch
        self._install_flow(egr, flow, self.host_port[egr], cookie)
        return cookie

    def _install_flow(self, dpid, flow, out, cookie=None):
        dp = self.dp.get(dpid)
        if dp is None:
            return
        if cookie is None:
            self.cookie += 1
            cookie = self.cookie
        self._add_flow(dp, cookie, self._flow_match(dp, flow),
                       [dp.ofproto_parser.OFPActionOutput(out)], self.idle)
        self.installed[dpid].add(cookie)

    def _choose(self, od, key):
        cands = self.pt.cand[od]
        if self.policy == "sp":
            return 0, self.sp_path[od]
        if self.policy == "ecmp":
            # a fixed hash of the 5-tuple, as an ECMP switch would compute it
            ec = self.pt.ecmp[od]
            return None, ec[zlib.crc32(repr(key).encode()) % len(ec)]
        if self.policy == "urm":
            import random
            i = random.randrange(len(cands))
            return i, cands[i]
        if self.policy == "greedy":
            best, bi = None, []
            for i, p in enumerate(cands):
                if self._full(p):
                    sc = -1e9
                else:
                    hot = max(self.live.get(n, 0) / self.cap for n in p)
                    sc = 1.0 - hot - 0.3 * (self.pt.stretch(od, p) - 1.0)
                if best is None or sc > best + 1e-12:
                    best, bi = sc, [i]
                elif abs(sc - best) <= 1e-12:
                    bi.append(i)
            i = bi[self._tie.randrange(len(bi))]
            return i, cands[i]
        if self.policy == "sp_retry":
            if not self._full(self.sp_path[od]):
                return 0, self.sp_path[od]
            for i, p in enumerate(cands):      # candidates are in order of cost
                if not self._full(p):
                    return i, p
            return 0, self.sp_path[od]
        a = self.auto[od]
        i = a.choose()
        if self.policy == "larm_retry" and self._full(cands[i]):
            ok = [j for j in range(len(cands)) if j != i and not self._full(cands[j])]
            if ok:
                self._retry_fail = (i, cands[i])
                pe = [float(a.p_eff()[j]) for j in ok]
                j = self._tie.choices(ok, weights=pe)[0]
                return j, cands[j]
        return i, cands[i]

    def _full(self, path):
        return any(self.live.get(n, 0) >= self.cap for n in path)

    # ---- helpers --------------------------------------------------------
    def _host_of_mac(self, mac):
        # MAC 00:00:00:00:00:HH encodes host id HH-1 (as IP 10.0.0.HH)
        try:
            hid = int(mac.split(":")[-1], 16) - 1
        except ValueError:
            return None
        return hid if hid in self.host_edge else None

    def _resend(self, dp, msg):
        # send the buffered packet back out via the newly installed path
        self._out(dp, msg, dp.ofproto.OFPP_TABLE)

    def _out(self, dp, msg, port):
        ofp, psr = dp.ofproto, dp.ofproto_parser
        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        dp.send_msg(psr.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                    in_port=msg.match["in_port"],
                    actions=[psr.OFPActionOutput(port)], data=data))

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _removed(self, ev):
        self.installed.get(self._node(ev.msg.datapath.id), set()).discard(ev.msg.cookie)
        # once a rule of a flow's path has expired, its next packet is a new setup
        owner = self.cookie_key.pop(ev.msg.cookie, None)
        if owner is not None:
            adversary, key = owner
            if adversary:
                self.adv_paths.pop(key, None)
            elif key in self.flows:
                self.flows[key]["path"] = None

    # ---- epoch: poll occupancy, learn ----------------------------------
    def _epoch_loop(self):
        while True:
            hub.sleep(self.epoch)
            # one poll round at a time: while switches have not answered the
            # last round, wait; after 3 s re-ask only the switches still silent
            now = time.time()
            if self._round_open:
                if now - self._round_open < 3.0:
                    continue
                todo = [n for n in self.dp if n not in self._occ]
            else:
                self._occ = {}
                todo = list(self.dp)
            self._round_open = now
            for n in todo:
                dp = self.dp[n]
                dp.send_msg(dp.ofproto_parser.OFPFlowStatsRequest(dp))

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _stats(self, ev):
        node = self._node(ev.msg.datapath.id)
        n = sum(1 for s in ev.msg.body if s.priority >= 10)
        self.live[node] = n                # authoritative count reconciles optimistic increments
        self._occ = getattr(self, "_occ", {})
        self._occ[node] = n / self.cap
        # once we have all switches, log and (for larm) learn
        if len(self._occ) >= len(self.dp) and self.dp:
            occ = dict(self._occ)
            self.occ_log.append(occ)
            self.t_log.append(round(time.time(), 3))
            self._round_open = 0.0
            if self.policy in LEARNING and self.pending:
                load = occ
                for od, idx, path, admitted in self.pending:
                    if not admitted:
                        reward = 0.0        # the path hit a full switch
                    else:
                        hot = max(load.get(n, 0.0) for n in path)
                        st = self.pt.stretch(od, path)
                        reward = max(0.0, 1.0 - hot - 0.3 * (st - 1.0))
                    self.auto[od].credit(idx, reward)
                for od in self.auto:
                    self.auto[od].update()
                self.pending = []
            self._occ = {}
            try:
                nf = len(self.flows)
                first = sum(1 for r in self.flows.values() if r["first"])
                ever = sum(1 for r in self.flows.values() if r["ok"])
                json.dump({"occ": self.occ_log, "t": self.t_log,
                           "flows_offered": nf, "flows_admitted_first": first,
                           "flows_admitted_any": ever,
                           "admission": first / nf if nf else 1.0,
                           "req_offered": self.offered, "req_admitted": self.admitted,
                           "req_admission": self.admitted / self.offered if self.offered else 1.0,
                           "n_other": getattr(self, "n_other", 0), "n_udp": getattr(self, "n_udp", 0),
                           "flow_log": [[round(r["t0"], 2), r["p0"], r["first"]] for r in self.flows.values()]},
                          open(self.logpath, "w"))
            except OSError:
                pass
