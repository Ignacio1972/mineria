"""
Funciones auxiliares para el servicio de prefactibilidad.

Extraídas de endpoints/prefactibilidad.py para mejor organización.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Optional

from app.db.models.proyecto import Proyecto
from app.services.llm import SeccionInforme

logger = logging.getLogger(__name__)


def construir_datos_proyecto(
    proyecto: Proyecto,
    ubicacion_gis: Optional[dict] = None
) -> dict[str, Any]:
    """
    Construye el diccionario de datos del proyecto para el motor de reglas.

    Args:
        proyecto: Instancia del modelo Proyecto
        ubicacion_gis: Ubicación detectada desde análisis GIS (opcional)

    Returns:
        Diccionario con los datos del proyecto
    """
    ubicacion_gis = ubicacion_gis or {}

    # Usar región/comuna del GIS si está disponible, sino la del proyecto
    region = ubicacion_gis.get("region") or proyecto.region
    comuna = ubicacion_gis.get("comuna") or proyecto.comuna

    return {
        "nombre": proyecto.nombre,
        "tipo_mineria": proyecto.tipo_mineria,
        "mineral_principal": proyecto.mineral_principal,
        "fase": proyecto.fase,
        "titular": proyecto.titular,
        "region": region,
        "comuna": comuna,
        "superficie_ha": float(proyecto.superficie_ha) if proyecto.superficie_ha else None,
        "produccion_estimada": proyecto.produccion_estimada,
        "vida_util_anos": proyecto.vida_util_anos,
        "uso_agua_lps": float(proyecto.uso_agua_lps) if proyecto.uso_agua_lps else None,
        "fuente_agua": proyecto.fuente_agua,
        "energia_mw": float(proyecto.energia_mw) if proyecto.energia_mw else None,
        "trabajadores_construccion": proyecto.trabajadores_construccion,
        "trabajadores_operacion": proyecto.trabajadores_operacion,
        "inversion_musd": float(proyecto.inversion_musd) if proyecto.inversion_musd else None,
        "descripcion": proyecto.descripcion,
        "requiere_reasentamiento": getattr(proyecto, 'requiere_reasentamiento', False),
        "afecta_patrimonio": getattr(proyecto, 'afecta_patrimonio', False),
    }


def calcular_checksum(proyecto: Proyecto) -> str:
    """
    Calcula SHA256 de los datos de entrada para reproducibilidad.

    Args:
        proyecto: Instancia del modelo Proyecto

    Returns:
        Hash SHA256 como string hexadecimal
    """
    datos = {
        "proyecto_id": proyecto.id,
        "nombre": proyecto.nombre,
        "region": proyecto.region,
        "comuna": proyecto.comuna,
        "superficie_ha": float(proyecto.superficie_ha) if proyecto.superficie_ha else None,
        "tipo_mineria": proyecto.tipo_mineria,
        "geom_wkt": proyecto.geom.desc if proyecto.geom else None,
        "timestamp": datetime.now().strftime("%Y-%m-%d"),
    }
    return hashlib.sha256(
        json.dumps(datos, sort_keys=True, default=str).encode()
    ).hexdigest()


def extraer_capas_usadas(resultado_gis: dict) -> list[dict]:
    """
    Extrae lista de capas GIS usadas en el análisis.

    Args:
        resultado_gis: Resultado del análisis espacial

    Returns:
        Lista de diccionarios con información de cada capa
    """
    capas = []
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    capas_map = {
        "areas_protegidas": "SNASPE / Areas Protegidas",
        "glaciares": "Inventario Glaciares DGA",
        "cuerpos_agua": "Cuerpos de Agua / Humedales",
        "comunidades_indigenas": "Comunidades Indigenas / ADI",
        "centros_poblados": "Centros Poblados INE",
        "sitios_patrimoniales": "Sitios Patrimoniales CMN",
    }

    for capa_key, capa_nombre in capas_map.items():
        elementos = resultado_gis.get(capa_key, [])
        if isinstance(elementos, list):
            capas.append({
                "nombre": capa_nombre,
                "fecha": fecha_hoy,
                "version": "v2024.2",
                "elementos_encontrados": len(elementos),
            })

    return capas


def extraer_normativa_citada(triggers: list, normativa_relevante: list) -> list[dict]:
    """
    Extrae normativa citada del análisis.

    Args:
        triggers: Lista de triggers detectados
        normativa_relevante: Lista de normativa encontrada por RAG

    Returns:
        Lista de diccionarios con la normativa citada
    """
    normativa = []

    # De los triggers (Art. 11)
    for trigger in triggers:
        normativa.append({
            "tipo": "Ley",
            "numero": "19300",
            "articulo": "11",
            "letra": trigger.letra.value if hasattr(trigger, 'letra') else str(trigger.get('letra', '')),
            "descripcion": trigger.descripcion if hasattr(trigger, 'descripcion') else trigger.get('descripcion', ''),
        })

    # De la normativa RAG
    for norma in normativa_relevante[:10]:
        if isinstance(norma, dict) and norma.get("documento"):
            normativa.append({
                "tipo": "Referencia",
                "numero": norma.get("documento", ""),
                "articulo": norma.get("seccion", ""),
                "letra": None,
                "descripcion": norma.get("relevancia", ""),
            })

    return normativa


def descripcion_seccion(seccion: SeccionInforme) -> str:
    """
    Retorna descripción de cada sección del informe.

    Args:
        seccion: Enum de la sección

    Returns:
        Descripción textual de la sección
    """
    descripciones = {
        SeccionInforme.RESUMEN_EJECUTIVO: "Síntesis de los hallazgos principales y recomendación",
        SeccionInforme.DESCRIPCION_PROYECTO: "Características técnicas del proyecto minero",
        SeccionInforme.ANALISIS_TERRITORIAL: "Análisis de sensibilidades territoriales identificadas",
        SeccionInforme.EVALUACION_SEIA: "Evaluación de triggers Art. 11 y clasificación DIA/EIA",
        SeccionInforme.NORMATIVA_APLICABLE: "Normativa ambiental aplicable al proyecto",
        SeccionInforme.ALERTAS_AMBIENTALES: "Alertas ambientales por componente",
        SeccionInforme.PERMISOS_REQUERIDOS: "Permisos ambientales sectoriales (PAS) requeridos",
        SeccionInforme.LINEA_BASE_SUGERIDA: "Componentes de línea base ambiental sugeridos",
        SeccionInforme.RECOMENDACIONES: "Recomendaciones técnicas y legales",
        SeccionInforme.CONCLUSION: "Conclusión y próximos pasos",
    }
    return descripciones.get(seccion, "")
