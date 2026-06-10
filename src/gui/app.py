"""Ventana principal y navegacion entre vistas."""

from __future__ import annotations

import customtkinter as ctk

from .. import config
from .descriptive_view import DescriptiveView
from .home_view import HomeView
from .nonparametric_view import NonParametricView
from .state import AppState


def _install_customtkinter_draw_guard() -> None:
    """Evita una excepcion espuria de customtkinter al cerrar/redibujar.

    En Windows puede quedar un evento Tk de redimensionado pendiente justo
    despues de que customtkinter libera el canvas interno de un CTkFrame. En
    ese caso, CTkFrame._draw intenta llamar ``self._canvas.winfo_exists()``
    cuando ``_canvas`` ya es None y Tk imprime:
    ``AttributeError: 'NoneType' object has no attribute 'winfo_exists'``.

    La guarda no cambia el comportamiento visual; solo ignora ese redibujado
    tardio cuando el widget ya esta en proceso de destruccion.
    """
    if getattr(ctk.CTkFrame, "_descriptivo y pruebas no paramétricas_draw_guard_installed", False):
        return

    original_draw = ctk.CTkFrame._draw

    def safe_draw(self, *args, **kwargs):
        if getattr(self, "_canvas", None) is None:
            return None
        return original_draw(self, *args, **kwargs)

    ctk.CTkFrame._draw = safe_draw
    ctk.CTkFrame._descriptivo_pruebas_no_parametricas_draw_guard_installed = True


class descriptivo_pruebas_no_parametricasApp(ctk.CTk):
    """Aplicacion principal del sistema de analisis descriptivo y pruebas no paramétricas."""

    def __init__(self) -> None:
        _install_customtkinter_draw_guard()
        super().__init__()
        ctk.set_appearance_mode(config.APPEARANCE_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)

        self.title(config.APP_NAME)
        self.geometry("1200x760")
        self.minsize(1000, 640)
        self.configure(fg_color=config.COLOR_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.state_data = AppState()

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.views: dict[str, ctk.CTkFrame] = {
            "home": HomeView(self.container, self.state_data, self.show),
            "nonparametric": NonParametricView(self.container, self.state_data, self.show),
            "descriptive": DescriptiveView(self.container, self.state_data, self.show),
        }
        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

        self.show("home")

    def show(self, name: str) -> None:
        """Muestra la vista indicada y refresca su contenido."""
        view = self.views[name]
        if hasattr(view, "refresh"):
            view.refresh()
        view.tkraise()

    def _on_close(self) -> None:
        """Cierre ordenado para evitar callbacks pendientes de Tk."""
        try:
            self.quit()
        finally:
            self.after_idle(self.destroy)


def run() -> None:
    """Punto de entrada para lanzar la aplicacion grafica."""
    app = descriptivo_pruebas_no_parametricasApp()
    app.mainloop()
