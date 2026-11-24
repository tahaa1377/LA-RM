import math

import numpy as np
from scipy import stats as _amar


def ci95(meghdarha, scale=1.0, nd=4):
    x = np.asarray(list(meghdarha), dtype=float) * scale
    n = len(x)
    if n == 0:
        return [0.0, 0.0]
    miyangin = float(x.mean())
    if n < 2:
        return [round(miyangin, nd), 0.0]
    nesf = float(_amar.t.ppf(0.975, n - 1) * x.std(ddof=1) / math.sqrt(n))
    return [round(miyangin, nd), round(nesf, nd)]
