"""
Router de LLM Multi-Proveedor.

Enruta tareas al modelo LLM mas apropiado segun el tipo de tarea:
- Claude Sonnet 4: Razonamiento complejo, generacion de informes
- Claude Haiku: Respuestas rapidas, fallback
- Perplexity Sonar: Busqueda web actualizada
- Perplexity Deep Research: Investigacion profunda
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Union

from app.core.config import settings
from app.services.llm.cliente import ClienteLLM, RespuestaLLM, get_cliente_llm
from app.services.llm.perplexity_client import (
    PerplexityClient,
    PerplexityResponse,
    PerplexityError,
    get_perplexity_client,
    is_perplexity_enabled,
)

logger = logging.getLogger(__name__)


class TipoTarea(str, Enum):
    """Tipos de tareas para enrutamiento LLM."""
    RAZONAMIENTO = "razonamiento"        # Analisis complejo, tool use
    BUSQUEDA_WEB = "busqueda_web"        # Busqueda con datos actualizados
    INVESTIGACION = "investigacion"      # Investigacion profunda
    GENERACION = "generacion"            # Generacion de informes/documentos
    RESPUESTA_RAPIDA = "respuesta_rapida"  # Respuestas simples


class Proveedor(str, Enum):
    """Proveedores de LLM disponibles."""
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"


@dataclass
class RespuestaRouter:
    """Respuesta unificada del router."""
    contenido: str
    proveedor: str
    modelo: str
    tokens_usados: int
    fuentes: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contenido": self.contenido,
            "proveedor": self.proveedor,
            "modelo": self.modelo,
            "tokens_usados": self.tokens_usados,
            "fuentes": self.fuentes,
            "metadata": self.metadata,
        }


class LLMRouter:
    """
    Router para enrutar tareas al LLM mas apropiado.

    Reglas de enrutamiento:
    - Razonamiento complejo    -> Claude Sonnet 4
    - Busqueda web actualizada -> Perplexity Sonar
    - Investigacion profunda   -> Perplexity Deep Research
    - Respuestas rapidas       -> Claude Haiku (fallback)
    - Generacion de informes   -> Claude Sonnet 4
    """

    # Mapeo de tipo de tarea a proveedor preferido
    ROUTING = {
        TipoTarea.RAZONAMIENTO: Proveedor.ANTHROPIC,
        TipoTarea.BUSQUEDA_WEB: Proveedor.PERPLEXITY,
        TipoTarea.INVESTIGACION: Proveedor.PERPLEXITY,
        TipoTarea.GENERACION: Proveedor.ANTHROPIC,
        TipoTarea.RESPUESTA_RAPIDA: Proveedor.ANTHROPIC,
    }

    # Mapeo de tipo de tarea a modo Perplexity
    MODOS_PERPLEXITY = {
        TipoTarea.BUSQUEDA_WEB: "chat",
        TipoTarea.INVESTIGACION: "research",
    }

    def __init__(
        self,
        anthropic_client: Optional[ClienteLLM] = None,
        perplexity_client: Optional[PerplexityClient] = None,
    ):
        """
        Inicializa el router LLM.

        Args:
            anthropic_client: Cliente de Anthropic. Si no se proporciona, usa singleton.
            perplexity_client: Cliente de Perplexity. Si no se proporciona, usa singleton.
        """
        self.anthropic = anthropic_client
        self.perplexity = perplexity_client
        self._initialized = False

        logger.info("LLMRouter inicializado")

    def _ensure_clients(self):
        """Inicializa los clientes de forma lazy."""
        if not self._initialized:
            if self.anthropic is None:
                self.anthropic = get_cliente_llm()

            if self.perplexity is None and is_perplexity_enabled():
                self.perplexity = get_perplexity_client()

            self._initialized = True

    def determinar_proveedor(self, tipo_tarea: TipoTarea) -> Proveedor:
        """
        Determina que proveedor usar segun el tipo de tarea.

        Si Perplexity no esta disponible, usa Anthropic como fallback.

        Args:
            tipo_tarea: Tipo de tarea a ejecutar

        Returns:
            Proveedor seleccionado
        """
        self._ensure_clients()

        proveedor_preferido = self.ROUTING.get(tipo_tarea, Proveedor.ANTHROPIC)

        # Si Perplexity no esta disponible, usar Anthropic
        if proveedor_preferido == Proveedor.PERPLEXITY:
            if not is_perplexity_enabled() or self.perplexity is None:
                logger.info(
                    f"Perplexity no disponible para {tipo_tarea}, "
                    f"usando Anthropic como fallback"
                )
                return Proveedor.ANTHROPIC

        return proveedor_preferido

    async def ejecutar(
        self,
        tipo_tarea: TipoTarea,
        prompt: str,
        prompt_sistema: Optional[str] = None,
        contexto_chile: bool = True,
        **kwargs
    ) -> RespuestaRouter:
        """
        Ejecuta una tarea con el proveedor apropiado.

        Args:
            tipo_tarea: Tipo de tarea a ejecutar
            prompt: Prompt o query del usuario
            prompt_sistema: Prompt de sistema (solo Anthropic)
            contexto_chile: Incluir contexto de normativa chilena (solo Perplexity)
            **kwargs: Argumentos adicionales para el proveedor

        Returns:
            RespuestaRouter con resultado unificado

        Raises:
            Exception: Si falla la ejecucion
        """
        self._ensure_clients()

        proveedor = self.determinar_proveedor(tipo_tarea)

        logger.info(f"LLMRouter: {tipo_tarea.value} -> {proveedor.value}")

        if proveedor == Proveedor.PERPLEXITY:
            return await self._ejecutar_perplexity(
                tipo_tarea=tipo_tarea,
                prompt=prompt,
                contexto_chile=contexto_chile,
                **kwargs
            )
        else:
            return await self._ejecutar_anthropic(
                prompt=prompt,
                prompt_sistema=prompt_sistema,
                **kwargs
            )

    async def _ejecutar_anthropic(
        self,
        prompt: str,
        prompt_sistema: Optional[str] = None,
        **kwargs
    ) -> RespuestaRouter:
        """Ejecuta con Anthropic Claude."""
        respuesta = await self.anthropic.generar(
            prompt_usuario=prompt,
            prompt_sistema=prompt_sistema,
            **kwargs
        )

        return RespuestaRouter(
            contenido=respuesta.contenido,
            proveedor=Proveedor.ANTHROPIC.value,
            modelo=respuesta.modelo,
            tokens_usados=respuesta.tokens_totales,
            metadata={
                "tiempo_ms": respuesta.tiempo_ms,
                "tokens_entrada": respuesta.tokens_entrada,
                "tokens_salida": respuesta.tokens_salida,
            }
        )

    async def _ejecutar_perplexity(
        self,
        tipo_tarea: TipoTarea,
        prompt: str,
        contexto_chile: bool = True,
        **kwargs
    ) -> RespuestaRouter:
        """Ejecuta con Perplexity."""
        modo = self.MODOS_PERPLEXITY.get(tipo_tarea, "chat")

        try:
            respuesta = await self.perplexity.buscar(
                query=prompt,
                modo=modo,
                contexto_chile=contexto_chile,
                **kwargs
            )

            return RespuestaRouter(
                contenido=respuesta.contenido,
                proveedor=Proveedor.PERPLEXITY.value,
                modelo=respuesta.modelo,
                tokens_usados=respuesta.tokens_usados,
                fuentes=[f.to_dict() for f in respuesta.fuentes],
                metadata={
                    "modo": modo,
                    "num_fuentes": len(respuesta.fuentes),
                }
            )

        except PerplexityError as e:
            # Fallback a Anthropic si Perplexity falla
            logger.warning(f"Perplexity fallo ({e}), usando Anthropic como fallback")
            return await self._ejecutar_anthropic(
                prompt=prompt,
                prompt_sistema=self._generar_contexto_fallback(contexto_chile),
            )

    def _generar_contexto_fallback(self, contexto_chile: bool) -> str:
        """Genera contexto para fallback cuando Perplexity no esta disponible."""
        if not contexto_chile:
            return ""

        return """Eres un asistente experto en normativa ambiental chilena.
Tu conocimiento incluye la Ley 19.300, DS 40/2012, y guias del SEA.
Responde basandote en tu conocimiento, pero aclara cuando la informacion
podria estar desactualizada y recomienda verificar en fuentes oficiales
como sea.gob.cl o bcn.cl."""

    async def buscar_web(
        self,
        query: str,
        modo: str = "chat",
        contexto_chile: bool = True,
    ) -> RespuestaRouter:
        """
        Atajo para busqueda web (wrapper de ejecutar con BUSQUEDA_WEB).

        Args:
            query: Consulta de busqueda
            modo: Modo de busqueda ("chat" o "research")
            contexto_chile: Incluir contexto de normativa chilena

        Returns:
            RespuestaRouter con resultado
        """
        tipo = TipoTarea.INVESTIGACION if modo == "research" else TipoTarea.BUSQUEDA_WEB

        return await self.ejecutar(
            tipo_tarea=tipo,
            prompt=query,
            contexto_chile=contexto_chile,
        )

    async def generar_informe(
        self,
        prompt: str,
        prompt_sistema: Optional[str] = None,
        **kwargs
    ) -> RespuestaRouter:
        """
        Atajo para generacion de informes.

        Args:
            prompt: Contenido a generar
            prompt_sistema: Contexto del sistema
            **kwargs: Argumentos adicionales

        Returns:
            RespuestaRouter con resultado
        """
        return await self.ejecutar(
            tipo_tarea=TipoTarea.GENERACION,
            prompt=prompt,
            prompt_sistema=prompt_sistema,
            **kwargs
        )

    async def razonar(
        self,
        prompt: str,
        prompt_sistema: Optional[str] = None,
        **kwargs
    ) -> RespuestaRouter:
        """
        Atajo para razonamiento complejo.

        Args:
            prompt: Problema a analizar
            prompt_sistema: Contexto del sistema
            **kwargs: Argumentos adicionales

        Returns:
            RespuestaRouter con resultado
        """
        return await self.ejecutar(
            tipo_tarea=TipoTarea.RAZONAMIENTO,
            prompt=prompt,
            prompt_sistema=prompt_sistema,
            **kwargs
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica la salud de todos los proveedores.

        Returns:
            Estado de salud de cada proveedor
        """
        self._ensure_clients()

        resultado = {
            "anthropic": {"status": "unknown"},
            "perplexity": {"status": "unknown"},
        }

        # Check Anthropic
        try:
            anthropic_health = await self.anthropic.health_check()
            resultado["anthropic"] = anthropic_health
        except Exception as e:
            resultado["anthropic"] = {
                "status": "error",
                "error": str(e),
            }

        # Check Perplexity
        if is_perplexity_enabled() and self.perplexity:
            try:
                perplexity_health = await self.perplexity.health_check()
                resultado["perplexity"] = perplexity_health
            except Exception as e:
                resultado["perplexity"] = {
                    "status": "error",
                    "error": str(e),
                }
        else:
            resultado["perplexity"] = {
                "status": "disabled",
                "reason": "PERPLEXITY_ENABLED=false or API key not set",
            }

        return resultado

    def get_routing_info(self) -> Dict[str, str]:
        """
        Retorna informacion sobre el enrutamiento configurado.

        Returns:
            Diccionario con tipo de tarea -> proveedor
        """
        return {
            tipo.value: self.determinar_proveedor(tipo).value
            for tipo in TipoTarea
        }


# Instancia singleton
_llm_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """
    Obtiene la instancia singleton del router LLM.

    Returns:
        LLMRouter configurado
    """
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
