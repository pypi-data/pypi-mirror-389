import numpy as np

from qf_data import step_from_str, trades_to_bars


def test_trades_to_bars_smoke():
    ts = np.array([0, 100_000_000, 600_000_000, 1_100_000_000], dtype=np.int64)
    px = np.array([100.0, 101.0, 99.0, 100.5])
    sz = np.array([0.5, 0.1, 0.2, 0.3])
    step = step_from_str("1s")
    out = trades_to_bars(ts, px, sz, step, start_ns=0, end_ns=2_000_000_000)

    expected_keys = {
        "ts",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "vwap",
        "ntrades",
        "qf_quality",
    }
    assert set(out.keys()) == expected_keys
    assert out["ts"].dtype == np.int64
    assert out["ntrades"].dtype == np.int32
