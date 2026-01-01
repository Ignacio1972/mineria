"""
Cliente para Perplexity AI API.

Proporciona busqueda web con IA para informacion actualizada
sobre normativa ambiental, proyectos SEIA, y guias del SEA.
"""

import logging
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from enum import Enum

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModoPerplexity(str, Enum):
    """Modos de busqueda disponibles en Perplexity."""
    CHAT = "chat"
    RESEARCH = "research"
    REASONING = "reasoning"


@dataclass
class FuentePerplexity:
    """Fuente citada por Perplexity."""
    titulo: str
    url: str
    fragmento: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "titulo": self.titulo,
            "url": self.url,
            "fragmento": self.fragmento,
        }


@dataclass
class PerplexityResponse:
    """Respuesta de Perplexity AI."""
    contenido: str
    fuentes: List[FuentePerplexity]
    modelo: str
    tokens_usados: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contenido": self.contenido,
            "fuentes": [f.to_dict() for f in self.fuentes],
            "modelo": self.modelo,
            "tokens_usados": self.tokens_usados,
            "metadata": self.metadata,
        }


class PerplexityError(Exception):
    """Error del cliente Perplexity."""
    pass


class PerplexityClient:
    """
    Cliente async para la API de Perplexity AI.

    Proporciona busqueda web con IA, ideal para:
    - Consultas sobre normativa ambiental actualizada
    - Proyectos recientes en e-SEIA
    - Guias y documentos del SEA
    - Cualquier informacion que requiera datos en tiempo real
    """

    BASE_URL = "https://api.perplexity.ai"

    MODELOS = {
        ModoPerplexity.CHAT: "sonar-pro",
        ModoPerplexity.RESEARCH: "sonar-deep-research",
        ModoPerplexity.REASONING: "sonar-reasoning-pro",
    }

    # Contexto por defecto para consultas ambientales chilenas
    CONTEXTO_CHILE = """Contexto: Sistema de Evaluacion de Impacto Ambiental (SEIA) de Chile.
Normativa relevante: Ley 19.300 de Bases Generales del Medio Ambiente,
DS 40/2012 Reglamento del SEIA, guias del SEA (Servicio de Evaluacion Ambiental).
Enfocate en informacion oficial de fuentes chilenas como sea.gob.cl, bcn.cl,
diariooficial.interior.gob.cl cuando sea posible."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Inicializa el cliente Perplexity.

        Args:
            api_key: API key de Perplexity. Si no se proporciona, usa settings.
            timeout: Timeout en segundos. Si no se proporciona, usa settings.
        """
        self.api_key = api_key or settings.PERPLEXITY_API_KEY
        self.timeout = timeout or settings.PERPLEXITY_TIMEOUT_SECONDS
        self._client: Optional[httpx.AsyncClient] = None

        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY no configurada")

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy loading del cliente HTTP."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def buscar(
        self,
        query: str,
        modo: Literal["chat", "research", "reasoning"] = "chat",
        contexto_chile: bool = True,
        contexto_adicional: Optional[str] = None,
    ) -> PerplexityResponse:
        """
        Realiza una busqueda con Perplexity AI.

        Args:
            query: Consulta de busqueda en lenguaje natural
            modo: Modo de busqueda:
                - "chat": Respuestas rapidas (sonar-pro)
                - "research": Investigacion profunda (sonar-deep-research)
                - "reasoning": Analisis logico (sonar-reasoning-pro)
            contexto_chile: Si True, agrega contexto de normativa chilena
            contexto_adicional: Contexto extra opcional

        Returns:
            PerplexityResponse con contenido y fuentes

        Raises:
            PerplexityError: Si hay error en la API
        """
        if not self.api_key:
            raise PerplexityError(
                "PERPLEXITY_API_KEY no configurada. "
                "Configure la variable de entorno o en el archivo .env"
            )

        # Determinar modelo
        modo_enum = ModoPerplexity(modo)
        modelo = self.MODELOS[modo_enum]

        # Construir mensajes
        mensajes = []

        # System message con contexto
        system_content = ""
        if contexto_chile:
            system_content = self.CONTEXTO_CHILE
        if contexto_adicional:
            system_content += f"\n\n{contexto_adicional}"

        if system_content:
            mensajes.append({
                "role": "system",
                "content": system_content.strip()
            })

        mensajes.append({
            "role": "user",
            "content": query
        })

        # Payload de la API
        payload = {
            "model": modelo,
            "messages": mensajes,
            "return_citations": True,
            "return_related_questions": False,
        }

        logger.info(f"Perplexity busqueda: modo={modo}, query={query[:100]}...")

        try:
            response = await self.client.post(
                "/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # Extraer contenido
            contenido = ""
            if data.get("choices"):
                contenido = data["choices"][0]["message"]["content"]

            # Extraer fuentes/citas
            fuentes = []
            citations = data.get("citations", [])
            for cite in citations:
                if isinstance(cite, dict):
                    fuentes.append(FuentePerplexity(
                        titulo=cite.get("title", ""),
                        url=cite.get("url", ""),
                        fragmento=cite.get("snippet"),
                    ))
                elif isinstance(cite, str):
                    # A veces las citas vienen como URLs directas
                    fuentes.append(FuentePerplexity(
                        titulo="Fuente",
                        url=cite,
                    ))

            # Tokens usados
            usage = data.get("usage", {})
            tokens = usage.get("total_tokens", 0)

            resultado = PerplexityResponse(
                contenido=contenido,
                fuentes=fuentes,
                modelo=data.get("model", modelo),
                tokens_usados=tokens,
                metadata={
                    "modo": modo,
                    "contexto_chile": contexto_chile,
                }
            )

            logger.info(
                f"Perplexity respuesta: {len(fuentes)} fuentes, "
                f"{tokens} tokens, modelo={resultado.modelo}"
            )

            return resultado

        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity HTTP error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                raise PerplexityError("API key invalida o expirada")
            elif e.response.status_code == 429:
                raise PerplexityError("Rate limit excedido. Intente mas tarde.")
            elif e.response.status_code >= 500:
                raise PerplexityError("Servicio Perplexity no disponible temporalmente")
            else:
                raise PerplexityError(f"Error HTTP {e.response.status_code}: {e.response.text}")

        except httpx.TimeoutException:
            logger.error(f"Perplexity timeout despues de {self.timeout}s")
            raise PerplexityError(f"Timeout: La busqueda tomo mas de {self.timeout} segundos")

        except httpx.RequestError as e:
            logger.error(f"Perplexity request error: {e}")
            raise PerplexityError(f"Error de conexion: {str(e)}")

    async def buscar_con_reintentos(
        self,
        query: str,
        modo: Literal["chat", "research", "reasoning"] = "chat",
        contexto_chile: bool = True,
        max_reintentos: int = 3,
        **kwargs
    ) -> PerplexityResponse:
        """
        Busqueda con reintentos automaticos para errores temporales.

        Args:
            query: Consulta de busqueda
            modo: Modo de busqueda
            contexto_chile: Si incluir contexto chileno
            max_reintentos: Numero maximo de reintentos
            **kwargs: Argumentos adicionales para buscar()

        Returns:
            PerplexityResponse

        Raises:
            PerplexityError: Si falla despues de todos los reintentos
        """
        ultimo_error = None

        for intento in range(max_reintentos):
            try:
                return await self.buscar(
                    query=query,
                    modo=modo,
                    contexto_chile=contexto_chile,
                    **kwargs
                )
            except PerplexityError as e:
                ultimo_error = e
                # Solo reintentar en errores de rate limit o servidor
                if "Rate limit" in str(e) or "no disponible" in str(e):
                    espera = min(2 ** intento * 2, 30)  # 2s, 4s, 8s... max 30s
                    logger.warning(
                        f"Perplexity error reintentable: {e}. "
                        f"Reintentando en {espera}s (intento {intento + 1}/{max_reintentos})"
                    )
                    await asyncio.sleep(espera)
                else:
                    # Error no reintentable
                    raise

        raise ultimo_error or PerplexityError("Error desconocido despues de reintentos")

    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica la conectividad con Perplexity API.

        Returns:
            Diccionario con estado de salud
        """
        if not self.api_key:
            return {
                "status": "unconfigured",
                "error": "PERPLEXITY_API_KEY no configurada",
            }

        try:
            respuesta = await self.buscar(
                query="test",
                modo="chat",
                contexto_chile=False,
            )
            return {
                "status": "healthy",
                "modelo": respuesta.modelo,
            }
        except PerplexityError as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def close(self):
        """Cierra el cliente HTTP."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Instancia singleton
_perplexity_client: Optional[PerplexityClient] = None


def get_perplexity_client() -> PerplexityClient:
    """
    Obtiene la instancia singleton del cliente Perplexity.

    Returns:
        PerplexityClient configurado
    """
    global _perplexity_client
    if _perplexity_client is None:
        _perplexity_client = PerplexityClient()
    return _perplexity_client


def is_perplexity_enabled() -> bool:
    """
    Verifica si Perplexity esta habilitado y configurado.

    Returns:
        True si esta habilitado y tiene API key
    """
    return (
        settings.PERPLEXITY_ENABLED and
        bool(settings.PERPLEXITY_API_KEY)
    )
