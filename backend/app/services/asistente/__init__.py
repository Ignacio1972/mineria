"""
Servicio de Asistente IA.

Este modulo proporciona el servicio principal del asistente conversacional
con soporte para tool use, memoria y confirmacion de acciones.
"""
from .service import (
    AsistenteService,
    get_asistente_service,
    GestorContexto,
    GestorMemoria,
    EjecutorHerramientas,
    SanitizadorEntrada,
)
from .tools import (
    Herramienta,
    ResultadoHerramienta,
    DefinicionHerramienta,
    CategoriaHerramienta,
    PermisoHerramienta,
    RegistroHerramientas,
    registro_herramientas,
    get_all_tools_anthropic,
    get_tools_count,
)

__all__ = [
    # Servicio principal
    "AsistenteService",
    "get_asistente_service",
    # Gestores
    "GestorContexto",
    "GestorMemoria",
    "EjecutorHerramientas",
    # Utilidades
    "SanitizadorEntrada",
    # Herramientas
    "Herramienta",
    "ResultadoHerramienta",
    "DefinicionHerramienta",
    "CategoriaHerramienta",
    "PermisoHerramienta",
    "RegistroHerramientas",
    "registro_herramientas",
    "get_all_tools_anthropic",
    "get_tools_count",
]
