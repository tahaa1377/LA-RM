import math

import numpy as np


def entropy(p):
    q = p[p > 0]
    return float(-(q * np.log(q)).sum())


class PathAutomaton:
    def __init__(self, r, a=0.05, eps=0.1, hmin_frac=0.5, forget=0.9,
                 prior_w=1.0, tie=0.01, rng=None, d0=0.5):
        self.r = r
        self.a = a
        self.eps = eps
        self.hmin = hmin_frac * math.log(r) if r > 1 else 0.0
        self.forget = forget
        self.prior_w = prior_w
        self.d0 = d0
        self.tie = tie
        self.rng = rng if rng is not None else np.random.default_rng()
        self.p = np.full(r, 1.0 / r)
        self.S = np.zeros(r)
        self.W = np.zeros(r)
        self._pe = None

    def p_eff(self):
        if self._pe is None:
            u = np.full(self.r, 1.0 / self.r)
            pe = (1.0 - self.eps) * self.p + self.eps * u
            if self.r > 1:
                while entropy(pe) < self.hmin:
                    pe = 0.9 * pe + 0.1 * u
            self._pe = pe
        return self._pe

    def choose(self):
        if self.r == 1:
            return 0
        return int(self.rng.choice(self.r, p=self.p_eff()))

    def credit(self, i, padash, weight=1.0):
        self.S[i] += weight * padash
        self.W[i] += weight

    def credit_all(self, padashha):
        self.S += padashha
        self.W += 1.0

    def estimates(self):
        return (self.S + self.d0 * self.prior_w) / (self.W + self.prior_w)

    def update(self):
        if self.r == 1:
            return
        d = self.estimates()
        behtarin = d.max()
        B = np.flatnonzero(d >= behtarin - self.tie)
        uB = np.zeros(self.r)
        uB[B] = 1.0 / len(B)
        self.p = (1.0 - self.a) * self.p + self.a * uB
        self.p /= self.p.sum()
        self._pe = None
        self.S *= self.forget
        self.W *= self.forget
