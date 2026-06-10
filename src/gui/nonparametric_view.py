"""Vista del modulo de pruebas no parametricas."""

from __future__ import annotations

import customtkinter as ctk

import pandas as pd

from .. import config
from ..core import nonparametric
from ..core.data_loader import get_numeric_columns
from ..core.exporter import export_sheets
from .state import AppState
from .widgets import DataFrameTable, Toast

# Pruebas disponibles
SPEARMAN_OC = "Correlacion Spearman: Ordinal vs Continua"
SPEARMAN_OO = "Correlacion Spearman: Ordinal vs Ordinal"
GROUPS = "Analisis por grupos: Ordinal vs Nominal"
CATEGORICAL = "Asociacion categorica: Nominal vs Nominal (Fisher)"

_SPEARMAN_TESTS = (SPEARMAN_OC, SPEARMAN_OO)
# Pruebas de rangos que admiten p-valores exactos por permutaciones
_RANK_TESTS = (SPEARMAN_OC, SPEARMAN_OO, GROUPS)


class NonParametricView(ctk.CTkFrame):
    """Pruebas: Spearman (ordinal-continua y ordinal-ordinal), analisis por
    grupos (ordinal vs nominal, flexible) y asociacion categorica (Fisher +
    V de Cramer). Las de rangos admiten p-valor exacto opcional."""

    def __init__(self, master, state: AppState, navigate):
        super().__init__(master, fg_color="transparent")
        self.state = state
        self.navigate = navigate
        self._last_result: nonparametric.TestResult | None = None

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
            header,
            text="< Inicio",
            width=90,
            fg_color="#334155",
            hover_color="#475569",
            command=lambda: self.navigate("home"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Pruebas Estadisticas No Parametricas",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=16)

    def _build_controls(self) -> None:
        panel = ctk.CTkScrollableFrame(
            self, width=320, fg_color=config.COLOR_SURFACE, corner_radius=14
        )
        panel.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)

        ctk.CTkLabel(
            panel, text="Configuracion de la prueba",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", pady=(4, 10))

        ctk.CTkLabel(panel, text="Tipo de prueba").pack(anchor="w")
        self.test_menu = ctk.CTkOptionMenu(
            panel,
            values=[SPEARMAN_OC, SPEARMAN_OO, GROUPS, CATEGORICAL],
            command=self._on_test_change,
            fg_color=config.COLOR_PRIMARY,
            button_color=config.COLOR_PRIMARY_HOVER,
            dynamic_resizing=False,
            width=290,
        )
        self.test_menu.pack(anchor="w", pady=(2, 10), fill="x")

        self.test_hint = ctk.CTkLabel(
            panel, text="", wraplength=290, justify="left",
            text_color="#94a3b8", font=ctk.CTkFont(size=11),
        )
        self.test_hint.pack(anchor="w", pady=(0, 10), fill="x")

        # Contenedor para los selectores que cambian segun la prueba elegida
        self.selector_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.selector_frame.pack(anchor="w", fill="x")

        # Spearman -> dos columnas a correlacionar
        self.label_x = ctk.CTkLabel(self.selector_frame, text="Variable X")
        self.menu_x = ctk.CTkOptionMenu(self.selector_frame, values=["-"], width=290, dynamic_resizing=False)
        self.label_y = ctk.CTkLabel(self.selector_frame, text="Variable Y")
        self.menu_y = ctk.CTkOptionMenu(self.selector_frame, values=["-"], width=290, dynamic_resizing=False)

        # Grupos -> columna nominal (agrupa) + columna ordinal a comparar
        self.label_group = ctk.CTkLabel(self.selector_frame, text="Variable NOMINAL (agrupa)")
        self.menu_group = ctk.CTkOptionMenu(self.selector_frame, values=["-"], width=290, dynamic_resizing=False)
        self.label_value = ctk.CTkLabel(self.selector_frame, text="Variable ORDINAL (a comparar)")
        self.menu_value = ctk.CTkOptionMenu(self.selector_frame, values=["-"], width=290, dynamic_resizing=False)

        # Categorica -> dos columnas categoricas/nominales
        self.label_cat_a = ctk.CTkLabel(self.selector_frame, text="Variable categorica A")
        self.menu_cat_a = ctk.CTkOptionMenu(self.selector_frame, values=["-"], width=290, dynamic_resizing=False)
        self.label_cat_b = ctk.CTkLabel(self.selector_frame, text="Variable categorica B")
        self.menu_cat_b = ctk.CTkOptionMenu(self.selector_frame, values=["-"], width=290, dynamic_resizing=False)

        # Checkbox de p-valores exactos (solo para pruebas de rangos).
        # Va en su propio contenedor para conservar la posicion al ocultarse.
        self.exact_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.exact_frame.pack(anchor="w", fill="x", pady=(8, 0))
        self.exact_check = ctk.CTkCheckBox(
            self.exact_frame,
            text="Usar p-valor exacto (permutaciones)\nrecomendado para muestras pequenas",
            font=ctk.CTkFont(size=11),
        )

        ctk.CTkButton(
            panel,
            text="Ejecutar prueba",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLOR_PRIMARY,
            hover_color=config.COLOR_PRIMARY_HOVER,
            command=self._run_test,
        ).pack(anchor="w", pady=(16, 8), fill="x")

        ctk.CTkLabel(panel, text="Guardar resultado (Excel en results/)").pack(anchor="w", pady=(8, 2))
        self.filename_entry = ctk.CTkEntry(panel, placeholder_text="nombre_resultado", width=290)
        self.filename_entry.pack(anchor="w", fill="x")
        self.btn_save = ctk.CTkButton(
            panel,
            text="Guardar resultado",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLOR_SUCCESS,
            hover_color=config.COLOR_SUCCESS_HOVER,
            state="disabled",
            command=self._save_result,
        )
        self.btn_save.pack(anchor="w", pady=(8, 4), fill="x")

        self.status = ctk.CTkLabel(panel, text="", wraplength=290, justify="left")
        self.status.pack(anchor="w", pady=(8, 4), fill="x")

    def _build_content(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=3)
        content.grid_rowconfigure(3, weight=2)

        ctk.CTkLabel(
            content, text="Datos cargados", font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.table = DataFrameTable(content)
        self.table.grid(row=1, column=0, sticky="nsew")

        ctk.CTkLabel(
            content,
            text="Previsualizacion del resultado",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=2, column=0, sticky="w", pady=(12, 6))
        self.result_box = ctk.CTkTextbox(
            content, fg_color=config.COLOR_SURFACE, font=ctk.CTkFont(size=13, family="Consolas")
        )
        self.result_box.grid(row=3, column=0, sticky="nsew")
        self.result_box.configure(state="disabled")

    # -------------------------------------------------------------- Eventos
    def refresh(self) -> None:
        """Recarga columnas y datos al entrar a la vista."""
        if not self.state.has_data:
            return
        df = self.state.dataframe
        self.table.show(df)
        all_cols = [str(c) for c in df.columns]
        numeric = get_numeric_columns(df) or all_cols

        self._set_menu(self.menu_x, numeric)
        self._set_menu(self.menu_y, numeric)
        self._set_menu(self.menu_group, all_cols)
        self._set_menu(self.menu_value, numeric or all_cols)
        self._set_menu(self.menu_cat_a, all_cols)
        self._set_menu(self.menu_cat_b, all_cols)
        self._on_test_change(self.test_menu.get())

    @staticmethod
    def _set_menu(menu: ctk.CTkOptionMenu, values: list[str]) -> None:
        values = values or ["-"]
        menu.configure(values=values)
        menu.set(values[0])

    def _on_test_change(self, choice: str) -> None:
        for w in (
            self.label_x, self.menu_x, self.label_y, self.menu_y,
            self.label_group, self.menu_group, self.label_value, self.menu_value,
            self.label_cat_a, self.menu_cat_a, self.label_cat_b, self.menu_cat_b,
        ):
            w.pack_forget()
        self.exact_check.pack_forget()

        if choice in _SPEARMAN_TESTS:
            if choice == SPEARMAN_OC:
                self.label_x.configure(text="Variable ORDINAL (1-5)")
                self.label_y.configure(text="Variable CONTINUA")
                self.test_hint.configure(
                    text="Spearman entre una variable ordinal (ej. percepcion 1-5) "
                    "y una continua (ej. accuracy de los logs)."
                )
            else:
                self.label_x.configure(text="Variable ORDINAL (1-5)")
                self.label_y.configure(text="Variable ORDINAL (1-5)")
                self.test_hint.configure(
                    text="Spearman entre dos variables ordinales (ej. precision vs "
                    "intuitividad). A mayor valoracion en una, mayor en la otra."
                )
            widgets = (self.label_x, self.menu_x, self.label_y, self.menu_y)
        elif choice == GROUPS:
            self.test_hint.configure(
                text="Compara las medianas de la variable ordinal entre las "
                "categorias de la nominal. 2 grupos: Mann-Whitney; 3+ grupos: "
                "Kruskal-Wallis. La nominal puede tener 2 o mas categorias."
            )
            widgets = (self.label_group, self.menu_group, self.label_value, self.menu_value)
        else:  # CATEGORICAL
            self.test_hint.configure(
                text="Asociacion entre dos variables categoricas/nominales. "
                "Usa Fisher exacto (2x2) o Monte Carlo (3+ categorias) y V de "
                "Cramer como tamano del efecto. Ya es exacta, no requiere opcion."
            )
            widgets = (self.label_cat_a, self.menu_cat_a, self.label_cat_b, self.menu_cat_b)
        for w in widgets:
            w.pack(anchor="w", pady=(2, 6), fill="x")

        # El p-valor exacto solo aplica a las pruebas de rangos
        if choice in _RANK_TESTS:
            self.exact_check.pack(anchor="w", pady=(2, 2))

    # -------------------------------------------------------------- Acciones
    def _run_test(self) -> None:
        if not self.state.has_data:
            Toast.show(self.status, "Primero cargue un documento.", "error")
            return
        df = self.state.dataframe
        choice = self.test_menu.get()
        exact = bool(self.exact_check.get())
        try:
            if choice in _SPEARMAN_TESTS:
                col_x, col_y = self.menu_x.get(), self.menu_y.get()
                if col_x == col_y:
                    raise ValueError("Seleccione dos columnas distintas.")
                context = (
                    "Ordinal vs Continua" if choice == SPEARMAN_OC
                    else "Ordinal vs Ordinal"
                )
                result = nonparametric.spearman_correlation(
                    df, col_x, col_y, context=context, exact=exact
                )
            elif choice == GROUPS:
                group, value = self.menu_group.get(), self.menu_value.get()
                if group == value:
                    raise ValueError("La nominal y la ordinal deben ser distintas.")
                result = nonparametric.group_comparison(df, group, value, exact=exact)
            else:  # CATEGORICAL
                cat_a, cat_b = self.menu_cat_a.get(), self.menu_cat_b.get()
                if cat_a == cat_b:
                    raise ValueError("Seleccione dos columnas distintas.")
                result = nonparametric.categorical_association(df, cat_a, cat_b)
        except Exception as exc:  # noqa: BLE001
            Toast.show(self.status, f"Error: {exc}", "error")
            return

        self._last_result = result
        self._render_result(result)
        self.btn_save.configure(state="normal")
        msg = "Prueba ejecutada. Revise la previsualizacion."
        if exact and choice in _RANK_TESTS:
            msg = "Prueba ejecutada (con p-valor exacto). Revise la previsualizacion."
        Toast.show(self.status, msg, "success")

    def _render_result(self, result: nonparametric.TestResult) -> None:
        lines = [f"=== {result.title} ===", "", "RESUMEN:"]
        lines += self._frame_to_lines(result.summary)
        if not result.detail.empty:
            lines += ["", "DETALLE:"]
            lines += self._frame_to_lines(result.detail)
        lines += ["", "INTERPRETACION:", result.interpretation]
        if result.simple_conclusion:
            lines += ["", "CONCLUSION SIMPLE:", result.simple_conclusion]

        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", "\n".join(lines))
        self.result_box.configure(state="disabled")

    @staticmethod
    def _frame_to_lines(df) -> list[str]:
        return df.to_string(index=False).splitlines()

    def _save_result(self) -> None:
        if self._last_result is None:
            return
        name = self.filename_entry.get().strip()
        if not name:
            Toast.show(self.status, "Indique un nombre para el archivo.", "error")
            return
        sheets = {"Resumen": self._last_result.summary}
        if not self._last_result.detail.empty:
            sheets["Detalle"] = self._last_result.detail
        sheets["Interpretacion"] = pd.DataFrame(
            {
                "Apartado": ["Interpretacion tecnica", "Conclusion simple"],
                "Texto": [
                    self._last_result.interpretation,
                    self._last_result.simple_conclusion,
                ],
            }
        )
        try:
            path = export_sheets(sheets, name)
        except Exception as exc:  # noqa: BLE001
            Toast.show(self.status, f"No se pudo guardar: {exc}", "error")
            return
        self._reset_after_save()
        Toast.show(self.status, f"Guardado en:\n{path}\nSeleccion reiniciada.", "success")

    def _reset_after_save(self) -> None:
        """Limpia la seleccion y el resultado procesado tras guardar."""
        self._last_result = None
        self.filename_entry.delete(0, "end")
        self.btn_save.configure(state="disabled")
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.configure(state="disabled")
        # Restablece los selectores a su primer valor disponible
        if self.state.has_data:
            df = self.state.dataframe
            all_cols = [str(c) for c in df.columns]
            numeric = get_numeric_columns(df) or all_cols
            self._set_menu(self.menu_x, numeric)
            self._set_menu(self.menu_y, numeric)
            self._set_menu(self.menu_group, all_cols)
            self._set_menu(self.menu_value, numeric or all_cols)
            self._set_menu(self.menu_cat_a, all_cols)
            self._set_menu(self.menu_cat_b, all_cols)
