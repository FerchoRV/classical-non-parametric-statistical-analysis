"""Carga de datos desde distintos formatos compatibles con pandas.

Soporta Excel (.xlsx/.xls), CSV (.csv), texto plano (.txt) y JSON (.json).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class DataLoadError(Exception):
    """Error controlado durante la carga de un archivo de datos."""


def load_dataframe(path: str | Path) -> pd.DataFrame:
    """Carga un archivo de datos y lo devuelve como ``pandas.DataFrame``.

    Detecta el formato por la extension del archivo. Para CSV y TXT intenta
    inferir el separador automaticamente y prueba varias codificaciones
    comunes (util para acentos y la letra n con virgulilla en espanol).
    """
    path = Path(path)
    if not path.exists():
        raise DataLoadError(f"El archivo no existe:\n{path}")

    suffix = path.suffix.lower()

    try:
        if suffix in (".xlsx", ".xls"):
            return pd.read_excel(path)
        if suffix == ".json":
            return _read_json(path)
        if suffix in (".csv", ".txt"):
            return _read_text_table(path)
    except DataLoadError:
        raise
    except Exception as exc:  # noqa: BLE001 - se reempaqueta como error controlado
        raise DataLoadError(f"No se pudo leer el archivo:\n{exc}") from exc

    raise DataLoadError(
        f"Formato no soportado: '{suffix}'.\n"
        "Use Excel, CSV, TXT o JSON."
    )


def _read_json(path: Path) -> pd.DataFrame:
    """Lee un JSON tolerando tanto listas de objetos como JSON por lineas."""
    for kwargs in ({}, {"lines": True}):
        try:
            df = pd.read_json(path, **kwargs)
            if not df.empty:
                return df
        except ValueError:
            continue
    raise DataLoadError("El JSON no tiene un formato tabular reconocible.")


def _read_text_table(path: Path) -> pd.DataFrame:
    """Lee CSV o TXT infiriendo separador y probando codificaciones."""
    encodings = ("utf-8-sig", "utf-8", "latin-1", "cp1252")
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            # sep=None + engine="python" => inferencia automatica del separador
            df = pd.read_csv(path, sep=None, engine="python", encoding=encoding)
            if df.shape[1] == 1:
                # Reintenta con separadores comunes si quedo una sola columna
                for sep in (";", "\t", ",", "|"):
                    alt = pd.read_csv(path, sep=sep, encoding=encoding)
                    if alt.shape[1] > 1:
                        return alt
            return df
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
    raise DataLoadError(
        f"No se pudo decodificar el archivo de texto.\n{last_error}"
    )


def get_numeric_columns(df: pd.DataFrame) -> list[str]:
    """Devuelve los nombres de columnas numericas del DataFrame."""
    return df.select_dtypes(include="number").columns.tolist()


def get_categorical_columns(df: pd.DataFrame) -> list[str]:
    """Devuelve columnas de texto/categoricas (object o category)."""
    return df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
