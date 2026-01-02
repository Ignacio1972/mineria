"""
Endpoints para gestion de documentos del corpus RAG.

Proporciona CRUD completo para documentos legales con:
- Upload de archivos PDF/DOCX
- Extraccion automatica de texto
- Procesamiento de fragmentos y embeddings
- Trazabilidad completa a fuentes originales
"""

import json
from datetime import date, datetime
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models.legal import Documento, Fragmento
from app.db.models.corpus import (
    Categoria, ArchivoOriginal, Coleccion, DocumentoColeccion,
    RelacionDocumento, HistorialVersion
)
from app.services.storage.archivo_service import get_archivo_service, ArchivoService


router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class DocumentoCreateData(BaseModel):
    """Datos para crear documento (enviado como JSON en Form)."""
    titulo: str = Field(..., min_length=1, max_length=500)
    tipo: str = Field(..., min_length=1, max_length=100)
    numero: Optional[str] = Field(None, max_length=100)
    fecha_publicacion: Optional[date] = None
    fecha_vigencia: Optional[date] = None
    organismo: Optional[str] = Field(None, max_length=255)
    url_fuente: Optional[str] = Field(None, max_length=500)
    resolucion_aprobatoria: Optional[str] = Field(None, max_length=100)

    # Categoria obligatoria
    categoria_id: int

    # Colecciones opcionales
    coleccion_ids: Optional[List[int]] = None

    # Aplicabilidad
    sectores: Optional[List[str]] = None
    tipologias_art3: Optional[List[str]] = None
    triggers_art11: Optional[List[str]] = None
    componentes_ambientales: Optional[List[str]] = None
    regiones_aplicables: Optional[List[str]] = None

    # Proceso SEIA
    etapa_proceso: Optional[str] = None
    actor_principal: Optional[str] = None

    # Contenido (si no se sube archivo)
    contenido: Optional[str] = None
    resumen: Optional[str] = None
    palabras_clave: Optional[List[str]] = None


class DocumentoResponse(BaseModel):
    """Respuesta basica de documento."""
    id: int
    titulo: str
    tipo: str
    numero: Optional[str]
    fecha_publicacion: Optional[date]
    estado: str
    categoria_id: Optional[int]
    categoria_nombre: Optional[str] = None
    tiene_archivo: bool = False
    fragmentos_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentoDetalleResponse(DocumentoResponse):
    """Respuesta completa de documento con todos los campos."""
    fecha_vigencia: Optional[date]
    fecha_vigencia_fin: Optional[date]
    organismo: Optional[str]
    url_fuente: Optional[str]
    resolucion_aprobatoria: Optional[str]

    sectores: List[str] = []
    tipologias_art3: List[str] = []
    triggers_art11: List[str] = []
    componentes_ambientales: List[str] = []
    regiones_aplicables: List[str] = []

    etapa_proceso: Optional[str]
    actor_principal: Optional[str]

    resumen: Optional[str]
    palabras_clave: List[str] = []

    # Contenido completo del documento
    contenido_completo: Optional[str] = None
    contenido_chars: int = 0

    # Archivo
    archivo_nombre: Optional[str] = None
    archivo_tipo: Optional[str] = None
    archivo_tamano_mb: Optional[float] = None

    # Relaciones
    colecciones: List[dict] = []
    documentos_relacionados: List[dict] = []

    version: int
    updated_at: Optional[datetime]


class DocumentoUpdateData(BaseModel):
    """Datos para actualizar documento."""
    titulo: Optional[str] = Field(None, min_length=1, max_length=500)
    tipo: Optional[str] = Field(None, min_length=1, max_length=100)
    numero: Optional[str] = Field(None, max_length=100)
    fecha_publicacion: Optional[date] = None
    fecha_vigencia: Optional[date] = None
    organismo: Optional[str] = None
    url_fuente: Optional[str] = None
    resolucion_aprobatoria: Optional[str] = None
    estado: Optional[str] = None

    categoria_id: Optional[int] = None
    coleccion_ids: Optional[List[int]] = None

    sectores: Optional[List[str]] = None
    tipologias_art3: Optional[List[str]] = None
    triggers_art11: Optional[List[str]] = None
    componentes_ambientales: Optional[List[str]] = None
    regiones_aplicables: Optional[List[str]] = None

    etapa_proceso: Optional[str] = None
    actor_principal: Optional[str] = None

    resumen: Optional[str] = None
    palabras_clave: Optional[List[str]] = None


class FragmentoResponse(BaseModel):
    """Respuesta de fragmento."""
    id: int
    seccion: Optional[str]
    contenido: str
    contenido_truncado: bool = False
    temas: List[str] = []
    tiene_embedding: bool = False


class ListaDocumentosResponse(BaseModel):
    """Respuesta de lista de documentos."""
    total: int
    limite: int
    offset: int
    documentos: List[DocumentoResponse]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/",
    response_model=DocumentoResponse,
    status_code=201,
    summary="Crear documento",
    description="""
    Crea un nuevo documento en el corpus RAG.

    **Flujo:**
    1. Si se sube archivo PDF/DOCX:
       - Se guarda en storage
       - Se extrae texto automaticamente
       - Se detectan duplicados por hash
    2. Se crea registro en BD
    3. Si procesar_automaticamente=true:
       - Se segmenta el contenido
       - Se generan embeddings
       - Se crean fragmentos
    """
)
async def crear_documento(
    datos: str = Form(..., description="JSON con DocumentoCreateData"),
    archivo: Optional[UploadFile] = File(None, description="Archivo PDF o DOCX"),
    procesar_automaticamente: bool = Form(True, description="Generar fragmentos y embeddings"),
    db: AsyncSession = Depends(get_db),
    archivo_service: ArchivoService = Depends(get_archivo_service),
) -> DocumentoResponse:
    """Crea un nuevo documento en el corpus."""
    # Parsear datos JSON
    try:
        documento_data = DocumentoCreateData(**json.loads(datos))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON invalido en campo 'datos'")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en datos: {str(e)}")

    # Verificar categoria existe
    categoria = await db.get(Categoria, documento_data.categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    if not categoria.activo:
        raise HTTPException(status_code=400, detail="La categoria esta desactivada")

    archivo_id = None
    contenido = documento_data.contenido

    # Procesar archivo si se subio
    if archivo:
        if not archivo.content_type:
            raise HTTPException(status_code=400, detail="No se pudo detectar tipo de archivo")

        if not archivo_service.validar_tipo_archivo(archivo.content_type):
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido: {archivo.content_type}. Solo PDF y DOCX."
            )

        # Leer contenido
        archivo_contenido = await archivo.read()

        # Verificar duplicado por hash
        hash_sha256 = archivo_service.calcular_hash(archivo_contenido)
        existe_hash = await db.execute(
            select(ArchivoOriginal).where(ArchivoOriginal.hash_sha256 == hash_sha256)
        )
        if existe_hash.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Este archivo ya existe en el sistema (duplicado detectado por hash)"
            )

        # Guardar archivo
        ruta_storage, _, tamano, nombre_storage = await archivo_service.guardar_archivo(
            contenido=archivo_contenido,
            nombre_original=archivo.filename or "documento",
            mime_type=archivo.content_type,
        )

        # Extraer texto
        try:
            texto_extraido, paginas = archivo_service.extraer_texto(ruta_storage, archivo.content_type)
        except Exception as e:
            # Si falla extraccion, eliminar archivo
            await archivo_service.eliminar_archivo(ruta_storage)
            raise HTTPException(status_code=500, detail=f"Error extrayendo texto: {str(e)}")

        # Crear registro de archivo
        archivo_original = ArchivoOriginal(
            nombre_original=archivo.filename or "documento",
            nombre_storage=nombre_storage,
            ruta_storage=ruta_storage,
            mime_type=archivo.content_type,
            tamano_bytes=tamano,
            hash_sha256=hash_sha256,
            texto_extraido=texto_extraido,
            paginas=paginas,
            procesado_at=datetime.utcnow(),
        )
        db.add(archivo_original)
        await db.flush()

        archivo_id = archivo_original.id
        contenido = texto_extraido

    # Validar que hay contenido
    if not contenido:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar contenido de texto o subir un archivo"
        )

    # Crear documento
    documento = Documento(
        titulo=documento_data.titulo,
        tipo=documento_data.tipo,
        numero=documento_data.numero,
        fecha_publicacion=documento_data.fecha_publicacion,
        fecha_vigencia=documento_data.fecha_vigencia,
        organismo=documento_data.organismo,
        url_fuente=documento_data.url_fuente,
        resolucion_aprobatoria=documento_data.resolucion_aprobatoria,
        contenido_completo=contenido,
        estado="vigente",
        categoria_id=documento_data.categoria_id,
        archivo_id=archivo_id,
        sectores=documento_data.sectores or [],
        tipologias_art3=documento_data.tipologias_art3 or [],
        triggers_art11=documento_data.triggers_art11 or [],
        componentes_ambientales=documento_data.componentes_ambientales or [],
        regiones_aplicables=documento_data.regiones_aplicables or [],
        etapa_proceso=documento_data.etapa_proceso,
        actor_principal=documento_data.actor_principal,
        resumen=documento_data.resumen,
        palabras_clave=documento_data.palabras_clave or [],
        version=1,
    )
    db.add(documento)
    await db.flush()

    # Agregar a colecciones
    if documento_data.coleccion_ids:
        for col_id in documento_data.coleccion_ids:
            coleccion = await db.get(Coleccion, col_id)
            if coleccion:
                db.add(DocumentoColeccion(
                    documento_id=documento.id,
                    coleccion_id=col_id,
                ))

    await db.commit()
    await db.refresh(documento)

    # Procesar fragmentos si esta habilitado
    if procesar_automaticamente and contenido:
        try:
            from app.services.rag.ingestor import IngestorLegal
            ingestor = IngestorLegal()
            await ingestor.procesar_documento_existente(db, documento.id)
        except Exception as e:
            # Log error pero no fallar la creacion
            import logging
            logging.getLogger(__name__).error(f"Error procesando fragmentos: {e}")

    return DocumentoResponse(
        id=documento.id,
        titulo=documento.titulo,
        tipo=documento.tipo,
        numero=documento.numero,
        fecha_publicacion=documento.fecha_publicacion,
        estado=documento.estado,
        categoria_id=documento.categoria_id,
        categoria_nombre=categoria.nombre,
        tiene_archivo=archivo_id is not None,
        fragmentos_count=0,
        created_at=documento.created_at,
    )


async def _obtener_ids_categoria_con_hijos(
    db: AsyncSession,
    categoria_id: int
) -> List[int]:
    """
    Obtiene el ID de una categoría y todos sus descendientes (hijos, nietos, etc).
    Útil para filtrar documentos incluyendo subcategorías.
    """
    from sqlalchemy import text

    # Usar CTE recursiva para obtener toda la jerarquía
    result = await db.execute(
        text("""
            WITH RECURSIVE categoria_tree AS (
                -- Caso base: la categoría seleccionada
                SELECT id FROM legal.categorias WHERE id = :cat_id
                UNION ALL
                -- Caso recursivo: hijos de las categorías en el árbol
                SELECT c.id
                FROM legal.categorias c
                INNER JOIN categoria_tree ct ON c.parent_id = ct.id
            )
            SELECT id FROM categoria_tree
        """),
        {"cat_id": categoria_id}
    )
    return [row[0] for row in result.fetchall()]


@router.get(
    "/",
    response_model=ListaDocumentosResponse,
    summary="Listar documentos",
    description="Lista documentos del corpus con filtros avanzados."
)
async def listar_documentos(
    # Filtros
    categoria_id: Optional[int] = Query(None, description="Filtrar por categoria (incluye subcategorias)"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de documento"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    sector: Optional[str] = Query(None, description="Filtrar por sector"),
    trigger_art11: Optional[str] = Query(None, description="Filtrar por trigger Art.11 (a-f)"),
    componente: Optional[str] = Query(None, description="Filtrar por componente ambiental"),
    coleccion_id: Optional[int] = Query(None, description="Filtrar por coleccion"),
    etapa_proceso: Optional[str] = Query(None, description="Filtrar por etapa SEIA"),
    actor_principal: Optional[str] = Query(None, description="Filtrar por actor"),

    # Busqueda
    q: Optional[str] = Query(None, description="Busqueda en titulo"),

    # Paginacion
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),

    # Ordenamiento
    orden: str = Query("fecha_desc", regex="^(fecha_desc|fecha_asc|titulo_asc|titulo_desc)$"),

    db: AsyncSession = Depends(get_db),
) -> ListaDocumentosResponse:
    """Lista documentos con filtros."""
    query = select(Documento)
    count_query = select(func.count(Documento.id))

    # Aplicar filtros
    filtros = []

    if categoria_id:
        # Obtener IDs de la categoría y todas sus subcategorías
        categoria_ids = await _obtener_ids_categoria_con_hijos(db, categoria_id)
        filtros.append(Documento.categoria_id.in_(categoria_ids))
    if tipo:
        filtros.append(Documento.tipo == tipo)
    if estado:
        filtros.append(Documento.estado == estado)
    if sector:
        filtros.append(Documento.sectores.contains([sector]))
    if trigger_art11:
        filtros.append(Documento.triggers_art11.contains([trigger_art11]))
    if componente:
        filtros.append(Documento.componentes_ambientales.contains([componente]))
    if etapa_proceso:
        filtros.append(Documento.etapa_proceso == etapa_proceso)
    if actor_principal:
        filtros.append(Documento.actor_principal == actor_principal)

    if coleccion_id:
        query = query.join(DocumentoColeccion).where(DocumentoColeccion.coleccion_id == coleccion_id)
        count_query = count_query.join(DocumentoColeccion).where(DocumentoColeccion.coleccion_id == coleccion_id)

    if q:
        filtros.append(Documento.titulo.ilike(f"%{q}%"))

    for f in filtros:
        query = query.where(f)
        count_query = count_query.where(f)

    # Obtener total
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Ordenamiento
    orden_map = {
        "fecha_desc": Documento.created_at.desc(),
        "fecha_asc": Documento.created_at.asc(),
        "titulo_asc": Documento.titulo.asc(),
        "titulo_desc": Documento.titulo.desc(),
    }
    query = query.order_by(orden_map[orden])

    # Paginacion
    query = query.limit(limite).offset(offset)

    # Ejecutar
    result = await db.execute(query.options(selectinload(Documento.categoria)))
    documentos = result.scalars().all()

    # Construir respuesta
    docs_response = []
    for doc in documentos:
        # Contar fragmentos
        frag_count_result = await db.execute(
            select(func.count(Fragmento.id)).where(Fragmento.documento_id == doc.id)
        )
        frag_count = frag_count_result.scalar() or 0

        docs_response.append(DocumentoResponse(
            id=doc.id,
            titulo=doc.titulo,
            tipo=doc.tipo,
            numero=doc.numero,
            fecha_publicacion=doc.fecha_publicacion,
            estado=doc.estado,
            categoria_id=doc.categoria_id,
            categoria_nombre=doc.categoria.nombre if doc.categoria else None,
            tiene_archivo=doc.archivo_id is not None,
            fragmentos_count=frag_count,
            created_at=doc.created_at,
        ))

    return ListaDocumentosResponse(
        total=total,
        limite=limite,
        offset=offset,
        documentos=docs_response,
    )


@router.get(
    "/tipos",
    summary="Listar tipos de documento",
    description="Lista los tipos de documento distintos en el corpus."
)
async def listar_tipos_documento(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista tipos de documento disponibles."""
    result = await db.execute(
        select(Documento.tipo, func.count(Documento.id))
        .group_by(Documento.tipo)
        .order_by(func.count(Documento.id).desc())
    )
    tipos = result.fetchall()

    return {
        "tipos": [{"tipo": t[0], "cantidad": t[1]} for t in tipos],
        "total_tipos": len(tipos),
    }


@router.get(
    "/{documento_id}",
    response_model=DocumentoDetalleResponse,
    summary="Obtener documento",
    description="Obtiene un documento con todos sus detalles."
)
async def obtener_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_db),
) -> DocumentoDetalleResponse:
    """Obtiene un documento completo."""
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Cargar categoria
    categoria = await db.get(Categoria, documento.categoria_id) if documento.categoria_id else None

    # Cargar archivo
    archivo = await db.get(ArchivoOriginal, documento.archivo_id) if documento.archivo_id else None

    # Contar fragmentos
    frag_count_result = await db.execute(
        select(func.count(Fragmento.id)).where(Fragmento.documento_id == documento.id)
    )
    frag_count = frag_count_result.scalar() or 0

    # Cargar colecciones
    colecciones_result = await db.execute(
        select(Coleccion)
        .join(DocumentoColeccion)
        .where(DocumentoColeccion.documento_id == documento.id)
    )
    colecciones = colecciones_result.scalars().all()

    # Cargar relaciones
    relaciones_result = await db.execute(
        select(RelacionDocumento, Documento)
        .join(Documento, RelacionDocumento.documento_destino_id == Documento.id)
        .where(RelacionDocumento.documento_origen_id == documento.id)
    )
    relaciones = relaciones_result.fetchall()

    return DocumentoDetalleResponse(
        id=documento.id,
        titulo=documento.titulo,
        tipo=documento.tipo,
        numero=documento.numero,
        fecha_publicacion=documento.fecha_publicacion,
        fecha_vigencia=documento.fecha_vigencia,
        fecha_vigencia_fin=documento.fecha_vigencia_fin,
        estado=documento.estado,
        organismo=documento.organismo,
        url_fuente=documento.url_fuente,
        resolucion_aprobatoria=documento.resolucion_aprobatoria,

        categoria_id=documento.categoria_id,
        categoria_nombre=categoria.nombre if categoria else None,

        sectores=documento.sectores or [],
        tipologias_art3=documento.tipologias_art3 or [],
        triggers_art11=documento.triggers_art11 or [],
        componentes_ambientales=documento.componentes_ambientales or [],
        regiones_aplicables=documento.regiones_aplicables or [],

        etapa_proceso=documento.etapa_proceso,
        actor_principal=documento.actor_principal,

        resumen=documento.resumen,
        palabras_clave=documento.palabras_clave or [],

        # Contenido completo
        contenido_completo=documento.contenido_completo,
        contenido_chars=len(documento.contenido_completo) if documento.contenido_completo else 0,

        tiene_archivo=archivo is not None,
        archivo_nombre=archivo.nombre_original if archivo else None,
        archivo_tipo=archivo.mime_type if archivo else None,
        archivo_tamano_mb=round(archivo.tamano_bytes / (1024 * 1024), 2) if archivo else None,

        colecciones=[{"id": c.id, "codigo": c.codigo, "nombre": c.nombre} for c in colecciones],
        documentos_relacionados=[
            {
                "id": doc.id,
                "titulo": doc.titulo,
                "tipo": doc.tipo,
                "relacion": rel.tipo_relacion,
            }
            for rel, doc in relaciones
        ],

        fragmentos_count=frag_count,
        version=documento.version,
        created_at=documento.created_at,
        updated_at=documento.updated_at,
    )


@router.get(
    "/{documento_id}/fragmentos",
    summary="Obtener fragmentos",
    description="Lista los fragmentos de un documento."
)
async def obtener_fragmentos_documento(
    documento_id: int,
    limite: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista fragmentos de un documento."""
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Contar total
    total_result = await db.execute(
        select(func.count(Fragmento.id)).where(Fragmento.documento_id == documento_id)
    )
    total = total_result.scalar() or 0

    # Obtener fragmentos
    result = await db.execute(
        select(Fragmento)
        .where(Fragmento.documento_id == documento_id)
        .order_by(Fragmento.id)
        .limit(limite)
        .offset(offset)
    )
    fragmentos = result.scalars().all()

    return {
        "documento_id": documento_id,
        "documento_titulo": documento.titulo,
        "total": total,
        "limite": limite,
        "offset": offset,
        "fragmentos": [
            FragmentoResponse(
                id=f.id,
                seccion=f.seccion,
                contenido=f.contenido[:1000] if len(f.contenido) > 1000 else f.contenido,
                contenido_truncado=len(f.contenido) > 1000,
                temas=f.temas or [],
                tiene_embedding=f.embedding is not None,
            )
            for f in fragmentos
        ],
    }


@router.get(
    "/{documento_id}/archivo",
    summary="Descargar archivo",
    description="Descarga el archivo original del documento."
)
async def descargar_archivo_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_db),
    archivo_service: ArchivoService = Depends(get_archivo_service),
):
    """Descarga el archivo original."""
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if not documento.archivo_id:
        raise HTTPException(status_code=404, detail="Este documento no tiene archivo original")

    archivo = await db.get(ArchivoOriginal, documento.archivo_id)
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado en BD")

    ruta = await archivo_service.obtener_ruta_completa(archivo.ruta_storage)
    if not ruta.exists():
        raise HTTPException(status_code=500, detail="Archivo fisico no encontrado")

    return FileResponse(
        path=str(ruta),
        filename=archivo.nombre_original,
        media_type=archivo.mime_type,
    )


@router.get(
    "/{documento_id}/contenido",
    summary="Descargar contenido como TXT",
    description="Descarga el contenido del documento como archivo de texto plano."
)
async def descargar_contenido_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Descarga el contenido del documento como TXT."""
    from fastapi.responses import Response

    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if not documento.contenido_completo:
        raise HTTPException(status_code=404, detail="Este documento no tiene contenido de texto")

    # Generar nombre de archivo seguro
    nombre_seguro = "".join(c for c in documento.titulo if c.isalnum() or c in (' ', '-', '_')).strip()
    nombre_seguro = nombre_seguro[:100]  # Limitar longitud
    if documento.numero:
        nombre_archivo = f"{documento.tipo}_{documento.numero}_{nombre_seguro}.txt"
    else:
        nombre_archivo = f"{documento.tipo}_{nombre_seguro}.txt"

    # Crear encabezado con metadatos
    encabezado = f"""================================================================================
{documento.titulo}
================================================================================
Tipo: {documento.tipo}
Numero: {documento.numero or 'N/A'}
Organismo: {documento.organismo or 'N/A'}
Fecha publicacion: {documento.fecha_publicacion or 'N/A'}
Estado: {documento.estado}
================================================================================

"""
    contenido_final = encabezado + documento.contenido_completo

    return Response(
        content=contenido_final.encode('utf-8'),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
        }
    )


@router.put(
    "/{documento_id}",
    response_model=DocumentoResponse,
    summary="Actualizar documento",
    description="Actualiza metadatos de un documento."
)
async def actualizar_documento(
    documento_id: int,
    datos: DocumentoUpdateData,
    db: AsyncSession = Depends(get_db),
) -> DocumentoResponse:
    """Actualiza un documento."""
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Verificar categoria si se proporciona
    if datos.categoria_id:
        categoria = await db.get(Categoria, datos.categoria_id)
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria no encontrada")

    # Guardar version anterior en historial
    historial = HistorialVersion(
        documento_id=documento.id,
        version=documento.version,
        datos_documento={
            "titulo": documento.titulo,
            "tipo": documento.tipo,
            "estado": documento.estado,
        },
        tipo_cambio="edicion",
        descripcion_cambio="Actualizacion de metadatos",
    )
    db.add(historial)

    # Actualizar campos
    update_data = datos.model_dump(exclude_unset=True, exclude={"coleccion_ids"})
    for campo, valor in update_data.items():
        setattr(documento, campo, valor)

    documento.version += 1

    # Actualizar colecciones si se proporcionan
    if datos.coleccion_ids is not None:
        # Eliminar colecciones actuales
        await db.execute(
            delete(DocumentoColeccion).where(DocumentoColeccion.documento_id == documento.id)
        )
        # Agregar nuevas
        for col_id in datos.coleccion_ids:
            db.add(DocumentoColeccion(documento_id=documento.id, coleccion_id=col_id))

    await db.commit()
    await db.refresh(documento)

    # Cargar categoria para respuesta
    categoria = await db.get(Categoria, documento.categoria_id) if documento.categoria_id else None

    return DocumentoResponse(
        id=documento.id,
        titulo=documento.titulo,
        tipo=documento.tipo,
        numero=documento.numero,
        fecha_publicacion=documento.fecha_publicacion,
        estado=documento.estado,
        categoria_id=documento.categoria_id,
        categoria_nombre=categoria.nombre if categoria else None,
        tiene_archivo=documento.archivo_id is not None,
        fragmentos_count=0,
        created_at=documento.created_at,
    )


@router.post(
    "/{documento_id}/reprocesar",
    summary="Reprocesar documento",
    description="Regenera fragmentos y embeddings de un documento."
)
async def reprocesar_documento(
    documento_id: int,
    regenerar_embeddings: bool = Query(True, description="Regenerar embeddings"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reprocesa fragmentos de un documento."""
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if not documento.contenido_completo:
        raise HTTPException(status_code=400, detail="Documento sin contenido para procesar")

    # Eliminar fragmentos existentes
    await db.execute(
        delete(Fragmento).where(Fragmento.documento_id == documento_id)
    )

    # Reprocesar
    try:
        from app.services.rag.ingestor import IngestorLegal
        ingestor = IngestorLegal()
        resultado = await ingestor.procesar_documento_existente(db, documento_id)

        return {
            "mensaje": "Documento reprocesado",
            "documento_id": documento_id,
            "fragmentos_creados": resultado.get("fragmentos_creados", 0),
            "temas_detectados": resultado.get("temas_detectados", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reprocesando: {str(e)}")


@router.delete(
    "/{documento_id}",
    status_code=204,
    summary="Eliminar documento",
    description="Elimina un documento y opcionalmente su archivo."
)
async def eliminar_documento(
    documento_id: int,
    eliminar_archivo: bool = Query(True, description="Eliminar archivo fisico"),
    db: AsyncSession = Depends(get_db),
    archivo_service: ArchivoService = Depends(get_archivo_service),
):
    """Elimina un documento."""
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Eliminar archivo si existe y se solicita
    if eliminar_archivo and documento.archivo_id:
        archivo = await db.get(ArchivoOriginal, documento.archivo_id)
        if archivo:
            await archivo_service.eliminar_archivo(archivo.ruta_storage)
            await db.delete(archivo)

    # Eliminar documento (cascade elimina fragmentos, relaciones, etc.)
    await db.delete(documento)
    await db.commit()


@router.post(
    "/{documento_id}/relacion",
    status_code=201,
    summary="Crear relacion",
    description="Crea una relacion entre dos documentos."
)
async def crear_relacion_documento(
    documento_id: int,
    documento_destino_id: int = Query(..., description="ID documento destino"),
    tipo_relacion: str = Query(..., description="Tipo: reglamenta, interpreta, reemplaza, complementa, cita"),
    descripcion: Optional[str] = Query(None, description="Descripcion de la relacion"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Crea relacion entre documentos."""
    # Verificar documentos existen
    origen = await db.get(Documento, documento_id)
    destino = await db.get(Documento, documento_destino_id)

    if not origen:
        raise HTTPException(status_code=404, detail="Documento origen no encontrado")
    if not destino:
        raise HTTPException(status_code=404, detail="Documento destino no encontrado")
    if documento_id == documento_destino_id:
        raise HTTPException(status_code=400, detail="No se puede crear relacion consigo mismo")

    # Verificar tipos validos
    tipos_validos = ["reglamenta", "interpreta", "reemplaza", "complementa", "cita", "modifica"]
    if tipo_relacion not in tipos_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo invalido. Permitidos: {', '.join(tipos_validos)}"
        )

    # Verificar no existe
    existe = await db.execute(
        select(RelacionDocumento).where(
            RelacionDocumento.documento_origen_id == documento_id,
            RelacionDocumento.documento_destino_id == documento_destino_id,
            RelacionDocumento.tipo_relacion == tipo_relacion,
        )
    )
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Esta relacion ya existe")

    relacion = RelacionDocumento(
        documento_origen_id=documento_id,
        documento_destino_id=documento_destino_id,
        tipo_relacion=tipo_relacion,
        descripcion=descripcion,
    )
    db.add(relacion)
    await db.commit()

    return {
        "mensaje": "Relacion creada",
        "id": relacion.id,
        "origen": {"id": origen.id, "titulo": origen.titulo},
        "destino": {"id": destino.id, "titulo": destino.titulo},
        "tipo": tipo_relacion,
    }
