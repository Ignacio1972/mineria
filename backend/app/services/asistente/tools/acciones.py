"""
Herramientas de acciones del asistente.
Operaciones que modifican datos y requieren confirmacion del usuario.

NOTA: Este archivo re-exporta desde el modulo acciones/ para compatibilidad.
Las implementaciones estan en:
- acciones/crear_proyecto.py
- acciones/ejecutar_analisis.py
- acciones/actualizar_proyecto.py
- acciones/guardar_ficha.py
"""
from .acciones import (
    # Constantes
    REGIONES_CHILE,
    TIPOS_MINERIA,
    FASES_PROYECTO,
    CATEGORIAS_FICHA,
    # Herramientas
    CrearProyecto,
    EjecutarAnalisis,
    ActualizarProyecto,
    GuardarFicha,
)

__all__ = [
    "REGIONES_CHILE",
    "TIPOS_MINERIA",
    "FASES_PROYECTO",
    "CATEGORIAS_FICHA",
    "CrearProyecto",
    "EjecutarAnalisis",
    "ActualizarProyecto",
    "GuardarFicha",
]
