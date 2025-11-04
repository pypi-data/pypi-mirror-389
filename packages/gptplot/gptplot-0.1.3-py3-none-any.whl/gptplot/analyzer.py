from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def summary(df: pd.DataFrame) -> pd.DataFrame:
    numeric = df.select_dtypes(include="number")
    desc = numeric.describe().T
    miss = numeric.isna().sum()
    desc["missing"] = miss
    return desc

def corr_heatmap(df: pd.DataFrame, title: str | None = None):
    corr = df.select_dtypes(include="number").corr(numeric_only=True)
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=False, cmap="vlag", ax=ax, square=True, cbar_kws={"label": "corr"})
    ax.set_title(title or "Correlation heatmap")
    return fig, ax

def fit_and_overlay(df: pd.DataFrame, x: str, y: str, degree: int = 1):
    # Scatter + polynomial trend line
    fig, ax = plt.subplots()
    ax.scatter(df[x], df[y], s=20, alpha=0.8, label="data")
    X = df[x].to_numpy()
    Y = df[y].to_numpy()
    coeff = np.polyfit(X, Y, deg=degree)
    poly = np.poly1d(coeff)
    xs = np.linspace(X.min(), X.max(), 300)
    ax.plot(xs, poly(xs), label=f"poly{degree} fit")
    ax.legend()
    ax.set_xlabel(x); ax.set_ylabel(y)
    ax.set_title(f"Fit (degree {degree}): {y} ~ poly({x})")
    return fig, ax, coeff
