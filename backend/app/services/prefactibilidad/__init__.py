"""
Servicio de Prefactibilidad Ambiental.

Módulo que encapsula la lógica de análisis de prefactibilidad,
separando la lógica de negocio de los endpoints HTTP.
"""

from app.services.prefactibilidad.service import ServicioPrefactibilidad
from app.services.prefactibilidad.helpers import (
    construir_datos_proyecto,
    calcular_checksum,
    extraer_capas_usadas,
    extraer_normativa_citada,
    descripcion_seccion,
)

__all__ = [
    "ServicioPrefactibilidad",
    "construir_datos_proyecto",
    "calcular_checksum",
    "extraer_capas_usadas",
    "extraer_normativa_citada",
    "descripcion_seccion",
]
