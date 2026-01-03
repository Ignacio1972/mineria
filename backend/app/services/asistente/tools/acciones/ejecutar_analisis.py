"""
Herramienta para ejecutar analisis de prefactibilidad ambiental.
"""
import logging
import time
import hashlib
import json
from typing import Any, Dict, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

from ..base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    ContextoHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)
from app.db.models import Proyecto
from app.db.models.proyecto import Analisis
from app.db.models.auditoria import AuditoriaAnalisis
from app.core.config import settings

logger = logging.getLogger(__name__)


@registro_herramientas.registrar
class EjecutarAnalisis(Herramienta):
    """Ejecuta un analisis de prefactibilidad ambiental."""

    nombre = "ejecutar_analisis"
    descripcion = """Ejecuta un analisis de prefactibilidad ambiental para un proyecto.
Usa esta herramienta cuando el usuario quiera:
- Analizar un proyecto
- Evaluar si es DIA o EIA
- Ejecutar el analisis de prefactibilidad
- Ver la clasificacion ambiental de un proyecto

IMPORTANTE: Esta accion requiere confirmacion del usuario.
El proyecto debe tener geometria definida para poder analizarse."""

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
                    "description": "ID del proyecto a analizar",
                },
                "tipo_analisis": {
                    "type": "string",
                    "description": "Tipo de analisis: 'rapido' (sin LLM) o 'completo' (con generacion de informe)",
                    "enum": ["rapido", "completo"],
                    "default": "completo",
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        tipo_analisis: str = "completo",
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta el analisis de prefactibilidad."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
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

            # Verificar que tiene geometria
            if not proyecto.geom:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"El proyecto '{proyecto.nombre}' no tiene geometria definida. "
                          f"Primero debe dibujar el area del proyecto en el mapa."
                )

            # Verificar estado
            if proyecto.estado == "archivado":
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="No se puede analizar un proyecto archivado"
                )

            # Ejecutar el analisis delegando a servicios especializados
            return await self._ejecutar_analisis_completo(
                db, proyecto, tipo_analisis
            )

        except Exception as e:
            logger.error(f"Error preparando analisis: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al preparar el analisis: {str(e)}"
            )

    async def _ejecutar_analisis_completo(
        self,
        db: AsyncSession,
        proyecto: Proyecto,
        tipo_analisis: str
    ) -> ResultadoHerramienta:
        """Orquesta la ejecucion del analisis completo."""
        from app.services.gis.analisis import analizar_proyecto_espacial
        from app.services.rag.busqueda import BuscadorLegal
        from app.services.reglas import MotorReglasSSEIA, SistemaAlertas
        from app.services.llm import GeneradorInformes

        inicio_total = time.time()
        logger.info(f"Ejecutando analisis {tipo_analisis} para proyecto_id={proyecto.id}")

        # 1. Convertir geometria a GeoJSON
        try:
            geom_shape = to_shape(proyecto.geom)
            geojson = mapping(geom_shape)
        except Exception as e:
            logger.error(f"Error convirtiendo geometria: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error procesando geometria del proyecto: {str(e)}"
            )

        # 2. Ejecutar analisis espacial GIS
        resultado_gis, tiempo_gis = await self._ejecutar_analisis_gis(db, geojson)

        # 3. Preparar datos del proyecto
        datos_proyecto = self._preparar_datos_proyecto(proyecto, resultado_gis)

        # 4. Ejecutar motor de reglas SEIA
        clasificacion = self._ejecutar_motor_reglas(resultado_gis, datos_proyecto)

        # 5. Generar alertas
        alertas, alertas_dict = self._generar_alertas(resultado_gis, datos_proyecto)

        # 6. Buscar normativa relevante (RAG)
        normativa_relevante, tiempo_rag = await self._buscar_normativa(
            db, clasificacion
        )

        # 7. Generar informe con LLM (solo si tipo=completo)
        informe_dict, tiempo_llm, tokens_usados = await self._generar_informe_llm(
            tipo_analisis, datos_proyecto, resultado_gis, normativa_relevante
        )

        tiempo_total = int((time.time() - inicio_total) * 1000)

        # 8. Persistir analisis y auditoria
        nuevo_analisis = await self._persistir_analisis(
            db, proyecto, tipo_analisis, resultado_gis, clasificacion,
            normativa_relevante, informe_dict, alertas_dict,
            tiempo_gis, tiempo_rag, tiempo_llm, tiempo_total
        )

        # 9. Actualizar estado del proyecto
        await self._actualizar_estado_proyecto(db, proyecto)

        await db.commit()
        await db.refresh(nuevo_analisis)

        logger.info(
            f"Analisis completado: analisis_id={nuevo_analisis.id}, "
            f"via={clasificacion.via_ingreso.value}, tiempo={tiempo_total}ms"
        )

        # Preparar resumen para el asistente
        return self._preparar_resultado(
            proyecto, nuevo_analisis, tipo_analisis, clasificacion,
            alertas, informe_dict, tiempo_total
        )

    async def _ejecutar_analisis_gis(self, db: AsyncSession, geojson: dict) -> tuple:
        """Ejecuta el analisis GIS y retorna resultado y tiempo."""
        from app.services.gis.analisis import analizar_proyecto_espacial

        inicio_gis = time.time()
        logger.info("Ejecutando analisis GIS...")
        resultado_gis = await analizar_proyecto_espacial(db, geojson)
        tiempo_gis = int((time.time() - inicio_gis) * 1000)
        return resultado_gis, tiempo_gis

    def _preparar_datos_proyecto(self, proyecto: Proyecto, resultado_gis: dict) -> dict:
        """Prepara los datos del proyecto para el motor de reglas."""
        ubicacion_gis = resultado_gis.get("ubicacion", {}) or {}
        region_detectada = ubicacion_gis.get("region") or proyecto.region
        comuna_detectada = ubicacion_gis.get("comuna") or proyecto.comuna

        return {
            "nombre": proyecto.nombre,
            "tipo_mineria": proyecto.tipo_mineria,
            "mineral_principal": proyecto.mineral_principal,
            "fase": proyecto.fase,
            "titular": proyecto.titular,
            "region": region_detectada,
            "comuna": comuna_detectada,
            "superficie_ha": float(proyecto.superficie_ha) if proyecto.superficie_ha else None,
            "produccion_estimada": proyecto.produccion_estimada,
            "vida_util_anos": proyecto.vida_util_anos,
            "uso_agua_lps": float(proyecto.uso_agua_lps) if proyecto.uso_agua_lps else None,
            "fuente_agua": proyecto.fuente_agua,
            "energia_mw": float(proyecto.energia_mw) if proyecto.energia_mw else None,
            "trabajadores_construccion": proyecto.trabajadores_construccion,
            "trabajadores_operacion": proyecto.trabajadores_operacion,
            "inversion_musd": float(proyecto.inversion_musd) if proyecto.inversion_musd else None,
            "descripcion": proyecto.descripcion,
            "requiere_reasentamiento": proyecto.requiere_reasentamiento,
            "afecta_patrimonio": proyecto.afecta_patrimonio,
        }

    def _ejecutar_motor_reglas(self, resultado_gis: dict, datos_proyecto: dict):
        """Ejecuta el motor de reglas SEIA."""
        from app.services.reglas import MotorReglasSSEIA

        logger.info("Ejecutando motor de reglas SEIA...")
        motor_reglas = MotorReglasSSEIA()
        return motor_reglas.clasificar_proyecto(resultado_gis, datos_proyecto)

    def _generar_alertas(self, resultado_gis: dict, datos_proyecto: dict) -> tuple:
        """Genera alertas y retorna lista y diccionario."""
        from app.services.reglas import SistemaAlertas

        logger.info("Generando alertas...")
        sistema_alertas = SistemaAlertas()
        alertas = sistema_alertas.generar_alertas(resultado_gis, datos_proyecto)
        alertas_dict = [a.to_dict() for a in alertas]
        return alertas, alertas_dict

    async def _buscar_normativa(self, db: AsyncSession, clasificacion) -> tuple:
        """Busca normativa relevante usando RAG."""
        from app.services.rag.busqueda import BuscadorLegal

        inicio_rag = time.time()
        logger.info("Buscando normativa relevante...")
        normativa_relevante = []

        try:
            buscador = BuscadorLegal()
            for trigger in clasificacion.triggers[:3]:
                query = f"Art. 11 letra {trigger.letra.value} {trigger.descripcion}"
                resultados = await buscador.buscar(db, query, limite=3)
                for r in resultados:
                    normativa_relevante.append({
                        "contenido": r.contenido,
                        "documento": r.documento_titulo,
                        "seccion": r.seccion,
                        "relevancia": f"Trigger {trigger.letra.value}",
                    })
        except Exception as e:
            logger.warning(f"RAG no disponible: {e}")

        tiempo_rag = int((time.time() - inicio_rag) * 1000)
        return normativa_relevante, tiempo_rag

    async def _generar_informe_llm(
        self,
        tipo_analisis: str,
        datos_proyecto: dict,
        resultado_gis: dict,
        normativa_relevante: list
    ) -> tuple:
        """Genera informe con LLM si es analisis completo."""
        from app.services.llm import GeneradorInformes

        informe_dict = None
        tiempo_llm = 0
        tokens_usados = 0

        if tipo_analisis == "completo":
            inicio_llm = time.time()
            logger.info("Generando informe con LLM...")
            try:
                generador = GeneradorInformes()
                informe = await generador.generar_informe(
                    datos_proyecto=datos_proyecto,
                    resultado_gis=resultado_gis,
                    normativa_relevante=normativa_relevante,
                    secciones_a_generar=None,
                )
                informe_dict = {
                    "secciones": [
                        {
                            "seccion": s.seccion.value,
                            "titulo": s.titulo,
                            "contenido": s.contenido,
                        }
                        for s in informe.secciones
                    ],
                    "texto_completo": informe.to_texto_plano(),
                }
                tokens_usados = len(informe.to_texto_plano()) // 4
            except Exception as e:
                logger.error(f"Error generando informe LLM: {e}")
                informe_dict = {"error": str(e)}
            tiempo_llm = int((time.time() - inicio_llm) * 1000)

        return informe_dict, tiempo_llm, tokens_usados

    async def _persistir_analisis(
        self,
        db: AsyncSession,
        proyecto: Proyecto,
        tipo_analisis: str,
        resultado_gis: dict,
        clasificacion,
        normativa_relevante: list,
        informe_dict: Optional[dict],
        alertas_dict: list,
        tiempo_gis: int,
        tiempo_rag: int,
        tiempo_llm: int,
        tiempo_total: int
    ) -> Analisis:
        """Persiste el analisis y la auditoria en la BD."""
        logger.info("Persistiendo analisis en BD...")

        nuevo_analisis = Analisis(
            proyecto_id=proyecto.id,
            tipo_analisis=tipo_analisis,
            resultado_gis=resultado_gis,
            via_ingreso_recomendada=clasificacion.via_ingreso.value,
            confianza_clasificacion=clasificacion.confianza,
            triggers_eia=[
                {
                    "letra": t.letra.value,
                    "descripcion": t.descripcion,
                    "severidad": t.severidad.value,
                    "peso": t.peso,
                }
                for t in clasificacion.triggers
            ],
            normativa_relevante=normativa_relevante[:20],
            informe_texto=informe_dict.get("texto_completo") if informe_dict and isinstance(informe_dict, dict) else None,
            informe_json=informe_dict,
            version_modelo=getattr(settings, 'LLM_MODEL', 'claude-sonnet-4-20250514'),
            tiempo_procesamiento_ms=tiempo_total,
            datos_extra={
                "alertas": alertas_dict,
                "metricas": {
                    "tiempo_gis_ms": tiempo_gis,
                    "tiempo_rag_ms": tiempo_rag,
                    "tiempo_llm_ms": tiempo_llm,
                },
                "ejecutado_via": "asistente_ia",
            }
        )
        db.add(nuevo_analisis)
        await db.flush()

        # Crear registro de auditoria
        await self._crear_auditoria(
            db, nuevo_analisis, proyecto, tipo_analisis, resultado_gis,
            clasificacion, tiempo_gis, tiempo_rag, tiempo_llm
        )

        return nuevo_analisis

    async def _crear_auditoria(
        self,
        db: AsyncSession,
        analisis: Analisis,
        proyecto: Proyecto,
        tipo_analisis: str,
        resultado_gis: dict,
        clasificacion,
        tiempo_gis: int,
        tiempo_rag: int,
        tiempo_llm: int
    ):
        """Crea el registro de auditoria."""
        logger.info("Creando registro de auditoria...")

        checksum_datos = {
            "proyecto_id": proyecto.id,
            "nombre": proyecto.nombre,
            "region": proyecto.region,
            "timestamp": datetime.now().strftime("%Y-%m-%d"),
        }
        checksum = hashlib.sha256(
            json.dumps(checksum_datos, sort_keys=True, default=str).encode()
        ).hexdigest()

        capas_usadas = self._obtener_capas_usadas(resultado_gis)
        normativa_citada = self._obtener_normativa_citada(clasificacion)

        tokens_usados = None
        if tipo_analisis == "completo":
            tokens_usados = 0  # Se calcula en _generar_informe_llm

        auditoria = AuditoriaAnalisis(
            analisis_id=analisis.id,
            capas_gis_usadas=capas_usadas,
            documentos_referenciados=[],
            normativa_citada=normativa_citada,
            checksum_datos_entrada=checksum,
            version_modelo_llm=getattr(settings, 'LLM_MODEL', 'claude-sonnet-4-20250514') if tipo_analisis == "completo" else None,
            version_sistema="1.0.0",
            tiempo_gis_ms=tiempo_gis,
            tiempo_rag_ms=tiempo_rag,
            tiempo_llm_ms=tiempo_llm if tipo_analisis == "completo" else None,
            tokens_usados=tokens_usados,
        )
        db.add(auditoria)

    def _obtener_capas_usadas(self, resultado_gis: dict) -> list:
        """Obtiene las capas GIS usadas en el analisis."""
        capas_map = {
            "areas_protegidas": "SNASPE / Areas Protegidas",
            "glaciares": "Inventario Glaciares DGA",
            "cuerpos_agua": "Cuerpos de Agua / Humedales",
            "comunidades_indigenas": "Comunidades Indigenas / ADI",
            "centros_poblados": "Centros Poblados INE",
            "sitios_patrimoniales": "Sitios Patrimoniales CMN",
        }

        capas_usadas = []
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")

        for capa_key, capa_nombre in capas_map.items():
            elementos = resultado_gis.get(capa_key, [])
            if isinstance(elementos, list):
                capas_usadas.append({
                    "nombre": capa_nombre,
                    "fecha": fecha_hoy,
                    "version": "v2024.2",
                    "elementos_encontrados": len(elementos),
                })

        return capas_usadas

    def _obtener_normativa_citada(self, clasificacion) -> list:
        """Obtiene la normativa citada para la auditoria."""
        normativa_citada = []
        for trigger in clasificacion.triggers:
            normativa_citada.append({
                "tipo": "Ley",
                "numero": "19300",
                "articulo": "11",
                "letra": trigger.letra.value,
                "descripcion": trigger.descripcion,
            })
        return normativa_citada

    async def _actualizar_estado_proyecto(self, db: AsyncSession, proyecto: Proyecto):
        """Actualiza el estado del proyecto si corresponde."""
        estado_anterior = proyecto.estado
        if proyecto.estado in ["con_geometria", "completo"]:
            proyecto.estado = "analizado"
            logger.info(f"Estado del proyecto actualizado: {estado_anterior} -> analizado")

    def _preparar_resultado(
        self,
        proyecto: Proyecto,
        analisis: Analisis,
        tipo_analisis: str,
        clasificacion,
        alertas: list,
        informe_dict: Optional[dict],
        tiempo_total: int
    ) -> ResultadoHerramienta:
        """Prepara el resultado final para el asistente."""
        alertas_criticas = sum(1 for a in alertas if hasattr(a, 'nivel') and a.nivel.value == "CRITICA")
        alertas_altas = sum(1 for a in alertas if hasattr(a, 'nivel') and a.nivel.value == "ALTA")

        return ResultadoHerramienta(
            exito=True,
            contenido={
                "proyecto_id": proyecto.id,
                "proyecto_nombre": proyecto.nombre,
                "analisis_id": analisis.id,
                "tipo_analisis": tipo_analisis,
                "estado": "completado",
                "via_ingreso_recomendada": clasificacion.via_ingreso.value,
                "confianza": clasificacion.confianza,
                "nivel_confianza": clasificacion.nivel_confianza.value,
                "justificacion": clasificacion.justificacion,
                "triggers_detectados": len(clasificacion.triggers),
                "triggers_resumen": [
                    f"Letra {t.letra.value}: {t.descripcion}"
                    for t in clasificacion.triggers[:5]
                ],
                "alertas_criticas": alertas_criticas,
                "alertas_altas": alertas_altas,
                "alertas_totales": len(alertas),
                "estado_proyecto": proyecto.estado,
                "tiempo_total_ms": tiempo_total,
                "tiene_informe": informe_dict is not None and "error" not in informe_dict,
                "mensaje": f"Analisis {tipo_analisis} completado. Recomendacion: {clasificacion.via_ingreso.value} "
                          f"(confianza {clasificacion.confianza:.0%}). "
                          f"Se detectaron {len(clasificacion.triggers)} triggers del Art. 11.",
            },
            metadata={
                "proyecto_id": proyecto.id,
                "analisis_id": analisis.id,
                "tipo_analisis": tipo_analisis,
                "accion": "ejecutar_analisis",
            }
        )

    def generar_descripcion_confirmacion(self, **kwargs) -> str:
        """Genera descripcion para confirmacion."""
        proyecto_id = kwargs.get("proyecto_id", "?")
        proyecto_nombre = kwargs.get("_proyecto_nombre")
        tipo = kwargs.get("tipo_analisis", "completo")
        tipo_legible = "completo (con informe LLM)" if tipo == "completo" else "rapido (sin LLM)"

        if proyecto_nombre:
            return f"Ejecutar analisis {tipo_legible} para el proyecto '{proyecto_nombre}'"
        return f"Ejecutar analisis {tipo_legible} para proyecto ID {proyecto_id}"
