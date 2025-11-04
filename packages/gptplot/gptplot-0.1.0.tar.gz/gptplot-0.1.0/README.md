# PlotAI

[![PyPI version](https://badge.fury.io/py/plotai.svg)](https://badge.fury.io/py/plotai)
[![Python](https://img.shields.io/pypi/pyversions/plotai.svg)](https://pypi.org/project/plotai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-powered scientific plotting tool inspired by gnuplot**

PlotAI combines the simplicity of gnuplot's CLI with the power of Python's scientific stack (matplotlib, pandas, seaborn). Create publication-quality plots from the command line or interactive shell.

## ✨ Features

- 🚀 **Fast CLI plotting** - Generate plots without writing code
- 📊 **Multiple plot types** - Line, scatter, heatmap, quiver, surface, and more
- 🎨 **Beautiful themes** - Journal, presentation, and dark modes
- 📁 **Smart data loading** - Auto-detects CSV, DAT, TXT formats
- ⚙️ **YAML configs** - Reproducible plots via configuration files
- 🔢 **Interactive mode** - Explore data with an interactive shell
- 📈 **Data analysis** - Built-in correlation, fitting, and statistics
- 🤖 **AI-Ready** - Designed for future LLM integration

## 🔧 Installation

```bash
pip install plotai
```

Requires Python 3.9+

## 🚀 Quick Start

### Basic plotting
```bash
# Simple line plot
plotai data.csv --x time --y voltage

# Auto-detect columns and plot type
plotai data.csv

# Create scatter plot with custom styling
plotai data.csv --type scatter --theme journal -o figure1
```

### Multiple plot types
```bash
# Heatmap
plotai grid.dat --x 1 --y 2 --z 3 --type heatmap --cmap viridis

# Histogram
plotai data.csv --y values --type hist --bins 50

# Box plot
plotai data.csv --x category --y measurement --type box
```

### Configuration files
```bash
# Create plot_config.yaml
cat > plot_config.yaml << EOF
type: scatter
x: time
y: voltage
xlabel: Time (s)
ylabel: Voltage (V)
theme: journal
dpi: 300
EOF

# Use config
plotai data.csv --config plot_config.yaml
```

### Interactive mode
```bash
plotai data.csv --interactive

# In the shell:
> plot x=time y=voltage type=line
> set theme dark
> save my_plot
> quit
```

## 📊 Examples

### Data Science Workflow
```bash
# Correlation heatmap
plotai data.csv --corr

# Statistical summary
plotai data.csv --summary

# Polynomial fitting
plotai data.csv --x time --y signal --fit poly2
```

### Scientific Plotting
```bash
# Vector field (quiver plot)
plotai spins.dat --no-header \
  --x 1 --y 2 --u 4 --v 5 --z 6 \
  --type quiver --cmap coolwarm

# 3D surface
plotai grid.dat --x 1 --y 2 --z 3 \
  --type surface --cmap viridis
```

## 🎨 Themes

Built-in professional themes:

```bash
--theme journal        # Clean, publication-ready
--theme presentation   # Large fonts, high contrast
--theme dark           # Dark background
--theme notebook       # Jupyter-style
```

## 📁 Supported Formats

- **Input**: CSV, DAT, TXT (auto-detected delimiters)
- **Output**: PNG, PDF, SVG
- **Config**: YAML, JSON

## 🛠️ Advanced Features

### Custom output directory
```bash
plotai data.csv -o myplot --output-dir figures/
```

### File naming schemes
```bash
# Overwrite (default)
plotai data.csv -o plot

# Timestamp (experiment tracking)
plotai data.csv --save-naming timestamp -o experiment

# Numbered (multiple runs)
plotai data.csv --save-naming numbered -o run
```

### Column specification
```bash
# By name
plotai data.csv --x time --y voltage

# By 1-based index
plotai data.dat --no-header --x 1 --y 2
```

## 🤖 Future: AI Integration

PlotAI is designed with future LLM integration in mind:
```bash
# Coming soon!
plotai --llm "plot voltage vs time with a dark theme"
```

## 📖 Documentation

Full documentation available at: [GitHub Repository](https://github.com/yourusername/plotai)

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

Inspired by gnuplot's simplicity and powered by Python's scientific stack:
- matplotlib
- pandas
- seaborn
- numpy
- scipy

## 📬 Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

**Made with ❤️ for scientists and data enthusiasts**
