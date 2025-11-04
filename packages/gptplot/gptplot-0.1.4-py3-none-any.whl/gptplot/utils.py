from __future__ import annotations
import os
import re
import uuid
from typing import Iterable, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

def parse_size(size_str: Optional[str]) -> Tuple[float, float]:
    """Parse size string like '6x4' into (width, height) tuple."""
    if not size_str:
        return (6.0, 4.0)
    m = re.match(r"^\s*([0-9]*\.?[0-9]+)\s*[xX]\s*([0-9]*\.?[0-9]+)\s*$", size_str)
    if not m:
        return (6.0, 4.0)
    return (float(m.group(1)), float(m.group(2)))


def resolve_column(df, col):
    """Resolve column by name or 1-based numeric index (string or int)."""
    if col is None:
        return None
    # Handle numeric index (either string or int)
    try:
        idx = int(col)
        if idx <= 0 or idx > len(df.columns):
            raise ValueError(f"Column index {idx} out of range.")
        return df.columns[idx - 1]
    except (ValueError, TypeError):
        # Fall back to name lookup
        if col in df.columns:
            return col
        raise KeyError(f"Column {col} not found. Available: {list(df.columns)}")


def is_numeric_series(s: pd.Series) -> bool:
    """Check if pandas Series contains numeric data."""
    return pd.api.types.is_numeric_dtype(s)


def auto_plot_type(df: pd.DataFrame, x: Optional[str], y: Optional[str], z: Optional[str]) -> str:
    """
    Automatically determine the appropriate plot type based on data.
    """
    if z is not None:
        # User wants 3D-like data; default heatmap for quick look
        return "heatmap"
    if y is None and x is not None:
        # single column → histogram
        return "hist"
    if x is not None and y is not None:
        xn, yn = is_numeric_series(df[x]), is_numeric_series(df[y])
        if xn and yn:
            # if x looks monotonic increasing, line; else scatter
            if df[x].is_monotonic_increasing:
                return "line"
            return "scatter"
        # categorical vs numeric → bar
        return "bar"
    # fallback
    return "hist"


def generate_filename(
    stem: str,
    fmt: str,
    naming_scheme: str = "overwrite",
    output_dir: str | Path = "."
) -> Path:
    """
    Generate filename based on naming scheme.
    
    Parameters
    ----------
    stem : str
        Base filename (without extension)
    fmt : str
        File format/extension (png, pdf, svg)
    naming_scheme : str
        One of: 'overwrite', 'timestamp', 'numbered', 'uuid'
    output_dir : str or Path
        Directory to save file in (default: current directory)
    
    Returns
    -------
    Path
        Full path to save file
    """
    output_dir = Path(output_dir)
    if output_dir != Path("."):
        output_dir.mkdir(exist_ok=True)
    
    # Clean the stem
    stem = re.sub(r"[^A-Za-z0-9_\-]+", "_", stem).strip("_") or "plot"
    ext = fmt.lstrip(".")
    
    if naming_scheme == "overwrite":
        # Simple: just stem.ext (overwrites existing)
        return output_dir / f"{stem}.{ext}"
    
    elif naming_scheme == "timestamp":
        # Add timestamp: stem_20241103_143052.ext
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return output_dir / f"{stem}_{timestamp}.{ext}"
    
    elif naming_scheme == "numbered":
        # Add incrementing number: stem_001.ext, stem_002.ext, ...
        counter = 1
        while True:
            filename = output_dir / f"{stem}_{counter:03d}.{ext}"
            if not filename.exists():
                return filename
            counter += 1
            if counter > 9999:  # Safety limit
                raise ValueError("Too many numbered files (>9999)")
    
    elif naming_scheme == "uuid":
        # Add short UUID: stem_a3f2c1.ext
        short_uuid = str(uuid.uuid4())[:6]
        return output_dir / f"{stem}_{short_uuid}.{ext}"
    
    else:
        raise ValueError(
            f"Unknown naming_scheme '{naming_scheme}'. "
            f"Must be one of: overwrite, timestamp, numbered, uuid"
        )


def save_figure(
    fig,
    output: str | None = None,
    fmt: str = "png",
    dpi: int = 150,
    naming_scheme: str = "overwrite",
    output_dir: str | Path = "."
) -> Path:
    """
    Save figure with configurable naming scheme.
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to save
    output : str, optional
        Base filename (without extension). If None, uses 'plot'
    fmt : str
        Output format (png, pdf, svg)
    dpi : int
        Resolution for raster formats
    naming_scheme : str
        How to handle filename conflicts ('overwrite', 'timestamp', 'numbered', 'uuid')
    output_dir : str or Path
        Directory to save file in (default: current directory)
    
    Returns
    -------
    Path
        Path where file was saved
    """
    stem = Path(output).stem if output else "plot"
    filename = generate_filename(stem, fmt, naming_scheme, output_dir)
    
    # Save the figure
    fig.savefig(filename, dpi=dpi, bbox_inches="tight", format=fmt)
    plt.close(fig)
    
    return filename


def pivot_xyz(df: pd.DataFrame, x: str, y: str, z: str):
    """
    Create meshgrid for surface/heatmap plotting.
    Pivots data assuming (x,y) coordinates cover a grid.
    """
    piv = df.pivot_table(index=y, columns=x, values=z, aggfunc="mean")
    X = piv.columns.values
    Y = piv.index.values
    Z = piv.values
    Xg, Yg = np.meshgrid(X, Y)
    return Xg, Yg, Z


def require_columns(df: pd.DataFrame, cols: Iterable[str]):
    """
    Validate that required columns exist in dataframe.
    Raises ValueError if any are missing.
    """
    missing = [c for c in cols if c is not None and c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Available: {list(df.columns)}")


def auto_infer_params(df: pd.DataFrame, args):
    """
    Automatically infer x/y columns, plot type, labels, and limits
    if not provided by the user or config.
    """
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    # --- Guess x and y ---
    if not args.x and not args.y:
        if len(numeric_cols) >= 2:
            args.x, args.y = numeric_cols[0], numeric_cols[1]
        elif len(numeric_cols) == 1:
            args.x, args.y = numeric_cols[0], None
    elif not args.y and args.x:
        # if only x given, maybe plot histogram
        args.y = None
    elif not args.x and args.y:
        # choose first numeric col different from y
        for c in numeric_cols:
            if c != args.y:
                args.x = c
                break

    # --- Guess plot type ---
    if args.type in [None, "auto"]:
        if args.y is None:
            args.type = "hist"
        elif args.x and args.y:
            # Detect monotonic increasing x → line plot
            xvals = df[args.x].values
            if np.all(np.diff(xvals) >= 0):
                args.type = "line"
            else:
                args.type = "scatter"
        else:
            args.type = "scatter"

    # --- Guess labels ---
    args.xlabel = args.xlabel or (args.x if args.x else "")
    args.ylabel = args.ylabel or (args.y if args.y else "")
    args.title = args.title or f"{args.type.capitalize()} of {args.y or args.x}"

    # --- Axis limits (with small margins) ---
    def margin_limits(series):
        vmin, vmax = np.nanmin(series), np.nanmax(series)
        if not np.isfinite(vmin) or not np.isfinite(vmax):
            return None
        delta = 0.05 * (vmax - vmin) if vmax != vmin else 1
        return [vmin - delta, vmax + delta]

    def is_numeric_str(s):
        try:
            float(s)
            return True
        except (TypeError, ValueError):
            return False

    if args.x and not is_numeric_str(args.x):
        args.xlim = getattr(args, "xlim", None) or margin_limits(df[args.x])
    if args.y and not is_numeric_str(args.y):
        args.ylim = getattr(args, "ylim", None) or margin_limits(df[args.y])

    # --- Set default save_naming if not specified ---
    if not hasattr(args, "save_naming") or args.save_naming is None:
        args.save_naming = "overwrite"

    return args


def apply_axis_limits(ax, args):
    """
    Apply axis limits from args if they exist.
    """
    xlim = getattr(args, "xlim", None)
    ylim = getattr(args, "ylim", None)

    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)
