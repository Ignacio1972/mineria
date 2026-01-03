"""
Exportacion de modelos SQLAlchemy.
"""
from .gis import AreaProtegida, Glaciar, CuerpoAgua, ComunidadIndigena, CentroPoblado
from .proyecto import Proyecto, Analisis, EstadoProyecto, HistorialEstado
from .legal import Documento as DocumentoLegal, Fragmento
from .cliente import Cliente
from .documento import DocumentoProyecto, CategoriaDocumento
from .auditoria import AuditoriaAnalisis
from .corpus import (
    Categoria,
    ArchivoOriginal,
    Tema,
    Coleccion,
    FragmentoTema,
    DocumentoColeccion,
    RelacionDocumento,
    HistorialVersion,
    PlazoProceso,
    ActorSeia,
)
from .asistente import (
    Conversacion,
    Mensaje,
    AccionPendiente,
    MemoriaUsuario,
    DocumentacionSistema,
    TriggerProactivo,
    NotificacionEnviada,
    Feedback,
    RolMensaje,
    EstadoAccion,
    TipoMemoria,
    TipoDocumentacion,
)
from .config_industria import (
    TipoProyecto,
    SubtipoProyecto,
    UmbralSEIA,
    PASPorTipo,
    NormativaPorTipo,
    OAECAPorTipo,
    ImpactoPorTipo,
    AnexoPorTipo,
    ArbolPregunta,
    Obligatoriedad,
    TipoNorma,
    RelevanciaOAECA,
    FaseProyecto,
    FrecuenciaImpacto,
    TipoRespuesta,
    ResultadoUmbral,
)
from .proyecto_extendido import (
    ProyectoUbicacion,
    ProyectoCaracteristica,
    ProyectoPAS,
    ProyectoAnalisisArt11,
    ProyectoDiagnostico,
    ProyectoConversacion,
    ProyectoConversacionMensaje,
    AlcanceTerritorial,
    FuenteDato,
    EstadoPAS,
    EstadoAnalisisArt11,
    ViaSugerida,
    EstadoConversacionProyecto,
    FaseConversacion,
    RolMensajeProyecto,
)

__all__ = [
    # GIS
    "AreaProtegida",
    "Glaciar",
    "CuerpoAgua",
    "ComunidadIndigena",
    "CentroPoblado",
    # Legal/RAG - Documentos y Fragmentos
    "DocumentoLegal",
    "Fragmento",
    # Corpus RAG - Nuevas entidades
    "Categoria",
    "ArchivoOriginal",
    "Tema",
    "Coleccion",
    "FragmentoTema",
    "DocumentoColeccion",
    "RelacionDocumento",
    "HistorialVersion",
    "PlazoProceso",
    "ActorSeia",
    # Clientes
    "Cliente",
    # Proyectos
    "Proyecto",
    "EstadoProyecto",
    "Analisis",
    "HistorialEstado",
    # Documentos de proyecto
    "DocumentoProyecto",
    "CategoriaDocumento",
    # Auditoria
    "AuditoriaAnalisis",
    # Asistente IA
    "Conversacion",
    "Mensaje",
    "AccionPendiente",
    "MemoriaUsuario",
    "DocumentacionSistema",
    "TriggerProactivo",
    "NotificacionEnviada",
    "Feedback",
    "RolMensaje",
    "EstadoAccion",
    "TipoMemoria",
    "TipoDocumentacion",
    # Configuración por industria
    "TipoProyecto",
    "SubtipoProyecto",
    "UmbralSEIA",
    "PASPorTipo",
    "NormativaPorTipo",
    "OAECAPorTipo",
    "ImpactoPorTipo",
    "AnexoPorTipo",
    "ArbolPregunta",
    "Obligatoriedad",
    "TipoNorma",
    "RelevanciaOAECA",
    "FaseProyecto",
    "FrecuenciaImpacto",
    "TipoRespuesta",
    "ResultadoUmbral",
    # Proyecto extendido (ficha acumulativa)
    "ProyectoUbicacion",
    "ProyectoCaracteristica",
    "ProyectoPAS",
    "ProyectoAnalisisArt11",
    "ProyectoDiagnostico",
    "ProyectoConversacion",
    "ProyectoConversacionMensaje",
    "AlcanceTerritorial",
    "FuenteDato",
    "EstadoPAS",
    "EstadoAnalisisArt11",
    "ViaSugerida",
    "EstadoConversacionProyecto",
    "FaseConversacion",
    "RolMensajeProyecto",
]
