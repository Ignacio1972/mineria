"""
Endpoints de Análisis de Prefactibilidad Ambiental

Endpoint principal que integra:
- Análisis espacial GIS
- Búsqueda semántica de normativa (RAG)
- Motor de reglas SEIA
- Generación de informes con LLM
"""

import logging
import time
from typing import Any, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

from app.db.session import get_db
from app.db.models.proyecto import Proyecto, Analisis
from app.db.models.auditoria import AuditoriaAnalisis
from app.services.gis.analisis import analizar_proyecto_espacial
from app.services.rag.busqueda import BuscadorLegal
from app.services.reglas import MotorReglasSSEIA, SistemaAlertas
from app.services.llm import GeneradorInformes, SeccionInforme
from app.schemas.auditoria import (
    AnalisisIntegradoInput,
    AnalisisIntegradoResponse,
    AuditoriaAnalisisResponse,
    MetricasEjecucion,
)
from app.schemas.prefactibilidad import (
    DatosProyectoInput,
    GeometriaInput,
    AnalisisPrefactibilidadInput,
    TriggerResponse,
    AlertaResponse,
    ClasificacionResponse,
    SeccionInformeResponse,
    AnalisisPrefactibilidadResponse,
    AnalisisRapidoResponse,
    EliminarAnalisisResponse,
)
from app.services.prefactibilidad import (
    ServicioPrefactibilidad,
    construir_datos_proyecto,
    calcular_checksum,
    extraer_capas_usadas,
    extraer_normativa_citada,
    descripcion_seccion,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# === Dependencias ===

def get_buscador_legal() -> BuscadorLegal:
    """Obtiene instancia del buscador legal."""
    return BuscadorLegal()


def get_motor_reglas() -> MotorReglasSSEIA:
    """Obtiene instancia del motor de reglas."""
    return MotorReglasSSEIA()


def get_sistema_alertas() -> SistemaAlertas:
    """Obtiene instancia del sistema de alertas."""
    return SistemaAlertas()


def get_generador_informes() -> GeneradorInformes:
    """Obtiene instancia del generador de informes."""
    return GeneradorInformes()


def get_servicio_prefactibilidad(
    buscador: BuscadorLegal = Depends(get_buscador_legal),
    motor_reglas: MotorReglasSSEIA = Depends(get_motor_reglas),
    sistema_alertas: SistemaAlertas = Depends(get_sistema_alertas),
    generador: GeneradorInformes = Depends(get_generador_informes),
) -> ServicioPrefactibilidad:
    """Obtiene instancia del servicio de prefactibilidad."""
    return ServicioPrefactibilidad(
        buscador=buscador,
        motor_reglas=motor_reglas,
        sistema_alertas=sistema_alertas,
        generador=generador,
    )


# === Endpoints ===

def _resultado_a_response(resultado, generar_informe_llm: bool) -> AnalisisPrefactibilidadResponse:
    """Convierte ResultadoAnalisis a AnalisisPrefactibilidadResponse."""
    return AnalisisPrefactibilidadResponse(
        id=resultado.id,
        fecha_analisis=resultado.fecha_analisis,
        proyecto=resultado.datos_proyecto,
        resultado_gis=resultado.resultado_gis,
        clasificacion_seia=ClasificacionResponse(
            via_ingreso_recomendada=resultado.clasificacion.via_ingreso.value,
            confianza=resultado.clasificacion.confianza,
            nivel_confianza=resultado.clasificacion.nivel_confianza.value,
            justificacion=resultado.clasificacion.justificacion,
            puntaje_matriz=resultado.clasificacion.puntaje_matriz,
        ),
        triggers=[
            TriggerResponse(
                letra=t.letra.value,
                descripcion=t.descripcion,
                detalle=t.detalle,
                severidad=t.severidad.value,
                fundamento_legal=t.fundamento_legal,
                peso=t.peso,
            )
            for t in resultado.clasificacion.triggers
        ],
        alertas=[
            AlertaResponse(
                id=a["id"],
                nivel=a["nivel"],
                categoria=a["categoria"],
                titulo=a["titulo"],
                descripcion=a["descripcion"],
                acciones_requeridas=a.get("acciones_requeridas", []),
            )
            for a in resultado.alertas_dict
        ],
        normativa_citada=resultado.normativa_relevante[:20],
        informe=resultado.informe,
        metricas={
            "tiempo_total_ms": resultado.tiempo_total_ms,
            "con_informe_llm": generar_informe_llm,
            "triggers_detectados": len(resultado.clasificacion.triggers),
            "alertas_generadas": len(resultado.alertas),
        }
    )


@router.post(
    "/analisis",
    response_model=AnalisisPrefactibilidadResponse,
    summary="Análisis completo de prefactibilidad ambiental",
    description="""
    Realiza un análisis completo de prefactibilidad ambiental para un proyecto minero.

    El análisis incluye:
    1. **Análisis espacial GIS**: Intersecciones con capas sensibles (áreas protegidas, glaciares, etc.)
    2. **Evaluación SEIA**: Detección de triggers del Art. 11 y clasificación DIA/EIA
    3. **Sistema de alertas**: Alertas por tipo de impacto y componente ambiental
    4. **Búsqueda normativa**: Normativa relevante del corpus legal (RAG)
    5. **Generación de informe**: Informe estructurado con LLM (opcional)

    El tiempo de respuesta depende de si se genera el informe con LLM (~30-60s) o solo el análisis automático (~2-5s).
    """,
)
async def analizar_prefactibilidad(
    input_data: AnalisisPrefactibilidadInput,
    db: AsyncSession = Depends(get_db),
    servicio: ServicioPrefactibilidad = Depends(get_servicio_prefactibilidad),
) -> AnalisisPrefactibilidadResponse:
    """Endpoint principal de análisis de prefactibilidad ambiental."""
    try:
        # Convertir geometría a formato GeoJSON
        geojson = {
            "type": input_data.geometria.type,
            "coordinates": input_data.geometria.coordinates,
        }

        # Ejecutar análisis usando el servicio
        resultado = await servicio.ejecutar_analisis(
            db=db,
            geojson=geojson,
            datos_proyecto=input_data.proyecto.model_dump(),
            generar_informe=input_data.generar_informe_llm,
            secciones=input_data.secciones,
        )

        return _resultado_a_response(resultado, input_data.generar_informe_llm)

    except Exception as e:
        logger.error(f"Error en análisis de prefactibilidad: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error en el análisis: {str(e)}"
        )


@router.post(
    "/analisis-rapido",
    response_model=AnalisisPrefactibilidadResponse,
    summary="Análisis rápido de clasificación SEIA",
    description="""
    Realiza un análisis rápido para determinar la vía de ingreso al SEIA.

    Este endpoint es más rápido (~2-5s) ya que NO genera el informe con LLM.
    Útil para validaciones preliminares o cuando se necesita una respuesta inmediata.

    Retorna la misma estructura que el análisis completo, pero sin el campo 'informe'.
    """,
)
async def analisis_rapido(
    input_data: AnalisisPrefactibilidadInput,
    db: AsyncSession = Depends(get_db),
    servicio: ServicioPrefactibilidad = Depends(get_servicio_prefactibilidad),
) -> AnalisisPrefactibilidadResponse:
    """
    Análisis rápido sin generación de informe LLM.
    Retorna la estructura completa para compatibilidad con el frontend.
    """
    try:
        # Convertir geometría a formato GeoJSON
        geojson = {
            "type": input_data.geometria.type,
            "coordinates": input_data.geometria.coordinates,
        }

        # Ejecutar análisis SIN informe LLM
        resultado = await servicio.ejecutar_analisis(
            db=db,
            geojson=geojson,
            datos_proyecto=input_data.proyecto.model_dump(),
            generar_informe=False,  # Sin LLM
            secciones=None,
        )

        return _resultado_a_response(resultado, generar_informe_llm=False)

    except Exception as e:
        logger.error(f"Error en análisis rápido: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/secciones-disponibles",
    summary="Lista secciones de informe disponibles",
    description="Retorna la lista de secciones que pueden generarse en el informe.",
)
async def obtener_secciones_disponibles() -> dict[str, Any]:
    """Retorna las secciones disponibles para generación."""
    return {
        "secciones": [
            {
                "id": s.value,
                "nombre": GeneradorInformes.TITULOS_SECCIONES.get(s, s.value),
                "descripcion": descripcion_seccion(s),
            }
            for s in SeccionInforme
        ]
    }


@router.get(
    "/matriz-decision",
    summary="Obtiene configuración de la matriz de decisión",
    description="Retorna los parámetros y reglas de la matriz de decisión DIA/EIA.",
)
async def obtener_matriz_decision(
    motor_reglas: MotorReglasSSEIA = Depends(get_motor_reglas),
) -> dict[str, Any]:
    """Retorna la configuración de la matriz de decisión."""
    return motor_reglas.obtener_matriz_decision()


@router.post(
    "/exportar/{formato}",
    summary="Exportar informe a PDF/DOCX/TXT/HTML",
    description="""
    Exporta un informe de prefactibilidad a diferentes formatos.

    Formatos disponibles:
    - **pdf**: Documento PDF formal
    - **docx**: Documento Word editable
    - **txt**: Texto plano
    - **html**: Documento HTML

    Requiere enviar el resultado de un análisis previo.
    """,
)
async def exportar_informe(
    formato: str,
    informe_data: dict[str, Any],
) -> StreamingResponse:
    """
    Exporta un informe al formato especificado.
    """
    from app.services.exportacion import ExportadorInformes, FormatoExportacion

    try:
        formato_enum = FormatoExportacion(formato.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: {formato}. Use: pdf, docx, txt, html"
        )

    exportador = ExportadorInformes()

    try:
        contenido = exportador.exportar(informe_data, formato_enum)

        # Configurar respuesta
        mime_types = {
            FormatoExportacion.PDF: "application/pdf",
            FormatoExportacion.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            FormatoExportacion.TXT: "text/plain",
            FormatoExportacion.HTML: "text/html",
        }
        extensions = {
            FormatoExportacion.PDF: ".pdf",
            FormatoExportacion.DOCX: ".docx",
            FormatoExportacion.TXT: ".txt",
            FormatoExportacion.HTML: ".html",
        }

        nombre_proyecto = informe_data.get("datos_proyecto", {}).get("nombre", "informe")
        nombre_archivo = f"prefactibilidad_{nombre_proyecto.replace(' ', '_')}{extensions[formato_enum]}"

        return StreamingResponse(
            iter([contenido]),
            media_type=mime_types[formato_enum],
            headers={
                "Content-Disposition": f"attachment; filename={nombre_archivo}"
            }
        )

    except Exception as e:
        logger.error(f"Error exportando informe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/formatos-exportacion",
    summary="Lista formatos de exportación disponibles",
    description="Retorna los formatos disponibles para exportar informes.",
)
async def obtener_formatos_exportacion() -> dict[str, Any]:
    """Retorna los formatos de exportación disponibles."""
    from app.services.exportacion import ExportadorInformes

    exportador = ExportadorInformes()
    return {"formatos": exportador.obtener_formatos_disponibles()}


# === Endpoint Integrado con Persistencia y Auditoria ===

@router.post(
    "/analisis-integrado",
    response_model=AnalisisIntegradoResponse,
    summary="Analisis integrado con persistencia y auditoria",
    description="""
    Ejecuta un analisis completo de prefactibilidad sobre un proyecto existente en BD.

    **Flujo del analisis:**
    1. Carga proyecto desde BD con su geometria
    2. Ejecuta analisis espacial GIS (intersecciones con capas sensibles)
    3. Evalua triggers Art. 11 Ley 19.300
    4. Clasifica via de ingreso (DIA vs EIA)
    5. Genera alertas por componente ambiental
    6. Busca normativa relevante (RAG)
    7. [Si tipo=completo] Genera informe con LLM
    8. Persiste analisis en BD
    9. Crea registro de auditoria para trazabilidad regulatoria
    10. Actualiza estado del proyecto a 'analizado'

    **Tipos de analisis:**
    - `rapido`: Solo GIS + reglas (~2-5 segundos)
    - `completo`: GIS + RAG + LLM (~30-60 segundos)

    **Trazabilidad:**
    Cada analisis genera un registro de auditoria inmutable que incluye:
    - Capas GIS consultadas con version y fecha
    - Normativa citada
    - Hash de datos de entrada (reproducibilidad)
    - Metricas de ejecucion
    """,
)
async def analisis_integrado(
    input_data: AnalisisIntegradoInput,
    db: AsyncSession = Depends(get_db),
    buscador: BuscadorLegal = Depends(get_buscador_legal),
    motor_reglas: MotorReglasSSEIA = Depends(get_motor_reglas),
    sistema_alertas: SistemaAlertas = Depends(get_sistema_alertas),
    generador: GeneradorInformes = Depends(get_generador_informes),
) -> AnalisisIntegradoResponse:
    """
    Endpoint de analisis integrado con persistencia y auditoria.
    """
    inicio_total = time.time()
    logger.info(f"Iniciando analisis integrado para proyecto_id={input_data.proyecto_id}")

    # 1. Cargar proyecto desde BD
    result = await db.execute(
        select(Proyecto).where(Proyecto.id == input_data.proyecto_id)
    )
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, f"Proyecto con id={input_data.proyecto_id} no encontrado")

    if not proyecto.geom:
        raise HTTPException(
            400,
            "El proyecto no tiene geometria definida. Dibuje un poligono antes de analizar."
        )

    if proyecto.estado == "archivado":
        raise HTTPException(400, "No se puede analizar un proyecto archivado")

    # 2. Convertir geometria a GeoJSON
    try:
        geom_shape = to_shape(proyecto.geom)
        geojson = mapping(geom_shape)
    except Exception as e:
        logger.error(f"Error convirtiendo geometria: {e}")
        raise HTTPException(500, f"Error procesando geometria: {e}")

    # 3. Ejecutar analisis espacial GIS
    inicio_gis = time.time()
    logger.info("Ejecutando analisis GIS...")
    resultado_gis = await analizar_proyecto_espacial(db, geojson)
    tiempo_gis = int((time.time() - inicio_gis) * 1000)

    # 3.1 Extraer ubicacion real desde el analisis GIS (basado en coordenadas)
    ubicacion_gis = resultado_gis.get("ubicacion", {}) or {}
    region_detectada = ubicacion_gis.get("region") or proyecto.region
    comuna_detectada = ubicacion_gis.get("comuna") or proyecto.comuna

    # 4. Preparar datos del proyecto para el motor de reglas
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

    # 5. Ejecutar motor de reglas SEIA
    logger.info("Ejecutando motor de reglas SEIA...")
    clasificacion = motor_reglas.clasificar_proyecto(resultado_gis, datos_proyecto)

    # 6. Generar alertas
    logger.info("Generando alertas...")
    alertas = sistema_alertas.generar_alertas(resultado_gis, datos_proyecto)
    alertas_dict = [a.to_dict() for a in alertas]

    alertas_criticas = sum(1 for a in alertas_dict if a["nivel"] == "CRITICA")
    alertas_altas = sum(1 for a in alertas_dict if a["nivel"] == "ALTA")

    # 7. Buscar normativa relevante (RAG)
    inicio_rag = time.time()
    logger.info("Buscando normativa relevante...")
    normativa_relevante = await _buscar_normativa_contextual(
        db, buscador, clasificacion, alertas
    )
    tiempo_rag = int((time.time() - inicio_rag) * 1000)

    # 8. Generar informe con LLM (solo si tipo=completo)
    informe_dict = None
    tiempo_llm = 0
    tokens_usados = 0

    if input_data.tipo == "completo":
        inicio_llm = time.time()
        logger.info("Generando informe con LLM...")

        secciones_a_generar = None
        if input_data.secciones:
            try:
                secciones_a_generar = [SeccionInforme(s) for s in input_data.secciones]
            except ValueError as e:
                raise HTTPException(400, f"Seccion invalida: {e}")

        try:
            informe = await generador.generar_informe(
                datos_proyecto=datos_proyecto,
                resultado_gis=resultado_gis,
                normativa_relevante=normativa_relevante,
                secciones_a_generar=secciones_a_generar,
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
            # Estimar tokens (aproximado)
            tokens_usados = len(informe.to_texto_plano()) // 4
        except Exception as e:
            logger.error(f"Error generando informe LLM: {e}")
            # Continuar sin informe
            informe_dict = {"error": str(e)}

        tiempo_llm = int((time.time() - inicio_llm) * 1000)

    tiempo_total = int((time.time() - inicio_total) * 1000)

    # 9. Persistir analisis en BD
    logger.info("Persistiendo analisis en BD...")

    nuevo_analisis = Analisis(
        proyecto_id=proyecto.id,
        tipo_analisis=input_data.tipo,
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
        informe_texto=informe_dict.get("texto_completo") if informe_dict else None,
        informe_json=informe_dict,
        version_modelo=getattr(settings, 'LLM_MODEL', 'claude-sonnet-4-20250514'),
        tiempo_procesamiento_ms=tiempo_total,
        datos_extra={
            "alertas": alertas_dict,
            "metricas": {
                "tiempo_gis_ms": tiempo_gis,
                "tiempo_rag_ms": tiempo_rag,
                "tiempo_llm_ms": tiempo_llm,
            }
        }
    )

    db.add(nuevo_analisis)
    await db.flush()  # Para obtener el ID

    # 10. Crear registro de auditoria
    logger.info("Creando registro de auditoria...")

    checksum = calcular_checksum(proyecto)
    capas_usadas = extraer_capas_usadas(resultado_gis)
    normativa_citada = extraer_normativa_citada(clasificacion.triggers, normativa_relevante)

    auditoria = AuditoriaAnalisis(
        analisis_id=nuevo_analisis.id,
        capas_gis_usadas=capas_usadas,
        documentos_referenciados=[],
        normativa_citada=normativa_citada,
        checksum_datos_entrada=checksum,
        version_modelo_llm=getattr(settings, 'LLM_MODEL', 'claude-sonnet-4-20250514') if input_data.tipo == "completo" else None,
        version_sistema="1.0.0",
        tiempo_gis_ms=tiempo_gis,
        tiempo_rag_ms=tiempo_rag,
        tiempo_llm_ms=tiempo_llm if input_data.tipo == "completo" else None,
        tokens_usados=tokens_usados if input_data.tipo == "completo" else None,
    )

    db.add(auditoria)

    # 11. Actualizar estado del proyecto
    estado_anterior = proyecto.estado
    if proyecto.estado in ["con_geometria", "completo"]:
        proyecto.estado = "analizado"
        logger.info(f"Estado del proyecto actualizado: {estado_anterior} -> analizado")

    await db.commit()
    await db.refresh(nuevo_analisis)
    await db.refresh(auditoria)

    logger.info(
        f"Analisis integrado completado: analisis_id={nuevo_analisis.id}, "
        f"auditoria_id={auditoria.id}, tiempo={tiempo_total}ms"
    )

    return AnalisisIntegradoResponse(
        analisis_id=nuevo_analisis.id,
        auditoria_id=auditoria.id,
        proyecto_id=proyecto.id,
        fecha_analisis=nuevo_analisis.fecha_analisis,
        tipo_analisis=input_data.tipo,
        via_ingreso_recomendada=clasificacion.via_ingreso.value,
        confianza=clasificacion.confianza,
        nivel_confianza=clasificacion.nivel_confianza.value,
        justificacion=clasificacion.justificacion,
        triggers_detectados=len(clasificacion.triggers),
        alertas_criticas=alertas_criticas,
        alertas_altas=alertas_altas,
        alertas_totales=len(alertas),
        estado_proyecto=proyecto.estado,
        metricas=MetricasEjecucion(
            tiempo_gis_ms=tiempo_gis,
            tiempo_rag_ms=tiempo_rag,
            tiempo_llm_ms=tiempo_llm,
            tiempo_total_ms=tiempo_total,
            tokens_usados=tokens_usados,
        ),
        informe=informe_dict,
    )


@router.get(
    "/analisis/{analisis_id}/auditoria",
    response_model=AuditoriaAnalisisResponse,
    summary="Obtener auditoria de un analisis",
    description="""
    Retorna el registro de auditoria de un analisis especifico.

    Este registro es inmutable y contiene:
    - Capas GIS consultadas con version y fecha
    - Normativa citada en el analisis
    - Hash de datos de entrada para reproducibilidad
    - Metricas de ejecucion (tiempos, tokens)
    - Version del sistema y modelo LLM usado
    """,
)
async def obtener_auditoria_analisis(
    analisis_id: int,
    db: AsyncSession = Depends(get_db),
) -> AuditoriaAnalisisResponse:
    """Obtiene el registro de auditoria de un analisis."""

    result = await db.execute(
        select(AuditoriaAnalisis).where(AuditoriaAnalisis.analisis_id == analisis_id)
    )
    auditoria = result.scalar()

    if not auditoria:
        raise HTTPException(404, f"Auditoria para analisis_id={analisis_id} no encontrada")

    return AuditoriaAnalisisResponse(
        id=auditoria.id,
        analisis_id=auditoria.analisis_id,
        capas_gis_usadas=auditoria.capas_gis_usadas or [],
        documentos_referenciados=auditoria.documentos_referenciados or [],
        normativa_citada=auditoria.normativa_citada or [],
        checksum_datos_entrada=auditoria.checksum_datos_entrada,
        version_modelo_llm=auditoria.version_modelo_llm,
        version_sistema=auditoria.version_sistema,
        tiempo_gis_ms=auditoria.tiempo_gis_ms,
        tiempo_rag_ms=auditoria.tiempo_rag_ms,
        tiempo_llm_ms=auditoria.tiempo_llm_ms,
        tokens_usados=auditoria.tokens_usados,
        created_at=auditoria.created_at,
    )


@router.get(
    "/proyecto/{proyecto_id}/historial-analisis",
    summary="Historial de analisis de un proyecto",
    description="Retorna todos los analisis realizados sobre un proyecto.",
)
async def historial_analisis_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Obtiene el historial de analisis de un proyecto."""

    # Verificar que existe el proyecto
    proyecto_result = await db.execute(
        select(Proyecto).where(Proyecto.id == proyecto_id)
    )
    if not proyecto_result.scalar():
        raise HTTPException(404, f"Proyecto con id={proyecto_id} no encontrado")

    # Obtener analisis
    result = await db.execute(
        select(Analisis)
        .where(Analisis.proyecto_id == proyecto_id)
        .order_by(Analisis.fecha_analisis.desc())
    )
    analisis_list = result.scalars().all()

    return [
        {
            "id": a.id,
            "fecha_analisis": a.fecha_analisis.isoformat() if a.fecha_analisis else None,
            "tipo_analisis": a.tipo_analisis,
            "via_ingreso_recomendada": a.via_ingreso_recomendada,
            "confianza": float(a.confianza_clasificacion) if a.confianza_clasificacion else None,
            "triggers_count": len(a.triggers_eia) if a.triggers_eia else 0,
            "tiempo_procesamiento_ms": a.tiempo_procesamiento_ms,
            "tiene_informe": a.informe_json is not None,
        }
        for a in analisis_list
    ]


@router.get(
    "/proyecto/{proyecto_id}/ultimo-analisis",
    response_model=AnalisisPrefactibilidadResponse,
    summary="Obtener ultimo analisis de un proyecto",
    description="Retorna el analisis mas reciente de un proyecto con todos sus datos.",
)
async def obtener_ultimo_analisis(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
) -> AnalisisPrefactibilidadResponse:
    """Obtiene el ultimo analisis completo de un proyecto."""

    # Verificar que existe el proyecto
    proyecto_result = await db.execute(
        select(Proyecto).where(Proyecto.id == proyecto_id)
    )
    proyecto = proyecto_result.scalar()
    if not proyecto:
        raise HTTPException(404, f"Proyecto con id={proyecto_id} no encontrado")

    # Obtener ultimo analisis
    result = await db.execute(
        select(Analisis)
        .where(Analisis.proyecto_id == proyecto_id)
        .order_by(Analisis.fecha_analisis.desc())
        .limit(1)
    )
    analisis = result.scalar()

    if not analisis:
        raise HTTPException(404, f"No hay analisis para el proyecto id={proyecto_id}")

    # Reconstruir datos del proyecto
    # Extraer ubicacion del resultado_gis guardado si existe
    resultado_gis_guardado = analisis.resultado_gis or {}
    ubicacion_gis = resultado_gis_guardado.get("ubicacion", {}) or {}
    region_detectada = ubicacion_gis.get("region") or proyecto.region
    comuna_detectada = ubicacion_gis.get("comuna") or proyecto.comuna

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
    }

    # Extraer alertas del campo datos_extra
    alertas_data = []
    if analisis.datos_extra and "alertas" in analisis.datos_extra:
        alertas_data = analisis.datos_extra["alertas"]

    return AnalisisPrefactibilidadResponse(
        id=str(analisis.id),
        fecha_analisis=analisis.fecha_analisis.isoformat() if analisis.fecha_analisis else datetime.now().isoformat(),
        proyecto=datos_proyecto,
        resultado_gis=analisis.resultado_gis or {},
        clasificacion_seia=ClasificacionResponse(
            via_ingreso_recomendada=analisis.via_ingreso_recomendada or "DIA",
            confianza=float(analisis.confianza_clasificacion) if analisis.confianza_clasificacion else 0.5,
            nivel_confianza="MEDIO",
            justificacion="Analisis recuperado de base de datos",
            puntaje_matriz=0.0,
        ),
        triggers=[
            TriggerResponse(
                letra=t.get("letra", ""),
                descripcion=t.get("descripcion", ""),
                detalle=t.get("detalle", ""),
                severidad=t.get("severidad", "MEDIA"),
                fundamento_legal=t.get("fundamento_legal", ""),
                peso=t.get("peso", 0.0),
            )
            for t in (analisis.triggers_eia or [])
        ],
        alertas=[
            AlertaResponse(
                id=a.get("id", ""),
                nivel=a.get("nivel", "MEDIA"),
                categoria=a.get("categoria", ""),
                titulo=a.get("titulo", ""),
                descripcion=a.get("descripcion", ""),
                acciones_requeridas=a.get("acciones_requeridas", []),
            )
            for a in alertas_data
        ],
        normativa_citada=analisis.normativa_relevante or [],
        informe=analisis.informe_json,
        metricas={
            "tiempo_total_ms": analisis.tiempo_procesamiento_ms or 0,
            "con_informe_llm": analisis.informe_json is not None,
            "triggers_detectados": len(analisis.triggers_eia) if analisis.triggers_eia else 0,
            "alertas_generadas": len(alertas_data),
            "recuperado_de_bd": True,
        }
    )


@router.delete(
    "/analisis/{analisis_id}",
    response_model=EliminarAnalisisResponse,
    summary="Eliminar un análisis",
    description="""
    Elimina un análisis específico y su registro de auditoría asociado.

    **Comportamiento:**
    - Si es el único análisis del proyecto, el estado del proyecto cambia a 'con_geometria'
    - La auditoría asociada se elimina automáticamente (CASCADE)
    - El proyecto NO se elimina, solo el análisis

    **Advertencia:** Esta acción es irreversible.
    """,
)
async def eliminar_analisis(
    analisis_id: int,
    db: AsyncSession = Depends(get_db),
) -> EliminarAnalisisResponse:
    """Elimina un análisis y su auditoría asociada."""
    from sqlalchemy import func

    logger.info(f"Solicitud de eliminación de análisis id={analisis_id}")

    # 1. Buscar el análisis
    result = await db.execute(
        select(Analisis).where(Analisis.id == analisis_id)
    )
    analisis = result.scalar()

    if not analisis:
        raise HTTPException(404, f"Análisis con id={analisis_id} no encontrado")

    proyecto_id = analisis.proyecto_id

    # 2. Obtener el proyecto
    proyecto_result = await db.execute(
        select(Proyecto).where(Proyecto.id == proyecto_id)
    )
    proyecto = proyecto_result.scalar()

    if not proyecto:
        raise HTTPException(404, f"Proyecto asociado no encontrado")

    # 3. Contar cuántos análisis tiene el proyecto
    count_result = await db.execute(
        select(func.count(Analisis.id)).where(Analisis.proyecto_id == proyecto_id)
    )
    total_analisis = count_result.scalar()

    era_ultimo = total_analisis == 1
    nuevo_estado = None

    # 4. Si es el último análisis, cambiar estado del proyecto
    if era_ultimo and proyecto.estado == "analizado":
        if proyecto.geom:
            proyecto.estado = "con_geometria"
        else:
            proyecto.estado = "completo" if proyecto.nombre else "borrador"
        nuevo_estado = proyecto.estado
        logger.info(f"Proyecto {proyecto_id} cambiado a estado '{nuevo_estado}' (era último análisis)")

    # 5. Eliminar el análisis (la auditoría se elimina por CASCADE)
    await db.delete(analisis)
    await db.commit()

    logger.info(f"Análisis id={analisis_id} eliminado exitosamente")

    return EliminarAnalisisResponse(
        mensaje="Análisis eliminado exitosamente",
        analisis_id=analisis_id,
        proyecto_id=proyecto_id,
        era_ultimo_analisis=era_ultimo,
        nuevo_estado_proyecto=nuevo_estado,
    )
