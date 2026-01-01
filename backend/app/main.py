import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.services.startup import inicializar_aplicacion

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    # Startup
    logger.info("Iniciando aplicación...")
    await inicializar_aplicacion()
    logger.info("Aplicación lista")
    yield
    # Shutdown
    logger.info("Cerrando aplicación...")


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    description="""
## Sistema de Prefactibilidad Ambiental para Proyectos Mineros en Chile

Este sistema permite:
- **Análisis espacial** de proyectos contra capas GIS (áreas protegidas, glaciares, comunidades, etc.)
- **Evaluación automática** de triggers del Art. 11 de la Ley 19.300
- **Clasificación** de vía de ingreso al SEIA (DIA vs EIA)
- **Búsqueda normativa** con RAG sobre corpus legal chileno
- **Generación de informes** de prefactibilidad ambiental

### Regiones prioritarias
- Antofagasta (II Región)
- Atacama (III Región)
- Coquimbo (IV Región)
    """,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:4001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información del sistema."""
    return {
        "nombre": settings.PROJECT_NAME,
        "version": "0.1.0",
        "estado": "operativo",
        "documentacion": "/docs",
        "endpoints": {
            "analisis_espacial": f"{settings.API_V1_PREFIX}/gis/analisis-espacial",
            "capas_gis": f"{settings.API_V1_PREFIX}/gis/capas",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check para monitoreo."""
    return {"status": "healthy"}


# Incluir router de API
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
