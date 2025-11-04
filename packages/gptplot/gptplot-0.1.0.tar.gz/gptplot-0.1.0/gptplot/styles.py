import seaborn as sns
import matplotlib as mpl

THEMES = {
    "journal": {
        "style": "white",
        "font_scale": 1.2,
        "rc": {
            "axes.titlesize": 13,
            "axes.labelsize": 12,
            "font.family": "serif",
            "grid.alpha": 0.15,
            "lines.linewidth": 1.5,
        },
    },
    "presentation": {
        "style": "whitegrid",
        "font_scale": 1.6,
        "rc": {
            "axes.titlesize": 18,
            "axes.labelsize": 16,
            "legend.fontsize": 14,
            "figure.dpi": 150,
            "lines.linewidth": 2.2,
        },
    },
    "dark": {
        "style": "darkgrid",
        "font_scale": 1.2,
        "rc": {
            "axes.facecolor": "#1E1E1E",
            "figure.facecolor": "#1E1E1E",
            "savefig.facecolor": "#1E1E1E",
            "axes.edgecolor": "white",
            "axes.labelcolor": "white",
            "text.color": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "grid.color": "#444444",
            "lines.linewidth": 1.8,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "axes.titlecolor": "white",
            "legend.facecolor": "#2a2a2a",
            "legend.edgecolor": "#2a2a2a",
            "legend.labelcolor": "white",
            "axes.prop_cycle": mpl.cycler(color=["#4FC3F7", "#FFB74D", "#E57373", "#AED581", "#BA68C8"])

        },
    },

    "notebook": {
        "style": "ticks",
        "font_scale": 1.1,
        "rc": {
            "axes.titlesize": 13,
            "axes.labelsize": 12,
            "lines.linewidth": 1.8,
        },
    },
}

import shutil
import seaborn as sns
import matplotlib as mpl

def apply_style(style: str | None = None, font_scale: float = 1.1, theme: str | None = None):
    """
    Apply consistent plotting style with optional LaTeX and theme presets.
    """
    from .styles import THEMES

    # If a theme is selected, override defaults
    if theme and theme in THEMES:
        cfg = THEMES[theme]
        style = cfg.get("style", style)
        font_scale = cfg.get("font_scale", font_scale)
        rc_dict = cfg.get("rc", {})
    else:
        rc_dict = {}

    sns.set_theme(style=style or "whitegrid", font_scale=font_scale, rc=rc_dict)

    # --- Publication defaults ---
    mpl.rcParams.update({
        "figure.dpi": 120,
        "savefig.bbox": "tight",
        "axes.linewidth": 1.0,
        "lines.markersize": 5.0,
    })

    # --- Conditional LaTeX fonts ---
    if shutil.which("latex"):
        try:
            mpl.rcParams.update({
                "text.usetex": True,
                "font.family": "serif",
                "font.serif": ["Computer Modern Roman"],
                "axes.unicode_minus": False,
            })
            print("[PySciPlot] Using LaTeX fonts for rendering.")
        except Exception:
            mpl.rcParams["text.usetex"] = False
            print("[PySciPlot] LaTeX detected but failed. Falling back.")
    else:
        mpl.rcParams["text.usetex"] = False
