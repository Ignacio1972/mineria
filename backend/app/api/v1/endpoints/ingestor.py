"""
Endpoints para ingestión de documentos legales.
Integrado con clasificación LLM y sistema de gestión documental.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
import tempfile
import os

from app.db.session import get_db
from app.services.rag.ingestor import (
    IngestorLegal,
    DocumentoAIngestar,
    ResultadoIngestion,
    extraer_texto_pdf,
    extraer_texto_docx,
    get_ingestor_legal,
)


router = APIRouter()


class DocumentoInput(BaseModel):
    """Datos para ingestar un documento de texto."""
    titulo: str = Field(..., description="Título del documento", min_length=3)
    tipo: str = Field(..., description="Tipo: Ley, Reglamento, Decreto, Guía SEA, Instructivo, Criterio")
    numero: Optional[str] = Field(None, description="Número del documento (ej: 19.300)")
    fecha_publicacion: Optional[date] = Field(None, description="Fecha de publicación")
    organismo: str = Field(..., description="Organismo emisor")
    contenido: str = Field(..., description="Contenido completo del documento", min_length=100)
    url_fuente: Optional[str] = Field(None, description="URL de la fuente original")
    # Nuevos campos para clasificación
    categoria_id: Optional[int] = Field(None, description="ID de categoría (si no se proporciona, se detecta con LLM)")
    sectores: Optional[List[str]] = Field(None, description="Sectores aplicables: mineria, energia, etc.")
    triggers_art11: Optional[List[str]] = Field(None, description="Triggers Art. 11: a, b, c, d, e, f")
    componentes_ambientales: Optional[List[str]] = Field(None, description="Componentes: agua, aire, suelo, etc.")
    etapa_proceso: Optional[str] = Field(None, description="Etapa SEIA: ingreso, evaluacion, calificacion, etc.")

    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Guía para la Evaluación de Impactos en Glaciares",
                "tipo": "Guía SEA",
                "numero": "RE 123/2024",
                "fecha_publicacion": "2024-01-15",
                "organismo": "Servicio de Evaluación Ambiental",
                "contenido": "Artículo 1. La presente guía establece los criterios para evaluar impactos en glaciares...",
                "url_fuente": "https://sea.gob.cl/documentacion/guias",
                "sectores": ["mineria"],
                "triggers_art11": ["b", "d"],
                "componentes_ambientales": ["glaciares", "agua"]
            }
        }


class IngestorResponse(BaseModel):
    """Respuesta de ingestión."""
    documento_id: int
    titulo: str
    fragmentos_creados: int
    temas_detectados: List[str]
    triggers_detectados: List[str]
    componentes_detectados: List[str]
    categoria_asignada: Optional[str]
    clasificacion_llm_usada: bool
    tiempo_procesamiento_ms: int
    errores: List[str] = []


class ReprocesarResponse(BaseModel):
    """Respuesta de reprocesamiento."""
    documento_id: int
    fragmentos_actualizados: int
    temas_actualizados: int
    tiempo_ms: int


@router.post(
    "/documento",
    response_model=IngestorResponse,
    summary="Ingestar documento de texto",
    description="""
    Ingesta un documento legal en formato texto plano.

    El documento será:
    1. Clasificado automáticamente con LLM (categoría, temas, triggers)
    2. Segmentado en artículos/secciones
    3. Cada fragmento clasificado con LLM para detectar temas específicos
    4. Convertido a embeddings para búsqueda semántica
    5. Almacenado con relaciones fragmento-tema en la base de datos

    Si se proporcionan categoria_id, sectores, triggers o componentes, se usan esos valores.
    Si no, el sistema los detecta automáticamente usando LLM.
    """
)
async def ingestar_documento(
    documento: DocumentoInput,
    usar_llm: bool = Query(True, description="Si usar LLM para clasificación automática"),
    db: AsyncSession = Depends(get_db),
) -> IngestorResponse:
    """Ingesta un documento de texto con clasificación LLM opcional."""

    ingestor = get_ingestor_legal(usar_llm=usar_llm)

    doc = DocumentoAIngestar(
        titulo=documento.titulo,
        tipo=documento.tipo,
        numero=documento.numero,
        fecha_publicacion=documento.fecha_publicacion,
        organismo=documento.organismo,
        contenido=documento.contenido,
        url_fuente=documento.url_fuente,
        categoria_id=documento.categoria_id,
        sectores=documento.sectores or [],
        triggers_art11=documento.triggers_art11 or [],
        componentes_ambientales=documento.componentes_ambientales or [],
        etapa_proceso=documento.etapa_proceso,
    )

    try:
        resultado: ResultadoIngestion = await ingestor.ingestar_documento(db, doc)

        return IngestorResponse(
            documento_id=resultado.documento_id,
            titulo=resultado.titulo,
            fragmentos_creados=resultado.fragmentos_creados,
            temas_detectados=resultado.temas_detectados,
            triggers_detectados=resultado.triggers_detectados,
            componentes_detectados=resultado.componentes_detectados,
            categoria_asignada=resultado.categoria_asignada,
            clasificacion_llm_usada=resultado.clasificacion_llm_usada,
            tiempo_procesamiento_ms=resultado.tiempo_procesamiento_ms,
            errores=resultado.errores,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en ingestión: {str(e)}"
        )


@router.post(
    "/pdf",
    response_model=IngestorResponse,
    summary="Ingestar documento PDF",
    description="""
    Ingesta un documento legal en formato PDF.

    El PDF será:
    1. Procesado para extraer texto
    2. Clasificado automáticamente con LLM
    3. Segmentado en artículos/secciones
    4. Convertido a embeddings para búsqueda semántica
    5. Almacenado con relaciones fragmento-tema
    """
)
async def ingestar_pdf(
    archivo: UploadFile = File(..., description="Archivo PDF a procesar"),
    titulo: str = Form(..., description="Título del documento"),
    tipo: str = Form(..., description="Tipo: Ley, Reglamento, Decreto, Guía SEA"),
    organismo: str = Form(..., description="Organismo emisor"),
    numero: Optional[str] = Form(None, description="Número del documento"),
    fecha_publicacion: Optional[str] = Form(None, description="Fecha YYYY-MM-DD"),
    url_fuente: Optional[str] = Form(None, description="URL de la fuente"),
    categoria_id: Optional[int] = Form(None, description="ID de categoría"),
    usar_llm: bool = Form(True, description="Usar LLM para clasificación"),
    db: AsyncSession = Depends(get_db),
) -> IngestorResponse:
    """Ingesta un documento PDF."""

    # Validar tipo de archivo
    if not archivo.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un PDF"
        )

    # Guardar archivo temporal
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            contenido = await archivo.read()
            tmp.write(contenido)
            tmp_path = tmp.name

        # Extraer texto del PDF
        texto = extraer_texto_pdf(tmp_path)

        if len(texto.strip()) < 100:
            raise HTTPException(
                status_code=400,
                detail="No se pudo extraer suficiente texto del PDF"
            )

        # Parsear fecha si se proporcionó
        fecha_pub = None
        if fecha_publicacion:
            try:
                from datetime import datetime
                fecha_pub = datetime.strptime(fecha_publicacion, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha inválido. Use YYYY-MM-DD"
                )

        # Crear documento e ingestar
        ingestor = get_ingestor_legal(usar_llm=usar_llm)

        doc = DocumentoAIngestar(
            titulo=titulo,
            tipo=tipo,
            numero=numero,
            fecha_publicacion=fecha_pub,
            organismo=organismo,
            contenido=texto,
            url_fuente=url_fuente,
            categoria_id=categoria_id,
        )

        resultado: ResultadoIngestion = await ingestor.ingestar_documento(db, doc)

        return IngestorResponse(
            documento_id=resultado.documento_id,
            titulo=resultado.titulo,
            fragmentos_creados=resultado.fragmentos_creados,
            temas_detectados=resultado.temas_detectados,
            triggers_detectados=resultado.triggers_detectados,
            componentes_detectados=resultado.componentes_detectados,
            categoria_asignada=resultado.categoria_asignada,
            clasificacion_llm_usada=resultado.clasificacion_llm_usada,
            tiempo_procesamiento_ms=resultado.tiempo_procesamiento_ms,
            errores=resultado.errores,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando PDF: {str(e)}"
        )
    finally:
        # Limpiar archivo temporal
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@router.post(
    "/documento/{documento_id}/reprocesar",
    response_model=ReprocesarResponse,
    summary="Reprocesar fragmentos de un documento",
    description="""
    Reprocesa los fragmentos de un documento existente.

    Útil para:
    - Regenerar embeddings con nuevo modelo
    - Reclasificar temas con LLM
    - Actualizar relaciones fragmento-tema
    """
)
async def reprocesar_documento(
    documento_id: int,
    regenerar_embeddings: bool = Query(True, description="Regenerar embeddings vectoriales"),
    reclasificar: bool = Query(True, description="Reclasificar temas con LLM"),
    db: AsyncSession = Depends(get_db),
) -> ReprocesarResponse:
    """Reprocesa un documento existente."""

    ingestor = get_ingestor_legal(usar_llm=reclasificar)

    try:
        resultado = await ingestor.reprocesar_fragmentos(
            db=db,
            documento_id=documento_id,
            regenerar_embeddings=regenerar_embeddings,
            reclasificar=reclasificar,
        )

        if "error" in resultado:
            raise HTTPException(status_code=404, detail=resultado["error"])

        return ReprocesarResponse(
            documento_id=resultado["documento_id"],
            fragmentos_actualizados=resultado["fragmentos_actualizados"],
            temas_actualizados=resultado["temas_actualizados"],
            tiempo_ms=resultado["tiempo_ms"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reprocesando documento: {str(e)}"
        )


@router.get(
    "/documentos",
    summary="Listar documentos ingestados",
    description="Retorna la lista de documentos legales en el corpus."
)
async def listar_documentos(
    tipo: Optional[str] = None,
    categoria_id: Optional[int] = None,
    limite: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista documentos del corpus."""
    from sqlalchemy import text

    sql = """
        SELECT
            d.id,
            d.titulo,
            d.tipo,
            d.numero,
            d.fecha_publicacion,
            d.organismo,
            d.estado,
            d.categoria_id,
            c.nombre as categoria_nombre,
            d.sectores,
            d.triggers_art11,
            COUNT(f.id) as fragmentos
        FROM legal.documentos d
        LEFT JOIN legal.fragmentos f ON d.id = f.documento_id
        LEFT JOIN legal.categorias c ON d.categoria_id = c.id
        WHERE 1=1
    """

    params = {"limite": limite}

    if tipo:
        sql += " AND d.tipo = :tipo"
        params["tipo"] = tipo

    if categoria_id:
        sql += " AND d.categoria_id = :categoria_id"
        params["categoria_id"] = categoria_id

    sql += """
        GROUP BY d.id, c.nombre
        ORDER BY d.created_at DESC
        LIMIT :limite
    """

    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    documentos = [
        {
            "id": row.id,
            "titulo": row.titulo,
            "tipo": row.tipo,
            "numero": row.numero,
            "fecha_publicacion": str(row.fecha_publicacion) if row.fecha_publicacion else None,
            "organismo": row.organismo,
            "estado": row.estado,
            "categoria_id": row.categoria_id,
            "categoria_nombre": row.categoria_nombre,
            "sectores": row.sectores,
            "triggers_art11": row.triggers_art11,
            "fragmentos": row.fragmentos,
        }
        for row in rows
    ]

    return {
        "total": len(documentos),
        "documentos": documentos,
    }


@router.delete(
    "/documento/{documento_id}",
    summary="Eliminar documento",
    description="Elimina un documento y todos sus fragmentos del corpus."
)
async def eliminar_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Elimina un documento del corpus."""
    from sqlalchemy import text

    # Verificar que existe
    result = await db.execute(
        text("SELECT titulo FROM legal.documentos WHERE id = :id"),
        {"id": documento_id}
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Documento {documento_id} no encontrado"
        )

    titulo = row.titulo

    # Eliminar (cascade eliminará fragmentos y relaciones)
    await db.execute(
        text("DELETE FROM legal.documentos WHERE id = :id"),
        {"id": documento_id}
    )
    await db.commit()

    return {
        "mensaje": f"Documento '{titulo}' eliminado correctamente",
        "documento_id": documento_id,
    }


class ActualizacionSEAResponse(BaseModel):
    """Respuesta de actualización de guías SEA."""
    guias_encontradas: int
    guias_nuevas: int
    guias_existentes: int
    errores: List[str]
    documentos_ingresados: List[dict]
    tiempo_total_ms: int


@router.post(
    "/actualizar-guias-sea",
    response_model=ActualizacionSEAResponse,
    summary="Actualizar guías del SEA",
    description="""
    Scrapea el sitio web del SEA para detectar guías y criterios nuevos.

    El proceso:
    1. Obtiene el listado actual de guías desde sea.gob.cl
    2. Compara con los documentos existentes en el corpus
    3. Descarga e ingesta automáticamente las guías nuevas
    4. Genera embeddings para búsqueda semántica

    Este endpoint puede tardar varios minutos si hay muchas guías nuevas.
    """
)
async def actualizar_guias_sea(
    db: AsyncSession = Depends(get_db),
) -> ActualizacionSEAResponse:
    """Actualiza el corpus con guías nuevas del SEA."""

    from app.services.rag.actualizador_guias import get_actualizador

    actualizador = get_actualizador()

    try:
        resultado = await actualizador.actualizar(db)

        return ActualizacionSEAResponse(
            guias_encontradas=resultado.guias_encontradas,
            guias_nuevas=resultado.guias_nuevas,
            guias_existentes=resultado.guias_existentes,
            errores=resultado.errores[:10],  # Limitar errores mostrados
            documentos_ingresados=resultado.documentos_ingresados,
            tiempo_total_ms=resultado.tiempo_total_ms,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando guías: {str(e)}"
        )


@router.get(
    "/estado-corpus-sea",
    summary="Estado del corpus SEA",
    description="Obtiene estadísticas del corpus de guías y criterios del SEA."
)
async def estado_corpus_sea(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Estadísticas del corpus SEA."""
    from sqlalchemy import text

    result = await db.execute(
        text("""
            SELECT
                tipo,
                COUNT(*) as documentos,
                SUM(fragmentos_count) as total_fragmentos,
                MIN(fecha_publicacion) as fecha_mas_antigua,
                MAX(fecha_publicacion) as fecha_mas_reciente
            FROM (
                SELECT d.tipo, d.id, d.fecha_publicacion, COUNT(f.id) as fragmentos_count
                FROM legal.documentos d
                LEFT JOIN legal.fragmentos f ON d.id = f.documento_id
                WHERE d.tipo IN ('Guía SEA', 'Criterio SEA')
                GROUP BY d.tipo, d.id, d.fecha_publicacion
            ) sub
            GROUP BY tipo
            ORDER BY documentos DESC
        """)
    )

    estadisticas = []
    for row in result.fetchall():
        estadisticas.append({
            "tipo": row.tipo,
            "documentos": row.documentos,
            "fragmentos": row.total_fragmentos or 0,
            "fecha_mas_antigua": str(row.fecha_mas_antigua) if row.fecha_mas_antigua else None,
            "fecha_mas_reciente": str(row.fecha_mas_reciente) if row.fecha_mas_reciente else None,
        })

    # Total general
    result = await db.execute(
        text("""
            SELECT COUNT(DISTINCT d.id) as docs, COUNT(f.id) as frags
            FROM legal.documentos d
            LEFT JOIN legal.fragmentos f ON d.id = f.documento_id
            WHERE d.tipo IN ('Guía SEA', 'Criterio SEA')
        """)
    )
    totales = result.fetchone()

    return {
        "por_tipo": estadisticas,
        "total_documentos": totales.docs if totales else 0,
        "total_fragmentos": totales.frags if totales else 0,
    }
