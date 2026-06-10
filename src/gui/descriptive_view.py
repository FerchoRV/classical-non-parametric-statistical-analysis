"""Vista del modulo de estadistica descriptiva y graficos."""

from __future__ import annotations

import customtkinter as ctk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog

from .. import config
from ..core import plotting
from ..core.data_loader import get_categorical_columns, get_numeric_columns
from ..core.descriptive import describe_columns
from ..core.exporter import export_sheets
from .state import AppState
from .widgets import DataFrameTable, Toast

CHART_BAR = "Barras (texto o numerica)"
CHART_BOX = "Cajas (columna numerica)"
CHART_SCATTER = "Dispersion (dos columnas numericas)"
CHART_PIE = "Circular (porcentaje, texto o numerica)"


class DescriptiveView(ctk.CTkFrame):
    """Calcula descriptivos y genera graficos personalizables."""

    def __init__(self, master, state: AppState, navigate):
        super().__init__(master, fg_color="transparent")
        self.state = state
        self.navigate = navigate
        self._last_describe: pd.DataFrame | None = None
        self._current_figure = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._column_checks: dict[str, ctk.CTkCheckBox] = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_controls()
        self._build_content()

    # ------------------------------------------------------------------ UI
    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 8))
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(
            header, text="< Inicio", width=90, fg_color="#334155",
            hover_color="#475569", command=lambda: self.navigate("home"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header, text="Estadistica Descriptiva y Graficos",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=16)

    def _build_controls(self) -> None:
        panel = ctk.CTkScrollableFrame(
            self, width=330, fg_color=config.COLOR_SURFACE, corner_radius=14
        )
        panel.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)

        ctk.CTkLabel(
            panel, text="1. Seleccion de columnas",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", pady=(4, 6))
        ctk.CTkLabel(
            panel, text="Marque las columnas a analizar:",
            text_color="#94a3b8", font=ctk.CTkFont(size=12),
        ).pack(anchor="w")
        self.checks_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.checks_frame.pack(anchor="w", fill="x", pady=(4, 12))

        # --- Descriptivos ---
        ctk.CTkLabel(
            panel, text="2. Calculo descriptivo",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", pady=(4, 6))
        ctk.CTkLabel(
            panel, text="Media, mediana y moda (columnas numericas)",
            text_color="#94a3b8", font=ctk.CTkFont(size=12), wraplength=300, justify="left",
        ).pack(anchor="w")
        ctk.CTkButton(
            panel, text="Calcular descriptivos", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLOR_PRIMARY, hover_color=config.COLOR_PRIMARY_HOVER,
            command=self._calculate,
        ).pack(anchor="w", fill="x", pady=(6, 4))
        self.desc_name = ctk.CTkEntry(panel, placeholder_text="nombre_descriptivos")
        self.desc_name.pack(anchor="w", fill="x", pady=(4, 4))
        self.btn_save_desc = ctk.CTkButton(
            panel, text="Guardar descriptivos (results/)", height=38,
            fg_color=config.COLOR_SUCCESS, hover_color=config.COLOR_SUCCESS_HOVER,
            state="disabled", command=self._save_descriptive,
        )
        self.btn_save_desc.pack(anchor="w", fill="x", pady=(0, 12))

        # --- Graficos ---
        ctk.CTkLabel(
            panel, text="3. Graficos",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", pady=(4, 6))
        ctk.CTkLabel(panel, text="Tipo de grafico").pack(anchor="w")
        self.chart_menu = ctk.CTkOptionMenu(
            panel, values=[CHART_BAR, CHART_BOX, CHART_SCATTER, CHART_PIE],
            fg_color=config.COLOR_PRIMARY, button_color=config.COLOR_PRIMARY_HOVER,
            dynamic_resizing=False, width=300,
        )
        self.chart_menu.pack(anchor="w", fill="x", pady=(2, 8))

        self._build_plot_options(panel)

        ctk.CTkButton(
            panel, text="Generar grafico", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLOR_SECONDARY, hover_color="#0284c7",
            command=self._generate_plot,
        ).pack(anchor="w", fill="x", pady=(10, 4))
        self.graph_name = ctk.CTkEntry(panel, placeholder_text="nombre_grafico")
        self.graph_name.pack(anchor="w", fill="x", pady=(4, 4))
        self.btn_save_graph = ctk.CTkButton(
            panel, text="Guardar grafico (graphics/)", height=38,
            fg_color=config.COLOR_SUCCESS, hover_color=config.COLOR_SUCCESS_HOVER,
            state="disabled", command=self._save_graph,
        )
        self.btn_save_graph.pack(anchor="w", fill="x", pady=(0, 8))

        self.status = ctk.CTkLabel(panel, text="", wraplength=300, justify="left")
        self.status.pack(anchor="w", fill="x", pady=(6, 4))

    def _build_plot_options(self, panel) -> None:
        opt = ctk.CTkFrame(panel, fg_color="transparent")
        opt.pack(anchor="w", fill="x")
        ctk.CTkLabel(opt, text="Titulo").pack(anchor="w")
        self.opt_title = ctk.CTkEntry(opt, placeholder_text="Titulo del grafico")
        self.opt_title.pack(anchor="w", fill="x", pady=(0, 4))
        ctk.CTkLabel(opt, text="Etiqueta eje X").pack(anchor="w")
        self.opt_xlabel = ctk.CTkEntry(opt, placeholder_text="Eje X")
        self.opt_xlabel.pack(anchor="w", fill="x", pady=(0, 4))
        ctk.CTkLabel(opt, text="Etiqueta eje Y").pack(anchor="w")
        self.opt_ylabel = ctk.CTkEntry(opt, placeholder_text="Eje Y")
        self.opt_ylabel.pack(anchor="w", fill="x", pady=(0, 4))

        self.opt_grid = ctk.CTkCheckBox(opt, text="Mostrar cuadricula (grid)")
        self.opt_grid.select()
        self.opt_grid.pack(anchor="w", pady=(4, 2))
        self.opt_legend = ctk.CTkCheckBox(opt, text="Mostrar leyenda")
        self.opt_legend.select()
        self.opt_legend.pack(anchor="w", pady=(2, 4))

    def _build_content(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)
        content.grid_rowconfigure(3, weight=2)

        ctk.CTkLabel(
            content, text="Datos cargados", font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.table = DataFrameTable(content, height=180)
        self.table.grid(row=1, column=0, sticky="nsew")

        self.preview_label = ctk.CTkLabel(
            content, text="Previsualizacion (resultados / grafico)",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.preview_label.grid(row=2, column=0, sticky="w", pady=(12, 6))
        self.preview = ctk.CTkFrame(content, fg_color=config.COLOR_SURFACE, corner_radius=10)
        self.preview.grid(row=3, column=0, sticky="nsew")
        self.preview.grid_columnconfigure(0, weight=1)
        self.preview.grid_rowconfigure(0, weight=1)

        self.result_box = ctk.CTkTextbox(
            self.preview, fg_color=config.COLOR_SURFACE,
            font=ctk.CTkFont(size=13, family="Consolas"),
        )
        self.result_box.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.result_box.configure(state="disabled")

    # -------------------------------------------------------------- Eventos
    def refresh(self) -> None:
        if not self.state.has_data:
            return
        df = self.state.dataframe
        self.table.show(df)
        self._populate_checks(df)

    def _populate_checks(self, df: pd.DataFrame) -> None:
        for child in self.checks_frame.winfo_children():
            child.destroy()
        self._column_checks.clear()

        numeric = set(get_numeric_columns(df))
        for col in df.columns:
            name = str(col)
            tag = "num" if col in numeric else "txt"
            chk = ctk.CTkCheckBox(
                self.checks_frame,
                text=f"{name}  [{tag}]",
                font=ctk.CTkFont(size=12),
            )
            chk.pack(anchor="w", pady=1)
            self._column_checks[name] = chk

    def _selected_columns(self) -> list[str]:
        return [name for name, chk in self._column_checks.items() if chk.get()]

    # -------------------------------------------------------------- Descriptivos
    def _calculate(self) -> None:
        if not self.state.has_data:
            Toast.show(self.status, "Primero cargue un documento.", "error")
            return
        cols = self._selected_columns()
        if not cols:
            Toast.show(self.status, "Marque al menos una columna.", "error")
            return
        df = self.state.dataframe
        numeric = set(get_numeric_columns(df))
        numeric_selected = [c for c in cols if c in numeric]
        if not numeric_selected:
            Toast.show(self.status, "Seleccione columnas numericas para descriptivos.", "error")
            return
        try:
            result = describe_columns(df, numeric_selected)
        except Exception as exc:  # noqa: BLE001
            Toast.show(self.status, f"Error: {exc}", "error")
            return
        self._last_describe = result
        self._show_text(result.to_string(index=False))
        self.btn_save_desc.configure(state="normal")
        Toast.show(self.status, "Descriptivos calculados.", "success")

    def _save_descriptive(self) -> None:
        if self._last_describe is None:
            return
        name = self.desc_name.get().strip()
        if not name:
            Toast.show(self.status, "Indique un nombre de archivo.", "error")
            return
        try:
            path = export_sheets({"Descriptivos": self._last_describe}, name)
        except Exception as exc:  # noqa: BLE001
            Toast.show(self.status, f"No se pudo guardar: {exc}", "error")
            return
        self._reset_after_save()
        Toast.show(self.status, f"Guardado en:\n{path}\nSeleccion reiniciada.", "success")

    # -------------------------------------------------------------- Graficos
    def _plot_options(self) -> plotting.PlotOptions:
        return plotting.PlotOptions(
            title=self.opt_title.get().strip(),
            xlabel=self.opt_xlabel.get().strip(),
            ylabel=self.opt_ylabel.get().strip(),
            grid=bool(self.opt_grid.get()),
            legend=bool(self.opt_legend.get()),
        )

    def _generate_plot(self) -> None:
        if not self.state.has_data:
            Toast.show(self.status, "Primero cargue un documento.", "error")
            return
        df = self.state.dataframe
        cols = self._selected_columns()
        kind = self.chart_menu.get()
        numeric = set(get_numeric_columns(df))
        options = self._plot_options()

        try:
            fig = self._build_figure(df, cols, kind, numeric, options)
        except Exception as exc:  # noqa: BLE001
            Toast.show(self.status, f"Error: {exc}", "error")
            return

        self._current_figure = fig
        self._embed_figure(fig)
        self.btn_save_graph.configure(state="normal")
        Toast.show(self.status, "Grafico generado. Previsualizacion lista.", "success")

    def _build_figure(self, df, cols, kind, numeric, options):
        if kind == CHART_BAR:
            if len(cols) != 1:
                raise ValueError(
                    "Para barras seleccione exactamente UNA columna (texto o numerica)."
                )
            return plotting.create_bar_chart(df, cols[0], options)
        if kind == CHART_BOX:
            num_cols = [c for c in cols if c in numeric]
            if not num_cols:
                raise ValueError("Para cajas seleccione una o mas columnas numericas.")
            return plotting.create_box_chart(df, num_cols, options)
        if kind == CHART_PIE:
            if len(cols) != 1:
                raise ValueError(
                    "Para circular seleccione exactamente UNA columna (texto o numerica)."
                )
            return plotting.create_pie_chart(df, cols[0], options)
        # Dispersion
        num_cols = [c for c in cols if c in numeric]
        if len(num_cols) != 2:
            raise ValueError(
                "Para dispersion seleccione exactamente DOS columnas numericas."
            )
        return plotting.create_scatter_chart(df, num_cols[0], num_cols[1], options)

    def _embed_figure(self, fig) -> None:
        self.result_box.grid_remove()
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
        self._canvas = FigureCanvasTkAgg(fig, master=self.preview)
        self._canvas.draw()
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

    def _save_graph(self) -> None:
        if self._current_figure is None:
            return
        name = self.graph_name.get().strip()
        if not name:
            Toast.show(self.status, "Indique un nombre para el grafico.", "error")
            return
        from pathlib import Path

        target = Path(name)
        if not target.is_absolute() and target.parent == Path("."):
            target = config.GRAPHICS_DIR / target.name
        try:
            path = plotting.save_figure(self._current_figure, target)
        except Exception as exc:  # noqa: BLE001
            Toast.show(self.status, f"No se pudo guardar: {exc}", "error")
            return
        self._reset_after_save()
        Toast.show(self.status, f"Grafico guardado en:\n{path}\nSeleccion reiniciada.", "success")

    def _reset_after_save(self) -> None:
        """Limpia columnas marcadas, previsualizacion y campos tras guardar."""
        self._last_describe = None
        self._current_figure = None
        self.desc_name.delete(0, "end")
        self.graph_name.delete(0, "end")
        self.btn_save_desc.configure(state="disabled")
        self.btn_save_graph.configure(state="disabled")
        for chk in self._column_checks.values():
            chk.deselect()
        # Limpia opciones de personalizacion del grafico
        self.opt_title.delete(0, "end")
        self.opt_xlabel.delete(0, "end")
        self.opt_ylabel.delete(0, "end")
        # Limpia la previsualizacion (texto o grafico)
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None
        self.result_box.grid()
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.configure(state="disabled")

    # -------------------------------------------------------------- Helpers
    def _show_text(self, text: str) -> None:
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None
        self.result_box.grid()
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", text)
        self.result_box.configure(state="disabled")
