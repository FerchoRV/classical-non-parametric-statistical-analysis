"""Vista de inicio: carga de documento y acceso a los modulos."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from .. import config
from ..core.data_loader import DataLoadError, load_dataframe
from .state import AppState
from .widgets import DataFrameTable, Toast


class HomeView(ctk.CTkFrame):
    """Pantalla principal con carga de datos y navegacion a modulos."""

    def __init__(self, master, state: AppState, navigate):
        super().__init__(master, fg_color="transparent")
        self.state = state
        self.navigate = navigate

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_actions()
        self._build_preview()

    # ------------------------------------------------------------------ UI
    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(24, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Sistema de Analisis Estadistico Colsign",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Estadistica no parametrica y descriptiva para la evaluacion de percepcion del usuario",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _build_actions(self) -> None:
        panel = ctk.CTkFrame(self, fg_color=config.COLOR_SURFACE, corner_radius=14)
        panel.grid(row=1, column=0, sticky="ew", padx=30, pady=10)
        for i in range(4):
            panel.grid_columnconfigure(i, weight=1)

        ctk.CTkButton(
            panel,
            text="Cargar documento",
            height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=config.COLOR_PRIMARY,
            hover_color=config.COLOR_PRIMARY_HOVER,
            command=self._load_file,
        ).grid(row=0, column=0, padx=14, pady=16, sticky="ew")

        self.file_label = ctk.CTkLabel(
            panel,
            text="Archivo: ninguno",
            font=ctk.CTkFont(size=13),
            text_color="#cbd5e1",
            anchor="w",
        )
        self.file_label.grid(row=0, column=1, padx=4, pady=16, sticky="ew")

        self.btn_nonparam = ctk.CTkButton(
            panel,
            text="Pruebas No Parametricas",
            height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=config.COLOR_SECONDARY,
            hover_color="#0284c7",
            state="disabled",
            command=lambda: self.navigate("nonparametric"),
        )
        self.btn_nonparam.grid(row=0, column=2, padx=14, pady=16, sticky="ew")

        self.btn_descriptive = ctk.CTkButton(
            panel,
            text="Estadistica Descriptiva",
            height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=config.COLOR_SUCCESS,
            hover_color=config.COLOR_SUCCESS_HOVER,
            state="disabled",
            command=lambda: self.navigate("descriptive"),
        )
        self.btn_descriptive.grid(row=0, column=3, padx=14, pady=16, sticky="ew")

        self.status = ctk.CTkLabel(panel, text="", font=ctk.CTkFont(size=13))
        self.status.grid(row=1, column=0, columnspan=4, padx=14, pady=(0, 12), sticky="w")

    def _build_preview(self) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=2, column=0, sticky="nsew", padx=30, pady=(10, 24))
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            wrapper,
            text="Vista previa de los datos",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.table = DataFrameTable(wrapper)
        self.table.grid(row=1, column=0, sticky="nsew")

    # -------------------------------------------------------------- Logica
    def _load_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccione el documento a procesar",
            initialdir=str(config.BASE_DIR),
            filetypes=[
                ("Todos los compatibles", "*.xlsx *.xls *.csv *.txt *.json"),
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("Texto", "*.txt"),
                ("JSON", "*.json"),
            ],
        )
        if not path:
            return
        try:
            df = load_dataframe(path)
        except DataLoadError as exc:
            Toast.show(self.status, str(exc), "error")
            return

        self.state.set_data(df, Path(path))
        self.file_label.configure(text=f"Archivo: {self.state.filename}")
        self.table.show(df)
        self.btn_nonparam.configure(state="normal")
        self.btn_descriptive.configure(state="normal")
        Toast.show(
            self.status,
            f"Datos cargados correctamente: {df.shape[0]} filas x {df.shape[1]} columnas.",
            "success",
        )

    def refresh(self) -> None:
        """Actualiza la vista cuando se regresa a la pantalla de inicio."""
        if self.state.has_data:
            self.file_label.configure(text=f"Archivo: {self.state.filename}")
            self.table.show(self.state.dataframe)
            self.btn_nonparam.configure(state="normal")
            self.btn_descriptive.configure(state="normal")
