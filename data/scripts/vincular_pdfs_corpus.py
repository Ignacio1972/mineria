#!/usr/bin/env python3
"""
Script para vincular PDFs existentes a documentos del corpus.

Los PDFs fueron descargados por ingestar_guias_sea.py pero no se crearon
los registros en legal.archivos_originales ni se vincularon a documentos.

Este script:
1. Lee documentos con url_fuente
2. Calcula hash MD5 de la URL para encontrar el PDF
3. Crea registro en archivos_originales con metadata del PDF
4. Actualiza documento.archivo_id
"""

import asyncio
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
import logging

# Agregar el directorio backend al path
if Path("/app").exists() and Path("/app/app").exists():
    sys.path.insert(0, "/app")
else:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración
DATA_BASE = Path("/app/data") if Path("/app/data").exists() else Path(__file__).parent.parent
PDF_DIR = DATA_BASE / "legal" / "guias_sea"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mineria:mineria_dev_2024@db:5432/mineria"
).replace("postgresql://", "postgresql+asyncpg://")


def calcular_hash_url(url: str) -> str:
    """Calcula el nombre de archivo basado en hash MD5 de la URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12] + ".pdf"


def calcular_sha256(ruta_archivo: Path) -> str:
    """Calcula hash SHA256 del contenido del archivo."""
    sha256 = hashlib.sha256()
    with open(ruta_archivo, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def contar_paginas_pdf(ruta_pdf: Path) -> int:
    """Cuenta las páginas de un PDF usando PyMuPDF."""
    try:
        import fitz
        with fitz.open(str(ruta_pdf)) as doc:
            return len(doc)
    except Exception as e:
        logger.warning(f"Error contando páginas de {ruta_pdf}: {e}")
        return 0


async def vincular_pdfs():
    """Proceso principal de vinculación."""
    print("=" * 70)
    print("VINCULACIÓN DE PDFs AL CORPUS")
    print("Sistema de Prefactibilidad Ambiental Minera")
    print("=" * 70)

    if not PDF_DIR.exists():
        logger.error(f"No existe directorio de PDFs: {PDF_DIR}")
        return

    # Listar PDFs disponibles
    pdfs_disponibles = {f.name: f for f in PDF_DIR.glob("*.pdf")}
    print(f"\nPDFs disponibles: {len(pdfs_disponibles)}")

    # Crear conexión a BD
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    stats = {
        "documentos_procesados": 0,
        "pdfs_encontrados": 0,
        "archivos_creados": 0,
        "documentos_actualizados": 0,
        "ya_vinculados": 0,
        "sin_pdf": 0,
        "errores": 0,
    }

    async with async_session() as session:
        # Obtener documentos con URL pero sin archivo
        result = await session.execute(
            text("""
                SELECT id, titulo, url_fuente
                FROM legal.documentos
                WHERE url_fuente IS NOT NULL
                  AND url_fuente <> ''
                  AND archivo_id IS NULL
                ORDER BY id
            """)
        )
        documentos = result.fetchall()
        print(f"Documentos sin vincular: {len(documentos)}\n")

        for doc_id, titulo, url_fuente in documentos:
            stats["documentos_procesados"] += 1
            titulo_corto = titulo[:55] + "..." if len(titulo) > 55 else titulo

            # Calcular nombre esperado del PDF
            nombre_pdf = calcular_hash_url(url_fuente)

            if nombre_pdf not in pdfs_disponibles:
                logger.debug(f"[{doc_id}] Sin PDF: {titulo_corto}")
                stats["sin_pdf"] += 1
                continue

            stats["pdfs_encontrados"] += 1
            ruta_pdf = pdfs_disponibles[nombre_pdf]

            try:
                # Calcular metadata del archivo
                tamano = ruta_pdf.stat().st_size
                hash_sha256 = calcular_sha256(ruta_pdf)
                paginas = contar_paginas_pdf(ruta_pdf)

                # Verificar si ya existe un archivo con este hash
                existing = await session.execute(
                    text("SELECT id FROM legal.archivos_originales WHERE hash_sha256 = :hash"),
                    {"hash": hash_sha256}
                )
                archivo_existente = existing.fetchone()

                if archivo_existente:
                    archivo_id = archivo_existente[0]
                    logger.debug(f"[{doc_id}] Archivo ya existe: {archivo_id}")
                else:
                    # Crear registro en archivos_originales
                    # Ruta relativa desde /app/data para storage
                    ruta_storage = f"legal/guias_sea/{nombre_pdf}"

                    result = await session.execute(
                        text("""
                            INSERT INTO legal.archivos_originales
                            (nombre_original, nombre_storage, ruta_storage, mime_type,
                             tamano_bytes, hash_sha256, paginas, procesado_at, subido_por)
                            VALUES (:nombre_original, :nombre_storage, :ruta_storage,
                                    :mime_type, :tamano, :hash, :paginas, :procesado_at, :subido_por)
                            RETURNING id
                        """),
                        {
                            "nombre_original": nombre_pdf,
                            "nombre_storage": nombre_pdf,
                            "ruta_storage": ruta_storage,
                            "mime_type": "application/pdf",
                            "tamano": tamano,
                            "hash": hash_sha256,
                            "paginas": paginas,
                            "procesado_at": datetime.now(),
                            "subido_por": "vincular_pdfs_corpus.py",
                        }
                    )
                    archivo_id = result.scalar()
                    stats["archivos_creados"] += 1
                    logger.debug(f"[{doc_id}] Archivo creado: {archivo_id}")

                # Actualizar documento con archivo_id
                await session.execute(
                    text("UPDATE legal.documentos SET archivo_id = :archivo_id WHERE id = :doc_id"),
                    {"archivo_id": archivo_id, "doc_id": doc_id}
                )
                stats["documentos_actualizados"] += 1

                print(f"[{doc_id}] ✓ {titulo_corto}")

            except Exception as e:
                logger.error(f"[{doc_id}] Error: {e}")
                stats["errores"] += 1
                continue

        await session.commit()

    await engine.dispose()

    # Resumen
    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Documentos procesados:    {stats['documentos_procesados']}")
    print(f"PDFs encontrados:         {stats['pdfs_encontrados']}")
    print(f"Archivos creados:         {stats['archivos_creados']}")
    print(f"Documentos actualizados:  {stats['documentos_actualizados']}")
    print(f"Sin PDF disponible:       {stats['sin_pdf']}")
    print(f"Errores:                  {stats['errores']}")
    print()


if __name__ == "__main__":
    asyncio.run(vincular_pdfs())
