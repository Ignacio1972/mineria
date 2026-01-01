"""
Servicios LLM - Fase 3

Modulo que implementa la integracion con LLMs para generacion de informes
de prefactibilidad ambiental.

Incluye:
- ClienteLLM: Cliente para Anthropic Claude
- PerplexityClient: Cliente para Perplexity AI (busqueda web)
- LLMRouter: Router multi-proveedor que enruta tareas al LLM apropiado
"""

from app.services.llm.cliente import (
    ClienteLLM,
    ConfiguracionLLM,
    RespuestaLLM,
    get_cliente_llm,
)
from app.services.llm.prompts import GestorPrompts, TipoPrompt
from app.services.llm.generador import GeneradorInformes, SeccionInforme
from app.services.llm.perplexity_client import (
    PerplexityClient,
    PerplexityResponse,
    PerplexityError,
    get_perplexity_client,
    is_perplexity_enabled,
)
from app.services.llm.router import (
    LLMRouter,
    TipoTarea,
    Proveedor,
    RespuestaRouter,
    get_llm_router,
)

__all__ = [
    # Cliente Anthropic
    "ClienteLLM",
    "ConfiguracionLLM",
    "RespuestaLLM",
    "get_cliente_llm",
    # Prompts
    "GestorPrompts",
    "TipoPrompt",
    # Generador
    "GeneradorInformes",
    "SeccionInforme",
    # Cliente Perplexity
    "PerplexityClient",
    "PerplexityResponse",
    "PerplexityError",
    "get_perplexity_client",
    "is_perplexity_enabled",
    # Router Multi-LLM
    "LLMRouter",
    "TipoTarea",
    "Proveedor",
    "RespuestaRouter",
    "get_llm_router",
]
