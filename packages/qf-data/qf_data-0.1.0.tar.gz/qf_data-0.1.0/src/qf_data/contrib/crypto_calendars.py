# Simple 24/7 calendar stubs. Extend with maintenance windows per venue.
def is_open(ts_ns: int) -> bool:
    return True


def next_open(ts_ns: int) -> int:
    return ts_ns
