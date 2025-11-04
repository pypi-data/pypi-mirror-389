# qf-data

Fast, minimal data utilities for trading. Asset-agnostic, crypto-friendly.

## Features
- Canonical Arrow schemas for trades, quotes, bars.
- UTC nanosecond time utilities.
- Trades→bars resampling. Bars→higher TF.
- Alignment and as-of joins.
- Missing-data handling and quality flags.
- Optional adapters for Pandas/Polars.

## Install
```bash
pip install qf-data
```

## Quick start
```python
import numpy as np
from qf_data import step_from_str, trades_to_bars

ts = np.array([0, 500_000_000, 1_100_000_000], dtype=np.int64)  # ns
px = np.array([100.0, 101.0, 99.5])
sz = np.array([0.4, 0.1, 0.2])

step = step_from_str("1s")
bars = trades_to_bars(ts, px, sz, step, start_ns=0, end_ns=2_000_000_000)
print(bars.keys())  # dict of arrays
```

## Design
- Pure Python + NumPy/Arrow. No pandas in core.
- Pure functions. No global state. UTC only.
- 24/7 by default. Calendars are pluggable.

## License
MIT
