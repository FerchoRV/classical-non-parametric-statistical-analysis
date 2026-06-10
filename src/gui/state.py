"""Estado compartido de la aplicacion entre vistas."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class AppState:
    """Contenedor del DataFrame cargado y su origen."""

    def __init__(self) -> None:
        self.dataframe: pd.DataFrame | None = None
        self.source_path: Path | None = None

    @property
    def has_data(self) -> bool:
        return self.dataframe is not None and not self.dataframe.empty

    def set_data(self, df: pd.DataFrame, path: Path) -> None:
        self.dataframe = df
        self.source_path = path

    @property
    def filename(self) -> str:
        return self.source_path.name if self.source_path else "Ninguno"
