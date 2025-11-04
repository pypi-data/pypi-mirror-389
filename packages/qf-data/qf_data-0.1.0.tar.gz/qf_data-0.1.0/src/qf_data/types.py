from enum import IntEnum


class Side(IntEnum):
    BUY = 1
    SELL = -1


TS_DTYPE = "int64"  # ns since epoch
