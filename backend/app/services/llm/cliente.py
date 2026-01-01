"""
Cliente LLM para Anthropic Claude

Wrapper para interactuar con la API de Anthropic Claude,
con manejo de errores, reintentos y logging.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
import asyncio

import anthropic
from anthropic import APIError, RateLimitError, APIConnectionError

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModeloLLM(str, Enum):
    """Modelos disponibles de Claude"""
    CLAUDE_SONNET = "claude-sonnet-4-20250514"
    CLAUDE_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_OPUS = "claude-opus-4-20250514"


@dataclass
class ConfiguracionLLM:
    """Configuración para el cliente LLM"""
    modelo: str = field(default_factory=lambda: settings.LLM_MODEL)
    max_tokens: int = field(default_factory=lambda: settings.LLM_MAX_TOKENS)
    temperatura: float = 0.3  # Baja para respuestas más consistentes
    top_p: float = 0.9
    reintentos: int = 3
    timeout_segundos: int = 120

    def to_dict(self) -> dict:
        return {
            "modelo": self.modelo,
            "max_tokens": self.max_tokens,
            "temperatura": self.temperatura,
            "top_p": self.top_p,
        }


@dataclass
class RespuestaLLM:
    """Respuesta del modelo LLM"""
    contenido: str
    tokens_entrada: int
    tokens_salida: int
    modelo: str
    tiempo_ms: int
    metadata: dict = field(default_factory=dict)

    @property
    def tokens_totales(self) -> int:
        return self.tokens_entrada + self.tokens_salida

    def to_dict(self) -> dict:
        return {
            "contenido": self.contenido,
            "tokens_entrada": self.tokens_entrada,
            "tokens_salida": self.tokens_salida,
            "tokens_totales": self.tokens_totales,
            "modelo": self.modelo,
            "tiempo_ms": self.tiempo_ms,
            "metadata": self.metadata,
        }


class ClienteLLM:
    """
    Cliente para interactuar con la API de Anthropic Claude.

    Proporciona:
    - Manejo de errores y reintentos automáticos
    - Logging estructurado
    - Configuración flexible
    - Soporte para mensajes de sistema y usuario
    """

    def __init__(self, configuracion: Optional[ConfiguracionLLM] = None):
        """
        Inicializa el cliente LLM.

        Args:
            configuracion: Configuración opcional. Si no se proporciona,
                          se usan los valores por defecto.
        """
        self.config = configuracion or ConfiguracionLLM()
        self._cliente: Optional[anthropic.AsyncAnthropic] = None
        logger.info(f"ClienteLLM inicializado con modelo: {self.config.modelo}")

    @property
    def cliente(self) -> anthropic.AsyncAnthropic:
        """Lazy loading del cliente de Anthropic."""
        if self._cliente is None:
            api_key = settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY no configurada. "
                    "Configure la variable de entorno o en el archivo .env"
                )
            self._cliente = anthropic.AsyncAnthropic(
                api_key=api_key,
                timeout=self.config.timeout_segundos,
            )
        return self._cliente

    async def generar(
        self,
        prompt_usuario: str,
        prompt_sistema: Optional[str] = None,
        **kwargs
    ) -> RespuestaLLM:
        """
        Genera una respuesta usando Claude.

        Args:
            prompt_usuario: El prompt/mensaje del usuario
            prompt_sistema: Prompt de sistema opcional para contexto
            **kwargs: Parámetros adicionales para la API

        Returns:
            RespuestaLLM con el contenido y metadatos

        Raises:
            Exception: Si falla después de todos los reintentos
        """
        import time
        inicio = time.time()

        # Construir mensajes
        mensajes = [{"role": "user", "content": prompt_usuario}]

        # Parámetros de la API
        params = {
            "model": kwargs.get("modelo", self.config.modelo),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperatura", self.config.temperatura),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "messages": mensajes,
        }

        if prompt_sistema:
            params["system"] = prompt_sistema

        logger.debug(f"Enviando solicitud a Claude: {len(prompt_usuario)} chars")

        # Intentar con reintentos
        ultimo_error = None
        for intento in range(self.config.reintentos):
            try:
                respuesta = await self.cliente.messages.create(**params)

                tiempo_ms = int((time.time() - inicio) * 1000)

                # Extraer contenido de la respuesta
                contenido = ""
                if respuesta.content:
                    contenido = respuesta.content[0].text

                resultado = RespuestaLLM(
                    contenido=contenido,
                    tokens_entrada=respuesta.usage.input_tokens,
                    tokens_salida=respuesta.usage.output_tokens,
                    modelo=respuesta.model,
                    tiempo_ms=tiempo_ms,
                    metadata={
                        "stop_reason": respuesta.stop_reason,
                        "intento": intento + 1,
                    }
                )

                logger.info(
                    f"Respuesta generada: {resultado.tokens_totales} tokens, "
                    f"{tiempo_ms}ms, intento {intento + 1}"
                )
                return resultado

            except RateLimitError as e:
                ultimo_error = e
                espera = min(2 ** intento * 5, 60)  # Exponential backoff, max 60s
                logger.warning(f"Rate limit alcanzado. Esperando {espera}s (intento {intento + 1})")
                await asyncio.sleep(espera)

            except APIConnectionError as e:
                ultimo_error = e
                logger.warning(f"Error de conexión: {e} (intento {intento + 1})")
                await asyncio.sleep(2 ** intento)

            except APIError as e:
                ultimo_error = e
                logger.error(f"Error de API: {e} (intento {intento + 1})")
                if e.status_code and e.status_code >= 500:
                    await asyncio.sleep(2 ** intento)
                else:
                    raise

        # Si llegamos aquí, fallaron todos los reintentos
        logger.error(f"Fallaron todos los reintentos: {ultimo_error}")
        raise ultimo_error or Exception("Error desconocido en generación LLM")

    async def generar_estructurado(
        self,
        prompt_usuario: str,
        prompt_sistema: Optional[str] = None,
        formato_salida: str = "json",
        **kwargs
    ) -> dict[str, Any]:
        """
        Genera una respuesta estructurada (JSON).

        Args:
            prompt_usuario: El prompt del usuario
            prompt_sistema: Prompt de sistema opcional
            formato_salida: Formato esperado ("json" por defecto)
            **kwargs: Parámetros adicionales

        Returns:
            Diccionario con la respuesta parseada
        """
        import json

        # Agregar instrucción de formato al prompt
        prompt_con_formato = f"""{prompt_usuario}

IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional antes o después.
No incluyas markdown, comentarios ni explicaciones fuera del JSON."""

        respuesta = await self.generar(
            prompt_usuario=prompt_con_formato,
            prompt_sistema=prompt_sistema,
            **kwargs
        )

        # Intentar parsear JSON
        contenido = respuesta.contenido.strip()

        # Limpiar posibles marcadores de código
        if contenido.startswith("```json"):
            contenido = contenido[7:]
        if contenido.startswith("```"):
            contenido = contenido[3:]
        if contenido.endswith("```"):
            contenido = contenido[:-3]

        contenido = contenido.strip()

        try:
            resultado = json.loads(contenido)
            return {
                "data": resultado,
                "metadata": respuesta.to_dict(),
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            logger.debug(f"Contenido recibido: {contenido[:500]}...")
            return {
                "data": None,
                "error": str(e),
                "contenido_raw": contenido,
                "metadata": respuesta.to_dict(),
            }

    async def health_check(self) -> dict[str, Any]:
        """
        Verifica la conectividad con la API de Anthropic.

        Returns:
            Diccionario con estado de salud
        """
        try:
            respuesta = await self.generar(
                prompt_usuario="Responde únicamente con: OK",
                max_tokens=10,
            )
            return {
                "status": "healthy",
                "modelo": respuesta.modelo,
                "latencia_ms": respuesta.tiempo_ms,
            }
        except Exception as e:
            logger.error(f"Health check fallido: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def obtener_configuracion(self) -> dict[str, Any]:
        """Retorna la configuración actual del cliente."""
        return {
            "modelo": self.config.modelo,
            "max_tokens": self.config.max_tokens,
            "temperatura": self.config.temperatura,
            "top_p": self.config.top_p,
            "reintentos": self.config.reintentos,
            "timeout_segundos": self.config.timeout_segundos,
        }


# Instancia singleton para uso en la aplicación
_cliente_llm: Optional[ClienteLLM] = None


def get_cliente_llm() -> ClienteLLM:
    """
    Obtiene la instancia singleton del cliente LLM.

    Returns:
        ClienteLLM configurado
    """
    global _cliente_llm
    if _cliente_llm is None:
        _cliente_llm = ClienteLLM()
    return _cliente_llm
