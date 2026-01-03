"""
Herramientas de acciones del asistente.
Operaciones que modifican datos y requieren confirmacion del usuario.
"""
import logging
import time
import hashlib
import json
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape, MultiPolygon, mapping

from .base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)
from app.db.models import Proyecto, Cliente
from app.db.models.proyecto import Analisis
from app.db.models.auditoria import AuditoriaAnalisis
from app.core.config import settings

logger = logging.getLogger(__name__)


# Lista de regiones validas de Chile
REGIONES_CHILE = [
    "Arica y Parinacota",
    "Tarapaca",
    "Antofagasta",
    "Atacama",
    "Coquimbo",
    "Valparaiso",
    "Metropolitana",
    "O'Higgins",
    "Maule",
    "Nuble",
    "Biobio",
    "Araucania",
    "Los Rios",
    "Los Lagos",
    "Aysen",
    "Magallanes",
]

TIPOS_MINERIA = [
    "cielo_abierto",
    "subterranea",
    "mixta",
    "placer",
    "in_situ",
]

FASES_PROYECTO = [
    "exploracion",
    "evaluacion",
    "desarrollo",
    "produccion",
    "cierre",
]


@registro_herramientas.registrar
class CrearProyecto(Herramienta):
    """Crea un nuevo proyecto minero en el sistema."""

    nombre = "crear_proyecto"
    descripcion = """Crea un nuevo proyecto minero en el sistema.
Usa esta herramienta cuando el usuario quiera:
- Crear un nuevo proyecto
- Registrar un proyecto minero
- Agregar un proyecto al sistema

IMPORTANTE: Esta accion requiere confirmacion del usuario antes de ejecutarse.
Los campos minimos requeridos son: nombre y region.
Otros campos opcionales mejoran el analisis posterior."""

    categoria = CategoriaHerramienta.ACCION
    requiere_confirmacion = True
    permisos = [PermisoHerramienta.ESCRITURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        """Establece la sesion de base de datos."""
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Nombre del proyecto minero (obligatorio)",
                    "minLength": 2,
                    "maxLength": 200,
                },
                "region": {
                    "type": "string",
                    "description": "Region de Chile donde se ubica el proyecto",
                    "enum": REGIONES_CHILE,
                },
                "comuna": {
                    "type": "string",
                    "description": "Comuna donde se ubica el proyecto",
                },
                "tipo_mineria": {
                    "type": "string",
                    "description": "Tipo de mineria del proyecto",
                    "enum": TIPOS_MINERIA,
                },
                "mineral_principal": {
                    "type": "string",
                    "description": "Mineral principal a extraer (ej: cobre, litio, oro)",
                },
                "fase": {
                    "type": "string",
                    "description": "Fase actual del proyecto",
                    "enum": FASES_PROYECTO,
                },
                "titular": {
                    "type": "string",
                    "description": "Nombre del titular o empresa responsable",
                },
                "cliente_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "ID del cliente asociado (si existe en el sistema)",
                },
                "superficie_ha": {
                    "type": "number",
                    "description": "Superficie del proyecto en hectareas",
                    "minimum": 0,
                },
                "vida_util_anos": {
                    "type": "integer",
                    "description": "Vida util estimada del proyecto en anos",
                    "minimum": 0,
                },
                "uso_agua_lps": {
                    "type": "number",
                    "description": "Uso de agua estimado en litros por segundo",
                    "minimum": 0,
                },
                "fuente_agua": {
                    "type": "string",
                    "description": "Fuente de agua (ej: subterranea, superficial, mar)",
                },
                "energia_mw": {
                    "type": "number",
                    "description": "Consumo de energia estimado en MW",
                    "minimum": 0,
                },
                "trabajadores_construccion": {
                    "type": "integer",
                    "description": "Numero de trabajadores en fase de construccion",
                    "minimum": 0,
                },
                "trabajadores_operacion": {
                    "type": "integer",
                    "description": "Numero de trabajadores en fase de operacion",
                    "minimum": 0,
                },
                "inversion_musd": {
                    "type": "number",
                    "description": "Inversion estimada en millones de USD",
                    "minimum": 0,
                },
                "descripcion": {
                    "type": "string",
                    "description": "Descripcion general del proyecto",
                },
            },
            "required": ["nombre", "region"],
        }

    async def ejecutar(
        self,
        nombre: str,
        region: str,
        comuna: Optional[str] = None,
        tipo_mineria: Optional[str] = None,
        mineral_principal: Optional[str] = None,
        fase: Optional[str] = None,
        titular: Optional[str] = None,
        cliente_id: Optional[str] = None,
        superficie_ha: Optional[float] = None,
        vida_util_anos: Optional[int] = None,
        uso_agua_lps: Optional[float] = None,
        fuente_agua: Optional[str] = None,
        energia_mw: Optional[float] = None,
        trabajadores_construccion: Optional[int] = None,
        trabajadores_operacion: Optional[int] = None,
        inversion_musd: Optional[float] = None,
        descripcion: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Crea un nuevo proyecto en la base de datos."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        # Validar nombre
        if not nombre or len(nombre.strip()) < 2:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="El nombre del proyecto debe tener al menos 2 caracteres"
            )

        # Validar region
        if region not in REGIONES_CHILE:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Region invalida. Regiones validas: {', '.join(REGIONES_CHILE)}"
            )

        # Validar tipo_mineria si se proporciona
        if tipo_mineria and tipo_mineria not in TIPOS_MINERIA:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Tipo de mineria invalido. Tipos validos: {', '.join(TIPOS_MINERIA)}"
            )

        # Validar fase si se proporciona
        if fase and fase not in FASES_PROYECTO:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Fase invalida. Fases validas: {', '.join(FASES_PROYECTO)}"
            )

        try:
            # Verificar cliente si se proporciona
            cliente = None
            cliente_uuid = None
            if cliente_id:
                try:
                    cliente_uuid = UUID(cliente_id)
                    result = await db.execute(
                        select(Cliente).where(
                            Cliente.id == cliente_uuid,
                            Cliente.activo == True
                        )
                    )
                    cliente = result.scalar()
                    if not cliente:
                        return ResultadoHerramienta(
                            exito=False,
                            contenido=None,
                            error=f"Cliente con ID {cliente_id} no encontrado o inactivo"
                        )
                except ValueError:
                    return ResultadoHerramienta(
                        exito=False,
                        contenido=None,
                        error=f"ID de cliente invalido: {cliente_id}"
                    )

            # Verificar si ya existe un proyecto con el mismo nombre
            existing = await db.execute(
                select(Proyecto).where(Proyecto.nombre == nombre.strip())
            )
            if existing.scalar():
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Ya existe un proyecto con el nombre '{nombre}'"
                )

            # Crear proyecto
            proyecto = Proyecto(
                nombre=nombre.strip(),
                region=region,
                comuna=comuna,
                tipo_mineria=tipo_mineria,
                mineral_principal=mineral_principal,
                fase=fase,
                titular=titular,
                cliente_id=cliente_uuid,
                superficie_ha=superficie_ha,
                vida_util_anos=vida_util_anos,
                uso_agua_lps=uso_agua_lps,
                fuente_agua=fuente_agua,
                energia_mw=energia_mw,
                trabajadores_construccion=trabajadores_construccion,
                trabajadores_operacion=trabajadores_operacion,
                inversion_musd=inversion_musd,
                descripcion=descripcion,
                estado="borrador",
            )

            db.add(proyecto)
            await db.commit()
            await db.refresh(proyecto)

            logger.info(f"Proyecto creado: {proyecto.id} - {proyecto.nombre}")

            # Construir respuesta
            resultado = {
                "proyecto_id": proyecto.id,
                "nombre": proyecto.nombre,
                "region": proyecto.region,
                "comuna": proyecto.comuna,
                "estado": proyecto.estado,
                "tipo_mineria": proyecto.tipo_mineria,
                "mineral_principal": proyecto.mineral_principal,
                "fase": proyecto.fase,
                "titular": proyecto.titular,
                "cliente": {
                    "id": str(cliente.id),
                    "razon_social": cliente.razon_social,
                } if cliente else None,
                "parametros_tecnicos": {
                    "superficie_ha": proyecto.superficie_ha,
                    "vida_util_anos": proyecto.vida_util_anos,
                    "uso_agua_lps": proyecto.uso_agua_lps,
                    "fuente_agua": proyecto.fuente_agua,
                    "energia_mw": proyecto.energia_mw,
                    "trabajadores_construccion": proyecto.trabajadores_construccion,
                    "trabajadores_operacion": proyecto.trabajadores_operacion,
                    "inversion_musd": proyecto.inversion_musd,
                },
                "tiene_geometria": False,
                "puede_analizar": False,
                "mensaje": f"Proyecto '{proyecto.nombre}' creado exitosamente con ID {proyecto.id}",
                "siguiente_paso": "Para ejecutar el analisis de prefactibilidad, primero debe definir la geometria del proyecto en el mapa.",
            }

            return ResultadoHerramienta(
                exito=True,
                contenido=resultado,
                metadata={
                    "proyecto_id": proyecto.id,
                    "accion": "crear_proyecto",
                }
            )

        except Exception as e:
            logger.error(f"Error creando proyecto: {e}")
            await db.rollback()
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al crear el proyecto: {str(e)}"
            )

    def generar_descripcion_confirmacion(self, **kwargs) -> str:
        """
        Genera una descripcion legible para el dialogo de confirmacion.
        """
        nombre = kwargs.get("nombre", "Sin nombre")
        region = kwargs.get("region", "Sin region")
        tipo = kwargs.get("tipo_mineria", "No especificado")
        mineral = kwargs.get("mineral_principal", "No especificado")

        descripcion = f"Crear proyecto '{nombre}' en {region}"

        detalles = []
        if tipo and tipo != "No especificado":
            detalles.append(f"Tipo: {tipo}")
        if mineral and mineral != "No especificado":
            detalles.append(f"Mineral: {mineral}")
        if kwargs.get("superficie_ha"):
            detalles.append(f"Superficie: {kwargs['superficie_ha']} ha")
        if kwargs.get("inversion_musd"):
            detalles.append(f"Inversion: {kwargs['inversion_musd']} MUSD")

        if detalles:
            descripcion += f" ({', '.join(detalles)})"

        return descripcion


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

            # Importar servicios de analisis
            from app.services.gis.analisis import analizar_proyecto_espacial
            from app.services.rag.busqueda import BuscadorLegal
            from app.services.reglas import MotorReglasSSEIA, SistemaAlertas
            from app.services.llm import GeneradorInformes, SeccionInforme

            inicio_total = time.time()
            logger.info(f"Ejecutando analisis {tipo_analisis} para proyecto_id={proyecto_id}")

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
            inicio_gis = time.time()
            logger.info("Ejecutando analisis GIS...")
            resultado_gis = await analizar_proyecto_espacial(db, geojson)
            tiempo_gis = int((time.time() - inicio_gis) * 1000)

            # 2.1 Extraer ubicacion real desde el analisis GIS (basado en coordenadas)
            ubicacion_gis = resultado_gis.get("ubicacion", {}) or {}
            region_detectada = ubicacion_gis.get("region") or proyecto.region
            comuna_detectada = ubicacion_gis.get("comuna") or proyecto.comuna

            # 3. Preparar datos del proyecto para el motor de reglas
            # IMPORTANTE: Usar region/comuna detectadas del GIS, no las manuales del proyecto
            datos_proyecto = {
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

            # 4. Ejecutar motor de reglas SEIA
            logger.info("Ejecutando motor de reglas SEIA...")
            motor_reglas = MotorReglasSSEIA()
            clasificacion = motor_reglas.clasificar_proyecto(resultado_gis, datos_proyecto)

            # 5. Generar alertas
            logger.info("Generando alertas...")
            sistema_alertas = SistemaAlertas()
            alertas = sistema_alertas.generar_alertas(resultado_gis, datos_proyecto)
            alertas_dict = [a.to_dict() for a in alertas]

            alertas_criticas = sum(1 for a in alertas_dict if a["nivel"] == "CRITICA")
            alertas_altas = sum(1 for a in alertas_dict if a["nivel"] == "ALTA")

            # 6. Buscar normativa relevante (RAG)
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

            # 7. Generar informe con LLM (solo si tipo=completo)
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

            tiempo_total = int((time.time() - inicio_total) * 1000)

            # 8. Persistir analisis en BD
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

            # 9. Crear registro de auditoria
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

            capas_usadas = []
            capas_map = {
                "areas_protegidas": "SNASPE / Areas Protegidas",
                "glaciares": "Inventario Glaciares DGA",
                "cuerpos_agua": "Cuerpos de Agua / Humedales",
                "comunidades_indigenas": "Comunidades Indigenas / ADI",
                "centros_poblados": "Centros Poblados INE",
                "sitios_patrimoniales": "Sitios Patrimoniales CMN",
            }
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

            normativa_citada = []
            for trigger in clasificacion.triggers:
                normativa_citada.append({
                    "tipo": "Ley",
                    "numero": "19300",
                    "articulo": "11",
                    "letra": trigger.letra.value,
                    "descripcion": trigger.descripcion,
                })

            auditoria = AuditoriaAnalisis(
                analisis_id=nuevo_analisis.id,
                capas_gis_usadas=capas_usadas,
                documentos_referenciados=[],
                normativa_citada=normativa_citada,
                checksum_datos_entrada=checksum,
                version_modelo_llm=getattr(settings, 'LLM_MODEL', 'claude-sonnet-4-20250514') if tipo_analisis == "completo" else None,
                version_sistema="1.0.0",
                tiempo_gis_ms=tiempo_gis,
                tiempo_rag_ms=tiempo_rag,
                tiempo_llm_ms=tiempo_llm if tipo_analisis == "completo" else None,
                tokens_usados=tokens_usados if tipo_analisis == "completo" else None,
            )
            db.add(auditoria)

            # 10. Actualizar estado del proyecto
            estado_anterior = proyecto.estado
            if proyecto.estado in ["con_geometria", "completo"]:
                proyecto.estado = "analizado"
                logger.info(f"Estado del proyecto actualizado: {estado_anterior} -> analizado")

            await db.commit()
            await db.refresh(nuevo_analisis)

            logger.info(
                f"Analisis completado: analisis_id={nuevo_analisis.id}, "
                f"via={clasificacion.via_ingreso.value}, tiempo={tiempo_total}ms"
            )

            # Preparar resumen para el asistente
            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto_id,
                    "proyecto_nombre": proyecto.nombre,
                    "analisis_id": nuevo_analisis.id,
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
                    "proyecto_id": proyecto_id,
                    "analisis_id": nuevo_analisis.id,
                    "tipo_analisis": tipo_analisis,
                    "accion": "ejecutar_analisis",
                }
            )

        except Exception as e:
            logger.error(f"Error preparando analisis: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al preparar el analisis: {str(e)}"
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


@registro_herramientas.registrar
class ActualizarProyecto(Herramienta):
    """Actualiza datos de un proyecto existente."""

    nombre = "actualizar_proyecto"
    descripcion = """Actualiza los datos de un proyecto existente.
Usa esta herramienta cuando el usuario quiera:
- Modificar datos de un proyecto
- Actualizar informacion del proyecto
- Cambiar parametros del proyecto

IMPORTANTE: Esta accion requiere confirmacion del usuario."""

    categoria = CategoriaHerramienta.ACCION
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
                    "description": "ID del proyecto a actualizar",
                },
                "nombre": {
                    "type": "string",
                    "description": "Nuevo nombre del proyecto",
                },
                "comuna": {
                    "type": "string",
                    "description": "Nueva comuna",
                },
                "tipo_mineria": {
                    "type": "string",
                    "enum": TIPOS_MINERIA,
                },
                "mineral_principal": {
                    "type": "string",
                },
                "fase": {
                    "type": "string",
                    "enum": FASES_PROYECTO,
                },
                "titular": {
                    "type": "string",
                },
                "superficie_ha": {
                    "type": "number",
                    "minimum": 0,
                },
                "vida_util_anos": {
                    "type": "integer",
                    "minimum": 0,
                },
                "uso_agua_lps": {
                    "type": "number",
                    "minimum": 0,
                },
                "fuente_agua": {
                    "type": "string",
                },
                "energia_mw": {
                    "type": "number",
                    "minimum": 0,
                },
                "trabajadores_construccion": {
                    "type": "integer",
                    "minimum": 0,
                },
                "trabajadores_operacion": {
                    "type": "integer",
                    "minimum": 0,
                },
                "inversion_musd": {
                    "type": "number",
                    "minimum": 0,
                },
                "descripcion": {
                    "type": "string",
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        nombre: Optional[str] = None,
        comuna: Optional[str] = None,
        tipo_mineria: Optional[str] = None,
        mineral_principal: Optional[str] = None,
        fase: Optional[str] = None,
        titular: Optional[str] = None,
        superficie_ha: Optional[float] = None,
        vida_util_anos: Optional[int] = None,
        uso_agua_lps: Optional[float] = None,
        fuente_agua: Optional[str] = None,
        energia_mw: Optional[float] = None,
        trabajadores_construccion: Optional[int] = None,
        trabajadores_operacion: Optional[int] = None,
        inversion_musd: Optional[float] = None,
        descripcion: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Actualiza el proyecto."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            # Obtener proyecto
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

            if proyecto.estado == "archivado":
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="No se puede modificar un proyecto archivado"
                )

            # Construir diccionario de cambios
            cambios = {}
            campos_actualizables = {
                "nombre": nombre,
                "comuna": comuna,
                "tipo_mineria": tipo_mineria,
                "mineral_principal": mineral_principal,
                "fase": fase,
                "titular": titular,
                "superficie_ha": superficie_ha,
                "vida_util_anos": vida_util_anos,
                "uso_agua_lps": uso_agua_lps,
                "fuente_agua": fuente_agua,
                "energia_mw": energia_mw,
                "trabajadores_construccion": trabajadores_construccion,
                "trabajadores_operacion": trabajadores_operacion,
                "inversion_musd": inversion_musd,
                "descripcion": descripcion,
            }

            for campo, valor in campos_actualizables.items():
                if valor is not None:
                    cambios[campo] = valor

            if not cambios:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="No se proporcionaron campos para actualizar"
                )

            # Validaciones
            if tipo_mineria and tipo_mineria not in TIPOS_MINERIA:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Tipo de mineria invalido. Valores validos: {', '.join(TIPOS_MINERIA)}"
                )

            if fase and fase not in FASES_PROYECTO:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Fase invalida. Valores validos: {', '.join(FASES_PROYECTO)}"
                )

            # Aplicar cambios
            for campo, valor in cambios.items():
                setattr(proyecto, campo, valor)

            await db.commit()
            await db.refresh(proyecto)

            logger.info(f"Proyecto actualizado: {proyecto.id} - Campos: {list(cambios.keys())}")

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto.id,
                    "nombre": proyecto.nombre,
                    "campos_actualizados": list(cambios.keys()),
                    "mensaje": f"Proyecto '{proyecto.nombre}' actualizado exitosamente",
                },
                metadata={
                    "proyecto_id": proyecto.id,
                    "cambios": cambios,
                    "accion": "actualizar_proyecto",
                }
            )

        except Exception as e:
            logger.error(f"Error actualizando proyecto: {e}")
            await db.rollback()
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al actualizar el proyecto: {str(e)}"
            )

    def generar_descripcion_confirmacion(self, **kwargs) -> str:
        """Genera descripcion para confirmacion."""
        proyecto_id = kwargs.get("proyecto_id", "?")
        proyecto_nombre = kwargs.get("_proyecto_nombre")
        campos = [k for k, v in kwargs.items() if v is not None and k not in ("proyecto_id", "_proyecto_nombre")]

        if proyecto_nombre:
            return f"Actualizar proyecto '{proyecto_nombre}': {', '.join(campos) if campos else 'sin cambios'}"
        return f"Actualizar proyecto ID {proyecto_id}: {', '.join(campos) if campos else 'sin cambios'}"


@registro_herramientas.registrar
class GuardarFicha(Herramienta):
    """Guarda informacion en la ficha acumulativa del proyecto."""

    nombre = "guardar_ficha"
    descripcion = """Guarda informacion recopilada en la ficha acumulativa del proyecto.
Usa esta herramienta cuando el usuario proporcione informacion sobre su proyecto que debe
ser persistida en la ficha, como:
- Datos de identificacion (nombre del titular, contacto, etc.)
- Parametros tecnicos (tonelaje, tipo de extraccion, minerales, etc.)
- Informacion sobre obras (plantas, depositos, caminos, etc.)
- Fases del proyecto (construccion, operacion, cierre)
- Insumos (agua, energia, combustibles)
- Emisiones y residuos
- Aspectos sociales (comunidades, trabajadores)
- Aspectos ambientales (flora, fauna, areas sensibles)

Esta herramienta NO requiere confirmacion porque solo guarda informacion que el usuario
ya proporciono durante la conversacion.

IMPORTANTE: Extrae los datos estructurados de la respuesta del usuario y guardalos
con la categoria y clave apropiadas."""

    categoria = CategoriaHerramienta.ACCION
    requiere_confirmacion = False  # No requiere confirmacion, solo guarda lo que el usuario dijo
    permisos = [PermisoHerramienta.ESCRITURA]

    # Categorias validas y sus claves tipicas
    CATEGORIAS_VALIDAS = {
        "identificacion": [
            "nombre_proyecto", "titular", "rut_titular", "representante_legal",
            "direccion", "telefono", "email", "tipo_titular", "razon_social"
        ],
        "tecnico": [
            "tipo_extraccion", "mineral_principal", "minerales_secundarios",
            "tonelaje_mensual", "tonelaje_anual", "ley_mineral", "vida_util_anos",
            "produccion_estimada", "metodo_explotacion", "profundidad_rajo",
            "profundidad_mina", "razon_estéril_mineral"
        ],
        "obras": [
            "planta_beneficio", "deposito_relaves", "botadero_esteriles",
            "caminos_acceso", "linea_transmision", "subestacion", "campamento",
            "piscinas", "tanques_combustible", "polvorin", "talleres",
            "oficinas", "laboratorio", "patio_acopio"
        ],
        "fases": [
            "fecha_inicio_construccion", "duracion_construccion_meses",
            "fecha_inicio_operacion", "duracion_operacion_anos",
            "fecha_inicio_cierre", "duracion_cierre_anos",
            "trabajadores_construccion", "trabajadores_operacion"
        ],
        "insumos": [
            "uso_agua_lps", "fuente_agua", "tipo_agua", "derechos_agua",
            "energia_mw", "fuente_energia", "combustible_tipo",
            "combustible_consumo", "explosivos_tipo", "explosivos_consumo",
            "reactivos", "acido_sulfurico"
        ],
        "emisiones": [
            "emisiones_mp", "emisiones_so2", "emisiones_nox",
            "ruido_diurno", "ruido_nocturno", "vibraciones",
            "residuos_solidos", "residuos_peligrosos", "efluentes",
            "drenaje_acido", "manejo_aguas_contacto"
        ],
        "social": [
            "comunidades_cercanas", "distancia_poblados", "poblacion_afectada",
            "comunidades_indigenas", "patrimonio_cultural", "sitios_arqueologicos",
            "participacion_ciudadana", "compromisos_sociales"
        ],
        "ambiental": [
            "areas_protegidas_cercanas", "distancia_areas_protegidas",
            "glaciares_cercanos", "humedales_cercanos", "cuerpos_agua",
            "flora_protegida", "fauna_protegida", "vegetacion_nativa",
            "especies_peligro", "habitat_critico"
        ],
    }

    def __init__(self):
        self._db: Optional[AsyncSession] = None
        self._proyecto_id: Optional[int] = None

    def set_db(self, db: AsyncSession):
        """Establece la sesion de base de datos."""
        self._db = db

    def set_proyecto_id(self, proyecto_id: int):
        """Establece el ID del proyecto contexto."""
        self._proyecto_id = proyecto_id

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "proyecto_id": {
                    "type": "integer",
                    "description": "ID del proyecto donde guardar (opcional si hay contexto)",
                },
                "datos": {
                    "type": "array",
                    "description": "Lista de datos a guardar en la ficha",
                    "items": {
                        "type": "object",
                        "properties": {
                            "categoria": {
                                "type": "string",
                                "description": "Categoria del dato",
                                "enum": [
                                    "identificacion", "tecnico", "obras", "fases",
                                    "insumos", "emisiones", "social", "ambiental"
                                ],
                            },
                            "clave": {
                                "type": "string",
                                "description": "Clave identificadora del dato (ej: tonelaje_mensual)",
                            },
                            "valor": {
                                "type": "string",
                                "description": "Valor textual del dato",
                            },
                            "valor_numerico": {
                                "type": "number",
                                "description": "Valor numerico si aplica (para comparaciones de umbral)",
                            },
                            "unidad": {
                                "type": "string",
                                "description": "Unidad de medida (ej: ton/mes, l/s, MW)",
                            },
                        },
                        "required": ["categoria", "clave"],
                    },
                    "minItems": 1,
                },
            },
            "required": ["datos"],
        }

    async def ejecutar(
        self,
        datos: List[Dict[str, Any]],
        proyecto_id: Optional[int] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Guarda datos en la ficha acumulativa del proyecto."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        # Determinar proyecto_id
        proyecto_id = proyecto_id or self._proyecto_id
        if not proyecto_id:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No se especifico proyecto_id y no hay proyecto en contexto"
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

            # Importar servicio de ficha
            from app.services.asistente.ficha import get_ficha_service
            from app.schemas.ficha import GuardarRespuestaAsistente, CategoriaCaracteristica

            ficha_service = get_ficha_service(db)

            # Preparar respuestas
            respuestas = []
            errores_validacion = []

            for dato in datos:
                categoria_str = dato.get("categoria", "").lower()
                clave = dato.get("clave", "")
                valor = dato.get("valor")
                valor_numerico = dato.get("valor_numerico")
                unidad = dato.get("unidad")

                # Validar categoria
                if categoria_str not in self.CATEGORIAS_VALIDAS:
                    errores_validacion.append({
                        "clave": clave,
                        "error": f"Categoria '{categoria_str}' no valida"
                    })
                    continue

                # Validar que hay al menos un valor
                if valor is None and valor_numerico is None:
                    errores_validacion.append({
                        "clave": clave,
                        "error": "Debe proporcionar valor o valor_numerico"
                    })
                    continue

                try:
                    categoria_enum = CategoriaCaracteristica(categoria_str)
                    respuestas.append(GuardarRespuestaAsistente(
                        categoria=categoria_enum,
                        clave=clave,
                        valor=str(valor) if valor else None,
                        valor_numerico=float(valor_numerico) if valor_numerico is not None else None,
                        unidad=unidad,
                    ))
                except Exception as e:
                    errores_validacion.append({
                        "clave": clave,
                        "error": str(e)
                    })

            if not respuestas:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"No hay datos validos para guardar. Errores: {errores_validacion}"
                )

            # Guardar respuestas
            resultado = await ficha_service.guardar_respuestas_asistente(
                proyecto_id,
                respuestas
            )
            await db.commit()

            logger.info(
                f"Ficha actualizada: proyecto_id={proyecto_id}, "
                f"guardadas={resultado.guardadas}, actualizadas={resultado.actualizadas}"
            )

            # Preparar resumen para el LLM
            datos_guardados = []
            for c in resultado.caracteristicas:
                datos_guardados.append({
                    "categoria": c.categoria.value if hasattr(c.categoria, 'value') else c.categoria,
                    "clave": c.clave,
                    "valor": c.valor or c.valor_numerico,
                    "unidad": c.unidad,
                })

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto_id,
                    "proyecto_nombre": proyecto.nombre,
                    "guardadas": resultado.guardadas,
                    "actualizadas": resultado.actualizadas,
                    "errores": resultado.errores + errores_validacion,
                    "datos_guardados": datos_guardados,
                    "mensaje": f"Se guardaron {resultado.guardadas + resultado.actualizadas} datos en la ficha del proyecto '{proyecto.nombre}'",
                },
                metadata={
                    "proyecto_id": proyecto_id,
                    "accion": "guardar_ficha",
                    "total_guardados": resultado.guardadas + resultado.actualizadas,
                }
            )

        except Exception as e:
            logger.error(f"Error guardando ficha: {e}")
            await db.rollback()
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al guardar en la ficha: {str(e)}"
            )

    def generar_descripcion_confirmacion(self, **kwargs) -> str:
        """Genera descripcion para confirmacion (aunque no la usa)."""
        datos = kwargs.get("datos", [])
        return f"Guardar {len(datos)} datos en la ficha del proyecto"
