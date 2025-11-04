import numpy as np

from .quality import QF
from .timeutils import floor_ns


def _make_full_index(start_ns: int, end_ns: int, step_ns: int) -> np.ndarray:
    if end_ns < start_ns:
        raise ValueError("end_ns < start_ns")
    n = ((end_ns - start_ns) // step_ns) + 1
    return start_ns + np.arange(n, dtype=np.int64) * step_ns


def trades_to_bars(ts_ns, price, size, step_ns, *, start_ns=None, end_ns=None):
    ts_ns = np.asarray(ts_ns, dtype=np.int64)
    price = np.asarray(price, dtype=np.float64)
    size = np.asarray(size, dtype=np.float64)

    if ts_ns.size == 0:
        if start_ns is None or end_ns is None:
            raise ValueError("empty trades require start_ns and end_ns")
        index = _make_full_index(start_ns, end_ns, step_ns)
        n = index.size
        nan = np.nan
        return {
            "ts": index,
            "open": np.full(n, nan),
            "high": np.full(n, nan),
            "low": np.full(n, nan),
            "close": np.full(n, nan),
            "volume": np.zeros(n, dtype=np.float64),
            "vwap": np.full(n, nan),
            "ntrades": np.zeros(n, dtype=np.int32),
            "qf_quality": np.full(n, QF.MISSING_BAR, dtype=np.uint32),
        }

    # Sort by time
    order = np.argsort(ts_ns, kind="stable")
    ts_ns = ts_ns[order]
    price = price[order]
    size = size[order]

    # Determine range
    t0 = ts_ns[0] if start_ns is None else start_ns
    t1 = ts_ns[-1] if end_ns is None else end_ns
    # Align bounds to bins
    t0 = floor_ns(np.array([t0], dtype=np.int64), step_ns)[0]
    t1 = floor_ns(np.array([t1], dtype=np.int64), step_ns)[0]
    index = _make_full_index(t0, t1, step_ns)
    n_bins = index.size

    # Bin per trade
    bins = floor_ns(ts_ns, step_ns)
    # Map bin value to position 0..n_bins-1
    pos = (bins - t0) // step_ns

    # Initialize outputs
    nan = np.nan
    open_ = np.full(n_bins, nan)
    high = np.full(n_bins, nan)
    low = np.full(n_bins, nan)
    close = np.full(n_bins, nan)
    volume = np.zeros(n_bins, dtype=np.float64)
    vwap_num = np.zeros(n_bins, dtype=np.float64)
    ntrades = np.zeros(n_bins, dtype=np.int32)
    quality = np.zeros(n_bins, dtype=np.uint32)

    # Aggregate
    for i in range(ts_ns.size):
        j = pos[i]
        px = price[i]
        sz = size[i]
        if ntrades[j] == 0:
            open_[j] = px
            high[j] = px
            low[j] = px
            close[j] = px
        else:
            if px > high[j] or np.isnan(high[j]):
                high[j] = px
            if px < low[j] or np.isnan(low[j]):
                low[j] = px
            close[j] = px
        volume[j] += sz
        vwap_num[j] += px * sz
        ntrades[j] += 1

    vwap = np.full(n_bins, nan)
    mask = volume > 0
    vwap[mask] = vwap_num[mask] / volume[mask]

    # Missing bars
    missing = ntrades == 0
    quality[missing] |= QF.MISSING_BAR

    # Large gaps (>5 consecutive missing)
    if missing.any():
        run = 0
        for k in range(n_bins):
            if missing[k]:
                run += 1
            else:
                if run >= 5:
                    quality[k - run : k] |= QF.LARGE_GAP
                run = 0
        if run >= 5:
            quality[n_bins - run : n_bins] |= QF.LARGE_GAP

    return {
        "ts": index,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "vwap": vwap,
        "ntrades": ntrades,
        "qf_quality": quality,
    }


def bars_to_tf(ts_ns, o, h, low, c, v, vw, n, out_step_ns):
    ts_ns = np.asarray(ts_ns, dtype=np.int64)
    o = np.asarray(o, dtype=np.float64)
    h = np.asarray(h, dtype=np.float64)
    low = np.asarray(low, dtype=np.float64)
    c = np.asarray(c, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    vw = np.asarray(vw, dtype=np.float64)
    n = np.asarray(n, dtype=np.int32)

    if ts_ns.size == 0:
        return {
            "ts": ts_ns,
            "open": o,
            "high": h,
            "low": low,
            "close": c,
            "volume": v,
            "vwap": vw,
            "ntrades": n,
            "qf_quality": np.zeros_like(n, dtype=np.uint32),
        }

    in_step = int(np.median(np.diff(ts_ns)))
    if out_step_ns % in_step != 0:
        raise ValueError("out_step_ns must be a multiple of input step")
    factor = out_step_ns // in_step

    n_out = (ts_ns.size + factor - 1) // factor
    nan = np.nan

    out_ts = (ts_ns[: n_out * factor : factor]).copy()
    out_o = np.full(n_out, nan)
    out_h = np.full(n_out, nan)
    out_low = np.full(n_out, nan)
    out_c = np.full(n_out, nan)
    out_v = np.zeros(n_out, dtype=np.float64)
    out_vw_num = np.zeros(n_out, dtype=np.float64)
    out_n = np.zeros(n_out, dtype=np.int32)
    out_q = np.zeros(n_out, dtype=np.uint32)

    for i in range(n_out):
        a = i * factor
        b = min((i + 1) * factor, ts_ns.size)
        if a >= b:
            continue
        block = slice(a, b)
        valid = n[block] > 0
        if valid.any():
            idx = np.flatnonzero(valid) + a
            out_o[i] = o[idx[0]]
            out_c[i] = c[idx[-1]]
            out_h[i] = np.nanmax(h[block][valid])
            out_low[i] = np.nanmin(low[block][valid])
        out_v[i] = np.nansum(v[block])
        out_vw_num[i] = np.nansum(vw[block] * v[block])
        out_n[i] = np.nansum(n[block])
        if (~valid).all():
            out_q[i] |= QF.MISSING_BAR

    out_vw = np.full(n_out, nan)
    mask = out_v > 0
    out_vw[mask] = out_vw_num[mask] / out_v[mask]

    return {
        "ts": out_ts,
        "open": out_o,
        "high": out_h,
        "low": out_low,
        "close": out_c,
        "volume": out_v,
        "vwap": out_vw,
        "ntrades": out_n,
        "qf_quality": out_q,
    }
