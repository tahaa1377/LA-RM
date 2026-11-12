import json
import os
import random
import sys
import time
import zlib

import numpy as np
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

LEARNING = ("larm", "larm_retry", "larm2", "larm2_nr")
POR = ("larm2", "larm2_nr")
TEKRAR = ("larm_retry", "larm2")


class RouteMutation(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tanzim = json.load(open(os.environ["RM_CONFIG"]))
        self.policy = tanzim["policy"]
        self.k = tanzim.get("k", 3)
        self.idle = tanzim.get("idle", 10)
        self.epoch = tanzim.get("epoch", 1.0)
        self.cap = tanzim.get("cap", 1000)
        self.max_stretch = tanzim.get("max_stretch", 2.5)
        self.logpath = tanzim["log"]
        self.G = TOPOS[tanzim["topo"]]()
        self.host_edge = {int(k): int(v) for k, v in tanzim["host_edge"].items()}
        yalha = sorted(set(self.host_edge.values()))
        self.ods = [(a, b) for a in yalha for b in yalha if a != b]
        self.pt = PathTable(self.G, self.ods, k=self.k, hadde_aksare_keshidegi=self.max_stretch)
        la_kw = {"a": 0.4} if self.policy in POR else {}
        self.auto = {od: PathAutomaton(len(self.pt.cand[od]), **la_kw) for od in self.ods} \
            if self.policy in LEARNING else {}
        self.count_mode = tanzim.get("count", "poll")
        self.count_gap = []
        self._retry_fail = None
        self._tie = random.Random(tanzim.get("seed", 0) + 7)
        tie = random.Random(tanzim.get("seed", 0))
        self.sp_path = {od: self.pt.ecmp[od][tie.randrange(len(self.pt.ecmp[od]))] for od in self.ods}
        self.dp = {}
        self.port = {}
        self.port = tanzim["ports"]
        self.port = {tuple(int(x) for x in k.split("-")): v for k, v in tanzim["ports"].items()}
        self.host_port = {int(k): int(v) for k, v in tanzim["host_port"].items()}
        self.installed = {}
        self.live = {}
        self.occ_log = []
        self.t_log = []
        self.cookie = 0
        self.pending = []
        self.offered = 0
        self.admitted = 0
        self.flows = {}
        self.cookie_key = {}
        self.adv_paths = {}
        self._round_open = 0.0
        self.adv_port = tanzim.get("adv_port", 9999)
        hub.spawn(self._epoch_loop)

    @staticmethod
    def _node(dpid):
        return dpid - 1

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _features(self, rooydad):
        dp = rooydad.msg.datapath
        self.dp[self._node(dp.id)] = dp
        self.installed.setdefault(self._node(dp.id), set())
        ofp, psr = dp.ofproto, dp.ofproto_parser
        self._add_flow(dp, 0, psr.OFPMatch(), [psr.OFPActionOutput(ofp.OFPP_CONTROLLER,
                       ofp.OFPCML_NO_BUFFER)], bikari=0, olaviyat=0)

    def _add_flow(self, dp, cookie, match, actions, bikari, olaviyat=10):
        ofp, psr = dp.ofproto, dp.ofproto_parser
        inst = [psr.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        dp.send_msg(psr.OFPFlowMod(datapath=dp, cookie=cookie, priority=olaviyat,
                    match=match, instructions=inst, idle_timeout=bikari,
                    flags=ofp.OFPFF_SEND_FLOW_REM))

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in(self, rooydad):
        payam = rooydad.msg
        dp = payam.datapath
        pkt = packet.Packet(payam.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None:
            return
        ip = pkt.get_protocol(ipv4.ipv4)
        u = pkt.get_protocol(udp.udp)
        if ip is None or u is None:
            self.n_other = getattr(self, "n_other", 0) + 1
            return
        self.n_udp = getattr(self, "n_udp", 0) + 1
        dst_h = self._host_of_mac(eth.dst)
        src_h = self._host_of_mac(eth.src)
        if dst_h is None or src_h is None:
            self.n_other = getattr(self, "n_other", 0) + 1
            return
        jaryan = dict(ipv4_src=ip.src, ipv4_dst=ip.dst, udp_src=u.src_port, udp_dst=u.dst_port)
        ing, egr = self.host_edge[src_h], self.host_edge[dst_h]
        mokhalef = (u.dst_port == self.adv_port)
        if ing == egr:
            self._install_flow(egr, jaryan, self.host_port[egr])
            self._resend(dp, payam)
            return
        od = (ing, egr)
        key = (ip.src, ip.dst, u.src_port, u.dst_port)
        if mokhalef and key in self.adv_paths:
            self._resend(dp, payam)
            return
        rekord = None if mokhalef else self.flows.get(key)
        if rekord is not None and rekord["path"] is not None:
            self._resend(dp, payam)
            return
        if mokhalef:
            shakhes, masir = 0, self.pt.cand[od][0]
        else:
            self._retry_fail = None
            shakhes, masir = self._choose(od, key)
            self.offered += 1
            if self._retry_fail is not None and self.policy in LEARNING:
                self.pending.append((od, self._retry_fail[0], self._retry_fail[1], False))
        blocked = any(self.live.get(n, 0) >= self.cap for n in masir)
        if not mokhalef and self.policy in LEARNING:
            self.pending.append((od, shakhes, masir, not blocked))
        if not mokhalef and rekord is None:
            rekord = self.flows[key] = {"first": not blocked, "ok": False, "path": None,
                                     "t0": time.time(), "p0": masir}
        if blocked:
            return
        cookie = self._install_path_flow(masir, egr, jaryan)
        self.cookie_key[cookie] = (mokhalef, key)
        if mokhalef:
            self.adv_paths[key] = masir
        else:
            self.admitted += 1
            rekord["ok"] = True
            rekord["path"] = masir
        self._resend(dp, payam)

    def _flow_match(self, dp, jaryan):
        return dp.ofproto_parser.OFPMatch(
            eth_type=0x0800, ip_proto=17,
            ipv4_src=jaryan["ipv4_src"], ipv4_dst=jaryan["ipv4_dst"],
            udp_src=jaryan["udp_src"], udp_dst=jaryan["udp_dst"])

    def _install_path_flow(self, masir, egr, jaryan):
        self.cookie += 1
        cookie = self.cookie
        for a, b in zip(masir[:-1], masir[1:]):
            dp = self.dp.get(a)
            if dp is None:
                continue
            khoroji = self.port[(a, b)]
            self._add_flow(dp, cookie, self._flow_match(dp, jaryan),
                           [dp.ofproto_parser.OFPActionOutput(khoroji)], self.idle)
            self.installed[a].add(cookie)
            self.live[a] = self.live.get(a, 0) + 1
        self._install_flow(egr, jaryan, self.host_port[egr], cookie)
        if self.count_mode == "event":
            self.live[egr] = self.live.get(egr, 0) + 1
        return cookie

    def _install_flow(self, dpid, jaryan, khoroji, cookie=None):
        dp = self.dp.get(dpid)
        if dp is None:
            return
        if cookie is None:
            self.cookie += 1
            cookie = self.cookie
        self._add_flow(dp, cookie, self._flow_match(dp, jaryan),
                       [dp.ofproto_parser.OFPActionOutput(khoroji)], self.idle)
        self.installed[dpid].add(cookie)

    def _choose(self, od, key):
        kandidha = self.pt.cand[od]
        if self.policy == "sp":
            return 0, self.sp_path[od]
        if self.policy == "ecmp":
            ec = self.pt.ecmp[od]
            return None, ec[zlib.crc32(repr(key).encode()) % len(ec)]
        if self.policy == "urm":
            import random
            i = random.randrange(len(kandidha))
            return i, kandidha[i]
        if self.policy == "greedy":
            behtarin, bi = None, []
            for i, p in enumerate(kandidha):
                if self._full(p):
                    sc = -1e9
                else:
                    dagh = max(self.live.get(n, 0) / self.cap for n in p)
                    sc = 1.0 - dagh - 0.3 * (self.pt.stretch(od, p) - 1.0)
                if behtarin is None or sc > behtarin + 1e-12:
                    behtarin, bi = sc, [i]
                elif abs(sc - behtarin) <= 1e-12:
                    bi.append(i)
            i = bi[self._tie.randrange(len(bi))]
            return i, kandidha[i]
        if self.policy == "sp_retry":
            if not self._full(self.sp_path[od]):
                return 0, self.sp_path[od]
            for i, p in enumerate(kandidha):
                if not self._full(p):
                    return i, p
            return 0, self.sp_path[od]
        a = self.auto[od]
        i = a.choose()
        if self.policy in TEKRAR and self._full(kandidha[i]):
            movafagh = [j for j in range(len(kandidha)) if j != i and not self._full(kandidha[j])]
            if movafagh:
                self._retry_fail = (i, kandidha[i])
                pe = [float(a.p_eff()[j]) for j in movafagh]
                j = self._tie.choices(movafagh, weights=pe)[0]
                return j, kandidha[j]
        return i, kandidha[i]

    def _full(self, masir):
        return any(self.live.get(n, 0) >= self.cap for n in masir)

    def _host_of_mac(self, mac):
        try:
            shenaseye_miyazban = int(mac.split(":")[-1], 16) - 1
        except ValueError:
            return None
        return shenaseye_miyazban if shenaseye_miyazban in self.host_edge else None

    def _resend(self, dp, payam):
        self._out(dp, payam, dp.ofproto.OFPP_TABLE)

    def _out(self, dp, payam, port):
        ofp, psr = dp.ofproto, dp.ofproto_parser
        data = payam.data if payam.buffer_id == ofp.OFP_NO_BUFFER else None
        dp.send_msg(psr.OFPPacketOut(datapath=dp, buffer_id=payam.buffer_id,
                    in_port=payam.match["in_port"],
                    actions=[psr.OFPActionOutput(port)], data=data))

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _removed(self, rooydad):
        gere = self._node(rooydad.msg.datapath.id)
        if self.count_mode == "event" and rooydad.msg.cookie in self.installed.get(gere, ()):
            self.live[gere] = max(0, self.live.get(gere, 0) - 1)
        self.installed.get(gere, set()).discard(rooydad.msg.cookie)
        owner = self.cookie_key.pop(rooydad.msg.cookie, None)
        if owner is not None:
            mokhalef, key = owner
            if mokhalef:
                self.adv_paths.pop(key, None)
            elif key in self.flows:
                self.flows[key]["path"] = None

    def _epoch_loop(self):
        while True:
            hub.sleep(self.epoch)
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
    def _stats(self, rooydad):
        gere = self._node(rooydad.msg.datapath.id)
        n = sum(1 for s in rooydad.msg.body if s.priority >= 10)
        self._gap = getattr(self, "_gap", 0)
        if self.count_mode == "event":
            self._gap = max(self._gap, abs(self.live.get(gere, 0) - n))
        else:
            self.live[gere] = n
        self._occ = getattr(self, "_occ", {})
        self._occ[gere] = n / self.cap
        if len(self._occ) >= len(self.dp) and self.dp:
            eshghal = dict(self._occ)
            self.occ_log.append(eshghal)
            self.t_log.append(round(time.time(), 3))
            self._round_open = 0.0
            self.count_gap.append(self._gap)
            self._gap = 0
            if self.policy in POR:
                for od, a in self.auto.items():
                    kandidha = self.pt.cand[od]
                    if len(kandidha) > 1:
                        a.credit_all(np.array([max(0.0, 1.0 - max(eshghal.get(n, 0.0) for n in p)
                                                   - 0.3 * (self.pt.stretch(od, p) - 1.0))
                                               for p in kandidha]))
                        a.update()
                self.pending = []
            elif self.policy in LEARNING and self.pending:
                load = eshghal
                for od, shakhes, masir, paziroofte in self.pending:
                    if not paziroofte:
                        padash = 0.0
                    else:
                        dagh = max(load.get(n, 0.0) for n in masir)
                        st = self.pt.stretch(od, masir)
                        padash = max(0.0, 1.0 - dagh - 0.3 * (st - 1.0))
                    self.auto[od].credit(shakhes, padash)
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
                           "count_mode": self.count_mode, "count_gap": self.count_gap,
                           "flow_log": [[round(r["t0"], 2), r["p0"], r["first"]] for r in self.flows.values()]},
                          open(self.logpath, "w"))
            except OSError:
                pass
