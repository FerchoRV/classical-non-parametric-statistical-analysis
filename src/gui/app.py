"""Ventana principal y navegacion entre vistas."""

from __future__ import annotations

import customtkinter as ctk

from .. import config
from .descriptive_view import DescriptiveView
from .home_view import HomeView
from .nonparametric_view import NonParametricView
from .state import AppState


class AnalisisApp(ctk.CTk):
    """Aplicacion principal del sistema de analisis estadistico."""

    def __init__(self) -> None:
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
    app = AnalisisApp()
    app.mainloop()
