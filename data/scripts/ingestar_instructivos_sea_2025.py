#!/usr/bin/env python3
"""
Script para descargar e ingestar los instructivos SEA 2025 al corpus RAG.

Los instructivos del SEA son documentos oficiales que establecen criterios
y procedimientos para la evaluación ambiental en el SEIA.

Ejecutar desde el contenedor del backend:
  docker exec mineria_backend python /app/data/scripts/ingestar_instructivos_sea_2025.py
"""

import asyncio
import httpx
import tempfile
import os
import sys
import hashlib
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote

# Asegurar que el path del backend esté disponible
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

# Directorio para guardar PDFs descargados
DATA_BASE = Path("/app/data") if Path("/app/data").exists() else Path(__file__).parent.parent
PDF_DIR = DATA_BASE / "legal" / "instructivos_sea"


# Instructivos SEA 2025 con sus metadatos
INSTRUCTIVOS_2025 = [
    {
        "url": "https://www.sea.gob.cl/sites/default/files/imce/archivos/2025/12/26/instructivo%20PCPI%20241225.pdf",
        "titulo": "Instructivo Proceso de Consulta a Pueblos Indigenas",
        "tipo": "Instructivo",
        "numero": "PCPI-2025",
        "fecha_publicacion": date(2025, 12, 26),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 19,  # instructivos_consulta_indigena
        "sectores": ["mineria", "energia", "infraestructura"],
        "triggers_art11": ["c", "d"],  # Reasentamiento y areas protegidas
        "componentes_ambientales": ["medio_humano", "patrimonio_cultural"],
        "etapa_proceso": "evaluacion",
        "descripcion": "Actualiza procedimientos de consulta segun Convenio 169 OIT"
    },
    {
        "url": "https://www.sea.gob.cl/sites/default/files/imce/archivos/2025/06/10/instructivo%20formatos%20PAC.pdf",
        "titulo": "Instructivo Documentacion Participacion Ciudadana",
        "tipo": "Instructivo",
        "numero": "PAC-2025",
        "fecha_publicacion": date(2025, 6, 10),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 14,  # guias_pac
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario"],
        "triggers_art11": ["a"],  # Riesgo salud poblacion
        "componentes_ambientales": ["medio_humano"],
        "etapa_proceso": "evaluacion",
        "descripcion": "Requisitos de documentacion para actividades de participacion ciudadana"
    },
    {
        "url": "https://www.sea.gob.cl/sites/default/files/imce/archivos/2025/05/14/Instructivo%20Procedimientos%20Administrativos%202025.pdf",
        "titulo": "Instructivo Procedimientos Administrativos e-SEIA 2025",
        "tipo": "Instructivo",
        "numero": "PROC-ADM-2025",
        "fecha_publicacion": date(2025, 5, 14),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 20,  # instructivos_procedimientos
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura"],
        "triggers_art11": [],
        "componentes_ambientales": [],
        "etapa_proceso": "ingreso",
        "descripcion": "Instrucciones para tramitaciones en plataforma e-SEIA"
    },
    {
        "url": "https://www.sea.gob.cl/sites/default/files/imce/archivos/2025/04/08/Instructivo%20municipalidades%20010425.pdf",
        "titulo": "Instructivo Competencias Municipales en el SEIA",
        "tipo": "Instructivo",
        "numero": "MUN-2025",
        "fecha_publicacion": date(2025, 4, 8),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 20,  # instructivos_procedimientos
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario"],
        "triggers_art11": ["a"],  # Riesgo salud poblacion
        "componentes_ambientales": ["medio_humano"],
        "etapa_proceso": "evaluacion",
        "descripcion": "Lineamientos para municipios en procesos SEIA"
    },
    {
        "url": "https://www.sea.gob.cl/sites/default/files/imce/archivos/2025/03/21/Oficio%20N%C2%B0202599102233_18%20de%20marzo_Imparte%20instrucciones%20Lobby.pdf",
        "titulo": "Instrucciones Cumplimiento Ley de Lobby",
        "tipo": "Instructivo",
        "numero": "LOBBY-2025",
        "fecha_publicacion": date(2025, 3, 21),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 20,  # instructivos_procedimientos
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura"],
        "triggers_art11": [],
        "componentes_ambientales": [],
        "etapa_proceso": "evaluacion",
        "descripcion": "Implementacion Ley 20.730 sobre regulacion del lobby"
    },
    {
        "url": "https://www.sea.gob.cl/sites/default/files/imce/archivos/2025/03/18/Instructivo%20para%20la%20utilizaci%C3%B3n%20de%20la%20geoinformaci%C3%B3n%20en%20el%20SEIA.pdf",
        "titulo": "Instructivo Uso de Geoinformacion en el SEIA",
        "tipo": "Instructivo",
        "numero": "GEO-2025",
        "fecha_publicacion": date(2025, 3, 18),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 3,  # instructivos_sea
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura"],
        "triggers_art11": ["b", "d"],  # Recursos naturales y areas protegidas
        "componentes_ambientales": ["agua", "suelo", "flora", "fauna"],
        "etapa_proceso": "ingreso",
        "descripcion": "Especificaciones tecnicas para datos geoespaciales en SEIA"
    },
    {
        "url": "https://www.sea.gob.cl/sites/default/files/imce/archivos/2025/09/04/Manual_Geoinformacion_V.16092025.pdf",
        "titulo": "Manual Tecnico de Geoinformacion SEIA",
        "tipo": "Manual",
        "numero": "MAN-GEO-2025",
        "fecha_publicacion": date(2025, 9, 4),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 3,  # instructivos_sea
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura"],
        "triggers_art11": ["b", "d"],
        "componentes_ambientales": ["agua", "suelo", "flora", "fauna"],
        "etapa_proceso": "ingreso",
        "descripcion": "Guia tecnica de implementacion con plantillas para geoinformacion"
    },
]


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
        return row[0]

    # Crear registro
    ruta_storage = f"legal/instructivos_sea/{nombre_archivo}"

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
            "nombre_original": nombre_archivo,
            "nombre_storage": nombre_archivo,
            "ruta_storage": ruta_storage,
            "mime_type": "application/pdf",
            "tamano": tamano,
            "hash": hash_sha256,
            "paginas": paginas,
            "procesado_at": datetime.now(),
            "subido_por": "ingestar_instructivos_sea_2025.py",
        }
    )
    return result.scalar()


async def descargar_pdf(url: str, timeout: float = 60.0) -> bytes | None:
    """Descarga un PDF desde una URL."""
    print(f"  Descargando: {unquote(url.split('/')[-1])[:60]}...")

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    except Exception as e:
        print(f"  ERROR descargando: {e}")
        return None


async def ingestar_instructivo(
    db,
    ingestor: IngestorLegal,
    instructivo: dict,
    contenido_pdf: bytes
) -> dict:
    """Ingesta un instructivo al corpus con vinculación de PDF."""

    # Crear directorio si no existe
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    # Generar nombre de archivo basado en hash de URL
    nombre_archivo = hashlib.md5(instructivo["url"].encode()).hexdigest()[:12] + ".pdf"
    ruta_pdf = PDF_DIR / nombre_archivo

    # Guardar PDF permanentemente
    ruta_pdf.write_bytes(contenido_pdf)

    try:
        texto = extraer_texto_pdf(str(ruta_pdf))

        if len(texto.strip()) < 100:
            return {
                "titulo": instructivo["titulo"],
                "error": "No se pudo extraer suficiente texto del PDF",
                "exito": False
            }

        # Crear registro en archivos_originales y obtener ID
        archivo_id = await crear_archivo_original(db, ruta_pdf, nombre_archivo)

        # Crear documento para ingesta con archivo_id
        doc = DocumentoAIngestar(
            titulo=instructivo["titulo"],
            tipo=instructivo["tipo"],
            numero=instructivo["numero"],
            fecha_publicacion=instructivo["fecha_publicacion"],
            organismo=instructivo["organismo"],
            contenido=texto,
            url_fuente=instructivo["url"],
            categoria_id=instructivo["categoria_id"],
            archivo_id=archivo_id,  # Vinculación con PDF
            sectores=instructivo["sectores"],
            triggers_art11=instructivo["triggers_art11"],
            componentes_ambientales=instructivo["componentes_ambientales"],
            etapa_proceso=instructivo["etapa_proceso"],
        )

        # Ingestar con clasificacion LLM
        resultado = await ingestor.ingestar_documento(db, doc, clasificar_con_llm=True)

        return {
            "titulo": instructivo["titulo"],
            "documento_id": resultado.documento_id,
            "archivo_id": archivo_id,
            "fragmentos": resultado.fragmentos_creados,
            "temas": resultado.temas_detectados,
            "tiempo_ms": resultado.tiempo_procesamiento_ms,
            "exito": True
        }

    except Exception as e:
        return {
            "titulo": instructivo["titulo"],
            "error": str(e),
            "exito": False
        }


async def main():
    """Funcion principal de ingesta."""
    print("=" * 70)
    print("INGESTA DE INSTRUCTIVOS SEA 2025 AL CORPUS RAG")
    print("=" * 70)
    print(f"\nDocumentos a procesar: {len(INSTRUCTIVOS_2025)}")
    print()

    # Inicializar ingestor
    ingestor = get_ingestor_legal(usar_llm=True)

    resultados = []
    exitosos = 0
    fallidos = 0

    async with AsyncSessionLocal() as db:
        for i, instructivo in enumerate(INSTRUCTIVOS_2025, 1):
            print(f"\n[{i}/{len(INSTRUCTIVOS_2025)}] {instructivo['titulo']}")
            print("-" * 50)

            # Verificar si ya existe
            from sqlalchemy import text
            result = await db.execute(
                text("SELECT id FROM legal.documentos WHERE numero = :numero"),
                {"numero": instructivo["numero"]}
            )
            existente = result.fetchone()

            if existente:
                print(f"  Ya existe en corpus (ID: {existente[0]}). Saltando...")
                resultados.append({
                    "titulo": instructivo["titulo"],
                    "existente": True,
                    "documento_id": existente[0]
                })
                continue

            # Descargar PDF
            contenido = await descargar_pdf(instructivo["url"])

            if not contenido:
                fallidos += 1
                resultados.append({
                    "titulo": instructivo["titulo"],
                    "error": "Fallo en descarga",
                    "exito": False
                })
                continue

            # Ingestar
            resultado = await ingestar_instructivo(db, ingestor, instructivo, contenido)
            resultados.append(resultado)

            if resultado.get("exito"):
                exitosos += 1
                print(f"  OK: {resultado['fragmentos']} fragmentos, {resultado['tiempo_ms']}ms")
            else:
                fallidos += 1
                print(f"  ERROR: {resultado.get('error')}")

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE INGESTA")
    print("=" * 70)
    print(f"Total procesados: {len(INSTRUCTIVOS_2025)}")
    print(f"Exitosos: {exitosos}")
    print(f"Fallidos: {fallidos}")
    print(f"Ya existentes: {len([r for r in resultados if r.get('existente')])}")

    print("\nDetalles:")
    for r in resultados:
        status = "EXISTENTE" if r.get("existente") else ("OK" if r.get("exito") else "ERROR")
        print(f"  [{status}] {r['titulo']}")

    return resultados


if __name__ == "__main__":
    asyncio.run(main())
