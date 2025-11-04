import pyarrow as pa

TRADE_SCHEMA = pa.schema(
    [
        ("ts", pa.timestamp("ns", tz="UTC")),
        ("price", pa.float64()),
        ("size", pa.float64()),
        ("side", pa.int8()),
    ]
)

QUOTE_SCHEMA = pa.schema(
    [
        ("ts", pa.timestamp("ns", tz="UTC")),
        ("bid_px", pa.float64()),
        ("bid_sz", pa.float64()),
        ("ask_px", pa.float64()),
        ("ask_sz", pa.float64()),
    ]
)

BAR_SCHEMA = pa.schema(
    [
        ("ts", pa.timestamp("ns", tz="UTC")),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("volume", pa.float64()),
        ("vwap", pa.float64()),
        ("ntrades", pa.int32()),
        ("qf_quality", pa.uint32()),
    ]
)
