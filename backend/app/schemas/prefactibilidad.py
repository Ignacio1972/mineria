"""
Schemas Pydantic para Análisis de Prefactibilidad Ambiental.

Extraídos de endpoints/prefactibilidad.py para mejor organización.
"""
from typing import Any, Optional
from pydantic import BaseModel, Field


# === Schemas de Input ===

class DatosProyectoInput(BaseModel):
    """Datos del proyecto minero para análisis."""
    nombre: str = Field(..., description="Nombre del proyecto", min_length=3)
    tipo_mineria: Optional[str] = Field(None, description="Tipo de minería (ej: 'Tajo abierto', 'Subterránea')")
    mineral_principal: Optional[str] = Field(None, description="Mineral principal a extraer")
    fase: Optional[str] = Field(None, description="Fase del proyecto (ej: 'Exploración', 'Explotación')")
    titular: Optional[str] = Field(None, description="Nombre del titular del proyecto")
    region: Optional[str] = Field(None, description="Región de ubicación")
    comuna: Optional[str] = Field(None, description="Comuna de ubicación")
    superficie_ha: Optional[float] = Field(None, description="Superficie del proyecto en hectáreas", ge=0)
    produccion_estimada: Optional[str] = Field(None, description="Producción estimada")
    vida_util_anos: Optional[int] = Field(None, description="Vida útil estimada en años", ge=0)
    uso_agua_lps: Optional[float] = Field(None, description="Uso de agua en litros por segundo", ge=0)
    fuente_agua: Optional[str] = Field(None, description="Fuente de agua (ej: 'Subterránea', 'Superficial', 'Mar')")
    energia_mw: Optional[float] = Field(None, description="Energía requerida en MW", ge=0)
    trabajadores_construccion: Optional[int] = Field(None, description="Trabajadores en fase de construcción", ge=0)
    trabajadores_operacion: Optional[int] = Field(None, description="Trabajadores en fase de operación", ge=0)
    inversion_musd: Optional[float] = Field(None, description="Inversión estimada en millones de USD", ge=0)
    descripcion: Optional[str] = Field(None, description="Descripción adicional del proyecto")

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Proyecto Minero Los Andes",
                "tipo_mineria": "Tajo abierto",
                "mineral_principal": "Cobre",
                "fase": "Explotación",
                "titular": "Minera Ejemplo SpA",
                "region": "Antofagasta",
                "comuna": "Calama",
                "superficie_ha": 500,
                "vida_util_anos": 25,
                "uso_agua_lps": 150,
                "fuente_agua": "Subterránea",
                "trabajadores_construccion": 800,
                "trabajadores_operacion": 400,
                "inversion_musd": 2500,
            }
        }


class GeometriaInput(BaseModel):
    """Geometría GeoJSON del proyecto."""
    type: str = Field(..., description="Tipo de geometría (Polygon, MultiPolygon)")
    coordinates: list = Field(..., description="Coordenadas de la geometría")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "Polygon",
                "coordinates": [[
                    [-68.9, -22.5],
                    [-68.8, -22.5],
                    [-68.8, -22.4],
                    [-68.9, -22.4],
                    [-68.9, -22.5]
                ]]
            }
        }


class AnalisisPrefactibilidadInput(BaseModel):
    """Input completo para análisis de prefactibilidad."""
    proyecto: DatosProyectoInput
    geometria: GeometriaInput
    generar_informe_llm: bool = Field(
        True,
        description="Si es True, genera informe con LLM. Si es False, solo análisis automático."
    )
    secciones: Optional[list[str]] = Field(
        None,
        description="Secciones específicas a generar. Si es None, genera todas."
    )


# === Schemas de Response ===

class TriggerResponse(BaseModel):
    """Respuesta de un trigger detectado."""
    letra: str
    descripcion: str
    detalle: str
    severidad: str
    fundamento_legal: str
    peso: float


class AlertaResponse(BaseModel):
    """Respuesta de una alerta detectada."""
    id: str
    nivel: str
    categoria: str
    titulo: str
    descripcion: str
    acciones_requeridas: list[str]


class ClasificacionResponse(BaseModel):
    """Respuesta de clasificación SEIA."""
    via_ingreso_recomendada: str
    confianza: float
    nivel_confianza: str
    justificacion: str
    puntaje_matriz: float


class SeccionInformeResponse(BaseModel):
    """Respuesta de una sección del informe."""
    seccion: str
    titulo: str
    contenido: str


class AnalisisPrefactibilidadResponse(BaseModel):
    """Respuesta completa del análisis de prefactibilidad."""
    id: str
    fecha_analisis: str
    proyecto: dict
    resultado_gis: dict
    clasificacion_seia: ClasificacionResponse
    triggers: list[TriggerResponse]
    alertas: list[AlertaResponse]
    normativa_citada: list[dict]
    informe: Optional[dict] = None
    metricas: dict


class AnalisisRapidoResponse(BaseModel):
    """Respuesta del análisis rápido (sin LLM)."""
    via_ingreso_recomendada: str
    confianza: float
    triggers_detectados: int
    alertas_criticas: int
    alertas_altas: int
    resumen: str


class EliminarAnalisisResponse(BaseModel):
    """Respuesta de eliminación de análisis."""
    mensaje: str
    analisis_id: int
    proyecto_id: int
    era_ultimo_analisis: bool
    nuevo_estado_proyecto: Optional[str] = None
