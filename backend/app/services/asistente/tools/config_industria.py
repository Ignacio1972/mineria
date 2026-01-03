"""
Herramientas de configuración por industria para el asistente.

Proporciona acceso a la configuración por tipo de proyecto, evaluación
de umbrales SEIA y navegación del árbol de preguntas.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    ContextoHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)

logger = logging.getLogger(__name__)


@registro_herramientas.registrar
class ObtenerConfigIndustria(Herramienta):
    """Obtiene la configuración completa de un tipo de proyecto."""

    nombre = "obtener_config_industria"
    descripcion = """Obtiene la configuración de un tipo de proyecto (industria).
Usa esta herramienta cuando:
- El usuario menciona qué tipo de proyecto tiene (minería, energía, inmobiliario, etc.)
- Necesitas saber qué preguntas hacer según el tipo de proyecto
- Quieres mostrar los subtipos disponibles para que el usuario elija
- Necesitas conocer los umbrales SEIA aplicables a ese tipo de proyecto

Retorna: subtipos disponibles, umbrales SEIA, PAS típicos, primera pregunta del árbol.

Tipos disponibles: mineria, energia, inmobiliario, acuicultura, infraestructura,
portuario, forestal, agroindustria"""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        """Establece la sesión de base de datos."""
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tipo_proyecto_codigo": {
                    "type": "string",
                    "description": "Código del tipo de proyecto (ej: mineria, energia, inmobiliario)",
                    "enum": [
                        "mineria", "energia", "inmobiliario", "acuicultura",
                        "infraestructura", "portuario", "forestal", "agroindustria"
                    ],
                },
                "subtipo_codigo": {
                    "type": "string",
                    "description": "Código del subtipo (opcional, para obtener config más específica)",
                },
            },
            "required": ["tipo_proyecto_codigo"],
        }

    async def ejecutar(
        self,
        tipo_proyecto_codigo: str,
        subtipo_codigo: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Obtiene la configuración completa de un tipo de proyecto."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesión de base de datos disponible"
            )

        try:
            from app.services.config_industria import get_config_industria_service

            service = get_config_industria_service(db)
            config = await service.get_config_completa(tipo_proyecto_codigo, subtipo_codigo)

            if not config:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"No se encontró configuración para el tipo '{tipo_proyecto_codigo}'"
                )

            # Preparar respuesta simplificada para el LLM
            subtipos_lista = [
                {"codigo": s.codigo, "nombre": s.nombre, "descripcion": s.descripcion}
                for s in config.subtipos_disponibles
            ]

            umbrales_lista = [
                {
                    "parametro": u.parametro,
                    "operador": u.operador,
                    "valor": float(u.valor),
                    "unidad": u.unidad,
                    "resultado": u.resultado.value if hasattr(u.resultado, 'value') else u.resultado,
                    "norma_referencia": u.norma_referencia,
                    "descripcion": u.descripcion,
                }
                for u in config.umbrales
            ]

            pas_lista = [
                {
                    "articulo": p.articulo,
                    "nombre": p.nombre,
                    "organismo": p.organismo,
                    "obligatoriedad": p.obligatoriedad.value if hasattr(p.obligatoriedad, 'value') else p.obligatoriedad,
                }
                for p in config.pas[:10]  # Limitar a 10 PAS
            ]

            # Obtener primera pregunta
            primera_pregunta = None
            if config.preguntas:
                p = config.preguntas[0]
                primera_pregunta = {
                    "codigo": p.codigo,
                    "texto": p.pregunta_texto,
                    "tipo_respuesta": p.tipo_respuesta.value if hasattr(p.tipo_respuesta, 'value') else p.tipo_respuesta,
                    "opciones": p.opciones,
                    "es_obligatoria": p.es_obligatoria,
                    "ayuda": p.ayuda,
                }

            resultado = {
                "tipo": {
                    "codigo": config.tipo.codigo,
                    "nombre": config.tipo.nombre,
                    "letra_art3": config.tipo.letra_art3,
                    "descripcion": config.tipo.descripcion,
                },
                "subtipo_seleccionado": {
                    "codigo": config.subtipo.codigo,
                    "nombre": config.subtipo.nombre,
                } if config.subtipo else None,
                "subtipos_disponibles": subtipos_lista,
                "umbrales_seia": umbrales_lista,
                "pas_tipicos": pas_lista,
                "primera_pregunta": primera_pregunta,
                "total_preguntas": len(config.preguntas),
                "mensaje": f"Configuración cargada para '{config.tipo.nombre}'. "
                          f"Hay {len(subtipos_lista)} subtipos, {len(umbrales_lista)} umbrales SEIA "
                          f"y {len(config.preguntas)} preguntas configuradas.",
            }

            logger.info(f"Config industria obtenida: {tipo_proyecto_codigo}")

            return ResultadoHerramienta(
                exito=True,
                contenido=resultado,
                metadata={
                    "tipo_proyecto": tipo_proyecto_codigo,
                    "subtipo": subtipo_codigo,
                }
            )

        except Exception as e:
            logger.error(f"Error obteniendo config industria: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al obtener configuración: {str(e)}"
            )


@registro_herramientas.registrar
class EvaluarUmbralSEIA(Herramienta):
    """Evalúa si un valor cumple umbral de ingreso al SEIA."""

    nombre = "evaluar_umbral_seia"
    descripcion = """Evalúa si un proyecto debe ingresar al SEIA según sus parámetros.
Usa esta herramienta cuando el usuario proporcione valores como:
- Tonelaje de producción (tonelaje_mensual)
- Potencia instalada (potencia_mw)
- Superficie del proyecto (superficie_ha)
- Número de viviendas (num_viviendas)
- Caudal de agua (caudal_lps)
- Capacidad de almacenamiento (capacidad_m3)

IMPORTANTE: Después de guardar un valor numérico en la ficha con guardar_ficha,
SIEMPRE usa esta herramienta para verificar si cumple algún umbral SEIA.

El resultado indica si el proyecto ingresaría al SEIA por ese parámetro específico."""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        """Establece la sesión de base de datos."""
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tipo_proyecto_codigo": {
                    "type": "string",
                    "description": "Código del tipo de proyecto",
                    "enum": [
                        "mineria", "energia", "inmobiliario", "acuicultura",
                        "infraestructura", "portuario", "forestal", "agroindustria"
                    ],
                },
                "parametros": {
                    "type": "object",
                    "description": "Parámetros a evaluar (ej: {\"tonelaje_mensual\": 6000})",
                    "additionalProperties": {
                        "type": "number"
                    },
                },
                "subtipo_codigo": {
                    "type": "string",
                    "description": "Código del subtipo (opcional)",
                },
            },
            "required": ["tipo_proyecto_codigo", "parametros"],
        }

    async def ejecutar(
        self,
        tipo_proyecto_codigo: str,
        parametros: Dict[str, float],
        subtipo_codigo: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Evalúa si los parámetros cumplen umbrales SEIA."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesión de base de datos disponible"
            )

        try:
            from app.services.config_industria import get_config_industria_service

            service = get_config_industria_service(db)
            resultado = await service.evaluar_umbral(
                tipo_proyecto_codigo,
                parametros,
                subtipo_codigo
            )

            if not resultado:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"No se pudo evaluar umbral para '{tipo_proyecto_codigo}'"
                )

            # Preparar respuesta detallada
            umbral_info = None
            if resultado.umbral_evaluado:
                u = resultado.umbral_evaluado
                umbral_info = {
                    "parametro": u.parametro,
                    "operador": u.operador,
                    "valor_umbral": float(u.valor),
                    "unidad": u.unidad,
                    "norma_referencia": u.norma_referencia,
                }

            respuesta = {
                "cumple_umbral": resultado.cumple_umbral,
                "resultado": resultado.resultado.value if hasattr(resultado.resultado, 'value') else resultado.resultado,
                "valor_proyecto": resultado.valor_proyecto,
                "diferencia": resultado.diferencia,
                "umbral_evaluado": umbral_info,
                "mensaje": resultado.mensaje,
                "recomendacion": self._generar_recomendacion(resultado),
            }

            logger.info(
                f"Umbral evaluado: {tipo_proyecto_codigo}, "
                f"parametros={parametros}, cumple={resultado.cumple_umbral}"
            )

            return ResultadoHerramienta(
                exito=True,
                contenido=respuesta,
                metadata={
                    "tipo_proyecto": tipo_proyecto_codigo,
                    "cumple_umbral": resultado.cumple_umbral,
                }
            )

        except Exception as e:
            logger.error(f"Error evaluando umbral SEIA: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al evaluar umbral: {str(e)}"
            )

    def _generar_recomendacion(self, resultado) -> str:
        """Genera recomendación basada en el resultado."""
        if resultado.cumple_umbral:
            if resultado.resultado.value == "requiere_eia":
                return (
                    "El proyecto DEBE ingresar al SEIA mediante EIA por este parámetro. "
                    "Continúa recopilando información para identificar otros triggers del Art. 11."
                )
            else:
                return (
                    "El proyecto DEBE ingresar al SEIA por este parámetro. "
                    "Ahora debemos evaluar si corresponde DIA o EIA según el Art. 11."
                )
        else:
            return (
                "Por este parámetro NO ingresaría al SEIA. Sin embargo, puede ingresar "
                "por otras causales (otros umbrales, ubicación en áreas protegidas, etc.). "
                "Continúa evaluando otros parámetros."
            )


@registro_herramientas.registrar
class ObtenerSiguientePregunta(Herramienta):
    """Obtiene la siguiente pregunta del árbol según respuestas previas."""

    nombre = "obtener_siguiente_pregunta"
    descripcion = """Obtiene la siguiente pregunta a hacer al usuario según el árbol configurado.
Usa esta herramienta para guiar la recopilación de información de forma ordenada.

El árbol de preguntas está configurado por tipo/subtipo de proyecto y considera
las respuestas previas para activar preguntas condicionales.

Las respuestas deben proporcionarse como un diccionario donde las claves son
los códigos de las preguntas ya respondidas."""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        """Establece la sesión de base de datos."""
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tipo_proyecto_codigo": {
                    "type": "string",
                    "description": "Código del tipo de proyecto",
                    "enum": [
                        "mineria", "energia", "inmobiliario", "acuicultura",
                        "infraestructura", "portuario", "forestal", "agroindustria"
                    ],
                },
                "respuestas_previas": {
                    "type": "object",
                    "description": "Respuestas ya recopiladas (codigo_pregunta: valor)",
                    "additionalProperties": True,
                },
                "subtipo_codigo": {
                    "type": "string",
                    "description": "Código del subtipo (opcional)",
                },
            },
            "required": ["tipo_proyecto_codigo", "respuestas_previas"],
        }

    async def ejecutar(
        self,
        tipo_proyecto_codigo: str,
        respuestas_previas: Dict[str, Any],
        subtipo_codigo: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Obtiene la siguiente pregunta del árbol."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesión de base de datos disponible"
            )

        try:
            from app.services.config_industria import get_config_industria_service

            service = get_config_industria_service(db)

            # Obtener siguiente pregunta
            pregunta = await service.get_siguiente_pregunta(
                tipo_proyecto_codigo,
                respuestas_previas,
                subtipo_codigo
            )

            # Calcular progreso
            respondidas, total = await service.calcular_progreso(
                tipo_proyecto_codigo,
                respuestas_previas,
                subtipo_codigo
            )

            if not pregunta:
                return ResultadoHerramienta(
                    exito=True,
                    contenido={
                        "hay_siguiente": False,
                        "recopilacion_completa": True,
                        "preguntas_respondidas": respondidas,
                        "total_preguntas": total,
                        "progreso_porcentaje": 100 if total == 0 else round((respondidas / total) * 100),
                        "mensaje": "Se completó la recopilación de información. "
                                  "Puedes proceder con el análisis de prefactibilidad.",
                    },
                    metadata={
                        "tipo_proyecto": tipo_proyecto_codigo,
                        "recopilacion_completa": True,
                    }
                )

            # Preparar información de la pregunta
            resultado = {
                "hay_siguiente": True,
                "recopilacion_completa": False,
                "pregunta": {
                    "codigo": pregunta.codigo,
                    "texto": pregunta.pregunta_texto,
                    "tipo_respuesta": pregunta.tipo_respuesta.value if hasattr(pregunta.tipo_respuesta, 'value') else pregunta.tipo_respuesta,
                    "opciones": pregunta.opciones,
                    "es_obligatoria": pregunta.es_obligatoria,
                    "valida_umbral": pregunta.valida_umbral,
                    "campo_destino": pregunta.campo_destino,
                    "categoria_destino": pregunta.categoria_destino,
                    "ayuda": pregunta.ayuda,
                },
                "preguntas_respondidas": respondidas,
                "total_preguntas": total,
                "progreso_porcentaje": round((respondidas / total) * 100) if total > 0 else 0,
                "mensaje": f"Pregunta {respondidas + 1} de {total}",
            }

            # Agregar indicación si la respuesta debe evaluar umbral
            if pregunta.valida_umbral:
                resultado["nota"] = (
                    "IMPORTANTE: Esta pregunta corresponde a un parámetro de umbral SEIA. "
                    "Después de guardar la respuesta, usa 'evaluar_umbral_seia' para "
                    "verificar si cumple el umbral de ingreso."
                )

            logger.info(
                f"Siguiente pregunta: {pregunta.codigo} "
                f"(progreso: {respondidas}/{total})"
            )

            return ResultadoHerramienta(
                exito=True,
                contenido=resultado,
                metadata={
                    "tipo_proyecto": tipo_proyecto_codigo,
                    "pregunta_codigo": pregunta.codigo,
                    "progreso": f"{respondidas}/{total}",
                }
            )

        except Exception as e:
            logger.error(f"Error obteniendo siguiente pregunta: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al obtener siguiente pregunta: {str(e)}"
            )
