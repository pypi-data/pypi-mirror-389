import cmd
import shlex
from rich.console import Console
from . import plotter_2d as p2
from . import plotter_3d as p3
from .utils import resolve_column, auto_plot_type, save_figure, parse_size, require_columns
from .formatting import apply_axis_format, apply_axis_limits

console = Console()

class PySciPlotShell(cmd.Cmd):
    intro = "\n[bold cyan]PySciPlot Interactive Mode[/]\nType 'help' for commands.\n"
    prompt = "> "

    def __init__(self, df, args):
        super().__init__()
        self.df = df
        self.args = args
        self.last_fig = None
        self.last_ax = None
        
        # Ensure save_naming is initialized
        if not hasattr(self.args, "save_naming") or self.args.save_naming is None:
            self.args.save_naming = "overwrite"
        
        # Ensure output_dir is initialized
        if not hasattr(self.args, "output_dir") or self.args.output_dir is None:
            self.args.output_dir = "."
        
        console.print(f"Loaded [green]{args.datafile}[/] with {len(df.columns)} columns: {', '.join(df.columns)}")

    # --- basic commands ---

    def do_show(self, arg):
        """show columns : List all column names"""
        console.print(f"Columns: {', '.join(self.df.columns)}")

    def do_plot(self, arg):
        """plot x=col1 y=col2 type=line color=red"""
        tokens = shlex.split(arg)
        for tok in tokens:
            if "=" in tok:
                key, val = tok.split("=", 1)
                setattr(self.args, key, val)

        x = resolve_column(self.df, self.args.x)
        y = resolve_column(self.df, self.args.y)
        z = resolve_column(self.df, self.args.z) if getattr(self.args, "z", None) else None
        color = resolve_column(self.df, getattr(self.args, "color", None)) if getattr(self.args, "color", None) else None

        ptype = self.args.type or auto_plot_type(self.df, x, y, z)
        width, height = parse_size(self.args.size)
        fig = None

        try:
            if ptype == "line":
                require_columns(self.df, [x, y])
                fig, ax = p2.line_plot(self.df, x, y, title=self.args.title, xlabel=self.args.xlabel, ylabel=self.args.ylabel)
            elif ptype == "scatter":
                require_columns(self.df, [x, y])
                fig, ax = p2.scatter_plot(self.df, x, y, color=color, title=self.args.title, xlabel=self.args.xlabel, ylabel=self.args.ylabel, cmap=self.args.cmap)
            elif ptype == "hist":
                col = y or x
                require_columns(self.df, [col])
                fig, ax = p2.hist_plot(self.df, col, bins=self.args.bins, title=self.args.title, xlabel=self.args.xlabel)
            elif ptype == "bar":
                require_columns(self.df, [x, y])
                fig, ax = p2.bar_plot(self.df, x, y, title=self.args.title, xlabel=self.args.xlabel, ylabel=self.args.ylabel)
            elif ptype == "box":
                require_columns(self.df, [x, y])
                fig, ax = p2.box_plot(self.df, x, y, title=self.args.title, xlabel=self.args.xlabel, ylabel=self.args.ylabel)
            elif ptype == "heatmap":
                require_columns(self.df, [x, y, z])
                fig, ax = p3.heatmap_plot(self.df, x, y, z, cmap=self.args.cmap, title=self.args.title)
            elif ptype == "surface":
                require_columns(self.df, [x, y, z])
                fig, ax = p3.surface_plot(self.df, x, y, z, cmap=self.args.cmap, title=self.args.title)
            elif ptype == "quiver":
                require_columns(self.df, [x, y, self.args.u, self.args.v])
                fig, ax = p3.quiver_plot(self.df, x, y, self.args.u, self.args.v, sz=z, cmap=self.args.cmap, title=self.args.title)
            else:
                console.print(f"[red]Unknown plot type: {ptype}[/]")
                return

            apply_axis_limits(ax, self.args)
            apply_axis_format(ax, self.args)
            fig.set_size_inches(width, height)
            self.last_fig, self.last_ax = fig, ax
            console.print(f"[green]Displayed {ptype} plot.[/]")
            fig.show()
        except Exception as e:
            console.print(f"[red]Plot error:[/] {e}")

    def do_set(self, arg):
        """set key value : Set plot attributes (title, xlabel, ylabel, save_naming, etc.)"""
        tokens = shlex.split(arg)
        if len(tokens) < 2:
            console.print("[yellow]Usage:[/] set title 'My Plot Title'")
            console.print("[yellow]      :[/] set save_naming timestamp")
            return
        key, value = tokens[0], " ".join(tokens[1:])
        
        # Validate save_naming
        if key == "save_naming":
            valid = ["overwrite", "timestamp", "numbered", "uuid"]
            if value not in valid:
                console.print(f"[red]Invalid save_naming.[/] Must be one of: {', '.join(valid)}")
                return
        
        setattr(self.args, key, value)
        console.print(f"Set {key} = '{value}'")

    def do_save(self, arg):
        """save filename.png : Save last plot to file"""
        if self.last_fig is None:
            console.print("[red]No plot available to save.[/]")
            return
        
        tokens = shlex.split(arg)
        fname = tokens[0] if tokens else "interactive_plot"
        
        saved = save_figure(
            self.last_fig, 
            fname, 
            self.args.format, 
            self.args.dpi,
            naming_scheme=getattr(self.args, "save_naming", "overwrite"),
            output_dir=getattr(self.args, "output_dir", ".")
        )
        console.print(f"[green]Saved plot to[/] {saved}")

    def do_exit(self, arg):
        """Exit interactive mode"""
        console.print("Exiting PySciPlot shell.")
        return True

    def do_quit(self, arg):
        """Alias for exit"""
        return self.do_exit(arg)

    def emptyline(self):
        pass
