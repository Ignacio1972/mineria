"""
Schemas Pydantic para configuración por industria.
Soporta tipos, subtipos, umbrales SEIA, PAS, normativa, OAECA, impactos, anexos y árboles de preguntas.
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class ObligatoriedadEnum(str, Enum):
    """Niveles de obligatoriedad de un PAS."""
    OBLIGATORIO = "obligatorio"
    FRECUENTE = "frecuente"
    CASO_A_CASO = "caso_a_caso"


class TipoNormaEnum(str, Enum):
    """Tipos de normativa ambiental."""
    CALIDAD = "calidad"
    EMISION = "emision"
    SECTORIAL = "sectorial"
    GENERAL = "general"


class RelevanciaOAECAEnum(str, Enum):
    """Relevancia del OAECA para un tipo de proyecto."""
    PRINCIPAL = "principal"
    SECUNDARIO = "secundario"


class FaseProyectoEnum(str, Enum):
    """Fases del proyecto donde aplica un impacto."""
    CONSTRUCCION = "construccion"
    OPERACION = "operacion"
    CIERRE = "cierre"
    TODAS = "todas"


class FrecuenciaImpactoEnum(str, Enum):
    """Frecuencia de ocurrencia de un impacto."""
    MUY_COMUN = "muy_comun"
    FRECUENTE = "frecuente"
    OCASIONAL = "ocasional"


class TipoRespuestaEnum(str, Enum):
    """Tipos de respuesta para preguntas del árbol."""
    TEXTO = "texto"
    NUMERO = "numero"
    OPCION = "opcion"
    ARCHIVO = "archivo"
    UBICACION = "ubicacion"
    BOOLEAN = "boolean"
    FECHA = "fecha"


class ResultadoUmbralEnum(str, Enum):
    """Resultado de la evaluación de umbral SEIA."""
    INGRESA_SEIA = "ingresa_seia"
    NO_INGRESA = "no_ingresa"
    REQUIERE_EIA = "requiere_eia"


# =============================================================================
# Tipos de Proyecto
# =============================================================================

class TipoProyectoBase(BaseModel):
    """Base para tipos de proyecto."""
    codigo: str = Field(..., min_length=2, max_length=50)
    nombre: str = Field(..., min_length=2, max_length=100)
    letra_art3: Optional[str] = Field(None, max_length=5)
    descripcion: Optional[str] = None
    activo: bool = True


class TipoProyectoCreate(TipoProyectoBase):
    """Crear tipo de proyecto."""
    pass


class TipoProyectoUpdate(BaseModel):
    """Actualizar tipo de proyecto."""
    nombre: Optional[str] = None
    letra_art3: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class TipoProyectoResponse(TipoProyectoBase):
    """Respuesta de tipo de proyecto."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TipoProyectoConSubtipos(TipoProyectoResponse):
    """Tipo de proyecto con sus subtipos."""
    subtipos: List["SubtipoProyectoResponse"] = []


# =============================================================================
# Subtipos de Proyecto
# =============================================================================

class SubtipoProyectoBase(BaseModel):
    """Base para subtipos de proyecto."""
    codigo: str = Field(..., min_length=2, max_length=50)
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    activo: bool = True


class SubtipoProyectoCreate(SubtipoProyectoBase):
    """Crear subtipo de proyecto."""
    tipo_proyecto_id: int


class SubtipoProyectoUpdate(BaseModel):
    """Actualizar subtipo de proyecto."""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class SubtipoProyectoResponse(SubtipoProyectoBase):
    """Respuesta de subtipo de proyecto."""
    id: int
    tipo_proyecto_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Umbrales SEIA
# =============================================================================

class UmbralSEIABase(BaseModel):
    """Base para umbrales SEIA."""
    parametro: str = Field(..., min_length=2, max_length=100)
    operador: str = Field(..., pattern=r'^(>=|>|<=|<|=)$')
    valor: Decimal
    unidad: Optional[str] = Field(None, max_length=50)
    resultado: ResultadoUmbralEnum
    descripcion: Optional[str] = None
    norma_referencia: Optional[str] = Field(None, max_length=100)
    activo: bool = True


class UmbralSEIACreate(UmbralSEIABase):
    """Crear umbral SEIA."""
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None


class UmbralSEIAUpdate(BaseModel):
    """Actualizar umbral SEIA."""
    parametro: Optional[str] = None
    operador: Optional[str] = None
    valor: Optional[Decimal] = None
    unidad: Optional[str] = None
    resultado: Optional[ResultadoUmbralEnum] = None
    descripcion: Optional[str] = None
    norma_referencia: Optional[str] = None
    activo: Optional[bool] = None


class UmbralSEIAResponse(UmbralSEIABase):
    """Respuesta de umbral SEIA."""
    id: int
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluarUmbralRequest(BaseModel):
    """Solicitud para evaluar umbral."""
    tipo_proyecto_codigo: str
    subtipo_codigo: Optional[str] = None
    parametros: Dict[str, float] = Field(..., description="Ej: {'tonelaje_mensual': 4500}")


class EvaluarUmbralResponse(BaseModel):
    """Respuesta de evaluación de umbral."""
    cumple_umbral: bool
    resultado: ResultadoUmbralEnum
    umbral_evaluado: Optional[UmbralSEIAResponse] = None
    valor_proyecto: float
    diferencia: float
    mensaje: str


# =============================================================================
# PAS por Tipo
# =============================================================================

class PASPorTipoBase(BaseModel):
    """Base para PAS por tipo."""
    articulo: int = Field(..., ge=100, le=200)
    nombre: str = Field(..., min_length=5, max_length=200)
    organismo: str = Field(..., min_length=2, max_length=100)
    obligatoriedad: ObligatoriedadEnum
    condicion_activacion: Optional[Dict[str, Any]] = None
    descripcion: Optional[str] = None
    activo: bool = True


class PASPorTipoCreate(PASPorTipoBase):
    """Crear PAS por tipo."""
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None


class PASPorTipoUpdate(BaseModel):
    """Actualizar PAS por tipo."""
    nombre: Optional[str] = None
    organismo: Optional[str] = None
    obligatoriedad: Optional[ObligatoriedadEnum] = None
    condicion_activacion: Optional[Dict[str, Any]] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class PASPorTipoResponse(PASPorTipoBase):
    """Respuesta de PAS por tipo."""
    id: int
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PASAplicableResponse(BaseModel):
    """PAS identificado como aplicable a un proyecto."""
    pas: PASPorTipoResponse
    aplica: bool
    razon: str


# =============================================================================
# Normativa por Tipo
# =============================================================================

class NormativaPorTipoBase(BaseModel):
    """Base para normativa por tipo."""
    norma: str = Field(..., min_length=2, max_length=100)
    nombre: str = Field(..., min_length=5, max_length=200)
    componente: Optional[str] = Field(None, max_length=100)
    tipo_norma: Optional[TipoNormaEnum] = None
    aplica_siempre: bool = False
    descripcion: Optional[str] = None
    activo: bool = True


class NormativaPorTipoCreate(NormativaPorTipoBase):
    """Crear normativa por tipo."""
    tipo_proyecto_id: int


class NormativaPorTipoUpdate(BaseModel):
    """Actualizar normativa por tipo."""
    nombre: Optional[str] = None
    componente: Optional[str] = None
    tipo_norma: Optional[TipoNormaEnum] = None
    aplica_siempre: Optional[bool] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class NormativaPorTipoResponse(NormativaPorTipoBase):
    """Respuesta de normativa por tipo."""
    id: int
    tipo_proyecto_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# OAECA por Tipo
# =============================================================================

class OAECAPorTipoBase(BaseModel):
    """Base para OAECA por tipo."""
    organismo: str = Field(..., min_length=2, max_length=100)
    competencias: Optional[List[str]] = None
    relevancia: RelevanciaOAECAEnum
    activo: bool = True


class OAECAPorTipoCreate(OAECAPorTipoBase):
    """Crear OAECA por tipo."""
    tipo_proyecto_id: int


class OAECAPorTipoUpdate(BaseModel):
    """Actualizar OAECA por tipo."""
    competencias: Optional[List[str]] = None
    relevancia: Optional[RelevanciaOAECAEnum] = None
    activo: Optional[bool] = None


class OAECAPorTipoResponse(OAECAPorTipoBase):
    """Respuesta de OAECA por tipo."""
    id: int
    tipo_proyecto_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Impactos por Tipo
# =============================================================================

class ImpactoPorTipoBase(BaseModel):
    """Base para impacto por tipo."""
    componente: str = Field(..., min_length=2, max_length=100)
    impacto: str = Field(..., min_length=5)
    fase: Optional[FaseProyectoEnum] = None
    frecuencia: Optional[FrecuenciaImpactoEnum] = None
    activo: bool = True


class ImpactoPorTipoCreate(ImpactoPorTipoBase):
    """Crear impacto por tipo."""
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None


class ImpactoPorTipoUpdate(BaseModel):
    """Actualizar impacto por tipo."""
    componente: Optional[str] = None
    impacto: Optional[str] = None
    fase: Optional[FaseProyectoEnum] = None
    frecuencia: Optional[FrecuenciaImpactoEnum] = None
    activo: Optional[bool] = None


class ImpactoPorTipoResponse(ImpactoPorTipoBase):
    """Respuesta de impacto por tipo."""
    id: int
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Anexos por Tipo
# =============================================================================

class AnexoPorTipoBase(BaseModel):
    """Base para anexo por tipo."""
    codigo: str = Field(..., min_length=1, max_length=10)
    nombre: str = Field(..., min_length=5, max_length=200)
    profesional_responsable: Optional[str] = Field(None, max_length=100)
    obligatorio: bool = False
    condicion_activacion: Optional[Dict[str, Any]] = None
    descripcion: Optional[str] = None
    activo: bool = True


class AnexoPorTipoCreate(AnexoPorTipoBase):
    """Crear anexo por tipo."""
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None


class AnexoPorTipoUpdate(BaseModel):
    """Actualizar anexo por tipo."""
    nombre: Optional[str] = None
    profesional_responsable: Optional[str] = None
    obligatorio: Optional[bool] = None
    condicion_activacion: Optional[Dict[str, Any]] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class AnexoPorTipoResponse(AnexoPorTipoBase):
    """Respuesta de anexo por tipo."""
    id: int
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Árbol de Preguntas
# =============================================================================

class ArbolPreguntaBase(BaseModel):
    """Base para pregunta del árbol."""
    codigo: str = Field(..., min_length=2, max_length=50)
    pregunta_texto: str = Field(..., min_length=5)
    tipo_respuesta: TipoRespuestaEnum
    opciones: Optional[Any] = None  # Puede ser dict o list
    orden: int = 0
    es_obligatoria: bool = False
    campo_destino: Optional[str] = Field(None, max_length=100)
    categoria_destino: Optional[str] = Field(None, max_length=50)
    condicion_activacion: Optional[Dict[str, Any]] = None
    valida_umbral: bool = False
    ayuda: Optional[str] = None
    activo: bool = True


class ArbolPreguntaCreate(ArbolPreguntaBase):
    """Crear pregunta del árbol."""
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None


class ArbolPreguntaUpdate(BaseModel):
    """Actualizar pregunta del árbol."""
    pregunta_texto: Optional[str] = None
    tipo_respuesta: Optional[TipoRespuestaEnum] = None
    opciones: Optional[Dict[str, Any]] = None
    orden: Optional[int] = None
    es_obligatoria: Optional[bool] = None
    campo_destino: Optional[str] = None
    categoria_destino: Optional[str] = None
    condicion_activacion: Optional[Dict[str, Any]] = None
    valida_umbral: Optional[bool] = None
    ayuda: Optional[str] = None
    activo: Optional[bool] = None


class ArbolPreguntaResponse(ArbolPreguntaBase):
    """Respuesta de pregunta del árbol."""
    id: int
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Configuración Completa por Industria
# =============================================================================

class ConfigIndustriaCompleta(BaseModel):
    """Configuración completa para un tipo/subtipo de proyecto."""
    tipo: TipoProyectoResponse
    subtipo: Optional[SubtipoProyectoResponse] = None
    subtipos_disponibles: List[SubtipoProyectoResponse] = []
    umbrales: List[UmbralSEIAResponse] = []
    pas: List[PASPorTipoResponse] = []
    normativa: List[NormativaPorTipoResponse] = []
    oaeca: List[OAECAPorTipoResponse] = []
    impactos: List[ImpactoPorTipoResponse] = []
    anexos: List[AnexoPorTipoResponse] = []
    preguntas: List[ArbolPreguntaResponse] = []


class ConfigIndustriaResumen(BaseModel):
    """Resumen de configuración de una industria."""
    tipo: TipoProyectoResponse
    num_subtipos: int
    num_umbrales: int
    num_pas: int
    num_normativas: int
    num_preguntas: int


# =============================================================================
# Listados
# =============================================================================

class TiposProyectoListResponse(BaseModel):
    """Lista de tipos de proyecto."""
    tipos: List[TipoProyectoConSubtipos]
    total: int


class PASListResponse(BaseModel):
    """Lista de PAS."""
    pas: List[PASPorTipoResponse]
    total: int


class NormativaListResponse(BaseModel):
    """Lista de normativas."""
    normativas: List[NormativaPorTipoResponse]
    total: int


class PreguntasListResponse(BaseModel):
    """Lista de preguntas del árbol."""
    preguntas: List[ArbolPreguntaResponse]
    total: int


# Actualizar forward references
TipoProyectoConSubtipos.model_rebuild()
