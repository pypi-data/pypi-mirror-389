from __future__ import annotations
import argparse
import matplotlib.pyplot as plt
from rich.console import Console
from . import styles
from .io_handler import load_table
from .utils import resolve_column, auto_plot_type, save_figure, parse_size, require_columns
from .utils import auto_infer_params, apply_axis_limits
from . import plotter_2d as p2
from . import plotter_3d as p3
from . import analyzer as an
from .config_loader import load_config, merge_config
from .formatting import apply_axis_format
from .interactive import PySciPlotShell


console = Console()

# ----------------------------------------------------
# Parser builder
# ----------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(
        prog="pysciplot",
        description="Python-based scientific plotting tool inspired by gnuplot",
    )
    p.add_argument("datafile", help="Path to .csv/.dat/.txt file")
    p.add_argument("--delimiter", default=None, help="Delimiter override (e.g., ',' or '\\t')")
    p.add_argument("--no-header", action="store_true", help="Treat file as headerless")

    # Columns (can be names or 1-based indices)
    p.add_argument("--x"); p.add_argument("--y"); p.add_argument("--z")
    p.add_argument("--u"); p.add_argument("--v"); p.add_argument("--color")

    # Plot selection
    p.add_argument("--type", choices=[
        "auto","line","scatter","hist","bar","box","surface","heatmap","quiver"
    ], default="auto")

    # Plot options
    p.add_argument("--bins", type=int, default=30)
    p.add_argument("--style", default=None, help="Seaborn style (white, whitegrid, darkgrid, ticks, etc.)")
    p.add_argument("--title", default=None)
    p.add_argument("--xlabel", default=None)
    p.add_argument("--ylabel", default=None)
    p.add_argument("--cmap", default="viridis")
    p.add_argument("--size", default="6x4", help="Figure size in inches, e.g., 6x4")
    p.add_argument("--dpi", type=int, default=150)

    # Quiver / vector field options
    p.add_argument("--scale", type=float, default=None, help="Arrow scaling for quiver plot (higher=shorter arrows)")

    # Heatmap / image options
    p.add_argument("--imshow", action="store_true", help="Use imshow instead of pcolormesh for heatmap (faster for uniform grids)")
    p.add_argument("--interpolation", default="none", help="Interpolation mode for imshow (none, bilinear, bicubic, etc.)")

    # Analysis helpers
    p.add_argument("--summary", action="store_true", help="Print numeric summary")
    p.add_argument("--corr", action="store_true", help="Show correlation heatmap")
    p.add_argument("--fit", choices=["linear","poly2","poly3"], default=None)

    # Saving options
    p.add_argument("-o", "--output", default=None, help="Output filename stem")
    p.add_argument("-f", "--format", default="png", choices=["png","pdf","svg"])
    p.add_argument("--output-dir", default=".", 
                   help="Output directory for saved plots (default: current directory)")
    p.add_argument("--save-naming", 
                   choices=["overwrite", "timestamp", "numbered", "uuid"],
                   default="overwrite",
                   help="File naming scheme (default: overwrite)")

    # Config file
    p.add_argument("--config", help="Path to YAML or JSON config file for plotting parameters")
    
    # Axis formatting
    p.add_argument("--no-grid", dest="grid", action="store_false",
               help="Disable background gridlines")
    
    # Theme presets
    p.add_argument("--theme", choices=["journal","presentation","dark","notebook"],
               help="Apply preset visual theme for publication or presentation")
    
    # Interactive mode    
    p.add_argument("--interactive", action="store_true",
               help="Launch interactive plotting shell")
    
    return p


# ----------------------------------------------------
# Main entry point
# ----------------------------------------------------
def main():
    p = build_parser()
    args = p.parse_args()

    # -------- Load configuration file if provided --------
    if args.config:
        try:
            cfg = load_config(args.config)
            args = merge_config(args, cfg)
            console.print(f"[green]✓[/] Loaded config from {args.config}")
        except FileNotFoundError as e:
            console.print(f"[red]✗[/] Config file not found: {e}")
            return
        except ValueError as e:
            console.print(f"[red]✗[/] Invalid config: {e}")
            return
        except Exception as e:
            console.print(f"[red]✗[/] Failed to load config: {e}")
            return

    # -------- Apply style --------
    styles.apply_style(args.style, theme=args.theme)

    # -------- Load data --------
    try:
        df = load_table(args.datafile, delimiter=args.delimiter, has_header=(not args.no_header))
        if args.no_header:
            df.columns = [str(i + 1) for i in range(len(df.columns))]
        console.print(f"[green]✓[/] Loaded {args.datafile} ({len(df)} rows, {len(df.columns)} columns)")
    except FileNotFoundError:
        console.print(f"[red]✗[/] Data file not found: {args.datafile}")
        return
    except Exception as e:
        console.print(f"[red]✗[/] Failed to load data: {e}")
        return

    # --- Interactive mode ---
    if args.interactive:
        shell = PySciPlotShell(df, args)
        shell.cmdloop()
        return

    # ---- Smart parameter inference ----
    args = auto_infer_params(df, args)
    
    # Resolve columns (allow numeric indices from CLI)
    def res(c):
        if c is None:
            return None
        try:
            ci = int(c)
            return resolve_column(df, ci)
        except ValueError:
            return resolve_column(df, c)

    try:
        x = res(args.x); y = res(args.y); z = res(args.z)
        u = res(args.u); v = res(args.v)
        color = res(args.color)
    except (KeyError, ValueError) as e:
        console.print(f"[red]✗[/] Column resolution error: {e}")
        return
    
    # -------- Analyses before plotting --------
    if args.summary:
        console.rule("[bold cyan]Summary Statistics")
        console.print(an.summary(df))
    if args.corr:
        try:
            fig, ax = an.corr_heatmap(df)
            saved = save_figure(
                fig, 
                args.output or "corr", 
                args.format, 
                args.dpi,
                naming_scheme=getattr(args, "save_naming", "overwrite"),
                output_dir=getattr(args, "output_dir", ".")
            )
            console.print(f"[green]✓[/] Saved correlation heatmap to {saved}")
        except Exception as e:
            console.print(f"[red]✗[/] Correlation plot failed: {e}")
            return

    # -------- Fitting --------
    if args.fit:
        deg = {"linear":1, "poly2":2, "poly3":3}[args.fit]
        if not (x and y):
            console.print("[red]✗[/] --fit requires --x and --y")
            return
        try:
            fig, ax, coeff = an.fit_and_overlay(df, x, y, degree=deg)
            saved = save_figure(
                fig, 
                args.output or f"fit_{y}_vs_{x}", 
                args.format, 
                args.dpi,
                naming_scheme=getattr(args, "save_naming", "overwrite"),
                output_dir=getattr(args, "output_dir", ".")
            )
            console.print(f"[green]✓[/] Saved fit plot to {saved}")
            console.print(f"[cyan]Coefficients:[/] {coeff}")
        except Exception as e:
            console.print(f"[red]✗[/] Fitting failed: {e}")
        return

    # -------- Decide plot type --------
    ptype = args.type
    if ptype == "auto":
        ptype = auto_plot_type(df, x, y, z)

    width, height = parse_size(args.size)

    # -------- Dispatch to plotter --------
    fig = None
    try:
        if ptype == "line":
            require_columns(df, [x, y])
            fig, ax = p2.line_plot(df, x, y, title=args.title, xlabel=args.xlabel, ylabel=args.ylabel)
        elif ptype == "scatter":
            require_columns(df, [x, y])
            fig, ax = p2.scatter_plot(df, x, y, color=color, title=args.title, xlabel=args.xlabel, ylabel=args.ylabel, cmap=args.cmap)
        elif ptype == "hist":
            col = y or x
            if col is None:
                console.print("[red]✗[/] Histogram needs one of --y or --x")
                return
            require_columns(df, [col])
            fig, ax = p2.hist_plot(df, col, bins=args.bins, title=args.title, xlabel=args.xlabel)
        elif ptype == "bar":
            require_columns(df, [x, y])
            fig, ax = p2.bar_plot(df, x, y, title=args.title, xlabel=args.xlabel, ylabel=args.ylabel)
        elif ptype == "box":
            require_columns(df, [x, y])
            fig, ax = p2.box_plot(df, x, y, title=args.title, xlabel=args.xlabel, ylabel=args.ylabel)
        elif ptype == "surface":
            require_columns(df, [x, y, z])
            fig, ax = p3.surface_plot(df, x, y, z, cmap=args.cmap, title=args.title)
        elif ptype == "heatmap":
            require_columns(df, [x, y, z])
            fig, ax = p3.heatmap_plot(
                df, x, y, z,
                cmap=args.cmap,
                title=args.title,
                use_imshow=args.imshow,
                interpolation=args.interpolation
            )
        elif ptype == "quiver":
            require_columns(df, [x, y, u, v])
            fig, ax = p3.quiver_plot(
                df, x, y, u, v,
                sz=z,
                cmap=args.cmap,
                scale=args.scale,
                title=args.title
            )
        else:
            console.print(f"[red]✗[/] Unknown plot type: {ptype}")
            return
    except Exception as e:
        console.print(f"[red]✗[/] Plotting failed: {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/]")
        return

    # -------- Finalize and save figure --------
    if fig is not None:
        try:
            apply_axis_limits(ax, args)
            apply_axis_format(ax, args)
            fig.set_size_inches(width, height)

            console.print("[cyan]Displaying plot... Close the window to continue.[/]")
            plt.show(block=True)

            save_prompt = input("Save this plot? (y/n): ").strip().lower()
            if save_prompt == "y":
                filename = input("Enter filename (without extension): ").strip() or "plot"
                fmt = input("Format [png/pdf/svg] (default png): ").strip().lower() or "png"
                
                saved = save_figure(
                    fig, 
                    filename, 
                    fmt, 
                    args.dpi,
                    naming_scheme=getattr(args, "save_naming", "overwrite"),
                    output_dir=getattr(args, "output_dir", ".")
                )
                console.print(f"[green]✓[/] Saved figure to {saved}")
            else:
                console.print("[yellow]Plot not saved.[/]")
        except Exception as e:
            console.print(f"[red]✗[/] Error during finalization: {e}")
