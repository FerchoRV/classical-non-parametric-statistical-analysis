"""Widgets reutilizables para la interfaz."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk
import pandas as pd

from .. import config


class DataFrameTable(ctk.CTkFrame):
    """Tabla con scroll para visualizar un ``pandas.DataFrame``.

    Usa internamente un ``ttk.Treeview`` estilizado para integrarse con el
    tema oscuro de customtkinter.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=config.COLOR_SURFACE, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._style_treeview()

        self.tree = ttk.Treeview(self, show="headings", style="descriptivo y pruebas no paramétricas.Treeview")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns", pady=8)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky="ew", padx=(8, 0))
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._placeholder = ctk.CTkLabel(
            self,
            text="Sin datos cargados",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=14),
        )
        self._placeholder.grid(row=0, column=0)

    def _style_treeview(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "descriptivo y pruebas no paramétricas.Treeview",
            background="#0f172a",
            foreground="#e2e8f0",
            fieldbackground="#0f172a",
            rowheight=26,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "descriptivo y pruebas no paramétricas.Treeview.Heading",
            background=config.COLOR_PRIMARY,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map(
            "descriptivo y pruebas no paramétricas.Treeview",
            background=[("selected", config.COLOR_SECONDARY)],
            foreground=[("selected", "white")],
        )
        style.map("descriptivo y pruebas no paramétricas.Treeview.Heading", background=[("active", config.COLOR_PRIMARY_HOVER)])

    def show(self, df: pd.DataFrame, max_rows: int = 500) -> None:
        """Muestra el DataFrame (limitado a ``max_rows`` filas por rendimiento)."""
        self.tree.delete(*self.tree.get_children())

        if df is None or df.empty:
            self.tree["columns"] = ()
            self._placeholder.lift()
            return

        self._placeholder.lower()
        view = df.head(max_rows)
        columns = [str(c) for c in view.columns]
        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(col, text=col)
            width = min(max(len(col) * 9, 80), 280)
            self.tree.column(col, width=width, anchor="center", stretch=False)

        for _, row in view.iterrows():
            values = ["" if pd.isna(v) else str(v) for v in row.tolist()]
            self.tree.insert("", "end", values=values)


class Toast:
    """Mensajes emergentes simples no bloqueantes en una etiqueta de estado."""

    @staticmethod
    def configure_label(label: ctk.CTkLabel) -> None:
        label.configure(text="")

    @staticmethod
    def show(label: ctk.CTkLabel, message: str, kind: str = "info") -> None:
        colors = {
            "info": "#38bdf8",
            "success": config.COLOR_SUCCESS,
            "error": config.COLOR_DANGER,
        }
        label.configure(text=message, text_color=colors.get(kind, "#38bdf8"))
