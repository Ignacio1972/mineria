"""
Herramientas de consulta del asistente.
Acceso a proyectos, analisis y estadisticas.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)

logger = logging.getLogger(__name__)


@registro_herramientas.registrar
class ConsultarProyecto(Herramienta):
    """Obtiene informacion detallada de un proyecto."""

    nombre = "consultar_proyecto"
    descripcion = """Obtiene datos completos de un proyecto incluyendo ubicacion, parametros tecnicos y estado.
Usa esta herramienta cuando el usuario pregunte sobre un proyecto especifico:
- Datos del proyecto
- Estado actual
- Ubicacion
- Parametros tecnicos (superficie, agua, trabajadores, etc.)"""
    categoria = CategoriaHerramienta.CONSULTA
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
        """Obtiene datos del proyecto."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            sql = """
                SELECT
                    p.*,
                    c.razon_social as cliente_razon_social,
                    c.email as cliente_email,
                    ST_AsGeoJSON(p.geom)::json as geometria,
                    (SELECT COUNT(*) FROM proyectos.documentos d WHERE d.proyecto_id = p.id) as total_documentos,
                    (SELECT COUNT(*) FROM proyectos.analisis a WHERE a.proyecto_id = p.id) as total_analisis,
                    (SELECT MAX(fecha_analisis) FROM proyectos.analisis a WHERE a.proyecto_id = p.id) as ultimo_analisis
                FROM proyectos.proyectos p
                LEFT JOIN proyectos.clientes c ON p.cliente_id = c.id
                WHERE p.id = :id
            """

            result = await db.execute(text(sql), {"id": proyecto_id})
            row = result.fetchone()

            if not row:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Proyecto con ID {proyecto_id} no encontrado"
                )

            proyecto = {
                "id": row.id,
                "nombre": row.nombre,
                "estado": row.estado,
                "cliente": {
                    "razon_social": row.cliente_razon_social,
                    "email": row.cliente_email,
                } if row.cliente_razon_social else None,
                "ubicacion": {
                    "region": row.region,
                    "comuna": row.comuna,
                    "tiene_geometria": row.geom is not None,
                },
                "tipo_mineria": row.tipo_mineria,
                "mineral_principal": row.mineral_principal,
                "fase": row.fase,
                "parametros_tecnicos": {
                    "superficie_ha": float(row.superficie_ha) if row.superficie_ha else None,
                    "vida_util_anos": row.vida_util_anos,
                    "uso_agua_lps": float(row.uso_agua_lps) if row.uso_agua_lps else None,
                    "fuente_agua": row.fuente_agua,
                    "energia_mw": float(row.energia_mw) if row.energia_mw else None,
                    "trabajadores_construccion": row.trabajadores_construccion,
                    "trabajadores_operacion": row.trabajadores_operacion,
                    "inversion_musd": float(row.inversion_musd) if row.inversion_musd else None,
                },
                "campos_seia": {
                    "afecta_glaciares": row.afecta_glaciares,
                    "dist_area_protegida_km": float(row.dist_area_protegida_km) if row.dist_area_protegida_km else None,
                    "dist_comunidad_indigena_km": float(row.dist_comunidad_indigena_km) if row.dist_comunidad_indigena_km else None,
                    "dist_centro_poblado_km": float(row.dist_centro_poblado_km) if row.dist_centro_poblado_km else None,
                    "requiere_reasentamiento": row.requiere_reasentamiento,
                    "afecta_patrimonio": row.afecta_patrimonio,
                },
                "estadisticas": {
                    "porcentaje_completado": row.porcentaje_completado,
                    "total_documentos": row.total_documentos,
                    "total_analisis": row.total_analisis,
                    "ultimo_analisis": row.ultimo_analisis.isoformat() if row.ultimo_analisis else None,
                },
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }

            return ResultadoHerramienta(
                exito=True,
                contenido=proyecto,
            )

        except Exception as e:
            logger.error(f"Error consultando proyecto: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ConsultarAnalisis(Herramienta):
    """Obtiene resultados de un analisis de prefactibilidad."""

    nombre = "consultar_analisis"
    descripcion = """Obtiene los resultados completos de un analisis de prefactibilidad.
Usa esta herramienta para:
- Ver clasificacion DIA/EIA
- Ver triggers detectados
- Ver alertas generadas
- Ver resumen del analisis"""
    categoria = CategoriaHerramienta.CONSULTA
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
                "analisis_id": {
                    "type": "integer",
                    "description": "ID del analisis"
                },
                "proyecto_id": {
                    "type": "integer",
                    "description": "ID del proyecto (retorna el ultimo analisis)"
                }
            }
        }

    async def ejecutar(
        self,
        analisis_id: Optional[int] = None,
        proyecto_id: Optional[int] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Obtiene resultados de analisis."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        if not analisis_id and not proyecto_id:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="Debe proporcionar analisis_id o proyecto_id"
            )

        try:
            if analisis_id:
                sql = """
                    SELECT a.*, p.nombre as proyecto_nombre
                    FROM proyectos.analisis a
                    JOIN proyectos.proyectos p ON a.proyecto_id = p.id
                    WHERE a.id = :id
                """
                result = await db.execute(text(sql), {"id": analisis_id})
            else:
                sql = """
                    SELECT a.*, p.nombre as proyecto_nombre
                    FROM proyectos.analisis a
                    JOIN proyectos.proyectos p ON a.proyecto_id = p.id
                    WHERE a.proyecto_id = :proyecto_id
                    ORDER BY a.fecha_analisis DESC
                    LIMIT 1
                """
                result = await db.execute(text(sql), {"proyecto_id": proyecto_id})

            row = result.fetchone()
            if not row:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="Analisis no encontrado"
                )

            analisis = {
                "id": row.id,
                "proyecto_id": row.proyecto_id,
                "proyecto_nombre": row.proyecto_nombre,
                "clasificacion": {
                    "via_ingreso": row.via_ingreso_recomendada,
                    "confianza": row.confianza,
                    "puntaje_matriz": row.puntaje_matriz,
                },
                "triggers_detectados": row.triggers_detectados or [],
                "alertas": row.alertas or [],
                "resumen": row.resumen,
                "recomendaciones": row.recomendaciones,
                "normativa_aplicable": row.normativa_aplicable or [],
                "fecha_analisis": row.fecha_analisis.isoformat() if row.fecha_analisis else None,
            }

            return ResultadoHerramienta(
                exito=True,
                contenido=analisis,
            )

        except Exception as e:
            logger.error(f"Error consultando analisis: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ListarProyectos(Herramienta):
    """Lista proyectos con filtros."""

    nombre = "listar_proyectos"
    descripcion = """Lista proyectos del sistema con filtros opcionales.
Usa esta herramienta cuando el usuario pregunte:
- ¿Cuantos proyectos hay?
- Muestrame los proyectos en Atacama
- Proyectos del cliente X
- Proyectos en estado borrador"""
    categoria = CategoriaHerramienta.CONSULTA
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
                "estado": {
                    "type": "string",
                    "description": "Filtrar por estado",
                    "enum": ["borrador", "completo", "con_geometria", "analizado", "en_revision", "aprobado", "rechazado", "archivado"]
                },
                "region": {
                    "type": "string",
                    "description": "Filtrar por region"
                },
                "busqueda": {
                    "type": "string",
                    "description": "Buscar en nombre del proyecto"
                },
                "limite": {
                    "type": "integer",
                    "description": "Numero maximo de resultados",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                }
            }
        }

    async def ejecutar(
        self,
        estado: Optional[str] = None,
        region: Optional[str] = None,
        busqueda: Optional[str] = None,
        limite: int = 10,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Lista proyectos."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            sql = """
                SELECT
                    p.id,
                    p.nombre,
                    p.estado,
                    p.region,
                    p.comuna,
                    p.tipo_mineria,
                    p.porcentaje_completado,
                    p.geom IS NOT NULL as tiene_geometria,
                    c.razon_social as cliente,
                    (SELECT COUNT(*) FROM proyectos.analisis a WHERE a.proyecto_id = p.id) as total_analisis
                FROM proyectos.proyectos p
                LEFT JOIN proyectos.clientes c ON p.cliente_id = c.id
                WHERE 1=1
            """
            params = {"limite": limite}

            if estado:
                sql += " AND p.estado = :estado"
                params["estado"] = estado

            if region:
                sql += " AND p.region ILIKE :region"
                params["region"] = f"%{region}%"

            if busqueda:
                sql += " AND p.nombre ILIKE :busqueda"
                params["busqueda"] = f"%{busqueda}%"

            sql += " ORDER BY p.updated_at DESC NULLS LAST, p.created_at DESC LIMIT :limite"

            result = await db.execute(text(sql), params)
            rows = result.fetchall()

            proyectos = []
            for row in rows:
                proyectos.append({
                    "id": row.id,
                    "nombre": row.nombre,
                    "estado": row.estado,
                    "region": row.region,
                    "comuna": row.comuna,
                    "tipo_mineria": row.tipo_mineria,
                    "porcentaje_completado": row.porcentaje_completado,
                    "tiene_geometria": row.tiene_geometria,
                    "cliente": row.cliente,
                    "total_analisis": row.total_analisis,
                })

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "total": len(proyectos),
                    "proyectos": proyectos,
                    "filtros_aplicados": {
                        "estado": estado,
                        "region": region,
                        "busqueda": busqueda,
                    }
                },
            )

        except Exception as e:
            logger.error(f"Error listando proyectos: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ObtenerEstadisticas(Herramienta):
    """Obtiene estadisticas del sistema."""

    nombre = "obtener_estadisticas"
    descripcion = """Obtiene estadisticas generales del sistema.
Usa esta herramienta cuando el usuario pregunte:
- ¿Cuantos proyectos hay?
- Estadisticas del sistema
- Resumen de actividad
- ¿Cuantos analisis se han hecho?"""
    categoria = CategoriaHerramienta.CONSULTA
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
                "periodo": {
                    "type": "string",
                    "description": "Periodo para estadisticas",
                    "enum": ["hoy", "semana", "mes", "total"],
                    "default": "total"
                }
            }
        }

    async def ejecutar(
        self,
        periodo: str = "total",
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Obtiene estadisticas."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            # Estadisticas generales
            stats_sql = """
                SELECT
                    (SELECT COUNT(*) FROM proyectos.clientes WHERE activo = TRUE) as total_clientes,
                    (SELECT COUNT(*) FROM proyectos.proyectos WHERE estado != 'archivado') as total_proyectos,
                    (SELECT COUNT(*) FROM proyectos.proyectos WHERE estado = 'borrador') as proyectos_borrador,
                    (SELECT COUNT(*) FROM proyectos.proyectos WHERE estado = 'analizado') as proyectos_analizados,
                    (SELECT COUNT(*) FROM proyectos.analisis) as total_analisis,
                    (SELECT COUNT(*) FROM proyectos.analisis WHERE via_ingreso_recomendada = 'EIA') as total_eia,
                    (SELECT COUNT(*) FROM proyectos.analisis WHERE via_ingreso_recomendada = 'DIA') as total_dia
            """

            result = await db.execute(text(stats_sql))
            row = result.fetchone()

            # Estadisticas por periodo
            periodo_sql = ""
            if periodo == "hoy":
                periodo_sql = "AND a.fecha_analisis >= CURRENT_DATE"
            elif periodo == "semana":
                periodo_sql = "AND a.fecha_analisis >= CURRENT_DATE - INTERVAL '7 days'"
            elif periodo == "mes":
                periodo_sql = "AND a.fecha_analisis >= CURRENT_DATE - INTERVAL '30 days'"

            analisis_periodo_sql = f"""
                SELECT COUNT(*) as analisis_periodo
                FROM proyectos.analisis a
                WHERE 1=1 {periodo_sql}
            """
            result_periodo = await db.execute(text(analisis_periodo_sql))
            analisis_periodo = result_periodo.scalar()

            # Por region
            regiones_sql = """
                SELECT region, COUNT(*) as cantidad
                FROM proyectos.proyectos
                WHERE region IS NOT NULL
                GROUP BY region
                ORDER BY cantidad DESC
                LIMIT 5
            """
            result_regiones = await db.execute(text(regiones_sql))
            por_region = {r.region: r.cantidad for r in result_regiones.fetchall()}

            stats = {
                "periodo": periodo,
                "totales": {
                    "clientes": row.total_clientes,
                    "proyectos": row.total_proyectos,
                    "analisis": row.total_analisis,
                },
                "proyectos_por_estado": {
                    "borrador": row.proyectos_borrador,
                    "analizados": row.proyectos_analizados,
                },
                "clasificaciones": {
                    "EIA": row.total_eia,
                    "DIA": row.total_dia,
                },
                "analisis_en_periodo": analisis_periodo,
                "proyectos_por_region": por_region,
            }

            return ResultadoHerramienta(
                exito=True,
                contenido=stats,
            )

        except Exception as e:
            logger.error(f"Error obteniendo estadisticas: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )
