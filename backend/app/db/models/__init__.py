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
]
