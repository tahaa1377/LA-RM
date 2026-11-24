import numpy as np

from .automaton import PathAutomaton
from .paths import PathTable


class Policy:
    SP = "sp"
    ECMP = "ecmp"
    URM = "urm"
    LARM = "larm"
    GREEDY = "greedy"
    SPR = "sp_retry"
    LARMR = "larm_retry"
    GREEDY_POLL = "greedy_poll"

    LARM2 = "larm2"
    LARM2_NR = "larm2_nr"

    LEARNING = ("larm", "larm_retry")


_PT_CACHE = {}


def _path_table(G, ods, nerkh, k, hadde_aksare_keshidegi, halat):
    majmoo = sum(nerkh.values()) or 1.0
    key = (id(G), k, hadde_aksare_keshidegi, halat,
           tuple((od, round(nerkh[od] / majmoo, 12)) for od in ods) if halat in ("np", "div") else tuple(ods))
    pt = _PT_CACHE.get(key)
    if pt is None:
        pt = _PT_CACHE[key] = PathTable(G, ods, k=k, hadde_aksare_keshidegi=hadde_aksare_keshidegi, halat=halat, nerkh=nerkh)
    return pt


class Sim:
    def __init__(self, G, taghaza, policy, k=4, zarfiat=None, bikari=10.0,
                 dore=1.0, ofogh=120.0, maghyase_nerkh=1.0, miyaneye_modat=10.0,
                 sigmaye_modat=0.6, jarimeye_keshidegi=0.3, hadde_aksare_keshidegi=None,
                 hamlegar=None, ghavanine_hamle=0, tokhm=0, la_kw=None, reward_mode="load",
                 ekhraj=False, smart_m=3, hamle_nasbe_mojadad=False, garmkardan=20.0,
                 retarget=None, hamle_avval=True, halate_kandid="yen", kandidhaye_hamle=None, la_full=False):
        self.policy_name = policy
        if policy in (Policy.LARM2, Policy.LARM2_NR):
            la_full = True
            la_kw = dict({"a": 0.4}, **(la_kw or {}))
            policy = Policy.LARMR if policy == Policy.LARM2 else Policy.LARM
        self.reward_mode = reward_mode
        self.la_full = la_full
        self.atk_first = hamle_avval
        self.evict = ekhraj
        self.smart_m = smart_m
        self.atk_reinstall = hamle_nasbe_mojadad
        self.warmup = garmkardan
        self.retarget = bikari if retarget is None else retarget
        self._ema = None
        self.G = G
        self.nodes = list(G.nodes())
        self.policy = policy
        self.idle = bikari
        self.epoch = dore
        self.horizon = ofogh
        self.dur_median = miyaneye_modat
        self.dur_sigma = sigmaye_modat
        self.stretch_pen = jarimeye_keshidegi
        self.rng = np.random.default_rng([tokhm, 1])
        self.rng_route = np.random.default_rng([tokhm, 2])
        self.rng_atk = np.random.default_rng([tokhm, 3])
        self.ods = list(taghaza.keys())
        majmoo = sum(taghaza.values())
        self.lam = {od: maghyase_nerkh * taghaza[od] / majmoo for od in self.ods}
        self.pt = _path_table(G, self.ods, self.lam, k, hadde_aksare_keshidegi, halate_kandid)
        self.pt_atk = self.pt if kandidhaye_hamle is None else _path_table(
            G, self.ods, self.lam, kandidhaye_hamle[0], hadde_aksare_keshidegi, kandidhaye_hamle[1])
        self.cap = zarfiat if zarfiat is not None else {n: 100 for n in self.nodes}
        if isinstance(self.cap, int):
            self.cap = {n: self.cap for n in self.nodes}
        la_kw = la_kw or {}
        self.auto = {}
        if policy in Policy.LEARNING:
            for od in self.ods:
                r = len(self.pt.cand[od])
                self.auto[od] = PathAutomaton(r, rng=self.rng_route, **la_kw)
        if self.auto and self.la_full:
            self._prep_full()
        self.hash0 = {od: int(self.rng_route.integers(1 << 30)) for od in self.ods}
        self.sp_path = {od: self.pt.ecmp[od][int(self.rng_route.integers(len(self.pt.ecmp[od])))]
                        for od in self.ods}
        self.table = {n: {} for n in self.nodes}
        self.rid = 0
        self.attacker = hamlegar
        self.atk_rules = ghavanine_hamle
        self.atk_flows = {}
        self._tgt = None
        self._tgt_t = None
        self._static_target = None
        self._aware_target = None
        self._cross = {}
        self._dem = {n: 0 for n in self.nodes}
        self.m = {"peak_occ": 0.0, "sum_occ": 0.0, "n_epoch": 0,
                  "installs": 0, "benign_installs": 0, "stretch_sum": 0.0,
                  "stretch_n": 0, "benign_lost": 0, "benign_offered": 0,
                  "benign_evicted": 0, "stretch_adm_sum": 0.0, "stretch_adm_n": 0}
        self._poll = {n: 0 for n in self.nodes}
        self.ol_trace = []
        self.trace = []
        self.watch_od = None
        self.p_trace = []
        self.adm_trace = []
        self.targets = []
        self.nfull_trace = []

    def _prep_full(self):
        shakhes = {n: j for j, n in enumerate(self.nodes)}
        pad = len(self.nodes)
        kmax = max(len(self.pt.cand[od]) for od in self.ods)
        lmax = max(len(p) for od in self.ods for p in self.pt.cand[od])
        self._fp = np.full((len(self.ods), kmax, lmax), pad, dtype=np.int64)
        self._fpen = np.zeros((len(self.ods), kmax))
        self._fn = np.array([len(self.pt.cand[od]) for od in self.ods])
        for a, od in enumerate(self.ods):
            for i, p in enumerate(self.pt.cand[od]):
                self._fp[a, i, :len(p)] = [shakhes[n] for n in p]
                self._fpen[a, i] = self.stretch_pen * (self.pt.stretch(od, p) - 1.0)
        self._fcap = np.array([self.cap[n] for n in self.nodes], dtype=float)

    def _credit_full(self):
        eshghal = np.zeros(len(self.nodes) + 1)
        eshghal[:-1] = np.array([len(self.table[n]) for n in self.nodes]) / self._fcap
        dagh = eshghal[self._fp].max(axis=2)
        rew = np.maximum(0.0, 1.0 - dagh - self._fpen)
        for a, od in enumerate(self.ods):
            r = self._fn[a]
            if r > 1:
                self.auto[od].credit_all(rew[a, :r])

    def _choose_path(self, od):
        kandidha = self.pt.cand[od]
        if self.policy == Policy.SP:
            return 0, self.sp_path[od]
        if self.policy == Policy.ECMP:
            ec = self.pt.ecmp[od]
            h = (self.hash0[od] + self.rid * 2654435761) % len(ec)
            return None, ec[h]
        if self.policy == Policy.URM:
            i = int(self.rng_route.integers(len(kandidha)))
            return i, kandidha[i]
        if self.policy == Policy.LARM:
            i = self.auto[od].choose()
            return i, kandidha[i]
        if self.policy in (Policy.GREEDY, Policy.GREEDY_POLL):
            if self.policy == Policy.GREEDY:
                cnt = lambda n: len(self.table[n])
            else:
                cnt = self._poll.__getitem__
            behtarin, bi = None, []
            for i, p in enumerate(kandidha):
                if any(cnt(n) >= self.cap[n] for n in p):
                    sc = -1e9
                else:
                    dagh = max(cnt(n) / self.cap[n] for n in p)
                    sc = 1.0 - dagh - self.stretch_pen * (self.pt.stretch(od, p) - 1.0)
                if behtarin is None or sc > behtarin + 1e-12:
                    behtarin, bi = sc, [i]
                elif abs(sc - behtarin) <= 1e-12:
                    bi.append(i)
            i = bi[int(self.rng_route.integers(len(bi)))] if len(bi) > 1 else bi[0]
            return i, kandidha[i]
        if self.policy == Policy.SPR:
            if not self._full(self.sp_path[od]):
                return 0, self.sp_path[od]
            for i, p in enumerate(kandidha):
                if not self._full(p):
                    return i, p
            return 0, self.sp_path[od]
        if self.policy == Policy.LARMR:
            a = self.auto[od]
            i = a.choose()
            if not self._full(kandidha[i]):
                return i, kandidha[i]
            self._retry_fail = (i, kandidha[i])
            movafagh = [j for j in range(len(kandidha)) if j != i and not self._full(kandidha[j])]
            if not movafagh:
                return i, kandidha[i]
            pe = a.p_eff()[movafagh]
            pe = pe / pe.sum()
            j = movafagh[int(self.rng_route.choice(len(movafagh), p=pe))]
            return j, kandidha[j]

    def _full(self, masir):
        return any(len(self.table[n]) >= self.cap[n] for n in masir)

    def _install(self, masir, engheza, salem=True, shomaresh=True):
        for n in masir:
            if len(self.table[n]) >= self.cap[n] and salem:
                if self.evict:
                    t = self.table[n]
                    ghadimitarin = min(t, key=lambda kk: kk[1])
                    if ghadimitarin[0] == "b" and shomaresh:
                        self.m["benign_evicted"] += 1
                    del t[ghadimitarin]
                else:
                    if shomaresh:
                        self.m["benign_lost"] += 1
                    return False
        self.rid += 1
        for n in masir:
            t = self.table[n]
            if len(t) < self.cap[n]:
                t[("a" if not salem else "b", self.rid)] = engheza
                if shomaresh:
                    self.m["installs"] += 1
                    if salem:
                        self.m["benign_installs"] += 1
        return True

    def _benign_demand(self):
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
        if self._aware_target is None:
            unavoid = {n: 0.0 for n in self.nodes}
            share = {n: 0.0 for n in self.nodes}
            for od in self.ods:
                kandidha = self.pt.cand[od]
                kk = len(kandidha)
                for n in self.nodes:
                    c = sum(1 for p in kandidha if n in p)
                    if c == kk:
                        unavoid[n] += self.lam[od]
                    if c:
                        share[n] += self.lam[od] * c / kk
            self._aware_target = max(self.nodes, key=lambda n: (round(unavoid[n], 12), share[n]))
        return self._aware_target

    def _targets(self, now):
        if self.attacker in ("static", "aware"):
            return [(self._fixed_target(), self.atk_rules)]
        due = self._tgt_t is None or now - self._tgt_t >= self.retarget - 1e-9
        if not due:
            if self.attacker == "smart":
                per = max(1, self.atk_rules // len(self._tgt))
                return [(t, per) for t in self._tgt]
            return [(self._tgt, self.atk_rules)]
        bare_taghaza = self._benign_demand()
        self._tgt_t = now
        if self.attacker == "smart":
            if self._ema is None:
                self._ema = dict(bare_taghaza)
            else:
                for n in self.nodes:
                    self._ema[n] = 0.6 * self._ema[n] + 0.4 * bare_taghaza[n]
            self._tgt = sorted(self.nodes, key=lambda n: -self._ema[n])[:max(1, self.smart_m)]
            per = max(1, self.atk_rules // len(self._tgt))
            return [(t, per) for t in self._tgt]
        behtarin = max(self.nodes, key=lambda n: bare_taghaza[n])
        if self._tgt is None or bare_taghaza[behtarin] > 1.25 * bare_taghaza[self._tgt]:
            self._tgt = behtarin
        return [(self._tgt, self.atk_rules)]

    def _attack_path(self, od, hadaf, agah):
        kandidha = self.pt_atk.cand[od]
        if not agah and hadaf in kandidha[0]:
            return kandidha[0]
        for p in kandidha:
            if hadaf in p:
                return p
        return None

    def _crossing(self, hadaf, agah):
        key = (hadaf, agah)
        if key not in self._cross:
            self._cross[key] = [od for od in self.ods if self._attack_path(od, hadaf, agah) is not None]
        return self._cross[key]

    def _adversary_refresh(self, now):
        if not self.atk_rules or self.attacker in (None, "none"):
            return
        hadafha = self._targets(now)
        self.targets.append([t for t, _ in hadafha])
        agah = self.attacker == "aware"
        if self.atk_reinstall:
            for n in self.nodes:
                self.table[n] = {k: e for k, e in self.table[n].items() if k[0] != "a"}
            self.atk_flows = {}
        self.atk_flows = {f: v for f, v in self.atk_flows.items() if ("a", f) in self.table[v["tgt"]]}
        zende_roye = {t: 0 for t, _ in hadafha}
        for f, v in self.atk_flows.items():
            if v["tgt"] not in zende_roye:
                for t, _ in hadafha:
                    if t in v["path"] and ("a", f) in self.table[t]:
                        v["tgt"] = t
                        break
            if v["tgt"] in zende_roye:
                zende_roye[v["tgt"]] += 1
                for n in v["path"]:
                    if ("a", f) in self.table[n]:
                        self.table[n][("a", f)] = now + self.idle
        azad = self.atk_rules - len(self.atk_flows)
        for hadaf, share in hadafha:
            niaz = min(share - zende_roye[hadaf], azad)
            crossing = self._crossing(hadaf, agah)
            talashha = 0
            while niaz > 0 and crossing and talashha < 3 * share:
                talashha += 1
                if len(self.table[hadaf]) >= self.cap[hadaf]:
                    break
                od = crossing[int(self.rng_atk.integers(len(crossing)))]
                masir = self._attack_path(od, hadaf, agah)
                self.rid += 1
                for n in masir:
                    if len(self.table[n]) < self.cap[n]:
                        self.table[n][("a", self.rid)] = now + self.idle
                self.atk_flows[self.rid] = {"tgt": hadaf, "path": masir}
                niaz -= 1
                azad -= 1

    def run(self):
        dt = self.epoch
        t = 0.0
        while t < self.horizon - 1e-9:
            measuring = t >= self.warmup - 1e-9
            for n in self.nodes:
                self.table[n] = {k: e for k, e in self.table[n].items() if e > t}
            if measuring and self.atk_first:
                self._adversary_refresh(t)
            montazer = {}
            off, az_dast_rafte = 0, 0
            for od in self.ods:
                tedade_jadid = int(self.rng.poisson(self.lam[od] * dt))
                for _ in range(tedade_jadid):
                    modat = float(self.rng.lognormal(np.log(self.dur_median), self.dur_sigma))
                    self._retry_fail = None
                    i, masir = self._choose_path(od)
                    if self._retry_fail is not None and self.policy in Policy.LEARNING:
                        montazer.setdefault(od, []).append((self._retry_fail[0], self._retry_fail[1], False))
                    for n in masir:
                        self._dem[n] += 1
                    movafagh = self._install(masir, t + modat + self.idle, salem=True, shomaresh=measuring)
                    off += 1
                    if not movafagh:
                        az_dast_rafte += 1
                    if measuring:
                        self.m["benign_offered"] += 1
                        st = self.pt.stretch(od, masir)
                        self.m["stretch_sum"] += st
                        self.m["stretch_n"] += 1
                        if movafagh:
                            self.m["stretch_adm_sum"] += st
                            self.m["stretch_adm_n"] += 1
                    if self.policy in Policy.LEARNING:
                        montazer.setdefault(od, []).append((i, masir, movafagh))
            if measuring and not self.atk_first:
                self._adversary_refresh(t)
            eshghal = max(len(self.table[n]) / self.cap[n] for n in self.nodes)
            self.trace.append(eshghal)
            self.adm_trace.append(1.0 - az_dast_rafte / off if off else 1.0)
            self.ol_trace.append((off, az_dast_rafte))
            if self.policy == Policy.GREEDY_POLL:
                self._poll = {n: len(self.table[n]) for n in self.nodes}
            if measuring:
                self.nfull_trace.append(sum(1 for n in self.nodes if len(self.table[n]) >= self.cap[n]))
                self.m["peak_occ"] = max(self.m["peak_occ"], eshghal)
                self.m["sum_occ"] += eshghal
                self.m["n_epoch"] += 1
            if self.policy in Policy.LEARNING and self.la_full:
                self._credit_full()
                for od in self.ods:
                    self.auto[od].update()
                if self.watch_od is not None and self.watch_od in self.auto:
                    self.p_trace.append(self.auto[self.watch_od].p.copy())
            elif self.policy in Policy.LEARNING:
                load = {n: len(self.table[n]) / self.cap[n] for n in self.nodes}
                for od, choices in montazer.items():
                    for i, masir, movafagh in choices:
                        if self.reward_mode == "noise":
                            padash = float(self.rng_route.random())
                        elif not movafagh:
                            padash = 0.0
                        else:
                            st = self.pt.stretch(od, masir)
                            dagh = max(load[n] for n in masir)
                            padash = max(0.0, 1.0 - dagh - self.stretch_pen * (st - 1.0))
                        self.auto[od].credit(i, padash)
                for od in self.ods:
                    self.auto[od].update()
                if self.watch_od is not None and self.watch_od in self.auto:
                    self.p_trace.append(self.auto[self.watch_od].p.copy())
            t += dt
        return self.summary()

    def summary(self):
        m = self.m
        ne = max(1, m["n_epoch"])
        baze = max(self.epoch, self.horizon - self.warmup)
        return {
            "policy": self.policy_name,
            "peak_occ": round(m["peak_occ"], 4),
            "sustained_occ": round(m["sum_occ"] / ne, 4),
            "mean_stretch": round(m["stretch_sum"] / max(1, m["stretch_n"]), 4),
            "mean_stretch_admitted": round(m["stretch_adm_sum"] / max(1, m["stretch_adm_n"]), 4),
            "installs_per_s": round(m["installs"] / baze, 2),
            "benign_lost": m["benign_lost"],
            "benign_offered": m["benign_offered"],
            "benign_evicted": m["benign_evicted"],
            "churn": round(m["benign_evicted"] / max(1, m["benign_offered"]), 4),
            "admission": round(1.0 - m["benign_lost"] / max(1, m["benign_offered"]), 4),
        }
