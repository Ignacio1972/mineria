"""
Herramientas del asistente para Estructura EIA (Fase 2).

Incluye:
- generar_estructura_eia: Genera estructura completa del EIA
- consultar_capitulos_eia: Consulta capítulos y estado
- consultar_plan_linea_base: Consulta plan de línea base
- estimar_complejidad_proyecto: Estima complejidad del EIA
"""
import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    ContextoHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)
from app.db.models import Proyecto
from app.db.models.proyecto_extendido import ProyectoDiagnostico
from app.services.estructura_eia.service import EstructuraEIAService

logger = logging.getLogger(__name__)


# =============================================================================
# generar_estructura_eia (Acción)
# =============================================================================

@registro_herramientas.registrar
class GenerarEstructuraEIA(Herramienta):
    """Genera la estructura completa del EIA para un proyecto."""

    nombre = "generar_estructura_eia"
    descripcion = """Genera la estructura completa del EIA (Estudio de Impacto Ambiental) para el proyecto.

Usa esta herramienta cuando:
- El usuario quiera ver o generar la estructura del EIA
- Se haya completado la recopilación de información básica (prefactibilidad >= 70%)
- Se quiera planificar el desarrollo del estudio
- El diagnóstico indique que el proyecto requiere EIA (via_sugerida = EIA)

IMPORTANTE: Cuando detectes que la prefactibilidad está completa (via_sugerida=EIA y progreso>=70%),
SUGIERE PROACTIVAMENTE generar la estructura del EIA.

Genera:
- 11 capítulos según Art. 18 DS 40 adaptados al tipo de proyecto
- Lista de PAS (Permisos Ambientales Sectoriales) requeridos
- Lista de anexos técnicos requeridos
- Plan de línea base con componentes y metodologías
- Estimación de complejidad (tiempo, recursos, riesgos)

NOTA: Esta acción requiere confirmación del usuario."""

    categoria = CategoriaHerramienta.ACCION
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = True
    permisos = [PermisoHerramienta.ESCRITURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "proyecto_id": {
                    "type": "integer",
                    "description": "ID del proyecto para el cual generar la estructura EIA",
                },
                "forzar_regenerar": {
                    "type": "boolean",
                    "description": "Si es true, regenera la estructura aunque ya exista una versión previa",
                    "default": False,
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        forzar_regenerar: bool = False,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta la generación de estructura EIA."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesión de base de datos disponible"
            )

        try:
            # Verificar que el proyecto existe
            result = await db.execute(
                select(Proyecto).where(Proyecto.id == proyecto_id)
            )
            proyecto = result.scalar()

            if not proyecto:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Proyecto con ID {proyecto_id} no encontrado"
                )

            # Verificar que tiene tipo de proyecto asignado
            if not proyecto.tipo_proyecto_id:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"El proyecto '{proyecto.nombre}' no tiene tipo de proyecto asignado. "
                          f"Primero debe configurar el tipo de proyecto (minería, energía, etc.)."
                )

            # Generar estructura
            service = EstructuraEIAService(db)
            estructura = await service.generar_estructura(
                proyecto_id=proyecto_id,
                forzar_regenerar=forzar_regenerar
            )

            if not estructura:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="No se pudo generar la estructura EIA"
                )

            # Preparar resumen para el asistente
            capitulos_info = [
                f"Cap. {c.numero}: {c.titulo} ({c.estado.value})"
                for c in estructura.capitulos[:5]
            ]

            pas_criticos = [
                f"Art. {p.articulo}: {p.nombre} ({p.estado.value})"
                for p in estructura.pas_requeridos
                if p.obligatoriedad.value == "obligatorio"
            ][:5]

            complejidad_info = {}
            if estructura.estimacion_complejidad:
                est = estructura.estimacion_complejidad
                complejidad_info = {
                    "nivel": est.nivel.value,
                    "puntaje": est.puntaje,
                    "tiempo_estimado_meses": est.tiempo_estimado_meses,
                    "riesgos_principales": est.riesgos_principales[:3],
                    "recomendaciones": est.recomendaciones[:3],
                }

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto_id,
                    "proyecto_nombre": proyecto.nombre,
                    "estructura_id": estructura.id,
                    "version": estructura.version,
                    "mensaje": f"Estructura EIA v{estructura.version} generada exitosamente para '{proyecto.nombre}'",
                    "resumen": {
                        "total_capitulos": len(estructura.capitulos),
                        "total_pas": len(estructura.pas_requeridos),
                        "total_anexos": len(estructura.anexos_requeridos),
                        "total_componentes_lb": len(estructura.plan_linea_base),
                        "progreso_general": estructura.progreso_general,
                    },
                    "capitulos_muestra": capitulos_info,
                    "pas_obligatorios": pas_criticos,
                    "complejidad": complejidad_info,
                    "siguiente_paso": "Puedes usar 'consultar_capitulos_eia' o 'consultar_plan_linea_base' "
                                     "para ver más detalles, o empezar a trabajar en los capítulos pendientes.",
                },
                metadata={
                    "proyecto_id": proyecto_id,
                    "estructura_id": estructura.id,
                    "version": estructura.version,
                    "accion": "generar_estructura_eia",
                }
            )

        except Exception as e:
            logger.error(f"Error generando estructura EIA: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al generar estructura EIA: {str(e)}"
            )

    def generar_descripcion_confirmacion(self, **kwargs) -> str:
        """Genera descripción para confirmación."""
        proyecto_id = kwargs.get("proyecto_id", "?")
        proyecto_nombre = kwargs.get("_proyecto_nombre")
        forzar = kwargs.get("forzar_regenerar", False)

        if proyecto_nombre:
            if forzar:
                return f"Regenerar estructura EIA para el proyecto '{proyecto_nombre}' (creará nueva versión)"
            return f"Generar estructura EIA para el proyecto '{proyecto_nombre}'"
        return f"Generar estructura EIA para proyecto ID {proyecto_id}"


# =============================================================================
# consultar_capitulos_eia (Consulta)
# =============================================================================

@registro_herramientas.registrar
class ConsultarCapitulosEIA(Herramienta):
    """Consulta los capítulos del EIA y su estado."""

    nombre = "consultar_capitulos_eia"
    descripcion = """Consulta los capítulos del EIA generados para el proyecto.

Usa esta herramienta cuando:
- El usuario quiera ver el estado de los capítulos del EIA
- Se necesite saber qué capítulos están pendientes, en progreso o completados
- Se quiera ver el contenido requerido de cada capítulo
- El usuario pregunte sobre algún capítulo específico

Retorna la lista de los 11 capítulos con:
- Estado (pendiente, en_progreso, completado)
- Progreso porcentual
- Secciones requeridas
- Notas adicionales"""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "proyecto_id": {
                    "type": "integer",
                    "description": "ID del proyecto",
                },
                "capitulo_numero": {
                    "type": "integer",
                    "description": "Número del capítulo específico a consultar (1-11). Si no se especifica, retorna todos.",
                    "minimum": 1,
                    "maximum": 11,
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        capitulo_numero: Optional[int] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Consulta los capítulos del EIA."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesión de base de datos disponible"
            )

        try:
            service = EstructuraEIAService(db)
            estructura = await service.get_estructura_proyecto(proyecto_id)

            if not estructura:
                return ResultadoHerramienta(
                    exito=True,
                    contenido={
                        "existe_estructura": False,
                        "mensaje": "No existe estructura EIA para este proyecto. "
                                  "Usa 'generar_estructura_eia' para crearla.",
                        "sugerencia": "generar_estructura_eia",
                    }
                )

            # Si se pidió un capítulo específico
            if capitulo_numero:
                capitulo = next(
                    (c for c in (estructura.capitulos or []) if c.get("numero") == capitulo_numero),
                    None
                )
                if not capitulo:
                    return ResultadoHerramienta(
                        exito=False,
                        contenido=None,
                        error=f"Capítulo {capitulo_numero} no encontrado"
                    )

                return ResultadoHerramienta(
                    exito=True,
                    contenido={
                        "proyecto_id": proyecto_id,
                        "capitulo": {
                            "numero": capitulo.get("numero"),
                            "titulo": capitulo.get("titulo"),
                            "descripcion": capitulo.get("descripcion"),
                            "estado": capitulo.get("estado"),
                            "progreso_porcentaje": capitulo.get("progreso_porcentaje", 0),
                            "es_obligatorio": capitulo.get("es_obligatorio", True),
                            "contenido_requerido": capitulo.get("contenido_requerido", []),
                            "secciones_completadas": capitulo.get("secciones_completadas", 0),
                            "secciones_totales": capitulo.get("secciones_totales", 0),
                            "notas": capitulo.get("notas"),
                        },
                    }
                )

            # Retornar todos los capítulos con resumen
            capitulos = estructura.capitulos or []
            completados = sum(1 for c in capitulos if c.get("estado") == "completado")
            en_progreso = sum(1 for c in capitulos if c.get("estado") == "en_progreso")
            pendientes = len(capitulos) - completados - en_progreso

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto_id,
                    "version": estructura.version,
                    "progreso_general": estructura.progreso_general,
                    "resumen": {
                        "total": len(capitulos),
                        "completados": completados,
                        "en_progreso": en_progreso,
                        "pendientes": pendientes,
                    },
                    "capitulos": [
                        {
                            "numero": c.get("numero"),
                            "titulo": c.get("titulo"),
                            "estado": c.get("estado"),
                            "progreso": c.get("progreso_porcentaje", 0),
                            "obligatorio": c.get("es_obligatorio", True),
                        }
                        for c in capitulos
                    ],
                }
            )

        except Exception as e:
            logger.error(f"Error consultando capítulos EIA: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al consultar capítulos: {str(e)}"
            )


# =============================================================================
# consultar_plan_linea_base (Consulta)
# =============================================================================

@registro_herramientas.registrar
class ConsultarPlanLineaBase(Herramienta):
    """Consulta el plan de línea base del proyecto."""

    nombre = "consultar_plan_linea_base"
    descripcion = """Consulta el plan de línea base generado para el EIA.

Usa esta herramienta cuando:
- El usuario quiera saber qué estudios de línea base necesita
- Se necesite conocer las metodologías recomendadas
- Se quiera ver las variables a monitorear por componente
- El usuario pregunte sobre estudios ambientales requeridos

Retorna los componentes de línea base con:
- Nombre del componente (clima, calidad del aire, fauna, etc.)
- Metodología recomendada
- Variables a monitorear
- Estudios técnicos requeridos
- Duración estimada en días
- Si es obligatorio o no"""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "proyecto_id": {
                    "type": "integer",
                    "description": "ID del proyecto",
                },
                "componente": {
                    "type": "string",
                    "description": "Filtrar por nombre de componente (ej: 'clima', 'fauna', 'aire')",
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        componente: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Consulta el plan de línea base."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesión de base de datos disponible"
            )

        try:
            service = EstructuraEIAService(db)
            estructura = await service.get_estructura_proyecto(proyecto_id)

            if not estructura:
                return ResultadoHerramienta(
                    exito=True,
                    contenido={
                        "existe_estructura": False,
                        "mensaje": "No existe estructura EIA para este proyecto. "
                                  "Usa 'generar_estructura_eia' para crearla.",
                    }
                )

            plan_lb = estructura.plan_linea_base or []

            # Filtrar por componente si se especificó
            if componente:
                componente_lower = componente.lower()
                plan_lb = [
                    c for c in plan_lb
                    if componente_lower in c.get("nombre", "").lower() or
                       componente_lower in c.get("codigo", "").lower()
                ]

            # Calcular duración total
            duracion_total = sum(c.get("duracion_estimada_dias", 0) for c in plan_lb)
            obligatorios = sum(1 for c in plan_lb if c.get("es_obligatorio", True))

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto_id,
                    "resumen": {
                        "total_componentes": len(plan_lb),
                        "obligatorios": obligatorios,
                        "duracion_total_dias": duracion_total,
                        "duracion_estimada_meses": round(duracion_total / 30, 1),
                    },
                    "componentes": [
                        {
                            "codigo": c.get("codigo"),
                            "nombre": c.get("nombre"),
                            "descripcion": c.get("descripcion"),
                            "metodologia": c.get("metodologia"),
                            "variables": c.get("variables_monitorear", []),
                            "estudios_requeridos": c.get("estudios_requeridos", []),
                            "duracion_dias": c.get("duracion_estimada_dias"),
                            "obligatorio": c.get("es_obligatorio", True),
                            "prioridad": c.get("prioridad", 1),
                        }
                        for c in plan_lb
                    ],
                    "recomendacion": "Considera iniciar primero los componentes con estacionalidad "
                                    "(flora/fauna) que requieren monitoreo en distintas épocas del año."
                                    if any("fauna" in c.get("nombre", "").lower() or "flora" in c.get("nombre", "").lower() for c in plan_lb)
                                    else None,
                }
            )

        except Exception as e:
            logger.error(f"Error consultando plan línea base: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al consultar plan de línea base: {str(e)}"
            )


# =============================================================================
# estimar_complejidad_proyecto (Consulta)
# =============================================================================

@registro_herramientas.registrar
class EstimarComplejidadProyecto(Herramienta):
    """Estima la complejidad y alcance del EIA."""

    nombre = "estimar_complejidad_proyecto"
    descripcion = """Estima el nivel de complejidad del EIA para el proyecto.

Usa esta herramienta cuando:
- El usuario quiera saber qué tan complejo es su EIA
- Se necesite estimar tiempos y recursos
- El usuario pregunte sobre riesgos o dificultades del proceso
- Se quiera planificar el proyecto de elaboración del EIA

Considera factores como:
- Número de triggers Art. 11 activados
- Ubicación (áreas sensibles, comunidades indígenas)
- Número de PAS requeridos
- Componentes ambientales afectados
- Escala del proyecto

Retorna:
- Nivel de complejidad (baja, media, alta, muy_alta)
- Puntaje (0-100)
- Tiempo estimado en meses
- Recursos sugeridos (profesionales, estudios)
- Riesgos principales
- Recomendaciones"""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "proyecto_id": {
                    "type": "integer",
                    "description": "ID del proyecto",
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Estima la complejidad del EIA."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesión de base de datos disponible"
            )

        try:
            service = EstructuraEIAService(db)
            estructura = await service.get_estructura_proyecto(proyecto_id)

            # Si ya hay estructura, usar la estimación guardada
            if estructura and estructura.estimacion_complejidad:
                est = estructura.estimacion_complejidad

                factores_detalle = [
                    {
                        "nombre": f.get("nombre"),
                        "descripcion": f.get("descripcion"),
                        "contribucion": f.get("contribucion", 0),
                    }
                    for f in est.get("factores", [])
                ]

                recursos = [
                    {
                        "tipo": r.get("tipo"),
                        "nombre": r.get("nombre"),
                        "cantidad": r.get("cantidad", 1),
                        "prioridad": r.get("prioridad"),
                    }
                    for r in est.get("recursos_sugeridos", [])
                ]

                return ResultadoHerramienta(
                    exito=True,
                    contenido={
                        "proyecto_id": proyecto_id,
                        "tiene_estructura": True,
                        "complejidad": {
                            "nivel": est.get("nivel"),
                            "puntaje": est.get("puntaje"),
                            "tiempo_estimado_meses": est.get("tiempo_estimado_meses"),
                        },
                        "factores": factores_detalle,
                        "recursos_sugeridos": recursos,
                        "riesgos": est.get("riesgos_principales", []),
                        "recomendaciones": est.get("recomendaciones", []),
                    }
                )

            # Si no hay estructura, hacer estimación básica
            result = await db.execute(
                select(Proyecto).where(Proyecto.id == proyecto_id)
            )
            proyecto = result.scalar()

            if not proyecto:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Proyecto con ID {proyecto_id} no encontrado"
                )

            # Estimación básica sin estructura
            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto_id,
                    "tiene_estructura": False,
                    "mensaje": "No existe estructura EIA generada. La estimación será más precisa "
                              "después de generar la estructura con 'generar_estructura_eia'.",
                    "complejidad_preliminar": {
                        "nivel": "por_determinar",
                        "nota": "Genera la estructura EIA para obtener una estimación detallada",
                    },
                    "sugerencia": "Usa 'generar_estructura_eia' primero para obtener una estimación precisa "
                                 "basada en el tipo de proyecto, ubicación y características específicas.",
                }
            )

        except Exception as e:
            logger.error(f"Error estimando complejidad: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al estimar complejidad: {str(e)}"
            )
