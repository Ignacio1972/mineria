"""
Herramientas externas del asistente.
Integraciones con APIs externas como Perplexity para busqueda web.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)
from app.services.llm.perplexity_client import (
    get_perplexity_client,
    is_perplexity_enabled,
    PerplexityError,
)

logger = logging.getLogger(__name__)


@registro_herramientas.registrar
class BuscarWebActualizada(Herramienta):
    """Busca informacion actualizada en la web usando Perplexity AI."""

    nombre = "buscar_web_actualizada"
    descripcion = """Busca informacion actualizada en la web usando Perplexity AI.
Ideal para consultar:
- Cambios recientes en normativa ambiental (Ley 19.300, DS 40)
- Proyectos mineros aprobados o en tramitacion en e-SEIA
- Ultimas guias y documentos del SEA
- Noticias y actualizaciones del sector ambiental chileno
- Cualquier informacion que requiera datos en tiempo real

Esta herramienta complementa la busqueda en el corpus legal local (buscar_normativa)
con informacion actualizada de internet.

IMPORTANTE: Usa esta herramienta cuando el usuario pregunte por:
- Informacion "reciente", "actualizada", "ultima", "este ano/mes"
- Cambios o modificaciones a normativa existente
- Estado actual de proyectos en tramitacion
- Cualquier dato que pueda haber cambiado desde la carga del corpus local"""

    categoria = CategoriaHerramienta.EXTERNA
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        """Establece la sesion de base de datos (no usada, pero requerida por interface)."""
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Consulta de busqueda en lenguaje natural. "
                                   "Se recomienda ser especifico, ej: "
                                   "'cambios ley 19300 2024' en lugar de solo 'ley 19300'"
                },
                "modo": {
                    "type": "string",
                    "description": "Modo de busqueda: "
                                   "'chat' para respuestas rapidas (default), "
                                   "'research' para investigacion profunda con mas fuentes, "
                                   "'reasoning' para analisis logico de temas complejos",
                    "enum": ["chat", "research", "reasoning"],
                    "default": "chat"
                },
                "contexto_chile": {
                    "type": "boolean",
                    "description": "Si es True (default), agrega contexto de normativa "
                                   "ambiental chilena para mejores resultados. "
                                   "Usar False solo para busquedas generales no relacionadas a Chile.",
                    "default": True
                }
            },
            "required": ["query"]
        }

    async def ejecutar(
        self,
        query: str,
        modo: str = "chat",
        contexto_chile: bool = True,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """
        Ejecuta busqueda web con Perplexity AI.

        Args:
            query: Consulta de busqueda
            modo: Modo de busqueda (chat, research, reasoning)
            contexto_chile: Si incluir contexto de normativa chilena
            db: Sesion de BD (no usada pero requerida por interface)

        Returns:
            ResultadoHerramienta con respuesta y fuentes
        """
        # Verificar si Perplexity esta habilitado
        if not is_perplexity_enabled():
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="La busqueda web no esta disponible. "
                      "Perplexity no esta configurado (falta PERPLEXITY_API_KEY)."
            )

        # Validar modo
        modos_validos = ["chat", "research", "reasoning"]
        if modo not in modos_validos:
            modo = "chat"
            logger.warning(f"Modo invalido, usando 'chat'. Validos: {modos_validos}")

        try:
            # Obtener cliente y ejecutar busqueda
            client = get_perplexity_client()
            respuesta = await client.buscar_con_reintentos(
                query=query,
                modo=modo,
                contexto_chile=contexto_chile,
            )

            # Formatear fuentes para el resultado
            fuentes_formateadas = []
            for fuente in respuesta.fuentes:
                fuentes_formateadas.append({
                    "titulo": fuente.titulo,
                    "url": fuente.url,
                    "fragmento": fuente.fragmento,
                })

            # Construir resultado
            resultado = {
                "respuesta": respuesta.contenido,
                "fuentes": fuentes_formateadas,
                "total_fuentes": len(fuentes_formateadas),
                "modo_usado": modo,
                "modelo": respuesta.modelo,
                "tokens_usados": respuesta.tokens_usados,
            }

            # Agregar nota sobre fuentes si hay
            if fuentes_formateadas:
                resultado["nota"] = (
                    f"Se encontraron {len(fuentes_formateadas)} fuentes. "
                    "Las URLs estan disponibles para referencia."
                )

            logger.info(
                f"Busqueda web exitosa: query='{query[:50]}...', "
                f"fuentes={len(fuentes_formateadas)}, modo={modo}"
            )

            return ResultadoHerramienta(
                exito=True,
                contenido=resultado,
                metadata={
                    "modelo": respuesta.modelo,
                    "tokens": respuesta.tokens_usados,
                    "modo": modo,
                }
            )

        except PerplexityError as e:
            logger.error(f"Error Perplexity: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error en busqueda web: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Error inesperado en busqueda web: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error inesperado: {str(e)}"
            )
