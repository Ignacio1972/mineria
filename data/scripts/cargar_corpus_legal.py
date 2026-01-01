#!/usr/bin/env python3
"""
Script para cargar el corpus legal inicial en la base de datos.
Procesa los archivos JSON del directorio processed y los ingesta usando el servicio RAG.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Agregar el directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text


# Configuración
DATA_DIR = Path(__file__).parent.parent / "legal" / "processed"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mineria:mineria_dev_2024@localhost:5432/mineria"
).replace("postgresql://", "postgresql+asyncpg://")


async def cargar_documento(session: AsyncSession, doc_data: dict) -> dict:
    """Carga un documento y sus fragmentos en la base de datos."""

    from app.services.rag.embeddings import get_embedding_service

    embedding_service = get_embedding_service()

    # Parsear fecha
    fecha_pub = None
    if doc_data.get("fecha_publicacion"):
        try:
            fecha_pub = datetime.strptime(doc_data["fecha_publicacion"], "%Y-%m-%d").date()
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
        print(f"  Documento ya existe (ID: {documento_id})")

        # Verificar si tiene fragmentos
        result = await session.execute(
            text("SELECT COUNT(*) FROM legal.fragmentos WHERE documento_id = :doc_id"),
            {"doc_id": documento_id}
        )
        count = result.scalar()
        if count > 0:
            return {"documento_id": documento_id, "fragmentos_creados": 0, "ya_existia": True}
    else:
        documento_id = row[0]

    # Procesar artículos como fragmentos
    articulos = doc_data.get("articulos", [])
    fragmentos_creados = 0

    # Preparar textos para embeddings en batch
    textos = []
    fragmentos_data = []

    for art in articulos:
        contenido = art.get("contenido", "")
        if len(contenido) < 50:
            continue

        # Detectar temas
        temas = detectar_temas(contenido)

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

    if textos:
        # Generar embeddings en batch
        print(f"  Generando embeddings para {len(textos)} fragmentos...")
        embeddings = embedding_service.embed_texts(textos)

        # Insertar fragmentos
        for frag, embedding in zip(fragmentos_data, embeddings):
            await session.execute(
                text("""
                    INSERT INTO legal.fragmentos
                    (documento_id, seccion, numero_seccion, contenido, temas, embedding)
                    VALUES (:doc_id, :seccion, :num, :contenido, :temas, :embedding::vector)
                """),
                {
                    "doc_id": documento_id,
                    "seccion": frag["seccion"],
                    "num": frag["numero"],
                    "contenido": frag["contenido"],
                    "temas": frag["temas"],
                    "embedding": embedding,
                }
            )
            fragmentos_creados += 1

    await session.commit()

    return {
        "documento_id": documento_id,
        "fragmentos_creados": fragmentos_creados,
        "temas": list(set(t for f in fragmentos_data for t in f["temas"])),
    }


def detectar_temas(texto: str) -> list:
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


async def main():
    """Carga todos los documentos del corpus legal."""

    print("=" * 60)
    print("CARGA DE CORPUS LEGAL - Sistema de Prefactibilidad Minera")
    print("=" * 60)

    # Crear conexión
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Buscar archivos JSON
    archivos = list(DATA_DIR.glob("*.json"))

    if not archivos:
        print(f"\nNo se encontraron archivos JSON en {DATA_DIR}")
        return

    print(f"\nEncontrados {len(archivos)} documentos para procesar:\n")

    estadisticas = {
        "documentos_procesados": 0,
        "fragmentos_creados": 0,
        "errores": 0,
    }

    async with async_session() as session:
        for archivo in archivos:
            print(f"Procesando: {archivo.name}")

            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)

                resultado = await cargar_documento(session, doc_data)

                if resultado.get("ya_existia"):
                    print(f"  -> Ya existía, omitiendo")
                else:
                    print(f"  -> ID: {resultado['documento_id']}, "
                          f"Fragmentos: {resultado['fragmentos_creados']}")
                    if resultado.get('temas'):
                        print(f"  -> Temas: {', '.join(resultado['temas'][:5])}")

                estadisticas["documentos_procesados"] += 1
                estadisticas["fragmentos_creados"] += resultado.get("fragmentos_creados", 0)

            except Exception as e:
                print(f"  -> ERROR: {e}")
                estadisticas["errores"] += 1

            print()

    await engine.dispose()

    # Resumen
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Documentos procesados: {estadisticas['documentos_procesados']}")
    print(f"Fragmentos creados:    {estadisticas['fragmentos_creados']}")
    print(f"Errores:               {estadisticas['errores']}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
