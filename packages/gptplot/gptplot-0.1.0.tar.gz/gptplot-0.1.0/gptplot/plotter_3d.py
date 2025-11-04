from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from .utils import pivot_xyz

def surface_plot(df: pd.DataFrame, x: str, y: str, z: str, cmap: str = "viridis", title=None, **kwargs):
    X, Y, Z = pivot_xyz(df, x, y, z)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(X, Y, Z, cmap=cmap, linewidth=0, antialiased=True)
    fig.colorbar(surf, ax=ax, shrink=0.75, aspect=20, label=z)
    ax.set_title(title or f"Surface: {z}({x},{y})")
    ax.set_xlabel(x); ax.set_ylabel(y); ax.set_zlabel(z)
    return fig, ax

def heatmap_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    cmap: str = "viridis",
    title: str | None = None,
    use_imshow: bool | None = None,
    interpolation: str = "none",
    **kwargs,
):
    """
    Heatmap (pm3d map-style) for z(x,y).

    Automatically chooses pcolormesh or imshow:
    - Uses pcolormesh when grid is non-uniform or use_imshow=False
    - Uses imshow when grid is uniform or use_imshow=True

    Parameters
    ----------
    x, y, z : str
        Column names (or numeric indices resolved before call)
    cmap : str
        Matplotlib colormap
    title : str, optional
        Plot title
    use_imshow : bool, optional
        Force imshow (True) or pcolormesh (False). If None, decide automatically.
    interpolation : str
        imshow interpolation mode ('none', 'bilinear', 'bicubic', etc.)
    """
    import numpy as np
    import matplotlib.pyplot as plt
    from .utils import pivot_xyz

    # Pivot data into X,Y,Z grids
    X, Y, Z = pivot_xyz(df, x, y, z)
    fig, ax = plt.subplots()

    # Detect grid regularity if user didn't specify
    if use_imshow is None:
        dx = np.diff(X[0, :])
        dy = np.diff(Y[:, 0])
        # if grid spacing nearly uniform (within 1e-6 relative tolerance)
        uniform_x = np.allclose(dx, dx[0], rtol=1e-6, atol=1e-9)
        uniform_y = np.allclose(dy, dy[0], rtol=1e-6, atol=1e-9)
        use_imshow = uniform_x and uniform_y

    if use_imshow:
        # --- Use imshow: faster, assumes uniform grid ---
        extent = [X.min(), X.max(), Y.min(), Y.max()]
        m = ax.imshow(
            Z,
            origin="lower",
            extent=extent,
            cmap=cmap,
            aspect="equal",
            interpolation=interpolation,
        )
        method = "imshow"
    else:
        # --- Use pcolormesh: exact mapping, nonuniform safe ---
        m = ax.pcolormesh(X, Y, Z, shading="auto", cmap=cmap)
        method = "pcolormesh"

    # Colorbar and labels
    cb = fig.colorbar(m, ax=ax)
    cb.set_label(z)
    ax.set_title(title or f"Heatmap ({method}): {z} on {x}-{y}")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_aspect("equal", adjustable="box")

    return fig, ax


def quiver_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    u: str,
    v: str,
    sz: str | None = None,
    scale: float | None = None,
    cmap: str = "coolwarm",
    title=None,
    **kwargs
):
    """
    Plot 2D vector field (Sx,Sy) with color representing Sz.

    Parameters
    ----------
    x, y : coordinates
    u, v : in-plane spin components (Sx, Sy)
    sz   : out-of-plane spin component (for color)
    scale: arrow scaling (higher value -> shorter arrows)
    cmap : colormap for Sz
    """
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots()
    X, Y, U, V = df[x], df[y], df[u], df[v]

    if sz and sz in df.columns:
        C = df[sz]
        norm = plt.Normalize(vmin=C.min(), vmax=C.max())
        colors = plt.cm.get_cmap(cmap)(norm(C))
        q = ax.quiver(
            X, Y, U, V, C,
            angles="xy", scale_units="xy", scale=scale,
            cmap=cmap, width=0.003, headwidth=3
        )
        cb = fig.colorbar(q, ax=ax)
        cb.set_label(f"{sz}")
    else:
        q = ax.quiver(
            X, Y, U, V,
            angles="xy", scale_units="xy", scale=scale,
            color="black", width=0.003, headwidth=3
        )

    ax.set_title(title or f"Spin field: color={sz or 'none'}")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)
    return fig, ax

