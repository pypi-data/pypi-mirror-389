import numpy as np


def asof_join(left_ts, left_vals, right_ts, right_vals, *, tolerance_ns=None):
    left_ts = np.asarray(left_ts, dtype=np.int64)
    right_ts = np.asarray(right_ts, dtype=np.int64)
    left_vals = np.asarray(left_vals)
    right_vals = np.asarray(right_vals)

    out = np.full(left_ts.shape, np.nan, dtype=float)
    j = 0
    for i, t in enumerate(left_ts):
        while j + 1 < right_ts.size and right_ts[j + 1] <= t:
            j += 1
        if right_ts.size == 0 or right_ts[j] > t:
            continue
        if tolerance_ns is not None and (t - right_ts[j]) > tolerance_ns:
            continue
        out[i] = right_vals[j]
    return out


def reindex(ts_ns, values, new_ts_ns, *, method="ffill", limit=None):
    ts_ns = np.asarray(ts_ns, dtype=np.int64)
    values = np.asarray(values, dtype=float)
    new_ts_ns = np.asarray(new_ts_ns, dtype=np.int64)

    if method not in {"ffill", "bfill", "none"}:
        raise ValueError("method must be 'ffill', 'bfill', or 'none'")

    if method == "none":
        out = np.full(new_ts_ns.shape, np.nan, dtype=float)
        # direct match
        pos = {t: i for i, t in enumerate(ts_ns.tolist())}
        for i, t in enumerate(new_ts_ns.tolist()):
            j = pos.get(t)
            if j is not None:
                out[i] = values[j]
        return out

    # as-of forward or backward
    out = np.full(new_ts_ns.shape, np.nan, dtype=float)
    if method == "ffill":
        j = -1
        last_t = None
        for i, t in enumerate(new_ts_ns):
            while j + 1 < ts_ns.size and ts_ns[j + 1] <= t:
                j += 1
                last_t = ts_ns[j]
            if j >= 0:
                if limit is None or (last_t is not None and t - last_t <= limit):
                    out[i] = values[j]
    else:  # bfill
        j = 0
        next_t = None
        for i in range(new_ts_ns.size - 1, -1, -1):
            t = new_ts_ns[i]
            while j < ts_ns.size and ts_ns[j] >= t:
                next_t = ts_ns[j]
                j += 1
            if j > 0:
                if limit is None or (next_t is not None and next_t - t <= limit):
                    out[i] = values[j - 1]
    return out
