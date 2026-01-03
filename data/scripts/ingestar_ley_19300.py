#!/usr/bin/env python3
"""
Script para ingestar la Ley 19.300 desde PDF local al corpus RAG.

Ejecutar desde el contenedor del backend:
  docker exec mineria_backend python /app/data/scripts/ingestar_ley_19300.py
"""

import asyncio
import hashlib
import sys
from datetime import date, datetime
from pathlib import Path

if '/app' not in sys.path:
    sys.path.insert(0, '/app')

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.services.rag.ingestor import (
    IngestorLegal,
    DocumentoAIngestar,
    extraer_texto_pdf,
    get_ingestor_legal,
)


# Ruta al PDF local (en directorio montado)
PDF_PATH = Path("/app/data/legal/leyes/ley_19300_completa.pdf")

# Metadatos del documento
DOCUMENTO = {
    "titulo": "Ley 19.300 - Bases Generales del Medio Ambiente (Completa)",
    "tipo": "Ley",
    "numero": "19.300-FULL",
    "fecha_publicacion": date(1994, 3, 9),
    "organismo": "Ministerio Secretaria General de la Presidencia",
    "url_fuente": "https://www.bcn.cl/leychile/navegar?idNorma=30667",
    "categoria_id": 1,  # leyes
    "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura"],
    "triggers_art11": ["a", "b", "c", "d", "e", "f"],
    "componentes_ambientales": ["agua", "aire", "suelo", "flora", "fauna", "medio_humano", "patrimonio_cultural"],
    "etapa_proceso": "evaluacion",
    "descripcion": "Ley marco del sistema de evaluacion ambiental chileno"
}

DATA_BASE = Path("/app/data") if Path("/app/data").exists() else Path(__file__).parent.parent
PDF_DIR = DATA_BASE / "legal" / "leyes"


def calcular_sha256(ruta_archivo: Path) -> str:
    """Calcula hash SHA256 del contenido del archivo."""
    sha256 = hashlib.sha256()
    with open(ruta_archivo, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def contar_paginas_pdf(ruta_pdf: Path) -> int:
    """Cuenta las paginas de un PDF usando PyMuPDF."""
    try:
        import fitz
        with fitz.open(str(ruta_pdf)) as doc:
            return len(doc)
    except Exception:
        return 0


async def crear_archivo_original(db, ruta_pdf: Path, nombre_archivo: str) -> int | None:
    """Crea o recupera un registro en archivos_originales para el PDF."""
    tamano = ruta_pdf.stat().st_size
    hash_sha256 = calcular_sha256(ruta_pdf)
    paginas = contar_paginas_pdf(ruta_pdf)

    # Verificar si ya existe
    existing = await db.execute(
        text("SELECT id FROM legal.archivos_originales WHERE hash_sha256 = :hash"),
        {"hash": hash_sha256}
    )
    row = existing.fetchone()
    if row:
        print(f"  Archivo ya existe (ID: {row[0]})")
        return row[0]

    # Crear registro
    ruta_storage = f"legal/leyes/{nombre_archivo}"

    result = await db.execute(
        text("""
            INSERT INTO legal.archivos_originales
            (nombre_original, nombre_storage, ruta_storage, mime_type,
             tamano_bytes, hash_sha256, paginas, procesado_at, subido_por)
            VALUES (:nombre_original, :nombre_storage, :ruta_storage,
                    :mime_type, :tamano, :hash, :paginas, :procesado_at, :subido_por)
            RETURNING id
        """),
        {
            "nombre_original": "LEY-19300_09-MAR-1994.pdf",
            "nombre_storage": nombre_archivo,
            "ruta_storage": ruta_storage,
            "mime_type": "application/pdf",
            "tamano": tamano,
            "hash": hash_sha256,
            "paginas": paginas,
            "procesado_at": datetime.now(),
            "subido_por": "ingestar_ley_19300.py",
        }
    )
    return result.scalar()


async def main():
    """Funcion principal de ingesta."""
    print("=" * 70)
    print("INGESTA DE LEY 19.300 DESDE PDF LOCAL")
    print("=" * 70)

    if not PDF_PATH.exists():
        print(f"\nERROR: No se encuentra el PDF en: {PDF_PATH}")
        return

    print(f"\nPDF: {PDF_PATH}")
    print(f"Tamano: {PDF_PATH.stat().st_size / 1024:.1f} KB")

    # Extraer texto
    print("\nExtrayendo texto del PDF...")
    texto = extraer_texto_pdf(str(PDF_PATH))
    print(f"Caracteres extraidos: {len(texto):,}")

    if len(texto.strip()) < 500:
        print("ERROR: No se pudo extraer suficiente texto del PDF")
        return

    # Inicializar ingestor
    ingestor = get_ingestor_legal(usar_llm=True)

    async with AsyncSessionLocal() as db:
        # Verificar si ya existe con este numero
        result = await db.execute(
            text("SELECT id FROM legal.documentos WHERE numero = :numero"),
            {"numero": DOCUMENTO["numero"]}
        )
        existente = result.fetchone()

        if existente:
            print(f"\nDocumento ya existe (ID: {existente[0]}). Para reingestar, elimine primero:")
            print(f"  DELETE FROM legal.fragmentos WHERE documento_id = {existente[0]};")
            print(f"  DELETE FROM legal.documentos WHERE id = {existente[0]};")
            return

        # Usar el PDF que ya esta en su ubicacion
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        nombre_archivo = "ley_19300_completa.pdf"
        destino = PDF_PATH  # Ya esta en la ubicacion correcta
        print(f"\nUsando PDF en: {destino}")

        # Crear registro de archivo
        archivo_id = await crear_archivo_original(db, destino, nombre_archivo)
        print(f"Archivo registrado (ID: {archivo_id})")

        # Crear documento para ingesta
        doc = DocumentoAIngestar(
            titulo=DOCUMENTO["titulo"],
            tipo=DOCUMENTO["tipo"],
            numero=DOCUMENTO["numero"],
            fecha_publicacion=DOCUMENTO["fecha_publicacion"],
            organismo=DOCUMENTO["organismo"],
            contenido=texto,
            url_fuente=DOCUMENTO["url_fuente"],
            categoria_id=DOCUMENTO["categoria_id"],
            archivo_id=archivo_id,
            sectores=DOCUMENTO["sectores"],
            triggers_art11=DOCUMENTO["triggers_art11"],
            componentes_ambientales=DOCUMENTO["componentes_ambientales"],
            etapa_proceso=DOCUMENTO["etapa_proceso"],
        )

        print("\nIngesting documento con clasificacion LLM...")
        resultado = await ingestor.ingestar_documento(db, doc, clasificar_con_llm=True)

        print("\n" + "=" * 70)
        print("RESULTADO")
        print("=" * 70)
        print(f"Documento ID: {resultado.documento_id}")
        print(f"Fragmentos creados: {resultado.fragmentos_creados}")
        print(f"Temas detectados: {', '.join(resultado.temas_detectados[:10])}")
        print(f"Tiempo: {resultado.tiempo_procesamiento_ms}ms")


if __name__ == "__main__":
    asyncio.run(main())
