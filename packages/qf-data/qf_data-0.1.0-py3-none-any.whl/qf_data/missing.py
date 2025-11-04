import numpy as np

from .quality import QF


def mark_large_gaps(ts_ns, step_ns, k=5):
    ts_ns = np.asarray(ts_ns, dtype=np.int64)
    q = np.zeros(ts_ns.shape, dtype=np.uint32)
    if ts_ns.size < 2:
        return q
    diffs = np.diff(ts_ns)
    mask = diffs > (k * step_ns)
    # mark the interval before the gap as large gap
    idx = np.flatnonzero(mask)
    for i in idx:
        q[i] |= QF.LARGE_GAP
    return q


def ffill(values, max_len=None):
    arr = np.asarray(values, dtype=float).copy()
    last = np.nan
    run = 0
    for i in range(arr.size):
        if np.isnan(arr[i]):
            run += 1
            if max_len is not None and run > max_len:
                last = np.nan
            arr[i] = last
        else:
            last = arr[i]
            run = 0
    return arr
