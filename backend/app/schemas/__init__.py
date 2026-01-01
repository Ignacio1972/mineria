"""
Exportacion de schemas Pydantic.
"""
from .cliente import (
    ClienteBase,
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    ClienteListResponse,
)
from .documento import (
    CategoriaDocumento,
    DocumentoBase,
    DocumentoCreate,
    DocumentoResponse,
    DocumentoListResponse,
)
from .proyecto import (
    EstadoProyecto,
    GeometriaGeoJSON,
    ProyectoBase,
    ProyectoCreate,
    ProyectoUpdate,
    ProyectoGeometriaUpdate,
    ProyectoResponse,
    ProyectoConGeometriaResponse,
    ProyectoListResponse,
    FiltrosProyecto,
)
from .auditoria import (
    NormativaCitada,
    CapaGISUsada,
    MetricasEjecucion,
    AuditoriaAnalisisCreate,
    AuditoriaAnalisisResponse,
    AnalisisIntegradoInput,
    AnalisisIntegradoResponse,
)

__all__ = [
    # Cliente
    "ClienteBase",
    "ClienteCreate",
    "ClienteUpdate",
    "ClienteResponse",
    "ClienteListResponse",
    # Documento
    "CategoriaDocumento",
    "DocumentoBase",
    "DocumentoCreate",
    "DocumentoResponse",
    "DocumentoListResponse",
    # Proyecto
    "EstadoProyecto",
    "GeometriaGeoJSON",
    "ProyectoBase",
    "ProyectoCreate",
    "ProyectoUpdate",
    "ProyectoGeometriaUpdate",
    "ProyectoResponse",
    "ProyectoConGeometriaResponse",
    "ProyectoListResponse",
    "FiltrosProyecto",
    # Auditoria
    "NormativaCitada",
    "CapaGISUsada",
    "MetricasEjecucion",
    "AuditoriaAnalisisCreate",
    "AuditoriaAnalisisResponse",
    "AnalisisIntegradoInput",
    "AnalisisIntegradoResponse",
]
