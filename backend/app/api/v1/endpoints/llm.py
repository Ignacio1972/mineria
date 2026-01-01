"""
Endpoints de Gestión de Modelos LLM

Permite administrar la configuración del modelo LLM en runtime:
- Listar modelos disponibles
- Ver/cambiar modelo activo
- Health check del servicio
- Búsqueda web actualizada (Perplexity)
"""

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.llm.gestor import get_gestor_modelos, GestorModelos, CATALOGO_MODELOS
from app.services.llm.cliente import get_cliente_llm
from app.services.llm.router import get_llm_router, LLMRouter, TipoTarea
from app.services.llm.perplexity_client import is_perplexity_enabled

router = APIRouter()


# ===== SCHEMAS =====

class ModeloInfo(BaseModel):
    """Información de un modelo LLM."""
    id: str = Field(..., description="ID del modelo")
    nombre: str = Field(..., description="Nombre legible")
    descripcion: str = Field(..., description="Descripción del modelo")
    costo_input_1k: float = Field(..., description="Costo por 1K tokens de entrada (USD)")
    costo_output_1k: float = Field(..., description="Costo por 1K tokens de salida (USD)")
    max_tokens: int = Field(..., description="Máximo de tokens de salida")
    velocidad: str = Field(..., description="Velocidad relativa")
    recomendado_para: list[str] = Field(..., description="Casos de uso recomendados")
    activo: bool = Field(..., description="Si es el modelo activo actualmente")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "claude-sonnet-4-20250514",
                "nombre": "Claude Sonnet 4",
                "descripcion": "Balance óptimo velocidad/calidad",
                "costo_input_1k": 0.003,
                "costo_output_1k": 0.015,
                "max_tokens": 8192,
                "velocidad": "rápido",
                "recomendado_para": ["análisis", "informes"],
                "activo": True
            }
        }


class ModelosListResponse(BaseModel):
    """Lista de modelos disponibles."""
    modelos: list[ModeloInfo]
    modelo_activo: str = Field(..., description="ID del modelo actualmente activo")
    total: int = Field(..., description="Total de modelos disponibles")


class ModeloActivoResponse(BaseModel):
    """Respuesta con información del modelo activo."""
    modelo: str = Field(..., description="ID del modelo activo")
    nombre: str = Field(..., description="Nombre del modelo")
    configuracion: dict[str, Any] = Field(..., description="Configuración actual del cliente")


class CambiarModeloRequest(BaseModel):
    """Request para cambiar el modelo activo."""
    modelo: str = Field(
        ...,
        description="ID del modelo a activar",
        json_schema_extra={"example": "claude-opus-4-20250514"}
    )


class CambiarModeloResponse(BaseModel):
    """Respuesta al cambiar modelo."""
    anterior: str = Field(..., description="Modelo anterior")
    nuevo: str = Field(..., description="Nuevo modelo activo")
    mensaje: str = Field(..., description="Mensaje de confirmación")
    persistido: bool = Field(..., description="Si se guardó en Redis")


class HealthResponse(BaseModel):
    """Respuesta del health check."""
    status: str = Field(..., description="Estado: healthy o unhealthy")
    modelo: str | None = Field(None, description="Modelo usado en la prueba")
    latencia_ms: int | None = Field(None, description="Latencia de la prueba en ms")
    error: str | None = Field(None, description="Mensaje de error si unhealthy")


# ===== DEPENDENCIAS =====

def get_gestor() -> GestorModelos:
    """Obtiene instancia del gestor de modelos."""
    return get_gestor_modelos()


# ===== ENDPOINTS =====

@router.get(
    "/modelos",
    response_model=ModelosListResponse,
    summary="Listar modelos disponibles",
    description="""
    Retorna la lista completa de modelos LLM disponibles con su metadata.

    Incluye información de costos, velocidad y casos de uso recomendados
    para cada modelo.
    """
)
async def listar_modelos(
    gestor: GestorModelos = Depends(get_gestor),
) -> ModelosListResponse:
    """Lista todos los modelos disponibles."""
    catalogo = gestor.obtener_catalogo()

    modelos = [ModeloInfo(**modelo) for modelo in catalogo]

    return ModelosListResponse(
        modelos=modelos,
        modelo_activo=gestor.modelo_activo,
        total=len(modelos),
    )


@router.get(
    "/modelo-activo",
    response_model=ModeloActivoResponse,
    summary="Obtener modelo activo",
    description="""
    Retorna información del modelo LLM actualmente activo
    junto con su configuración.
    """
)
async def obtener_modelo_activo(
    gestor: GestorModelos = Depends(get_gestor),
) -> ModeloActivoResponse:
    """Obtiene información del modelo activo."""
    info = gestor.info_modelo_activo
    config = gestor.obtener_configuracion_cliente()

    return ModeloActivoResponse(
        modelo=info["id"],
        nombre=info["nombre"],
        configuracion=config,
    )


@router.put(
    "/modelo-activo",
    response_model=CambiarModeloResponse,
    summary="Cambiar modelo activo",
    description="""
    Cambia el modelo LLM activo en runtime.

    El cambio es inmediato y afecta a todas las solicitudes
    posteriores que usen el servicio LLM (generación de informes).

    El modelo se persiste en Redis para mantener la selección
    entre reinicios del servidor.

    **Modelos disponibles:**
    - `claude-sonnet-4-20250514`: Balance velocidad/calidad (recomendado)
    - `claude-3-5-haiku-20241022`: Más rápido y económico
    - `claude-opus-4-20250514`: Máxima calidad
    """
)
async def cambiar_modelo_activo(
    request: CambiarModeloRequest,
    gestor: GestorModelos = Depends(get_gestor),
) -> CambiarModeloResponse:
    """Cambia el modelo activo."""
    try:
        resultado = gestor.cambiar_modelo(request.modelo)
        return CambiarModeloResponse(**resultado)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check del servicio LLM",
    description="""
    Verifica la conectividad con la API de Anthropic.

    Envía un prompt de prueba mínimo y mide la latencia.
    Útil para diagnóstico y monitoreo.
    """
)
async def health_check_llm(
    gestor: GestorModelos = Depends(get_gestor),
) -> HealthResponse:
    """Verifica el estado del servicio LLM."""
    cliente = get_cliente_llm()

    resultado = await cliente.health_check()

    return HealthResponse(
        status=resultado.get("status", "unknown"),
        modelo=resultado.get("modelo"),
        latencia_ms=resultado.get("latencia_ms"),
        error=resultado.get("error"),
    )


@router.get(
    "/catalogo",
    summary="Obtener catálogo de modelos (raw)",
    description="Retorna el catálogo de modelos en formato raw para debugging."
)
async def obtener_catalogo_raw() -> dict[str, Any]:
    """Retorna el catálogo de modelos sin procesar."""
    return {
        "catalogo": CATALOGO_MODELOS,
        "total": len(CATALOGO_MODELOS),
    }


# ===== SCHEMAS BUSQUEDA WEB =====

class FuenteCitada(BaseModel):
    """Fuente citada en la búsqueda web."""
    titulo: str = Field(..., description="Título de la fuente")
    url: str = Field(..., description="URL de la fuente")
    fragmento: Optional[str] = Field(None, description="Fragmento relevante")


class BusquedaWebRequest(BaseModel):
    """Request para búsqueda web actualizada."""
    query: str = Field(
        ...,
        description="Consulta de búsqueda en lenguaje natural",
        min_length=3,
        max_length=2000,
        json_schema_extra={"example": "¿Hay cambios recientes en la Ley 19.300?"}
    )
    modo: Literal["chat", "research", "reasoning"] = Field(
        default="chat",
        description="Modo de búsqueda: chat (rápido), research (profundo), reasoning (analítico)"
    )
    contexto_chile: bool = Field(
        default=True,
        description="Agregar contexto de normativa ambiental chilena"
    )


class BusquedaWebResponse(BaseModel):
    """Respuesta de búsqueda web actualizada."""
    respuesta: str = Field(..., description="Respuesta generada por el modelo")
    fuentes: list[FuenteCitada] = Field(
        default_factory=list,
        description="Fuentes citadas con URLs"
    )
    proveedor: str = Field(..., description="Proveedor usado (perplexity o anthropic)")
    modelo: str = Field(..., description="Modelo específico usado")
    tokens_usados: int = Field(..., description="Tokens consumidos")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata adicional de la búsqueda"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "respuesta": "La Ley 19.300 fue modificada en...",
                "fuentes": [
                    {
                        "titulo": "BCN - Ley 19.300",
                        "url": "https://www.bcn.cl/leychile/navegar?idNorma=30667",
                        "fragmento": "Artículo 11..."
                    }
                ],
                "proveedor": "perplexity",
                "modelo": "sonar-pro",
                "tokens_usados": 1500,
                "metadata": {"modo": "chat", "num_fuentes": 3}
            }
        }


class RouterHealthResponse(BaseModel):
    """Respuesta del health check del router multi-LLM."""
    anthropic: dict[str, Any] = Field(..., description="Estado de Anthropic")
    perplexity: dict[str, Any] = Field(..., description="Estado de Perplexity")


class RouterInfoResponse(BaseModel):
    """Información del enrutamiento LLM."""
    routing: dict[str, str] = Field(..., description="Mapeo tipo_tarea -> proveedor")
    perplexity_habilitado: bool = Field(..., description="Si Perplexity está habilitado")


# ===== DEPENDENCIAS ROUTER =====

def get_router() -> LLMRouter:
    """Obtiene instancia del router LLM."""
    return get_llm_router()


# ===== ENDPOINTS BUSQUEDA WEB =====

@router.post(
    "/buscar-web",
    response_model=BusquedaWebResponse,
    summary="Búsqueda web actualizada",
    description="""
    Busca información actualizada en la web usando Perplexity AI.

    Ideal para consultar:
    - Normativa ambiental reciente
    - Proyectos aprobados en e-SEIA
    - Guías del SEA actualizadas
    - Cualquier información que requiera datos en tiempo real

    **Modos de búsqueda:**
    - `chat`: Respuestas rápidas (sonar-pro)
    - `research`: Investigación profunda (sonar-deep-research)
    - `reasoning`: Análisis lógico complejo (sonar-reasoning-pro)

    Si Perplexity no está disponible, usa Claude como fallback.
    """
)
async def buscar_web_actualizada(
    request: BusquedaWebRequest,
    llm_router: LLMRouter = Depends(get_router),
) -> BusquedaWebResponse:
    """
    Realiza búsqueda web con IA para información actualizada.

    Usa Perplexity para consultar SEA, e-SEIA, BCN y otras fuentes
    en tiempo real. Retorna respuesta con fuentes citadas.
    """
    try:
        # Determinar tipo de tarea según modo
        tipo_tarea = TipoTarea.INVESTIGACION if request.modo == "research" else TipoTarea.BUSQUEDA_WEB

        resultado = await llm_router.ejecutar(
            tipo_tarea=tipo_tarea,
            prompt=request.query,
            contexto_chile=request.contexto_chile,
        )

        # Convertir fuentes a schema
        fuentes = [
            FuenteCitada(
                titulo=f.get("titulo", "Fuente"),
                url=f.get("url", ""),
                fragmento=f.get("fragmento"),
            )
            for f in resultado.fuentes
        ]

        return BusquedaWebResponse(
            respuesta=resultado.contenido,
            fuentes=fuentes,
            proveedor=resultado.proveedor,
            modelo=resultado.modelo,
            tokens_usados=resultado.tokens_usados,
            metadata=resultado.metadata,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en búsqueda web: {str(e)}",
        )


@router.get(
    "/router/health",
    response_model=RouterHealthResponse,
    summary="Health check del router multi-LLM",
    description="""
    Verifica la conectividad con todos los proveedores LLM configurados.

    Retorna el estado de:
    - Anthropic (Claude)
    - Perplexity (si está habilitado)
    """
)
async def health_check_router(
    llm_router: LLMRouter = Depends(get_router),
) -> RouterHealthResponse:
    """Verifica el estado de todos los proveedores LLM."""
    resultado = await llm_router.health_check()
    return RouterHealthResponse(**resultado)


@router.get(
    "/router/info",
    response_model=RouterInfoResponse,
    summary="Información del router LLM",
    description="""
    Retorna información sobre el enrutamiento configurado.

    Muestra qué proveedor se usa para cada tipo de tarea.
    """
)
async def obtener_info_router(
    llm_router: LLMRouter = Depends(get_router),
) -> RouterInfoResponse:
    """Obtiene información del enrutamiento LLM."""
    return RouterInfoResponse(
        routing=llm_router.get_routing_info(),
        perplexity_habilitado=is_perplexity_enabled(),
    )
