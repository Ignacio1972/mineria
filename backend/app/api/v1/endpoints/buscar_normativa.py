"""
Endpoints para búsqueda de normativa legal.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Any, Optional
import time

from app.db.session import get_db
from app.services.rag.busqueda import BuscadorLegal, ResultadoBusqueda


router = APIRouter()


def get_buscador() -> BuscadorLegal:
    """Dependency para obtener instancia del buscador."""
    return BuscadorLegal()


class BusquedaRequest(BaseModel):
    """Request para búsqueda semántica."""
    query: str = Field(..., description="Consulta en lenguaje natural", min_length=3)
    limite: int = Field(10, description="Número máximo de resultados", ge=1, le=50)
    tipo_documento: Optional[str] = Field(None, description="Filtrar por tipo (Ley, Reglamento, Guía SEA)")
    temas: Optional[list[str]] = Field(None, description="Filtrar por temas específicos")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "requisitos para proyectos mineros en áreas protegidas",
                "limite": 5,
                "tipo_documento": "Ley",
                "temas": ["areas_protegidas", "mineria"]
            }
        }


class FragmentoResponse(BaseModel):
    """Fragmento de documento encontrado."""
    fragmento_id: int
    documento_titulo: str
    documento_tipo: str
    seccion: str
    contenido: str
    temas: list[str]
    similitud: float


class BusquedaResponse(BaseModel):
    """Respuesta de búsqueda semántica."""
    query: str
    tiempo_ms: int
    total_resultados: int
    resultados: list[FragmentoResponse]


@router.post(
    "/buscar",
    response_model=BusquedaResponse,
    summary="Búsqueda semántica de normativa",
    description="""
    Busca fragmentos de normativa legal relevantes usando similitud semántica.

    La búsqueda utiliza embeddings para encontrar pasajes conceptualmente
    relacionados con la consulta, no solo coincidencias exactas de palabras.

    **Temas disponibles:**
    - agua, aire, flora_fauna, suelo
    - comunidades_indigenas, patrimonio
    - participacion, eia, dia, rca
    - areas_protegidas, glaciares, mineria
    """
)
async def buscar_normativa(
    request: BusquedaRequest,
    db: AsyncSession = Depends(get_db),
    buscador: BuscadorLegal = Depends(get_buscador),
) -> BusquedaResponse:
    """Endpoint de búsqueda semántica."""

    start_time = time.time()

    try:
        resultados = await buscador.buscar(
            db=db,
            query=request.query,
            limite=request.limite,
            filtro_tipo=request.tipo_documento,
            filtro_temas=request.temas,
        )

        tiempo_ms = int((time.time() - start_time) * 1000)

        return BusquedaResponse(
            query=request.query,
            tiempo_ms=tiempo_ms,
            total_resultados=len(resultados),
            resultados=[
                FragmentoResponse(
                    fragmento_id=r.fragmento_id,
                    documento_titulo=r.documento_titulo,
                    documento_tipo=r.documento_tipo,
                    seccion=r.seccion,
                    contenido=r.contenido,
                    temas=r.temas,
                    similitud=r.similitud,
                )
                for r in resultados
            ],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en búsqueda: {str(e)}"
        )


@router.get(
    "/estadisticas",
    summary="Estadísticas del corpus legal",
    description="Retorna estadísticas sobre el corpus legal indexado."
)
async def estadisticas_corpus(
    db: AsyncSession = Depends(get_db),
    buscador: BuscadorLegal = Depends(get_buscador),
) -> dict[str, Any]:
    """Estadísticas del corpus."""

    try:
        return await buscador.obtener_estadisticas(db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.get(
    "/temas",
    summary="Listar temas disponibles",
    description="Retorna la lista de temas disponibles para filtrar búsquedas."
)
async def listar_temas() -> dict[str, Any]:
    """Lista temas disponibles."""

    from app.services.rag.ingestor import IngestorLegal

    return {
        "temas": list(IngestorLegal.TEMAS_KEYWORDS.keys()),
        "descripcion": {
            "agua": "Recursos hídricos, DGA, derechos de agua",
            "aire": "Calidad del aire, emisiones atmosféricas",
            "flora_fauna": "Biodiversidad, especies protegidas",
            "suelo": "Contaminación de suelos, erosión",
            "comunidades_indigenas": "Pueblos originarios, consulta indígena",
            "patrimonio": "Sitios arqueológicos, monumentos históricos",
            "participacion": "Participación ciudadana, consulta pública",
            "eia": "Estudio de Impacto Ambiental",
            "dia": "Declaración de Impacto Ambiental",
            "rca": "Resolución de Calificación Ambiental",
            "areas_protegidas": "SNASPE, parques nacionales, reservas",
            "glaciares": "Protección de glaciares y ambiente periglaciar",
            "mineria": "Normativa específica sector minero",
        }
    }
