import pandas as pd
import pyarrow as pa


def trades_df_to_arrow(df: pd.DataFrame) -> pa.Table:
    cols = {"ts", "price", "size", "side"}
    missing = cols - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {missing}")
    tbl = pa.Table.from_pandas(df, preserve_index=False)
    return tbl


def bars_arrow_to_df(tbl: pa.Table) -> pd.DataFrame:
    return tbl.to_pandas()
