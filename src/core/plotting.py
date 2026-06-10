"""Generacion de graficos con matplotlib/seaborn.

Tipos soportados:
  * Barras    -> columnas de texto/categoricas o numericas (frecuencias).
  * Cajas     -> columnas numericas (distribucion y atipicos).
  * Dispersion-> dos columnas numericas (relacion entre variables).
  * Circular  -> columnas categoricas o numericas (porcentaje por categoria).
  * Barra apilada -> tendencia de una ordinal por grupo (cantidad + % total).
  * Mapa de calor -> tendencia de una ordinal por grupo (matriz % total y conteo).

Todas las funciones devuelven una ``matplotlib.figure.Figure`` para poder
previsualizarla en la interfaz antes de guardarla como PNG.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sin ventana; la GUI incrusta la figura
import matplotlib.pyplot as plt
import numpy as np
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


def _crosstab_counts_pct(df, group_col, ordinal_col):
    """Construye tablas de conteo y de porcentaje por fila (grupo).

    Filas = categorias del grupo; columnas = niveles de la ordinal.
    El porcentaje se normaliza dentro de cada grupo (cada fila suma 100%).
    """
    work = df[[group_col, ordinal_col]].copy()
    work[ordinal_col] = pd.to_numeric(work[ordinal_col], errors="coerce")
    work = work.dropna()
    if work.empty:
        raise ValueError("No hay datos validos para cruzar las columnas elegidas.")
    work[group_col] = work[group_col].astype(str)

    counts = pd.crosstab(work[group_col], work[ordinal_col])
    counts = counts.reindex(sorted(counts.columns), axis=1)
    row_tot = counts.sum(axis=1).replace(0, np.nan)
    pct = counts.div(row_tot, axis=0) * 100.0
    return counts, pct.fillna(0.0)


def create_stacked_bar_chart(
    df: pd.DataFrame,
    group_col: str,
    ordinal_col: str,
    options: PlotOptions | None = None,
) -> plt.Figure:
    """Barra apilada (por cantidad): tendencia de una ordinal segun el grupo.

    Una barra por cada categoria del grupo, dividida por los niveles de la
    variable ordinal (colores). La altura de cada segmento es la **cantidad de
    respuestas**, por lo que las barras tienen distinto tamano segun el numero
    de personas de cada grupo. Cada segmento se anota con el **porcentaje sobre
    el total de los datos** y, entre parentesis, la frecuencia absoluta.
    """
    options = options or PlotOptions()
    counts, _pct_group = _crosstab_counts_pct(df, group_col, ordinal_col)

    total = float(counts.values.sum())
    groups = list(counts.index)
    levels = list(counts.columns)
    x = np.arange(len(groups))
    colors = sns.color_palette(options.palette, len(levels))

    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=100)
    bottom = np.zeros(len(groups))
    for i, level in enumerate(levels):
        heights = counts[level].to_numpy().astype(float)
        ax.bar(x, heights, bottom=bottom, color=colors[i], label=str(level), width=0.7)
        for j, (h, b) in enumerate(zip(heights, bottom)):
            if h > 0:
                cantidad = int(round(h))
                pct_total = (h / total * 100.0) if total else 0.0
                ax.text(
                    x[j], b + h / 2.0, f"{pct_total:.0f}%\n({cantidad})",
                    ha="center", va="center", fontsize=8,
                    color=_text_color_for(colors[i]), fontweight="bold",
                )
        bottom += heights

    ax.set_title(
        options.title or f"Tendencia de {ordinal_col} por {group_col}",
        fontsize=13, weight="bold",
    )
    ax.set_xlabel(options.xlabel or group_col)
    ax.set_ylabel(options.ylabel or "Cantidad de respuestas")
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.grid(options.grid, axis="y", linestyle="--", alpha=0.5)
    _rotate_if_needed(ax, groups)
    if options.legend:
        # Leyenda sin titulo (lista los niveles de la variable ordinal)
        ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9)
    fig.tight_layout()
    return fig


def create_heatmap_chart(
    df: pd.DataFrame,
    group_col: str,
    ordinal_col: str,
    options: PlotOptions | None = None,
) -> plt.Figure:
    """Mapa de calor: tendencia de una ordinal segun el grupo.

    Filas = categorias del grupo; columnas = niveles de la ordinal. El color
    refleja el porcentaje sobre el **total de los datos** y cada celda se anota
    con ese porcentaje y la frecuencia absoluta.
    """
    options = options or PlotOptions()
    counts, _pct_group = _crosstab_counts_pct(df, group_col, ordinal_col)

    total = float(counts.values.sum())
    pct_total = counts / total * 100.0 if total else counts * 0.0

    annot = np.empty(pct_total.shape, dtype=object)
    for i in range(pct_total.shape[0]):
        for j in range(pct_total.shape[1]):
            annot[i, j] = f"{pct_total.values[i, j]:.0f}%\n({int(counts.values[i, j])})"

    height = max(3.5, 0.7 * pct_total.shape[0] + 2)
    fig, ax = plt.subplots(figsize=(8.5, height), dpi=100)
    sns.heatmap(
        pct_total,
        annot=annot,
        fmt="",
        cmap=options.palette or "viridis",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "% del total"},
        ax=ax,
        annot_kws={"fontsize": 9},
    )
    ax.set_title(
        options.title or f"Tendencia de {ordinal_col} por {group_col}",
        fontsize=13, weight="bold",
    )
    ax.set_xlabel(options.xlabel or ordinal_col)
    ax.set_ylabel(options.ylabel or group_col)
    fig.tight_layout()
    return fig


def _text_color_for(rgb) -> str:
    """Elige texto blanco o negro segun la luminancia del color de fondo."""
    r, g, b = rgb[0], rgb[1], rgb[2]
    luminancia = 0.299 * r + 0.587 * g + 0.114 * b
    return "black" if luminancia > 0.6 else "white"


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
