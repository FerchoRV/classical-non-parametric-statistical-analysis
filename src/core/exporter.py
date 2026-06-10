"""Exportacion de resultados a archivos Excel en la carpeta results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..config import RESULTS_DIR


def _resolve_results_path(filename: str) -> Path:
    """Construye la ruta destino dentro de results/ con extension .xlsx."""
    name = filename.strip()
    if not name:
        raise ValueError("Debe indicar un nombre de archivo.")
    path = Path(name)
    if path.suffix.lower() not in (".xlsx", ".xls"):
        path = path.with_suffix(".xlsx")
    # Si el usuario solo dio un nombre, guardarlo dentro de results/
    if not path.is_absolute() and path.parent == Path("."):
        path = RESULTS_DIR / path.name
    return path


def export_sheets(sheets: dict[str, pd.DataFrame], filename: str) -> Path:
    """Exporta varios DataFrames a un Excel, uno por hoja.

    Args:
        sheets: mapeo {nombre_de_hoja: DataFrame}.
        filename: nombre del archivo (se guarda en results/ si no es ruta).
    """
    path = _resolve_results_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, frame in sheets.items():
            safe_name = sheet_name[:31] if sheet_name else "Hoja"
            frame.to_excel(writer, sheet_name=safe_name, index=False)
    return path
