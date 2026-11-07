"""Network-level flow-table occupancy simulator.

One discrete-time model of an SDN where every switch on a flow's path holds one
rule for that flow while it is active, plus an idle timeout after its last
packet. Benign demand drives flow arrivals per OD pair. A low-rate adversary
keeps a set of rules alive on a chosen bottleneck switch. Routing policy decides
which candidate path each new flow takes. We measure, per switch, how full the
flow table gets, and what the routing costs in path length and control load.

Each run starts with a warm-up without attack, so tables reach their benign
steady state before the adversary chooses a target; all metrics are measured
after the warm-up. Benign arrivals and durations come from their own random
stream, so for a given seed every policy sees exactly the same benign traffic
(paired comparisons).

Within an epoch, expired rules are removed first; the adversary then tops up its
flows (it probes continuously, so it claims an entry freed by an expiry before a
benign flow can), and only then are the epoch's benign flows routed. With
atk_first=False the order of the last two steps is reversed: benign flows win
every race for a freed entry, a weaker adversary used as a robustness check.

This is an evaluation model for a defence; the adversary is represented only by
the occupancy it sustains, not by any packet-level tooling.
"""
import numpy as np

from .automaton import PathAutomaton
from .paths import PathTable


class Policy:
    SP = "sp"          # shortest path, ties between equal-cost paths broken at random per OD pair
    ECMP = "ecmp"      # equal-cost multipath, hashed per flow
    URM = "urm"        # uniform route mutation (MTD without learning)
    LARM = "larm"      # learning-automata route mutation (this work)
    # Baselines added in revision. They use the same candidate paths and the same
    # occupancy signal as LA-RM, but no learning:
    GREEDY = "greedy"  # occupancy-aware routing in the style of STAR/DIFF: each new flow
                       # takes the candidate with the best score 1 - max occupancy
                       # - beta*(stretch-1) on the *current* tables (no full switch if
                       # possible); deterministic up to random tie-breaking
    SPR = "sp_retry"   # shortest path with retry: if the shortest path crosses a full
                       # switch, take the cheapest candidate that does not
    LARMR = "larm_retry"  # LA-RM with retry: a draw that crosses a full switch is
                          # credited 0 and the flow is re-drawn among the candidates
                          # that avoid full switches (from the mixed vector)

    LEARNING = ("larm", "larm_retry")


class Sim:
    def __init__(self, G, dem, policy, k=4, cap=None, idle=10.0,
                 epoch=1.0, horizon=120.0, lam_scale=1.0, dur_median=10.0,
                 dur_sigma=0.6, stretch_pen=0.3, max_stretch=None,
                 attacker=None, atk_rules=0, seed=0, la_kw=None, reward_mode="load",
                 evict=False, smart_m=3, atk_reinstall=False, warmup=20.0,
                 retarget=None, atk_first=True):
        self.reward_mode = reward_mode
        self.atk_first = atk_first      # adversary tops up before the epoch's benign arrivals
        self.evict = evict              # single-switch detect-and-evict baseline
        self.smart_m = smart_m          # targets held by the smart (multi-target) adversary
        self.atk_reinstall = atk_reinstall  # attacker re-creates its rules each epoch (they look newest)
        self.warmup = warmup            # epochs of benign traffic before the attack starts
        # the adaptive and smart adversaries re-evaluate their targets once per
        # idle timeout: the time a rule they stop refreshing takes to lapse
        self.retarget = idle if retarget is None else retarget
        self._ema = None
        self.G = G
        self.nodes = list(G.nodes())
        self.policy = policy
        self.idle = idle
        self.epoch = epoch
        self.horizon = horizon
        self.dur_median = dur_median
        self.dur_sigma = dur_sigma
        self.stretch_pen = stretch_pen
        # separate random streams: benign traffic (identical across policies for a
        # seed), routing randomness, and the adversary's choices
        self.rng = np.random.default_rng([seed, 1])
        self.rng_route = np.random.default_rng([seed, 2])
        self.rng_atk = np.random.default_rng([seed, 3])
        self.ods = list(dem.keys())
        tot = sum(dem.values())
        # per-OD benign flow arrival rate (flows/s), scaled to target load
        self.lam = {od: lam_scale * dem[od] / tot for od in self.ods}
        self.pt = PathTable(G, self.ods, k=k, max_stretch=max_stretch)
        self.cap = cap if cap is not None else {n: 100 for n in self.nodes}
        if isinstance(self.cap, int):
            self.cap = {n: self.cap for n in self.nodes}
        # learning automaton per OD pair (LARM only)
        la_kw = la_kw or {}
        self.auto = {}
        if policy in Policy.LEARNING:
            for od in self.ods:
                r = len(self.pt.cand[od])
                self.auto[od] = PathAutomaton(r, rng=self.rng_route, **la_kw)
        # ECMP hash seed per OD; shortest path: one equal-cost path per OD, at random
        self.hash0 = {od: int(self.rng_route.integers(1 << 30)) for od in self.ods}
        self.sp_path = {od: self.pt.ecmp[od][int(self.rng_route.integers(len(self.pt.ecmp[od])))]
                        for od in self.ods}
        # live rules: node -> dict(rule_id -> expiry_time); attacker rules flagged "a"
        self.table = {n: {} for n in self.nodes}
        self.rid = 0
        self.attacker = attacker
        self.atk_rules = atk_rules
        self.atk_flows = {}     # attacker flow id -> {"tgt": switch, "path": path}
        self._tgt = None        # current target(s) of the adaptive / smart adversary
        self._tgt_t = None      # time of the last targeting decision
        self._static_target = None
        self._aware_target = None
        self._cross = {}        # (target, aware) -> OD pairs whose attack path crosses it
        self._dem = {n: 0 for n in self.nodes}   # benign flows routed through each switch since the last decision
        self.m = {"peak_occ": 0.0, "sum_occ": 0.0, "n_epoch": 0,
                  "installs": 0, "benign_installs": 0, "stretch_sum": 0.0,
                  "stretch_n": 0, "benign_lost": 0, "benign_offered": 0,
                  "benign_evicted": 0}
        self.trace = []   # busiest-switch occupancy per epoch (warm-up included)
        self.watch_od = None   # set to an OD pair to record its automaton's p each epoch
        self.p_trace = []
        self.adm_trace = []    # per-epoch benign admission rate (warm-up included)
        self.targets = []      # adversary target(s) per epoch, for diagnostics

    # ---- routing -------------------------------------------------------
    def _choose_path(self, od):
        cands = self.pt.cand[od]
        if self.policy == Policy.SP:
            return 0, self.sp_path[od]
        if self.policy == Policy.ECMP:
            ec = self.pt.ecmp[od]
            h = (self.hash0[od] + self.rid * 2654435761) % len(ec)
            return None, ec[h]
        if self.policy == Policy.URM:
            i = int(self.rng_route.integers(len(cands)))
            return i, cands[i]
        if self.policy == Policy.LARM:
            i = self.auto[od].choose()
            return i, cands[i]
        if self.policy == Policy.GREEDY:
            # score every candidate on the current tables; a candidate crossing a
            # full switch is never preferred to one that does not
            best, bi = None, []
            for i, p in enumerate(cands):
                if self._full(p):
                    sc = -1e9
                else:
                    hot = max(len(self.table[n]) / self.cap[n] for n in p)
                    sc = 1.0 - hot - self.stretch_pen * (self.pt.stretch(od, p) - 1.0)
                if best is None or sc > best + 1e-12:
                    best, bi = sc, [i]
                elif abs(sc - best) <= 1e-12:
                    bi.append(i)
            i = bi[int(self.rng_route.integers(len(bi)))] if len(bi) > 1 else bi[0]
            return i, cands[i]
        if self.policy == Policy.SPR:
            if not self._full(self.sp_path[od]):
                return 0, self.sp_path[od]
            for i, p in enumerate(cands):      # candidates are in order of cost
                if not self._full(p):
                    return i, p
            return 0, self.sp_path[od]
        if self.policy == Policy.LARMR:
            a = self.auto[od]
            i = a.choose()
            if not self._full(cands[i]):
                return i, cands[i]
            self._retry_fail = (i, cands[i])   # credited 0 at the end of the epoch
            ok = [j for j in range(len(cands)) if j != i and not self._full(cands[j])]
            if not ok:
                return i, cands[i]
            pe = a.p_eff()[ok]
            pe = pe / pe.sum()
            j = ok[int(self.rng_route.choice(len(ok), p=pe))]
            return j, cands[j]

    def _full(self, path):
        return any(len(self.table[n]) >= self.cap[n] for n in path)

    def _install(self, path, expiry, benign=True, count=True):
        """Try to install one rule per switch on path; fail if any switch full.

        With self.evict (the detect-and-evict baseline), a benign flow that meets a
        full switch does not fail outright: the switch evicts its oldest installed
        rule to make room. This is the single-switch eviction class of defence; it
        uses no attacker labels (it evicts by install order), so it also evicts
        long-lived benign rules, which we count as churn (benign rule evictions).
        """
        for n in path:
            if len(self.table[n]) >= self.cap[n] and benign:
                if self.evict:
                    t = self.table[n]
                    oldest = min(t, key=lambda kk: kk[1])  # smallest rule id = oldest
                    if oldest[0] == "b" and count:
                        self.m["benign_evicted"] += 1
                    del t[oldest]
                else:
                    if count:
                        self.m["benign_lost"] += 1
                    return False
        self.rid += 1
        for n in path:
            t = self.table[n]
            if len(t) < self.cap[n]:
                t[("a" if not benign else "b", self.rid)] = expiry
                if count:
                    self.m["installs"] += 1
                    if benign:
                        self.m["benign_installs"] += 1
        return True

    # ---- adversary -----------------------------------------------------
    def _benign_demand(self):
        """Benign flows routed through each switch since the last targeting
        decision, admitted or blocked: where filling a table blocks the most
        benign traffic. (Counting current benign rules instead would make the
        adversary abandon a switch it had already filled, since blocked flows
        hold no rules.)"""
        d = dict(self._dem)
        self._dem = {n: 0 for n in self.nodes}
        return d

    def _fixed_target(self):
        import networkx as nx
        if self.attacker == "static":
            if self._static_target is None:
                bc = nx.betweenness_centrality(self.G, weight="weight")
                self._static_target = max(bc, key=bc.get)
            return self._static_target
        # mutation-aware: knows the defender's candidate-path sets and aims at the
        # least-avoidable switch: the one that the most benign demand cannot avoid
        # (every candidate of those OD pairs crosses it), ties broken by the
        # demand-weighted share of candidate paths that cross it
        if self._aware_target is None:
            unavoid = {n: 0.0 for n in self.nodes}
            share = {n: 0.0 for n in self.nodes}
            for od in self.ods:
                cands = self.pt.cand[od]
                kk = len(cands)
                for n in self.nodes:
                    c = sum(1 for p in cands if n in p)
                    if c == kk:
                        unavoid[n] += self.lam[od]
                    if c:
                        share[n] += self.lam[od] * c / kk
            self._aware_target = max(self.nodes, key=lambda n: (round(unavoid[n], 12), share[n]))
        return self._aware_target

    def _targets(self, now):
        """Current target switch(es) with their share of the rule budget."""
        if self.attacker in ("static", "aware"):
            return [(self._fixed_target(), self.atk_rules)]
        due = self._tgt_t is None or now - self._tgt_t >= self.retarget - 1e-9
        if not due:
            if self.attacker == "smart":
                per = max(1, self.atk_rules // len(self._tgt))
                return [(t, per) for t in self._tgt]
            return [(self._tgt, self.atk_rules)]
        demand = self._benign_demand()
        self._tgt_t = now
        if self.attacker == "smart":
            # the top-m switches by benign demand, smoothed across decisions
            if self._ema is None:
                self._ema = dict(demand)
            else:
                for n in self.nodes:
                    self._ema[n] = 0.6 * self._ema[n] + 0.4 * demand[n]
            self._tgt = sorted(self.nodes, key=lambda n: -self._ema[n])[:max(1, self.smart_m)]
            per = max(1, self.atk_rules // len(self._tgt))
            return [(t, per) for t in self._tgt]
        # adaptive: the switch through which the most benign flows were routed.
        # Re-aiming leaves the old target's rules to lapse while the new ones are
        # added, so the adversary moves only for a clear gain (25% more demand).
        best = max(self.nodes, key=lambda n: demand[n])
        if self._tgt is None or demand[best] > 1.25 * demand[self._tgt]:
            self._tgt = best
        return [(self._tgt, self.atk_rules)]

    def _attack_path(self, od, tgt, aware):
        cands = self.pt.cand[od]
        if not aware and tgt in cands[0]:
            return cands[0]
        for p in cands:
            if tgt in p:
                return p
        return None

    def _crossing(self, tgt, aware):
        key = (tgt, aware)
        if key not in self._cross:
            self._cross[key] = [od for od in self.ods if self._attack_path(od, tgt, aware) is not None]
        return self._cross[key]

    def _adversary_refresh(self, now):
        """Keep at most atk_rules attacker flows alive, all aimed at the current
        target(s). Each flow holds one rule on every switch of its path; the
        adversary refreshes the flows that cross a current target, and a flow it
        stops refreshing lapses after the idle timeout like any other rule. New
        flows are added only while fewer than atk_rules are alive, so the budget
        bounds the adversary's footprint at all times, including after it re-aims.
        Occupancy level only (no packet tooling)."""
        if not self.atk_rules or self.attacker in (None, "none"):
            return
        targets = self._targets(now)
        self.targets.append([t for t, _ in targets])
        aware = self.attacker == "aware"
        if self.atk_reinstall:
            # the attacker re-creates its rules every epoch, so they are always the
            # newest entries (an oldest-first eviction then removes benign rules)
            for n in self.nodes:
                self.table[n] = {k: e for k, e in self.table[n].items() if k[0] != "a"}
            self.atk_flows = {}
        # forget flows whose rule on their target has lapsed
        self.atk_flows = {f: v for f, v in self.atk_flows.items() if ("a", f) in self.table[v["tgt"]]}
        alive_on = {t: 0 for t, _ in targets}
        for f, v in self.atk_flows.items():
            if v["tgt"] not in alive_on:
                # a flow kept from an earlier target that also crosses a current one
                for t, _ in targets:
                    if t in v["path"] and ("a", f) in self.table[t]:
                        v["tgt"] = t
                        break
            if v["tgt"] in alive_on:
                alive_on[v["tgt"]] += 1
                for n in v["path"]:
                    if ("a", f) in self.table[n]:
                        self.table[n][("a", f)] = now + self.idle
        free = self.atk_rules - len(self.atk_flows)
        for tgt, share in targets:
            need = min(share - alive_on[tgt], free)
            crossing = self._crossing(tgt, aware)
            tries = 0
            while need > 0 and crossing and tries < 3 * share:
                tries += 1
                if len(self.table[tgt]) >= self.cap[tgt]:
                    break
                od = crossing[int(self.rng_atk.integers(len(crossing)))]
                path = self._attack_path(od, tgt, aware)
                self.rid += 1
                for n in path:
                    if len(self.table[n]) < self.cap[n]:
                        self.table[n][("a", self.rid)] = now + self.idle
                self.atk_flows[self.rid] = {"tgt": tgt, "path": path}
                need -= 1
                free -= 1

    # ---- main loop -----------------------------------------------------
    def run(self):
        dt = self.epoch
        t = 0.0
        while t < self.horizon - 1e-9:
            measuring = t >= self.warmup - 1e-9
            # 1. expire rules
            for n in self.nodes:
                self.table[n] = {k: e for k, e in self.table[n].items() if e > t}
            # 2. the adversary keeps its rules alive and claims freed entries
            #    (after the warm-up); with atk_first=False it acts after step 3
            if measuring and self.atk_first:
                self._adversary_refresh(t)
            # 3. benign arrivals this epoch (Poisson per OD), from the traffic stream
            pend = {}
            off, lost = 0, 0
            for od in self.ods:
                nnew = int(self.rng.poisson(self.lam[od] * dt))
                for _ in range(nnew):
                    dur = float(self.rng.lognormal(np.log(self.dur_median), self.dur_sigma))
                    self._retry_fail = None
                    i, path = self._choose_path(od)
                    if self._retry_fail is not None and self.policy in Policy.LEARNING:
                        # the first draw met a full switch: it earns 0, like a block
                        pend.setdefault(od, []).append((self._retry_fail[0], self._retry_fail[1], False))
                    for n in path:
                        self._dem[n] += 1
                    ok = self._install(path, t + dur + self.idle, benign=True, count=measuring)
                    off += 1
                    if not ok:
                        lost += 1
                    if measuring:
                        self.m["benign_offered"] += 1
                        st = self.pt.stretch(od, path)
                        self.m["stretch_sum"] += st
                        self.m["stretch_n"] += 1
                    if self.policy in Policy.LEARNING:
                        pend.setdefault(od, []).append((i, path, ok))
            if measuring and not self.atk_first:
                self._adversary_refresh(t)
            # 4. occupancy measurement
            occ = max(len(self.table[n]) / self.cap[n] for n in self.nodes)
            self.trace.append(occ)
            self.adm_trace.append(1.0 - lost / off if off else 1.0)
            if measuring:
                self.m["peak_occ"] = max(self.m["peak_occ"], occ)
                self.m["sum_occ"] += occ
                self.m["n_epoch"] += 1
            # 5. learning: reward is path-local so paths are distinguishable.
            # A blocked flow earns 0; an admitted one earns
            # 1 - (busiest switch on its path) - stretch penalty.
            if self.policy in Policy.LEARNING:
                load = {n: len(self.table[n]) / self.cap[n] for n in self.nodes}
                for od, choices in pend.items():
                    for i, path, ok in choices:
                        if self.reward_mode == "noise":
                            reward = float(self.rng_route.random())  # no-information control
                        elif not ok:
                            reward = 0.0
                        else:
                            st = self.pt.stretch(od, path)
                            hot = max(load[n] for n in path)
                            reward = max(0.0, 1.0 - hot - self.stretch_pen * (st - 1.0))
                        self.auto[od].credit(i, reward)
                for od in self.ods:
                    self.auto[od].update()
                if self.watch_od is not None and self.watch_od in self.auto:
                    self.p_trace.append(self.auto[self.watch_od].p.copy())
            t += dt
        return self.summary()

    def summary(self):
        m = self.m
        ne = max(1, m["n_epoch"])
        span = max(self.epoch, self.horizon - self.warmup)
        return {
            "policy": self.policy,
            "peak_occ": round(m["peak_occ"], 4),
            "sustained_occ": round(m["sum_occ"] / ne, 4),
            "mean_stretch": round(m["stretch_sum"] / max(1, m["stretch_n"]), 4),
            "installs_per_s": round(m["installs"] / span, 2),
            "benign_lost": m["benign_lost"],
            "benign_offered": m["benign_offered"],
            "benign_evicted": m["benign_evicted"],
            "churn": round(m["benign_evicted"] / max(1, m["benign_offered"]), 4),
            "admission": round(1.0 - m["benign_lost"] / max(1, m["benign_offered"]), 4),
        }
