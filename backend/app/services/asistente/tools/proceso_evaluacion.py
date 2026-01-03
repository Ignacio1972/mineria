"""
Herramientas del Asistente IA para Gestion de Proceso de Evaluacion SEIA.

Incluye:
- Consulta de estado del proceso
- Registro de ICSARA y observaciones
- Registro de Adendas y respuestas
- Actualizacion de estados
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.proceso_evaluacion.service import ProcesoEvaluacionService
from app.db.models.proceso_evaluacion import OAECAS_MINERIA

from .base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    ContextoHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)

logger = logging.getLogger(__name__)


# =============================================================================
# HERRAMIENTAS DE CONSULTA
# =============================================================================

@registro_herramientas.registrar
class ConsultarProcesoEvaluacion(Herramienta):
    """Consulta el estado del proceso de evaluación SEIA de un proyecto."""

    nombre = "consultar_proceso_evaluacion"
    descripcion = """
    Consulta el estado del proceso de evaluación ambiental SEIA de un proyecto.

    Retorna:
    - Estado administrativo actual (ingresado, en evaluación, RCA, etc.)
    - Plazos legales y días transcurridos/restantes
    - ICSARA emitidos con sus observaciones
    - Adendas presentadas y su estado
    - Próximos pasos y fechas límite
    - Alertas si hay plazos próximos a vencer

    Usa esta herramienta cuando el usuario pregunte:
    - ¿En qué estado está la evaluación del proyecto?
    - ¿Cuántos días quedan de plazo?
    - ¿Cuántas observaciones tiene el proyecto?
    - ¿Cuál es el siguiente paso en la evaluación?
    """
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
                    "description": "ID del proyecto a consultar"
                },
                "incluir_observaciones": {
                    "type": "boolean",
                    "description": "Si incluir el detalle de observaciones ICSARA",
                    "default": False
                },
                "incluir_timeline": {
                    "type": "boolean",
                    "description": "Si incluir el timeline de estados",
                    "default": False
                }
            },
            "required": ["proyecto_id"]
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        incluir_observaciones: bool = False,
        incluir_timeline: bool = False,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            service = ProcesoEvaluacionService(db)

            # Obtener resumen del proceso
            resumen = await service.get_resumen_proceso(proyecto_id)

            if not resumen:
                return ResultadoHerramienta(
                    exito=True,
                    contenido={
                        "mensaje": "El proyecto no tiene un proceso de evaluación iniciado",
                        "proyecto_id": proyecto_id,
                        "estado": "no_ingresado",
                        "recomendacion": "Para iniciar el proceso, primero debe ingresar el proyecto al SEIA"
                    }
                )

            resultado = {
                "proyecto_id": resumen.proyecto_id,
                "proyecto_nombre": resumen.proyecto_nombre,
                "estado": {
                    "codigo": resumen.estado_actual,
                    "descripcion": resumen.estado_label,
                },
                "plazos": {
                    "dias_transcurridos": resumen.dias_transcurridos,
                    "dias_restantes": resumen.dias_restantes,
                    "porcentaje_plazo": round(resumen.porcentaje_plazo, 1),
                    "fecha_ingreso": resumen.fecha_ingreso.isoformat() if resumen.fecha_ingreso else None,
                },
                "icsara": {
                    "total": resumen.total_icsara,
                    "actual": resumen.icsara_actual,
                    "observaciones_totales": resumen.observaciones_totales,
                    "observaciones_pendientes": resumen.observaciones_pendientes,
                    "observaciones_resueltas": resumen.observaciones_resueltas,
                    "por_organismo": resumen.observaciones_por_oaeca,
                    "organismos_criticos": resumen.oaeca_criticos,
                },
                "adendas": {
                    "total": resumen.total_adendas,
                    "ultima_fecha": resumen.ultima_adenda_fecha.isoformat() if resumen.ultima_adenda_fecha else None,
                },
                "proxima_accion": resumen.proxima_accion,
                "fecha_limite": resumen.fecha_limite.isoformat() if resumen.fecha_limite else None,
                "alerta": resumen.alerta,
            }

            # Incluir timeline si se solicita
            if incluir_timeline:
                timeline = await service.get_timeline_evaluacion(proyecto_id)
                resultado["timeline"] = {
                    "estados": [e.model_dump() for e in timeline.estados],
                    "progreso_porcentaje": timeline.progreso_porcentaje,
                }

            # Incluir observaciones detalladas si se solicita
            if incluir_observaciones:
                proceso = await service.get_proceso_by_proyecto(proyecto_id)
                if proceso and proceso.icsaras:
                    observaciones_detalle = []
                    for icsara in proceso.icsaras:
                        for obs in (icsara.observaciones or []):
                            observaciones_detalle.append({
                                "icsara": icsara.numero_icsara,
                                **obs
                            })
                    resultado["observaciones_detalle"] = observaciones_detalle

            return ResultadoHerramienta(
                exito=True,
                contenido=resultado,
                metadata={"tipo": "proceso_evaluacion"}
            )

        except Exception as e:
            logger.error(f"Error consultando proceso de evaluación: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ConsultarEstadisticasICSARA(Herramienta):
    """Consulta estadísticas detalladas de observaciones ICSARA."""

    nombre = "consultar_estadisticas_icsara"
    descripcion = """
    Obtiene estadísticas detalladas de las observaciones ICSARA del proyecto.

    Retorna:
    - Total de observaciones
    - Distribución por tipo (ampliación, aclaración, rectificación)
    - Distribución por prioridad (crítica, importante, menor)
    - Distribución por organismo (OAECA)
    - Distribución por capítulo del EIA
    - Estado de las observaciones (pendientes, resueltas)

    Útil para entender dónde están los principales focos de observaciones.
    """
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
                    "description": "ID del proyecto"
                }
            },
            "required": ["proyecto_id"]
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            service = ProcesoEvaluacionService(db)
            stats = await service.get_estadisticas_icsara(proyecto_id)

            if not stats:
                return ResultadoHerramienta(
                    exito=True,
                    contenido={
                        "mensaje": "No hay observaciones ICSARA registradas para este proyecto",
                        "proyecto_id": proyecto_id
                    }
                )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto_id,
                    "total_observaciones": stats.total_observaciones,
                    "por_tipo": stats.por_tipo,
                    "por_prioridad": stats.por_prioridad,
                    "por_organismo": stats.por_oaeca,
                    "por_capitulo": stats.por_capitulo,
                    "por_estado": stats.por_estado,
                    "organismo_mas_observaciones": stats.oaeca_mas_observaciones,
                    "capitulo_mas_observaciones": stats.capitulo_mas_observaciones,
                }
            )

        except Exception as e:
            logger.error(f"Error consultando estadísticas ICSARA: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


# =============================================================================
# HERRAMIENTAS DE ACCIÓN
# =============================================================================

@registro_herramientas.registrar
class IniciarProcesoEvaluacion(Herramienta):
    """Inicia el proceso de evaluación SEIA para un proyecto."""

    nombre = "iniciar_proceso_evaluacion"
    descripcion = """
    Inicia el proceso de evaluación ambiental SEIA para un proyecto.

    Registra:
    - Fecha de ingreso al SEIA
    - Plazo legal de evaluación (120 días para EIA, 60 para DIA)
    - Estado inicial como "ingresado"

    IMPORTANTE: Esta acción requiere confirmación del usuario.
    Solo usar cuando el proyecto efectivamente se ha ingresado al e-SEIA.
    """
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
                    "description": "ID del proyecto"
                },
                "fecha_ingreso": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha de ingreso al SEIA (YYYY-MM-DD)"
                },
                "instrumento": {
                    "type": "string",
                    "enum": ["EIA", "DIA"],
                    "description": "Tipo de instrumento (determina plazo legal)"
                }
            },
            "required": ["proyecto_id", "fecha_ingreso", "instrumento"]
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        fecha_ingreso: str,
        instrumento: str,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            fecha = date.fromisoformat(fecha_ingreso)
            plazo = 120 if instrumento == "EIA" else 60

            service = ProcesoEvaluacionService(db)
            proceso = await service.iniciar_proceso(
                proyecto_id=proyecto_id,
                fecha_ingreso=fecha,
                plazo_legal_dias=plazo
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "mensaje": f"Proceso de evaluación iniciado exitosamente",
                    "proceso_id": proceso.id,
                    "proyecto_id": proyecto_id,
                    "instrumento": instrumento,
                    "fecha_ingreso": fecha_ingreso,
                    "plazo_legal_dias": plazo,
                    "estado": "ingresado"
                }
            )

        except ValueError as e:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Error iniciando proceso de evaluación: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class RegistrarICSARA(Herramienta):
    """Registra un nuevo ICSARA con sus observaciones."""

    nombre = "registrar_icsara"
    descripcion = """
    Registra un nuevo ICSARA (Informe Consolidado de Solicitud de Aclaraciones,
    Rectificaciones y Ampliaciones) con sus observaciones.

    El ICSARA contiene las observaciones de los organismos con competencia
    ambiental (OAECA) como SERNAGEOMIN, DGA, SAG, CONAF, SEREMI Salud, etc.

    Parámetros:
    - numero: Número de ICSARA (1, 2, o excepcionalmente 3)
    - fecha_emision: Fecha en que se emitió el ICSARA
    - fecha_limite: Fecha límite para presentar la Adenda
    - observaciones: Lista de observaciones (opcional, se pueden agregar después)

    IMPORTANTE: Esta acción requiere confirmación del usuario.
    """
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
                    "description": "ID del proyecto"
                },
                "numero": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 3,
                    "description": "Número de ICSARA (1, 2, o 3)"
                },
                "fecha_emision": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha de emisión del ICSARA (YYYY-MM-DD)"
                },
                "fecha_limite": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha límite para responder (YYYY-MM-DD)"
                },
                "observaciones": {
                    "type": "array",
                    "description": "Lista de observaciones",
                    "items": {
                        "type": "object",
                        "properties": {
                            "oaeca": {
                                "type": "string",
                                "description": "Organismo que emite la observación"
                            },
                            "capitulo_eia": {
                                "type": "integer",
                                "description": "Capítulo del EIA (1-11)"
                            },
                            "tipo": {
                                "type": "string",
                                "enum": ["ampliacion", "aclaracion", "rectificacion"]
                            },
                            "texto": {
                                "type": "string",
                                "description": "Texto de la observación"
                            },
                            "prioridad": {
                                "type": "string",
                                "enum": ["critica", "importante", "menor"]
                            }
                        }
                    }
                }
            },
            "required": ["proyecto_id", "numero", "fecha_emision", "fecha_limite"]
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        numero: int,
        fecha_emision: str,
        fecha_limite: str,
        observaciones: Optional[List[Dict[str, Any]]] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            fecha_em = date.fromisoformat(fecha_emision)
            fecha_lim = date.fromisoformat(fecha_limite)

            service = ProcesoEvaluacionService(db)

            # Obtener proceso
            proceso = await service.get_proceso_by_proyecto(proyecto_id)
            if not proceso:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="El proyecto no tiene un proceso de evaluación iniciado"
                )

            icsara = await service.registrar_icsara(
                proceso_id=proceso.id,
                numero=numero,
                fecha_emision=fecha_em,
                fecha_limite_respuesta=fecha_lim,
                observaciones=observaciones
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "mensaje": f"ICSARA #{numero} registrado exitosamente",
                    "icsara_id": icsara.id,
                    "numero_icsara": icsara.numero_icsara,
                    "fecha_emision": fecha_emision,
                    "fecha_limite": fecha_limite,
                    "total_observaciones": icsara.total_observaciones,
                    "dias_para_responder": icsara.dias_para_responder,
                }
            )

        except ValueError as e:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Error registrando ICSARA: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class RegistrarAdenda(Herramienta):
    """Registra una Adenda como respuesta a un ICSARA."""

    nombre = "registrar_adenda"
    descripcion = """
    Registra una Adenda (documento de respuesta) a un ICSARA.

    La Adenda contiene las respuestas del titular a las observaciones
    de los organismos. Puede incluir nuevos estudios, aclaraciones,
    y referencias a anexos complementarios.

    Parámetros:
    - icsara_id: ID del ICSARA que responde
    - numero: Número de Adenda
    - fecha_presentacion: Fecha de presentación
    - respuestas: Lista de respuestas a observaciones

    IMPORTANTE: Esta acción requiere confirmación del usuario.
    """
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
                "icsara_id": {
                    "type": "integer",
                    "description": "ID del ICSARA que responde"
                },
                "numero": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Número de Adenda"
                },
                "fecha_presentacion": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha de presentación (YYYY-MM-DD)"
                },
                "respuestas": {
                    "type": "array",
                    "description": "Lista de respuestas a observaciones",
                    "items": {
                        "type": "object",
                        "properties": {
                            "observacion_id": {
                                "type": "string",
                                "description": "ID de la observación que responde"
                            },
                            "respuesta": {
                                "type": "string",
                                "description": "Texto de la respuesta"
                            },
                            "anexos_referenciados": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Códigos de anexos"
                            },
                            "estado": {
                                "type": "string",
                                "enum": ["respondida", "parcial", "no_respondida"]
                            }
                        }
                    }
                }
            },
            "required": ["icsara_id", "numero", "fecha_presentacion"]
        }

    async def ejecutar(
        self,
        icsara_id: int,
        numero: int,
        fecha_presentacion: str,
        respuestas: Optional[List[Dict[str, Any]]] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            fecha = date.fromisoformat(fecha_presentacion)

            service = ProcesoEvaluacionService(db)
            adenda = await service.registrar_adenda(
                icsara_id=icsara_id,
                numero=numero,
                fecha_presentacion=fecha,
                respuestas=respuestas
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "mensaje": f"Adenda #{numero} registrada exitosamente",
                    "adenda_id": adenda.id,
                    "numero_adenda": adenda.numero_adenda,
                    "fecha_presentacion": fecha_presentacion,
                    "total_respuestas": adenda.total_respuestas,
                    "observaciones_resueltas": adenda.observaciones_resueltas,
                    "observaciones_pendientes": adenda.observaciones_pendientes,
                }
            )

        except ValueError as e:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Error registrando Adenda: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ActualizarEstadoObservacion(Herramienta):
    """Actualiza el estado de una observación ICSARA."""

    nombre = "actualizar_estado_observacion"
    descripcion = """
    Actualiza el estado de una observación específica del ICSARA.

    Estados posibles:
    - pendiente: Aún no respondida
    - respondida: Respuesta completa presentada
    - parcial: Respuesta parcial, requiere más información

    IMPORTANTE: Esta acción requiere confirmación del usuario.
    """
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
                "icsara_id": {
                    "type": "integer",
                    "description": "ID del ICSARA"
                },
                "observacion_id": {
                    "type": "string",
                    "description": "ID de la observación (ej: OBS-001)"
                },
                "estado": {
                    "type": "string",
                    "enum": ["pendiente", "respondida", "parcial"],
                    "description": "Nuevo estado de la observación"
                }
            },
            "required": ["icsara_id", "observacion_id", "estado"]
        }

    async def ejecutar(
        self,
        icsara_id: int,
        observacion_id: str,
        estado: str,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            service = ProcesoEvaluacionService(db)
            icsara = await service.actualizar_estado_observacion(
                icsara_id=icsara_id,
                observacion_id=observacion_id,
                nuevo_estado=estado
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "mensaje": f"Observación {observacion_id} actualizada a estado '{estado}'",
                    "icsara_id": icsara_id,
                    "observacion_id": observacion_id,
                    "nuevo_estado": estado,
                    "observaciones_pendientes": icsara.observaciones_pendientes_count,
                    "observaciones_resueltas": icsara.observaciones_resueltas,
                }
            )

        except ValueError as e:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Error actualizando observación: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class RegistrarRCA(Herramienta):
    """Registra la Resolución de Calificación Ambiental (RCA)."""

    nombre = "registrar_rca"
    descripcion = """
    Registra la Resolución de Calificación Ambiental (RCA) final del proyecto.

    Resultados posibles:
    - favorable: Proyecto aprobado sin condiciones adicionales
    - favorable_con_condiciones: Aprobado con condiciones específicas
    - desfavorable: Proyecto rechazado

    Puede incluir condiciones de la RCA (si aplica).

    IMPORTANTE: Esta acción requiere confirmación del usuario.
    Esta es la resolución final del proceso de evaluación.
    """
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
                    "description": "ID del proyecto"
                },
                "resultado": {
                    "type": "string",
                    "enum": ["favorable", "favorable_con_condiciones", "desfavorable"],
                    "description": "Resultado de la RCA"
                },
                "numero_rca": {
                    "type": "string",
                    "description": "Número de la RCA"
                },
                "fecha": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha de la RCA (YYYY-MM-DD)"
                },
                "condiciones": {
                    "type": "array",
                    "description": "Condiciones de la RCA (si aplica)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "numero": {"type": "integer"},
                            "descripcion": {"type": "string"},
                            "plazo": {"type": "string"}
                        }
                    }
                },
                "url": {
                    "type": "string",
                    "description": "URL del documento RCA"
                }
            },
            "required": ["proyecto_id", "resultado", "numero_rca", "fecha"]
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        resultado: str,
        numero_rca: str,
        fecha: str,
        condiciones: Optional[List[Dict[str, Any]]] = None,
        url: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            fecha_rca = date.fromisoformat(fecha)

            service = ProcesoEvaluacionService(db)

            # Obtener proceso
            proceso = await service.get_proceso_by_proyecto(proyecto_id)
            if not proceso:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="El proyecto no tiene un proceso de evaluación"
                )

            proceso = await service.registrar_rca(
                proceso_id=proceso.id,
                resultado=resultado,
                numero_rca=numero_rca,
                fecha=fecha_rca,
                condiciones=condiciones,
                url=url
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "mensaje": f"RCA registrada exitosamente",
                    "proyecto_id": proyecto_id,
                    "numero_rca": numero_rca,
                    "resultado": resultado,
                    "fecha": fecha,
                    "estado_proceso": proceso.estado_evaluacion,
                    "condiciones": len(condiciones) if condiciones else 0,
                }
            )

        except ValueError as e:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Error registrando RCA: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ListarOAECAS(Herramienta):
    """Lista los organismos con competencia ambiental (OAECA)."""

    nombre = "listar_oaecas"
    descripcion = """
    Lista los Organismos con Competencia Ambiental (OAECA) que participan
    en la evaluación ambiental de proyectos mineros.

    Útil para:
    - Identificar qué organismos pueden emitir observaciones
    - Conocer las competencias de cada organismo
    """
    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.AMBOS
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def ejecutar(self, **kwargs) -> ResultadoHerramienta:
        oaecas_info = {
            "SERNAGEOMIN": {
                "nombre_completo": "Servicio Nacional de Geología y Minería",
                "competencias": ["Geología", "Relaves", "Botaderos", "Plan de cierre minero"]
            },
            "DGA": {
                "nombre_completo": "Dirección General de Aguas",
                "competencias": ["Recursos hídricos", "Derechos de agua", "Hidrogeología"]
            },
            "SAG": {
                "nombre_completo": "Servicio Agrícola y Ganadero",
                "competencias": ["Flora", "Fauna", "Suelos agrícolas", "Subdivisión predios"]
            },
            "CONAF": {
                "nombre_completo": "Corporación Nacional Forestal",
                "competencias": ["Bosques", "Áreas silvestres protegidas", "Flora nativa"]
            },
            "SEREMI Salud": {
                "nombre_completo": "Secretaría Regional Ministerial de Salud",
                "competencias": ["Residuos", "Aguas servidas", "Ruido", "Calidad del aire"]
            },
            "SEREMI MMA": {
                "nombre_completo": "Secretaría Regional Ministerial del Medio Ambiente",
                "competencias": ["Coordinación", "Biodiversidad", "Áreas protegidas"]
            },
            "CMN": {
                "nombre_completo": "Consejo de Monumentos Nacionales",
                "competencias": ["Patrimonio arqueológico", "Patrimonio histórico"]
            },
            "CONADI": {
                "nombre_completo": "Corporación Nacional de Desarrollo Indígena",
                "competencias": ["Pueblos indígenas", "Tierras indígenas", "CPLI"]
            },
            "Municipalidad": {
                "nombre_completo": "Municipalidad respectiva",
                "competencias": ["Uso de suelo", "Planificación territorial"]
            },
            "SERNATUR": {
                "nombre_completo": "Servicio Nacional de Turismo",
                "competencias": ["Turismo", "ZOIT (Zonas de Interés Turístico)"]
            },
        }

        return ResultadoHerramienta(
            exito=True,
            contenido={
                "oaecas": oaecas_info,
                "total": len(oaecas_info),
                "nota": "Estos son los principales OAECA para proyectos mineros. Pueden participar otros organismos según las características específicas del proyecto."
            }
        )
