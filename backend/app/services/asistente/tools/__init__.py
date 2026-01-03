"""
Herramientas del Asistente IA.

Este modulo exporta todas las herramientas disponibles y el registro central.
Las herramientas se registran automaticamente al importar este modulo.
"""
from .base import (
    Herramienta,
    ResultadoHerramienta,
    DefinicionHerramienta,
    CategoriaHerramienta,
    PermisoHerramienta,
    RegistroHerramientas,
    registro_herramientas,
)

# Importar herramientas para que se registren automaticamente
from . import rag
from . import consultas
from . import acciones
from . import externa

# Herramientas RAG
from .rag import (
    BuscarNormativa,
    BuscarDocumentacion,
    ExplicarClasificacion,
)

# Herramientas de consulta
from .consultas import (
    ConsultarProyecto,
    ConsultarAnalisis,
    ListarProyectos,
    ObtenerEstadisticas,
)

# Herramientas de accion (requieren confirmacion)
from .acciones import (
    CrearProyecto,
    EjecutarAnalisis,
    ActualizarProyecto,
    GuardarFicha,
)

# Herramientas externas (APIs de terceros)
from .externa import (
    BuscarWebActualizada,
)

__all__ = [
    # Base
    "Herramienta",
    "ResultadoHerramienta",
    "DefinicionHerramienta",
    "CategoriaHerramienta",
    "PermisoHerramienta",
    "RegistroHerramientas",
    "registro_herramientas",
    # RAG
    "BuscarNormativa",
    "BuscarDocumentacion",
    "ExplicarClasificacion",
    # Consultas
    "ConsultarProyecto",
    "ConsultarAnalisis",
    "ListarProyectos",
    "ObtenerEstadisticas",
    # Acciones
    "CrearProyecto",
    "EjecutarAnalisis",
    "ActualizarProyecto",
    "GuardarFicha",
    # Externas
    "BuscarWebActualizada",
]


def get_tools_count() -> dict:
    """Retorna conteo de herramientas por categoria."""
    from collections import Counter
    definiciones = registro_herramientas.listar()
    return dict(Counter(d.categoria.value for d in definiciones))


def get_all_tools_anthropic() -> list:
    """Retorna todas las herramientas en formato Anthropic."""
    return registro_herramientas.obtener_tools_anthropic()
