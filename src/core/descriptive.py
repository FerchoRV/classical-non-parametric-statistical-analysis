"""Estadistica descriptiva: media, mediana y moda de columnas numericas."""

from __future__ import annotations

import pandas as pd


def describe_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Calcula estadisticos descriptivos para las columnas numericas dadas.

    Devuelve una tabla con N, media, mediana, moda, desviacion estandar,
    minimo y maximo por cada columna seleccionada.
    """
    if not columns:
        raise ValueError("Seleccione al menos una columna numerica.")

    rows: list[dict[str, object]] = []
    for col in columns:
        serie = pd.to_numeric(df[col], errors="coerce").dropna()
        if serie.empty:
            raise ValueError(
                f"La columna '{col}' no contiene valores numericos validos."
            )

        modas = serie.mode()
        moda_txt = ", ".join(str(_clean(m)) for m in modas.tolist()) if not modas.empty else "N/D"

        rows.append(
            {
                "Columna": col,
                "N": int(serie.count()),
                "Media": round(float(serie.mean()), 4),
                "Mediana": round(float(serie.median()), 4),
                "Moda": moda_txt,
                "Desv. Estandar": round(float(serie.std()), 4),
                "Minimo": _clean(serie.min()),
                "Maximo": _clean(serie.max()),
            }
        )

    return pd.DataFrame(rows)


def _clean(value: object) -> object:
    """Convierte enteros tipo float (3.0) a int para una vista mas limpia."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value
