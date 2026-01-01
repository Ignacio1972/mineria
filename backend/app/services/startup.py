"""
Servicio de inicialización del backend.
Verifica y carga datos necesarios al iniciar la aplicación.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Directorio de datos legales
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "legal" / "processed"


async def verificar_corpus_legal() -> bool:
    """Verifica si el corpus legal está cargado."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM legal.fragmentos")
        )
        count = result.scalar()
        return count > 0


async def cargar_corpus_legal() -> dict:
    """
    Carga el corpus legal si está vacío.

    Returns:
        Estadísticas de la carga
    """
    # Verificar si ya hay datos
    if await verificar_corpus_legal():
        logger.info("Corpus legal ya cargado, omitiendo inicialización")
        return {"status": "already_loaded"}

    logger.info("Corpus legal vacío, iniciando carga automática...")

    # Importar aquí para evitar carga circular
    from app.services.rag.embeddings import get_embedding_service

    embedding_service = get_embedding_service()

    # Buscar archivos JSON
    archivos = list(DATA_DIR.glob("*.json")) if DATA_DIR.exists() else []

    if not archivos:
        logger.warning(f"No se encontraron archivos JSON en {DATA_DIR}")
        return {"status": "no_files", "path": str(DATA_DIR)}

    estadisticas = {
        "status": "loaded",
        "documentos_procesados": 0,
        "fragmentos_creados": 0,
        "errores": [],
    }

    async with AsyncSessionLocal() as session:
        for archivo in archivos:
            try:
                logger.info(f"Procesando: {archivo.name}")

                with open(archivo, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)

                resultado = await _cargar_documento(
                    session, doc_data, embedding_service
                )

                estadisticas["documentos_procesados"] += 1
                estadisticas["fragmentos_creados"] += resultado.get("fragmentos_creados", 0)

                logger.info(
                    f"  -> {archivo.name}: {resultado.get('fragmentos_creados', 0)} fragmentos"
                )

            except Exception as e:
                logger.error(f"Error procesando {archivo.name}: {e}")
                estadisticas["errores"].append(str(e))

    logger.info(
        f"Carga completada: {estadisticas['documentos_procesados']} docs, "
        f"{estadisticas['fragmentos_creados']} fragmentos"
    )

    return estadisticas


async def _cargar_documento(
    session: AsyncSession,
    doc_data: dict,
    embedding_service
) -> dict:
    """Carga un documento y sus fragmentos."""

    # Parsear fecha
    fecha_pub = None
    if doc_data.get("fecha_publicacion"):
        try:
            fecha_pub = datetime.strptime(
                doc_data["fecha_publicacion"], "%Y-%m-%d"
            ).date()
        except ValueError:
            pass

    # Insertar documento
    result = await session.execute(
        text("""
            INSERT INTO legal.documentos
            (titulo, tipo, numero, fecha_publicacion, organismo, url_fuente, estado)
            VALUES (:titulo, :tipo, :numero, :fecha, :organismo, :url, 'vigente')
            ON CONFLICT DO NOTHING
            RETURNING id
        """),
        {
            "titulo": doc_data["titulo"],
            "tipo": doc_data["tipo"],
            "numero": doc_data.get("numero"),
            "fecha": fecha_pub,
            "organismo": doc_data.get("organismo"),
            "url": doc_data.get("url_fuente"),
        }
    )

    row = result.fetchone()
    if not row:
        # El documento ya existe
        result = await session.execute(
            text("SELECT id FROM legal.documentos WHERE titulo = :titulo"),
            {"titulo": doc_data["titulo"]}
        )
        row = result.fetchone()
        documento_id = row[0]

        # Verificar si tiene fragmentos
        result = await session.execute(
            text("SELECT COUNT(*) FROM legal.fragmentos WHERE documento_id = :doc_id"),
            {"doc_id": documento_id}
        )
        count = result.scalar()
        if count > 0:
            return {"documento_id": documento_id, "fragmentos_creados": 0}
    else:
        documento_id = row[0]

    # Procesar artículos como fragmentos
    articulos = doc_data.get("articulos", [])
    textos = []
    fragmentos_data = []

    for art in articulos:
        contenido = art.get("contenido", "")
        if len(contenido) < 50:
            continue

        temas = _detectar_temas(contenido)

        seccion = f"Artículo {art['numero']}"
        if art.get("titulo"):
            seccion += f" - {art['titulo']}"

        textos.append(contenido)
        fragmentos_data.append({
            "seccion": seccion,
            "numero": art["numero"],
            "contenido": contenido,
            "temas": temas,
        })

    fragmentos_creados = 0

    if textos:
        # Generar embeddings en batch
        embeddings = embedding_service.embed_texts(textos)

        # Insertar fragmentos
        for frag, embedding in zip(fragmentos_data, embeddings):
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
            await session.execute(
                text(f"""
                    INSERT INTO legal.fragmentos
                    (documento_id, seccion, numero_seccion, contenido, temas, embedding)
                    VALUES (:doc_id, :seccion, :num, :contenido, :temas, '{embedding_str}'::vector)
                """),
                {
                    "doc_id": documento_id,
                    "seccion": frag["seccion"],
                    "num": frag["numero"],
                    "contenido": frag["contenido"],
                    "temas": frag["temas"],
                }
            )
            fragmentos_creados += 1

    await session.commit()

    return {
        "documento_id": documento_id,
        "fragmentos_creados": fragmentos_creados,
    }


def _detectar_temas(texto: str) -> list:
    """Detecta temas relevantes en un texto."""

    TEMAS_KEYWORDS = {
        'agua': ['agua', 'hídrico', 'río', 'lago', 'humedal', 'acuífero', 'caudal', 'DGA'],
        'aire': ['aire', 'emisión', 'atmosférico', 'material particulado', 'contaminante'],
        'flora_fauna': ['flora', 'fauna', 'especie', 'biodiversidad', 'hábitat', 'SAG'],
        'suelo': ['suelo', 'erosión', 'contaminación del suelo', 'residuo'],
        'comunidades_indigenas': ['indígena', 'pueblo originario', 'consulta', 'CONADI', 'ADI'],
        'patrimonio': ['patrimonio', 'arqueológico', 'histórico', 'monumento', 'CMN'],
        'participacion': ['participación ciudadana', 'consulta pública', 'observación'],
        'eia': ['EIA', 'estudio de impacto', 'línea base', 'predicción de impactos'],
        'dia': ['DIA', 'declaración de impacto'],
        'rca': ['RCA', 'resolución de calificación', 'condición', 'compromiso'],
        'areas_protegidas': ['área protegida', 'SNASPE', 'parque nacional', 'reserva', 'santuario'],
        'glaciares': ['glaciar', 'criósfera', 'permafrost', 'ambiente periglaciar'],
        'mineria': ['minería', 'faena minera', 'SERNAGEOMIN', 'relaves', 'botadero', 'mineral'],
    }

    texto_lower = texto.lower()
    temas = []

    for tema, keywords in TEMAS_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in texto_lower:
                temas.append(tema)
                break

    return temas if temas else ['general']


async def inicializar_aplicacion():
    """
    Punto de entrada para inicialización del backend.
    Se ejecuta al iniciar la aplicación.
    """
    logger.info("Iniciando verificación de datos...")

    try:
        resultado = await cargar_corpus_legal()
        if resultado["status"] == "loaded":
            logger.info(
                f"Corpus legal inicializado: {resultado['fragmentos_creados']} fragmentos"
            )
        elif resultado["status"] == "already_loaded":
            logger.info("Corpus legal verificado OK")
        else:
            logger.warning(f"Estado del corpus: {resultado}")
    except Exception as e:
        logger.error(f"Error en inicialización del corpus: {e}")
        # No fallar el inicio, el sistema puede funcionar sin RAG
