import re

import numpy as np

NS = 1
US = 1_000
MS = 1_000_000
S = 1_000_000_000
MIN = 60 * S
H = 60 * MIN

_STEP_RE = re.compile(r"^(\d+)(ns|us|ms|s|m|h)$", re.IGNORECASE)


def floor_ns(ts_ns: np.ndarray, step_ns: int) -> np.ndarray:
    return (ts_ns // step_ns) * step_ns


def step_from_str(s: str) -> int:
    m = _STEP_RE.match(s.strip())
    if not m:
        raise ValueError(f"invalid step string: {s}")
    val = int(m.group(1))
    unit = m.group(2).lower()
    mult = {"ns": NS, "us": US, "ms": MS, "s": S, "m": MIN, "h": H}[unit]
    return val * mult
