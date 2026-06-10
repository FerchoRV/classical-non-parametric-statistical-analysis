"""Generacion de graficos con matplotlib/seaborn.

Tipos soportados:
  * Barras    -> columnas de texto/categoricas o numericas (frecuencias).
  * Cajas     -> columnas numericas (distribucion y atipicos).
  * Dispersion-> dos columnas numericas (relacion entre variables).
  * Circular  -> columnas categoricas o numericas (porcentaje por categoria).

Todas las funciones devuelven una ``matplotlib.figure.Figure`` para poder
previsualizarla en la interfaz antes de guardarla como PNG.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sin ventana; la GUI incrusta la figura
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")


@dataclass
class PlotOptions:
    """Opciones de personalizacion del grafico definidas por el usuario."""

    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    grid: bool = True
    legend: bool = True
    color: str = "#2563eb"
    palette: str = "viridis"


def create_bar_chart(
    df: pd.DataFrame,
    column: str,
    options: PlotOptions | None = None,
) -> plt.Figure:
    """Grafico de barras de frecuencias para una columna categorica o numerica.

    Cada valor distinto de la columna se trata como una categoria y se grafica
    su frecuencia (numero de apariciones).
    """
    options = options or PlotOptions()
    counts = df[column].astype(str).value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
    sns.barplot(
        x=counts.index,
        y=counts.values,
        hue=counts.index,
        palette=options.palette,
        legend=False,
        ax=ax,
    )
    ax.set_title(options.title or f"Frecuencia de {column}", fontsize=13, weight="bold")
    ax.set_xlabel(options.xlabel or column)
    ax.set_ylabel(options.ylabel or "Frecuencia")
    _apply_common(ax, options, legend_available=False)
    _rotate_if_needed(ax, counts.index)
    fig.tight_layout()
    return fig


def create_box_chart(
    df: pd.DataFrame,
    columns: list[str],
    options: PlotOptions | None = None,
) -> plt.Figure:
    """Grafico de cajas para una o varias columnas numericas."""
    options = options or PlotOptions()
    data = df[columns].apply(pd.to_numeric, errors="coerce")

    fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
    sns.boxplot(data=data, palette=options.palette, ax=ax)
    ax.set_title(
        options.title or f"Diagrama de cajas: {', '.join(columns)}",
        fontsize=13,
        weight="bold",
    )
    ax.set_xlabel(options.xlabel or "Variable")
    ax.set_ylabel(options.ylabel or "Valor")
    _apply_common(ax, options, legend_available=False)
    fig.tight_layout()
    return fig


def create_scatter_chart(
    df: pd.DataFrame,
    col_x: str,
    col_y: str,
    options: PlotOptions | None = None,
) -> plt.Figure:
    """Grafico de dispersion entre dos columnas numericas."""
    options = options or PlotOptions()
    data = df[[col_x, col_y]].apply(pd.to_numeric, errors="coerce").dropna()

    fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
    ax.scatter(
        data[col_x],
        data[col_y],
        color=options.color,
        alpha=0.75,
        edgecolors="white",
        s=70,
        label=f"{col_x} vs {col_y}",
    )
    ax.set_title(
        options.title or f"Dispersion: {col_x} vs {col_y}",
        fontsize=13,
        weight="bold",
    )
    ax.set_xlabel(options.xlabel or col_x)
    ax.set_ylabel(options.ylabel or col_y)
    _apply_common(ax, options, legend_available=True)
    fig.tight_layout()
    return fig


def create_pie_chart(
    df: pd.DataFrame,
    column: str,
    options: PlotOptions | None = None,
) -> plt.Figure:
    """Grafico circular para una columna categorica o numerica.

    Calcula la frecuencia de cada categoria, la convierte a porcentaje y lo
    muestra dentro de la porcion correspondiente del circulo.
    """
    options = options or PlotOptions()
    counts = df[column].astype(str).value_counts().sort_index()
    if counts.empty:
        raise ValueError(f"La columna '{column}' no tiene datos para graficar.")

    total = int(counts.sum())
    colors = sns.color_palette(options.palette, len(counts))

    fig, ax = plt.subplots(figsize=(7.5, 6), dpi=100)

    def _autopct(pct: float) -> str:
        # Reconstruye la frecuencia absoluta a partir del porcentaje
        cantidad = int(round(pct * total / 100.0))
        return f"{pct:.1f}%\n({cantidad})"

    wedges, _texts, autotexts = ax.pie(
        counts.values,
        labels=None if options.legend else counts.index,
        autopct=_autopct,
        startangle=90,
        counterclock=False,
        colors=colors,
        pctdistance=0.72,
        wedgeprops={"edgecolor": "white", "linewidth": 1.2},
    )
    for txt in autotexts:
        txt.set_color("white")
        txt.set_fontsize(9)
        txt.set_fontweight("bold")

    ax.set_title(
        options.title or f"Distribucion de {column} (%)",
        fontsize=13,
        weight="bold",
    )
    ax.axis("equal")  # circulo perfecto

    if options.legend:
        ax.legend(
            wedges,
            [f"{idx} ({val})" for idx, val in zip(counts.index, counts.values)],
            title=options.xlabel or column,
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
            fontsize=9,
        )
    fig.tight_layout()
    return fig


def save_figure(fig: plt.Figure, path: str | Path) -> Path:
    """Guarda la figura como PNG y devuelve la ruta final."""
    path = Path(path)
    if path.suffix.lower() != ".png":
        path = path.with_suffix(".png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return path


def _apply_common(ax: plt.Axes, options: PlotOptions, legend_available: bool) -> None:
    ax.grid(options.grid, linestyle="--", alpha=0.5)
    if legend_available and options.legend:
        ax.legend()
    elif ax.get_legend() is not None and not options.legend:
        ax.get_legend().remove()


def _rotate_if_needed(ax: plt.Axes, labels) -> None:
    if any(len(str(label)) > 8 for label in labels) or len(labels) > 6:
        ax.tick_params(axis="x", rotation=30)
        for label in ax.get_xticklabels():
            label.set_ha("right")
