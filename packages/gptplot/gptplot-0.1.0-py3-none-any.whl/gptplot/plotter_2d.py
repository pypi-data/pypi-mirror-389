from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def line_plot(df: pd.DataFrame, x: str, y: str, title=None, xlabel=None, ylabel=None, **kwargs):
    fig, ax = plt.subplots()
    ax.plot(df[x], df[y], marker=kwargs.get("marker", None))
    ax.set_title(title or f"{y} vs {x}")
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    ax.grid(True, alpha=0.3)
    return fig, ax

def scatter_plot(df: pd.DataFrame, x: str, y: str, color=None, title=None, xlabel=None, ylabel=None, **kwargs):
    fig, ax = plt.subplots()
    if color and color in df.columns:
        sc = ax.scatter(df[x], df[y], c=df[color], cmap=kwargs.get("cmap", "viridis"))
        cb = plt.colorbar(sc, ax=ax)
        cb.set_label(color)
    else:
        ax.scatter(df[x], df[y], alpha=0.9, s=kwargs.get("s", 25))
    ax.set_title(title or f"{y} vs {x}")
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    ax.grid(True, alpha=0.3)
    return fig, ax

def hist_plot(df: pd.DataFrame, y: str, bins=30, title=None, xlabel=None, **kwargs):
    fig, ax = plt.subplots()
    ax.hist(df[y].dropna(), bins=bins)
    ax.set_title(title or f"Histogram of {y}")
    ax.set_xlabel(xlabel or y)
    ax.set_ylabel("Count")
    return fig, ax

def bar_plot(df: pd.DataFrame, x: str, y: str, title=None, xlabel=None, ylabel=None, **kwargs):
    fig, ax = plt.subplots()
    sns.barplot(df, x=x, y=y, ax=ax, estimator=kwargs.get("estimator", "mean"))
    ax.set_title(title or f"{y} by {x}")
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    for c in ax.containers:
        ax.bar_label(c, fmt="%.2g", padding=2)
    return fig, ax

def box_plot(df: pd.DataFrame, x: str, y: str, title=None, xlabel=None, ylabel=None, **kwargs):
    fig, ax = plt.subplots()
    sns.boxplot(df, x=x, y=y, ax=ax)
    ax.set_title(title or f"Box plot of {y} by {x}")
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    return fig, ax
