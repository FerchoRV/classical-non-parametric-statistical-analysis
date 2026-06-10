"""Configuracion global: rutas, constantes y parametros de la aplicacion."""

from __future__ import annotations

from pathlib import Path

# Raiz del proyecto (carpeta que contiene main.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Carpetas de salida solicitadas por el usuario
RESULTS_DIR = BASE_DIR / "results"
GRAPHICS_DIR = BASE_DIR / "graphics"

# Crear las carpetas si no existen
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
GRAPHICS_DIR.mkdir(parents=True, exist_ok=True)

# Nivel de significancia estadistica por defecto
ALPHA = 0.05

# Extensiones de archivo soportadas para la carga de datos
SUPPORTED_EXTENSIONS = (".xlsx", ".xls", ".csv", ".txt", ".json")

# Apariencia de la interfaz
APP_NAME = "Analisis Estadistico"
APPEARANCE_MODE = "dark"          # "dark", "light" o "system"
COLOR_THEME = "blue"              # "blue", "green", "dark-blue"

# Paleta de colores personalizada
COLOR_PRIMARY = "#2563eb"
COLOR_PRIMARY_HOVER = "#1d4ed8"
COLOR_SECONDARY = "#0ea5e9"
COLOR_SUCCESS = "#16a34a"
COLOR_SUCCESS_HOVER = "#15803d"
COLOR_DANGER = "#dc2626"
COLOR_SURFACE = "#1e293b"
COLOR_BG = "#0f172a"
