from fastapi import APIRouter

from app.api.v1.endpoints import (
    analisis_espacial,
    buscar_normativa,
    ingestor,
    prefactibilidad,
    clientes,
    proyectos,
    documentos,
    dashboard,
    llm,
    # Corpus RAG - Sistema de Gestion Documental
    categorias,
    corpus,
    colecciones,
    temas,
    # Asistente IA
    asistente,
    # Configuración por Industria
    config_industria,
    # Ficha Acumulativa del Proyecto
    ficha,
    # Estructura EIA (Fase 2)
    estructura_eia,
    # Recopilacion Guiada (Fase 3)
    recopilacion,
    # Generacion EIA (Fase 4)
    generacion,
    # Proceso Evaluacion SEIA (Gestor ICSARA/Adendas)
    proceso_evaluacion,
)

api_router = APIRouter()

# Endpoints existentes
api_router.include_router(
    analisis_espacial.router,
    prefix="/gis",
    tags=["GIS - Análisis Espacial"],
)

api_router.include_router(
    buscar_normativa.router,
    prefix="/legal",
    tags=["Legal - Búsqueda Normativa"],
)

api_router.include_router(
    ingestor.router,
    prefix="/ingestor",
    tags=["Ingestor - Carga de Documentos"],
)

api_router.include_router(
    prefactibilidad.router,
    prefix="/prefactibilidad",
    tags=["Prefactibilidad - Análisis Ambiental"],
)

# Nuevos endpoints - CRUD Clientes, Proyectos, Documentos
api_router.include_router(
    clientes.router,
    prefix="/clientes",
    tags=["Clientes"],
)

api_router.include_router(
    proyectos.router,
    prefix="/proyectos",
    tags=["Proyectos"],
)

api_router.include_router(
    documentos.router,
    prefix="/documentos",
    tags=["Documentos"],
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
)

api_router.include_router(
    llm.router,
    prefix="/llm",
    tags=["LLM - Gestión de Modelos"],
)

# ============================================================================
# Corpus RAG - Sistema de Gestion Documental
# ============================================================================

api_router.include_router(
    categorias.router,
    prefix="/categorias",
    tags=["Corpus RAG - Categorías"],
)

api_router.include_router(
    corpus.router,
    prefix="/corpus",
    tags=["Corpus RAG - Documentos"],
)

api_router.include_router(
    colecciones.router,
    prefix="/colecciones",
    tags=["Corpus RAG - Colecciones"],
)

api_router.include_router(
    temas.router,
    prefix="/temas",
    tags=["Corpus RAG - Temas"],
)

# ============================================================================
# Asistente IA - Chat Conversacional con Tool Use
# ============================================================================

api_router.include_router(
    asistente.router,
    prefix="/asistente",
    tags=["Asistente IA"],
)

# ============================================================================
# Configuración por Industria - Multi-industria
# ============================================================================

api_router.include_router(
    config_industria.router,
    prefix="/config",
    tags=["Configuración por Industria"],
)

# ============================================================================
# Ficha Acumulativa del Proyecto
# ============================================================================

api_router.include_router(
    ficha.router,
    prefix="/ficha",
    tags=["Ficha Acumulativa"],
)

# ============================================================================
# Estructura EIA (Fase 2)
# ============================================================================

api_router.include_router(
    estructura_eia.router,
    prefix="/estructura-eia",
    tags=["Estructura EIA"],
)

# ============================================================================
# Recopilacion Guiada (Fase 3)
# ============================================================================

api_router.include_router(
    recopilacion.router,
    prefix="/recopilacion",
    tags=["Recopilacion Guiada"],
)

# ============================================================================
# Generacion EIA (Fase 4)
# ============================================================================

api_router.include_router(
    generacion.router,
    prefix="/generacion",
    tags=["Generacion EIA"],
)

# ============================================================================
# Proceso Evaluacion SEIA (Gestor ICSARA/Adendas)
# ============================================================================

api_router.include_router(
    proceso_evaluacion.router,
    prefix="/proceso-evaluacion",
    tags=["Proceso Evaluacion SEIA"],
)
