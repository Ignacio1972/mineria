"""
Schemas Pydantic para Documento y Documentación Requerida SEA.
"""
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class CategoriaDocumento(str, Enum):
    """Categorias de documentos (legacy)."""
    LEGAL = "legal"
    TECNICO = "tecnico"
    AMBIENTAL = "ambiental"
    CARTOGRAFIA = "cartografia"
    OTRO = "otro"


class CategoriaDocumentoSEA(str, Enum):
    """Categorías de documentos según requerimientos SEA."""
    # Documentos geográficos/cartográficos
    CARTOGRAFIA_PLANOS = "cartografia_planos"

    # Documentos de personal
    TITULO_PROFESIONAL = "titulo_profesional"
    CERTIFICADO_CONSULTORA = "certificado_consultora"
    CERTIFICADO_LABORATORIO = "certificado_laboratorio"

    # Estudios técnicos especializados
    ESTUDIO_AIRE = "estudio_aire"
    ESTUDIO_AGUA = "estudio_agua"
    ESTUDIO_SUELO = "estudio_suelo"
    ESTUDIO_FLORA = "estudio_flora"
    ESTUDIO_FAUNA = "estudio_fauna"
    ESTUDIO_SOCIAL = "estudio_social"
    ESTUDIO_ARQUEOLOGICO = "estudio_arqueologico"
    ESTUDIO_RUIDO = "estudio_ruido"
    ESTUDIO_VIBRACIONES = "estudio_vibraciones"
    ESTUDIO_PAISAJE = "estudio_paisaje"
    ESTUDIO_HIDROGEOLOGICO = "estudio_hidrogeologico"

    # Documentos legales y permisos
    RESOLUCION_SANITARIA = "resolucion_sanitaria"
    ANTECEDENTE_PAS = "antecedente_pas"
    CERTIFICADO_PERTENENCIA = "certificado_pertenencia"
    CONTRATO_SERVIDUMBRE = "contrato_servidumbre"

    # Participación ciudadana
    ACTA_PARTICIPACION = "acta_participacion"
    COMPROMISO_VOLUNTARIO = "compromiso_voluntario"
    CONSULTA_INDIGENA = "consulta_indigena"

    # Evaluaciones de riesgo
    EVALUACION_RIESGO = "evaluacion_riesgo"
    PLAN_EMERGENCIA = "plan_emergencia"
    PLAN_CIERRE = "plan_cierre"

    # Otros documentos técnicos
    MEMORIA_TECNICA = "memoria_tecnica"
    CRONOGRAMA = "cronograma"
    PRESUPUESTO_AMBIENTAL = "presupuesto_ambiental"
    OTRO = "otro"


class EstadoValidacion(str, Enum):
    """Estados de validación de documentos."""
    PENDIENTE = "pendiente"
    SUBIDO = "subido"
    VALIDANDO = "validando"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    NO_APLICA = "no_aplica"


# =============================================================================
# Schemas de Documento
# =============================================================================

class DocumentoBase(BaseModel):
    """Campos base del documento."""
    nombre: str = Field(..., min_length=1, max_length=255)
    categoria: CategoriaDocumento = CategoriaDocumento.OTRO
    categoria_sea: Optional[CategoriaDocumentoSEA] = CategoriaDocumentoSEA.OTRO
    descripcion: Optional[str] = None
    profesional_responsable: Optional[str] = Field(None, max_length=200)
    fecha_documento: Optional[date] = None
    fecha_vigencia: Optional[date] = None


class DocumentoCreate(DocumentoBase):
    """Schema para crear documento (el archivo se envia como form-data)."""
    pass


class ValidacionFormato(BaseModel):
    """Resultado de validación de formato."""
    valido: bool = False
    errores: List[str] = []
    warnings: List[str] = []
    crs: Optional[str] = None
    geometria_tipo: Optional[str] = None
    num_features: Optional[int] = None


class DocumentoResponse(DocumentoBase):
    """Schema de respuesta del documento."""
    id: UUID
    proyecto_id: int
    nombre_original: str
    archivo_path: str
    mime_type: str
    tamano_bytes: int
    tamano_mb: float = 0.0
    checksum_sha256: Optional[str] = None
    num_paginas: Optional[int] = None
    validacion_formato: Optional[Dict[str, Any]] = None
    esta_vigente: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentoListResponse(BaseModel):
    """Lista de documentos."""
    items: List[DocumentoResponse]
    total: int
    total_bytes: int
    total_mb: float


# =============================================================================
# Schemas de Requerimientos de Documentos
# =============================================================================

class RequerimientoDocumentoBase(BaseModel):
    """Campos base de requerimiento de documento."""
    categoria_sea: CategoriaDocumentoSEA
    nombre_display: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    notas_sea: Optional[str] = None
    es_obligatorio: bool = False
    obligatorio_para_dia: bool = False
    obligatorio_para_eia: bool = False
    seccion_eia: Optional[str] = None
    orden: int = 100


class RequerimientoDocumentoResponse(RequerimientoDocumentoBase):
    """Respuesta de requerimiento de documento."""
    id: int
    tipo_proyecto_id: Optional[int] = None
    subtipo_proyecto_id: Optional[int] = None
    formatos_permitidos: List[str] = ["application/pdf"]
    tamano_max_mb: int = 50
    requiere_firma_digital: bool = False
    requiere_profesional_responsable: bool = False
    requiere_crs_wgs84: bool = False
    formatos_gis_permitidos: List[str] = ["shp", "geojson", "kml", "gml"]
    activo: bool = True

    class Config:
        from_attributes = True


class DocumentoRequeridoEstado(BaseModel):
    """Estado de un documento requerido para un proyecto."""
    requerimiento_id: int
    categoria_sea: CategoriaDocumentoSEA
    nombre_display: str
    descripcion: Optional[str] = None
    notas_sea: Optional[str] = None
    es_obligatorio: bool
    obligatorio_segun_via: bool  # Considera DIA vs EIA
    seccion_eia: Optional[str] = None
    orden: int

    # Estado actual
    documento_id: Optional[UUID] = None
    documento_nombre: Optional[str] = None
    estado_cumplimiento: EstadoValidacion = EstadoValidacion.PENDIENTE

    # Validaciones requeridas
    formatos_permitidos: List[str] = []
    requiere_crs_wgs84: bool = False

    class Config:
        from_attributes = True


class DocumentosRequeridosResponse(BaseModel):
    """Lista de documentos requeridos con su estado."""
    proyecto_id: int
    via_evaluacion: str = "EIA"  # DIA o EIA
    items: List[DocumentoRequeridoEstado]
    total_requeridos: int
    total_obligatorios: int
    total_subidos: int


# =============================================================================
# Schemas de Validación de Completitud
# =============================================================================

class ValidacionCompletitudResponse(BaseModel):
    """Resultado de validación de completitud de documentación."""
    proyecto_id: int
    es_completo: bool
    total_requeridos: int
    total_obligatorios: int
    total_subidos: int
    porcentaje_completitud: float

    # Documentos faltantes
    obligatorios_faltantes: List[str] = []
    opcionales_faltantes: List[str] = []

    # Alertas y recomendaciones
    alertas: List[str] = []
    puede_continuar: bool = False  # True si obligatorios están completos

    class Config:
        from_attributes = True


class DocumentoValidacionResponse(BaseModel):
    """Estado de validación de un documento específico."""
    id: int
    proyecto_id: int
    categoria_sea: CategoriaDocumentoSEA
    estado: EstadoValidacion
    documento_id: Optional[UUID] = None

    validacion_formato: Optional[bool] = None
    validacion_contenido: Optional[bool] = None
    validacion_firma: Optional[bool] = None

    observaciones: Optional[str] = None
    observaciones_sea: Optional[str] = None

    validado_por: Optional[str] = None
    validado_fecha: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Schemas para validación de cartografía
# =============================================================================

class ValidacionCartografiaRequest(BaseModel):
    """Request para validar archivo de cartografía."""
    documento_id: UUID


class ValidacionCartografiaResponse(BaseModel):
    """Resultado de validación de cartografía."""
    documento_id: UUID
    valido: bool
    crs_detectado: Optional[str] = None
    crs_es_wgs84: bool = False
    tipo_geometria: Optional[str] = None  # Point, Polygon, MultiPolygon, etc.
    num_features: int = 0
    bbox: Optional[List[float]] = None  # [minx, miny, maxx, maxy]
    area_total_ha: Optional[float] = None

    errores: List[str] = []
    warnings: List[str] = []


# =============================================================================
# Nombres legibles de categorías SEA
# =============================================================================

CATEGORIA_SEA_NOMBRES: Dict[str, str] = {
    "cartografia_planos": "Cartografía y Planos",
    "titulo_profesional": "Títulos Profesionales",
    "certificado_consultora": "Certificados de Consultoras",
    "certificado_laboratorio": "Certificados de Laboratorios",
    "estudio_aire": "Estudio de Calidad del Aire",
    "estudio_agua": "Estudio de Recursos Hídricos",
    "estudio_suelo": "Estudio de Suelos",
    "estudio_flora": "Estudio de Flora y Vegetación",
    "estudio_fauna": "Estudio de Fauna",
    "estudio_social": "Línea Base Social",
    "estudio_arqueologico": "Estudio Arqueológico",
    "estudio_ruido": "Estudio de Ruido",
    "estudio_vibraciones": "Estudio de Vibraciones",
    "estudio_paisaje": "Estudio de Paisaje",
    "estudio_hidrogeologico": "Estudio Hidrogeológico",
    "resolucion_sanitaria": "Resoluciones Sanitarias",
    "antecedente_pas": "Antecedentes de PAS",
    "certificado_pertenencia": "Certificados de Pertenencia",
    "contrato_servidumbre": "Contratos de Servidumbre",
    "acta_participacion": "Actas de Participación",
    "compromiso_voluntario": "Compromisos Voluntarios",
    "consulta_indigena": "Documentación Consulta Indígena",
    "evaluacion_riesgo": "Evaluaciones de Riesgo",
    "plan_emergencia": "Plan de Emergencia",
    "plan_cierre": "Plan de Cierre",
    "memoria_tecnica": "Memoria Técnica",
    "cronograma": "Cronograma",
    "presupuesto_ambiental": "Presupuesto Ambiental",
    "otro": "Otro Documento",
}


def get_nombre_categoria_sea(categoria: str) -> str:
    """Obtiene el nombre legible de una categoría SEA."""
    return CATEGORIA_SEA_NOMBRES.get(categoria, categoria)
