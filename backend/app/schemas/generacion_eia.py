"""
Schemas Pydantic para Generación de EIA (Fase 4).
Define tipos para compilación, generación, validación y exportación de documentos EIA.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class EstadoDocumentoEnum(str, Enum):
    """Estados posibles de un documento EIA."""
    BORRADOR = "borrador"
    EN_REVISION = "en_revision"
    VALIDADO = "validado"
    FINAL = "final"


class FormatoExportacionEnum(str, Enum):
    """Formatos de exportación disponibles."""
    PDF = "pdf"
    DOCX = "docx"
    ESEIA_XML = "eseia_xml"


class TipoValidacionEnum(str, Enum):
    """Tipos de validación SEA."""
    CONTENIDO = "contenido"
    FORMATO = "formato"
    REFERENCIA = "referencia"
    COMPLETITUD = "completitud"
    NORMATIVA = "normativa"


class SeveridadEnum(str, Enum):
    """Niveles de severidad de observaciones."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EstadoObservacionEnum(str, Enum):
    """Estados de observaciones de validación."""
    PENDIENTE = "pendiente"
    CORREGIDA = "corregida"
    IGNORADA = "ignorada"


# =============================================================================
# Documento EIA
# =============================================================================

class ContenidoCapitulo(BaseModel):
    """Contenido de un capítulo individual."""
    numero: int = Field(..., ge=1, le=11)
    titulo: str
    contenido: str
    subsecciones: Dict[str, Any] = Field(default_factory=dict)
    figuras: List[str] = Field(default_factory=list)
    tablas: List[str] = Field(default_factory=list)
    referencias: List[str] = Field(default_factory=list)


class MetadatosDocumento(BaseModel):
    """Metadatos del documento EIA."""
    fecha_elaboracion: Optional[datetime] = None
    empresa_consultora: Optional[str] = None
    autores: List[str] = Field(default_factory=list)
    revisores: List[str] = Field(default_factory=list)
    version_doc: Optional[str] = None
    resumen_ejecutivo: Optional[str] = None


class EstadisticasDocumento(BaseModel):
    """Estadísticas del documento."""
    total_paginas: int = 0
    total_palabras: int = 0
    total_figuras: int = 0
    total_tablas: int = 0
    total_referencias: int = 0
    capitulos_completados: int = 0
    porcentaje_completitud: float = 0.0


class DocumentoEIABase(BaseModel):
    """Base para documento EIA."""
    proyecto_id: int
    titulo: str = Field(..., min_length=10, max_length=500)
    estado: EstadoDocumentoEnum = EstadoDocumentoEnum.BORRADOR


class DocumentoEIACreate(DocumentoEIABase):
    """Schema para crear documento EIA."""
    metadatos: Optional[MetadatosDocumento] = None


class DocumentoEIAUpdate(BaseModel):
    """Schema para actualizar documento EIA."""
    titulo: Optional[str] = Field(None, min_length=10, max_length=500)
    estado: Optional[EstadoDocumentoEnum] = None
    contenido_capitulos: Optional[Dict[str, ContenidoCapitulo]] = None
    metadatos: Optional[MetadatosDocumento] = None


class DocumentoEIAResponse(DocumentoEIABase):
    """Respuesta de documento EIA."""
    id: int
    version: int
    contenido_capitulos: Optional[Dict[str, Any]] = None
    metadatos: Optional[Dict[str, Any]] = None
    validaciones: Optional[Dict[str, Any]] = None
    estadisticas: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Versiones
# =============================================================================

class VersionEIACreate(BaseModel):
    """Schema para crear versión."""
    cambios: str = Field(..., min_length=10)
    creado_por: Optional[str] = None


class VersionEIAResponse(BaseModel):
    """Respuesta de versión EIA."""
    id: int
    documento_id: int
    version: int
    cambios: str
    creado_por: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Generación
# =============================================================================

class GenerarCapituloRequest(BaseModel):
    """Request para generar un capítulo específico."""
    capitulo_numero: int = Field(..., ge=1, le=11)
    regenerar: bool = False
    instrucciones_adicionales: Optional[str] = None


class RegenerarSeccionRequest(BaseModel):
    """Request para regenerar una sección específica."""
    capitulo_numero: int = Field(..., ge=1, le=11)
    seccion_codigo: str
    instrucciones: str = Field(..., min_length=10)


class CompilarDocumentoRequest(BaseModel):
    """Request para compilar documento completo."""
    incluir_capitulos: Optional[List[int]] = None  # Si es None, incluye todos
    regenerar_existentes: bool = False


class ProgresoGeneracion(BaseModel):
    """Progreso de generación por capítulo."""
    capitulo_numero: int
    titulo: str
    estado: str  # pendiente, generando, completado, error
    progreso_porcentaje: int = 0
    palabras_generadas: int = 0
    tiempo_estimado_segundos: Optional[int] = None
    error: Optional[str] = None


class GeneracionResponse(BaseModel):
    """Respuesta de proceso de generación."""
    documento_id: int
    capitulos_generados: List[int]
    capitulos_con_error: List[int]
    tiempo_total_segundos: float
    estadisticas: EstadisticasDocumento


# =============================================================================
# Validación
# =============================================================================

class ReglaValidacionSEABase(BaseModel):
    """Base para regla de validación."""
    codigo_regla: str = Field(..., min_length=3, max_length=50)
    descripcion: str
    tipo_validacion: TipoValidacionEnum
    criterio: Dict[str, Any]
    mensaje_error: str
    mensaje_sugerencia: Optional[str] = None
    severidad: SeveridadEnum = SeveridadEnum.WARNING


class ReglaValidacionSEACreate(ReglaValidacionSEABase):
    """Schema para crear regla de validación."""
    tipo_proyecto_id: Optional[int] = None
    capitulo_numero: Optional[int] = None


class ReglaValidacionSEAResponse(ReglaValidacionSEABase):
    """Respuesta de regla de validación."""
    id: int
    tipo_proyecto_id: Optional[int]
    capitulo_numero: Optional[int]
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ObservacionValidacionBase(BaseModel):
    """Base para observación de validación."""
    tipo_observacion: str
    severidad: SeveridadEnum
    mensaje: str
    sugerencia: Optional[str] = None


class ObservacionValidacionCreate(ObservacionValidacionBase):
    """Schema para crear observación."""
    documento_id: int
    regla_id: Optional[int] = None
    capitulo_numero: Optional[int] = None
    seccion: Optional[str] = None
    contexto: Optional[Dict[str, Any]] = None


class ObservacionValidacionResponse(ObservacionValidacionBase):
    """Respuesta de observación."""
    id: int
    documento_id: int
    regla_id: Optional[int]
    capitulo_numero: Optional[int]
    seccion: Optional[str]
    contexto: Optional[Dict[str, Any]]
    estado: EstadoObservacionEnum
    created_at: datetime
    resuelta_at: Optional[datetime]

    class Config:
        from_attributes = True


class ValidacionRequest(BaseModel):
    """Request para validar documento."""
    incluir_capitulos: Optional[List[int]] = None
    nivel_severidad_minima: SeveridadEnum = SeveridadEnum.INFO


class ResultadoValidacion(BaseModel):
    """Resultado de validación de documento."""
    documento_id: int
    total_observaciones: int
    observaciones_por_severidad: Dict[str, int]
    observaciones_por_capitulo: Dict[int, int]
    observaciones: List[ObservacionValidacionResponse]
    es_valido: bool
    mensaje_resumen: str


# =============================================================================
# Exportación
# =============================================================================

class ConfiguracionPDF(BaseModel):
    """Configuración para exportación PDF."""
    incluir_portada: bool = True
    incluir_indice: bool = True
    incluir_figuras: bool = True
    incluir_tablas: bool = True
    tamano_pagina: str = "A4"
    orientacion: str = "portrait"  # portrait, landscape
    margen_cm: float = 2.5
    fuente: str = "Arial"
    tamano_fuente: int = 11
    logo_empresa: Optional[str] = None


class ConfiguracionDOCX(BaseModel):
    """Configuración para exportación DOCX."""
    incluir_portada: bool = True
    incluir_indice: bool = True
    incluir_figuras: bool = True
    incluir_tablas: bool = True
    estilo_documento: str = "SEA_Estandar"
    logo_empresa: Optional[str] = None


class ConfiguracionESEIA(BaseModel):
    """Configuración para exportación e-SEIA XML."""
    incluir_anexos_digitales: bool = True
    version_esquema: str = "2.0"


class ExportacionRequest(BaseModel):
    """Request para exportar documento."""
    formato: FormatoExportacionEnum
    configuracion: Optional[Dict[str, Any]] = None


class ExportacionResponse(BaseModel):
    """Respuesta de exportación."""
    id: int
    documento_id: int
    formato: FormatoExportacionEnum
    archivo_path: Optional[str]
    tamano_bytes: Optional[int]
    generado_exitoso: bool
    error_mensaje: Optional[str]
    created_at: datetime
    url_descarga: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Templates
# =============================================================================

class TemplateCapituloBase(BaseModel):
    """Base para template de capítulo."""
    capitulo_numero: int = Field(..., ge=1, le=11)
    titulo: str = Field(..., min_length=5, max_length=200)
    template_prompt: str = Field(..., min_length=50)
    instrucciones_generacion: Optional[str] = None


class TemplateCapituloCreate(TemplateCapituloBase):
    """Schema para crear template."""
    tipo_proyecto_id: int
    estructura_esperada: Optional[Dict[str, Any]] = None
    ejemplos: Optional[str] = None


class TemplateCapituloResponse(TemplateCapituloBase):
    """Respuesta de template."""
    id: int
    tipo_proyecto_id: int
    estructura_esperada: Optional[Dict[str, Any]]
    ejemplos: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Respuestas Compuestas
# =============================================================================

class DocumentoCompletoResponse(BaseModel):
    """Respuesta completa de documento con todas sus relaciones."""
    documento: DocumentoEIAResponse
    versiones: List[VersionEIAResponse]
    exportaciones: List[ExportacionResponse]
    observaciones_pendientes: List[ObservacionValidacionResponse]
    estadisticas: EstadisticasDocumento
    progreso_capitulos: List[ProgresoGeneracion]
