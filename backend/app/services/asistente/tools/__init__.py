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
    ContextoHerramienta,
    PermisoHerramienta,
    RegistroHerramientas,
    registro_herramientas,
)

# Importar herramientas para que se registren automaticamente
from . import rag
from . import consultas
from . import acciones
from . import externa
from . import config_industria
from . import estructura_eia
from . import recopilacion
from . import generacion_eia
from . import proceso_evaluacion

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

# Herramientas de configuracion por industria
from .config_industria import (
    ObtenerConfigIndustria,
    EvaluarUmbralSEIA,
    ObtenerSiguientePregunta,
)

# Herramientas de Estructura EIA (Fase 2)
from .estructura_eia import (
    GenerarEstructuraEIA,
    ConsultarCapitulosEIA,
    ConsultarPlanLineaBase,
    EstimarComplejidadProyecto,
)

# Herramientas de Recopilacion Guiada (Fase 3)
from .recopilacion import (
    IniciarRecopilacionCapitulo,
    GuardarContenidoSeccion,
    ConsultarProgresoCapitulo,
    ExtraerDatosDocumento,
    ValidarConsistenciaEIA,
    SugerirRedaccion,
    VincularDocumentoSeccion,
)

# Herramientas de Generacion EIA (Fase 4)
from .generacion_eia import (
    CompilarDocumentoEIA,
    GenerarCapituloEIA,
    RegenerarSeccionEIA,
    CrearVersionDocumento,
    ExportarDocumentoEIA,
    ConsultarEstadoDocumento,
    ConsultarValidacionesSEA,
    ConsultarProgresoGeneracion,
    ConsultarVersionesDocumento,
)

# Herramientas de Proceso de Evaluacion SEIA (ICSARA/Adendas)
from .proceso_evaluacion import (
    ConsultarProcesoEvaluacion,
    ConsultarEstadisticasICSARA,
    IniciarProcesoEvaluacion,
    RegistrarICSARA,
    RegistrarAdenda,
    ActualizarEstadoObservacion,
    RegistrarRCA,
    ListarOAECAS,
)

__all__ = [
    # Base
    "Herramienta",
    "ResultadoHerramienta",
    "DefinicionHerramienta",
    "CategoriaHerramienta",
    "ContextoHerramienta",
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
    # Config Industria
    "ObtenerConfigIndustria",
    "EvaluarUmbralSEIA",
    "ObtenerSiguientePregunta",
    # Estructura EIA (Fase 2)
    "GenerarEstructuraEIA",
    "ConsultarCapitulosEIA",
    "ConsultarPlanLineaBase",
    "EstimarComplejidadProyecto",
    # Recopilacion Guiada (Fase 3)
    "IniciarRecopilacionCapitulo",
    "GuardarContenidoSeccion",
    "ConsultarProgresoCapitulo",
    "ExtraerDatosDocumento",
    "ValidarConsistenciaEIA",
    "SugerirRedaccion",
    "VincularDocumentoSeccion",
    # Generacion EIA (Fase 4)
    "CompilarDocumentoEIA",
    "GenerarCapituloEIA",
    "RegenerarSeccionEIA",
    "CrearVersionDocumento",
    "ExportarDocumentoEIA",
    "ConsultarEstadoDocumento",
    "ConsultarValidacionesSEA",
    "ConsultarProgresoGeneracion",
    "ConsultarVersionesDocumento",
    # Proceso Evaluacion SEIA (ICSARA/Adendas)
    "ConsultarProcesoEvaluacion",
    "ConsultarEstadisticasICSARA",
    "IniciarProcesoEvaluacion",
    "RegistrarICSARA",
    "RegistrarAdenda",
    "ActualizarEstadoObservacion",
    "RegistrarRCA",
    "ListarOAECAS",
]


def get_tools_count() -> dict:
    """Retorna conteo de herramientas por categoria."""
    from collections import Counter
    definiciones = registro_herramientas.listar()
    return dict(Counter(d.categoria.value for d in definiciones))


def get_all_tools_anthropic() -> list:
    """Retorna todas las herramientas en formato Anthropic."""
    return registro_herramientas.obtener_tools_anthropic()
