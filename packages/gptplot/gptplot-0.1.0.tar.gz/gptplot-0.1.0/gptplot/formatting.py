import matplotlib.ticker as mticker

def apply_axis_format(ax, args=None, kind="2d"):
    """
    Apply clean, consistent axis formatting.
    Works for 1D, 2D, and 3D plots.
    """
    # --- Smart tick spacing ---
    ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=6))
    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6))

    # --- Scientific notation when needed ---
    ax.ticklabel_format(style="sci", axis="both", scilimits=(-3, 3))

    # --- Equal aspect for 2D data (optional) ---
    if kind == "2d":
        ax.set_aspect("auto", adjustable="box")

    # --- Optional grid ---
    grid_on = getattr(args, "grid", None)
    if grid_on is None:
        grid_on = True
    if grid_on:
        ax.grid(True, color="gray", alpha=0.2, linewidth=0.5)

    # --- Tight layout so labels never clip ---
    try:
        ax.figure.tight_layout(pad=0.5)
    except Exception:
        pass

def apply_axis_limits(ax, args):
    """
    Apply user-specified xlim and ylim if provided.
    """
    if getattr(args, "xlim", None):
        try:
            ax.set_xlim(args.xlim)
        except Exception:
            pass
    if getattr(args, "ylim", None):
        try:
            ax.set_ylim(args.ylim)
        except Exception:
            pass
