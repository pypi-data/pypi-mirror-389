from __future__ import annotations
import pandas as pd

def load_table(
    path: str,
    delimiter: str | None = None,
    has_header: bool = True,
) -> pd.DataFrame:
    """
    Load .dat/.txt/.csv with auto delimiter detection when delimiter=None.
    Set has_header=False to assign numeric headers C1..Ck like gnuplot.
    """
    header = 0 if has_header else None
    df = pd.read_csv(
        path,
        sep=delimiter if delimiter is not None else None,
        engine="python",
        header=header,
        comment="#",
    )
    if not has_header:
        df.columns = [f"C{i+1}" for i in range(df.shape[1])]
    return df
