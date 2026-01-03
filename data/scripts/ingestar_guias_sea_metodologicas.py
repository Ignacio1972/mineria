#!/usr/bin/env python3
"""
Script para descargar e ingestar las Guias Metodologicas y Sectoriales del SEA.

Estas guias son documentos oficiales que establecen metodologias de evaluacion
para los distintos componentes ambientales y sectores productivos en el SEIA.

Documentos de referencia:
- Guia de Area de Influencia en el SEIA (2017)
- Guia de Ecosistemas Terrestres en el SEIA (2025, 2a ed.)
- Guia de Ecosistemas Acuaticos Continentales (2022)
- Guia de Sistemas de Vida y Costumbres de Grupos Humanos (2020, 2a ed.)
- Guia de Evaluacion de Impactos en Paisaje (2019)
- Guia de Participacion Ciudadana (2023, 2a ed.)
- Guia de Consulta Indigena CPLI (2023, 2a ed.)
- Guias sectoriales (mineria, energia, inmobiliario, etc.)

Ejecutar desde el contenedor del backend:
  docker exec mineria_backend python /app/data/scripts/ingestar_guias_sea_metodologicas.py

Nota: Las URLs deben verificarse en https://www.sea.gob.cl/documentacion/guias-y-criterios
ya que pueden cambiar con el tiempo.
"""

import asyncio
import httpx
import hashlib
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote

# Asegurar que el path del backend este disponible
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
PDF_DIR = DATA_BASE / "legal" / "guias_sea"


# =============================================================================
# GUIAS METODOLOGICAS GENERALES
# =============================================================================
# IMPORTANTE: Verificar URLs actuales en https://www.sea.gob.cl/documentacion/guias-y-criterios
# Las URLs pueden cambiar. Si una descarga falla, buscar el documento actualizado.

GUIAS_METODOLOGICAS = [
    # ---------------------------------------------------------------------
    # GUIA DE AREA DE INFLUENCIA (Fundamental para todos los proyectos)
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_area_influencia.pdf",
        "titulo": "Guia para la Descripcion del Area de Influencia en el SEIA",
        "tipo": "Guia Metodologica",
        "numero": "GUIA-AI-2017",
        "fecha_publicacion": date(2017, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 2,  # guias_seia
        "edicion": "1a Edicion",
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura", "forestal"],
        "triggers_art11": ["b", "c", "d", "e", "f"],
        "componentes_ambientales": [
            "clima", "calidad_aire", "ruido", "geologia", "suelos",
            "hidrogeologia", "hidrologia", "flora_vegetacion", "fauna_terrestre",
            "ecosistemas_acuaticos", "medio_humano", "paisaje", "arqueologia"
        ],
        "etapa_proceso": "ingreso",
        "descripcion": """
        Guia fundamental que establece los criterios para definir el area de influencia
        de un proyecto. El AI debe justificarse por CADA elemento ambiental que sera
        impactado de forma significativa. No existe una unica area de influencia.

        Contenido clave:
        - Concepto de area de influencia por componente
        - Criterios de delimitacion espacial
        - Metodologias de definicion (modelacion, analisis biofisico)
        - Diferenciacion AI significativo vs no significativo
        - Ejemplos por tipo de proyecto
        """
    },

    # ---------------------------------------------------------------------
    # GUIA DE ECOSISTEMAS TERRESTRES (Flora y Fauna)
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_ecosistemas_terrestres_2025.pdf",
        "titulo": "Guia para la Evaluacion de Impactos sobre Ecosistemas Terrestres",
        "tipo": "Guia Metodologica",
        "numero": "GUIA-ET-2025",
        "fecha_publicacion": date(2025, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 2,
        "edicion": "2a Edicion",
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "forestal"],
        "triggers_art11": ["b"],  # Recursos naturales renovables
        "componentes_ambientales": ["flora_vegetacion", "fauna_terrestre"],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Metodologias actualizadas para caracterizar y evaluar impactos en ecosistemas
        terrestres. Segunda edicion incorpora criterios de cambio climatico.

        Contenido clave:
        - Metodologias de muestreo de flora (transectos, parcelas)
        - Metodologias de muestreo de fauna (trampas, camaras, transectos)
        - Consideracion de estacionalidad (campanas primavera/otono)
        - Especies en categorias de conservacion (RCE)
        - Habitats criticos y fragmentacion
        - Evaluacion de impactos acumulativos
        - Medidas de mitigacion y compensacion de biodiversidad
        """
    },

    # ---------------------------------------------------------------------
    # GUIA DE ECOSISTEMAS ACUATICOS CONTINENTALES
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_ecosistemas_acuaticos.pdf",
        "titulo": "Guia para la Evaluacion de Impactos sobre Ecosistemas Acuaticos Continentales",
        "tipo": "Guia Metodologica",
        "numero": "GUIA-EAC-2022",
        "fecha_publicacion": date(2022, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 2,
        "edicion": "1a Edicion",
        "sectores": ["mineria", "energia", "infraestructura", "acuicultura"],
        "triggers_art11": ["b"],
        "componentes_ambientales": ["ecosistemas_acuaticos", "hidrologia", "hidrogeologia"],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Metodologias para caracterizar rios, lagos, humedales y aguas subterraneas.

        Contenido clave:
        - Caracterizacion de cuerpos de agua (caudales, regimen hidrologico)
        - Calidad de aguas (fisicoquimica, metales, nutrientes)
        - Biota acuatica (bentos, peces, macrofitas)
        - Humedales y turberas (especial proteccion)
        - Glaciares y ecosistemas criogenos
        - Modelacion de impactos hidricos
        - Caudal ecologico
        """
    },

    # ---------------------------------------------------------------------
    # GUIA DE MEDIO HUMANO (Las 5 dimensiones)
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_sistemas_vida_costumbres.pdf",
        "titulo": "Guia para la Descripcion de los Sistemas de Vida y Costumbres de Grupos Humanos",
        "tipo": "Guia Metodologica",
        "numero": "GUIA-SVG-2020",
        "fecha_publicacion": date(2020, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 2,
        "edicion": "2a Edicion",
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura"],
        "triggers_art11": ["c"],  # Reasentamiento o alteracion sistemas de vida
        "componentes_ambientales": ["medio_humano", "pueblos_indigenas"],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Guia fundamental que establece las 5 DIMENSIONES del medio humano:

        1. DIMENSION GEOGRAFICA
           - Distribucion espacial de la poblacion
           - Asentamientos y localidades
           - Conectividad y accesibilidad

        2. DIMENSION DEMOGRAFICA
           - Estructura poblacional (piramide etaria)
           - Tasas de natalidad, mortalidad, migracion
           - Proyecciones demograficas

        3. DIMENSION ANTROPOLOGICA
           - Cultura e identidad territorial
           - Valores, tradiciones, costumbres
           - Practicas religiosas y ceremoniales
           - Historia local

        4. DIMENSION SOCIOECONOMICA
           - Actividades economicas
           - Empleo e ingresos
           - Pobreza multidimensional
           - Cadenas de valor locales

        5. DIMENSION BIENESTAR SOCIAL
           - Salud (coberturas, establecimientos)
           - Educacion
           - Vivienda y servicios basicos
           - Organizaciones comunitarias

        Metodologias:
        - Analisis de datos censales INE
        - Encuestas sociodemograficas
        - Etnografia y observacion participante
        - Entrevistas en profundidad
        - Mapeo participativo
        """
    },

    # ---------------------------------------------------------------------
    # GUIA DE PAISAJE
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_paisaje.pdf",
        "titulo": "Guia para la Evaluacion de Impactos sobre el Valor Paisajistico",
        "tipo": "Guia Metodologica",
        "numero": "GUIA-PAISAJE-2019",
        "fecha_publicacion": date(2019, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 2,
        "edicion": "1a Edicion",
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario"],
        "triggers_art11": ["e"],  # Valor paisajistico o turistico
        "componentes_ambientales": ["paisaje"],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Metodologia para evaluar alteracion del valor paisajistico o turistico.

        Contenido clave:
        - Concepto de paisaje y sus componentes
        - Unidades de paisaje
        - Cuencas visuales (visibilidad del proyecto)
        - Calidad visual y fragilidad
        - Puntos de observacion clave
        - Simulaciones visuales (fotomontajes)
        - Medidas de integracion paisajistica
        """
    },

    # ---------------------------------------------------------------------
    # GUIA DE PARTICIPACION CIUDADANA (PAC)
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_participacion_ciudadana.pdf",
        "titulo": "Guia de Participacion Ciudadana en el SEIA",
        "tipo": "Guia Metodologica",
        "numero": "GUIA-PAC-2023",
        "fecha_publicacion": date(2023, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 14,  # guias_pac
        "edicion": "2a Edicion",
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura"],
        "triggers_art11": ["a", "c"],
        "componentes_ambientales": ["medio_humano"],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Procedimientos de participacion ciudadana en la evaluacion ambiental.

        Contenido clave:
        - Tipos de PAC (obligatoria en EIA, voluntaria en DIA)
        - Plazos y etapas del proceso
        - Convocatoria y difusion
        - Reunion con la comunidad
        - Observaciones ciudadanas
        - Respuesta a observaciones
        - Cierre de PAC
        """
    },

    # ---------------------------------------------------------------------
    # GUIA DE CONSULTA INDIGENA (CPLI)
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_cpli.pdf",
        "titulo": "Guia de Consulta a Pueblos Indigenas en el SEIA",
        "tipo": "Guia Metodologica",
        "numero": "GUIA-CPLI-2023",
        "fecha_publicacion": date(2023, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 19,  # instructivos_consulta_indigena
        "edicion": "2a Edicion",
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura"],
        "triggers_art11": ["c", "d"],
        "componentes_ambientales": ["pueblos_indigenas", "medio_humano", "patrimonio_cultural"],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Procedimiento de Consulta a Pueblos Indigenas segun Art. 85 DS 40
        y Convenio 169 de la OIT.

        Contenido clave:
        - Susceptibilidad de afectacion directa
        - Pueblos y comunidades indigenas
        - Tierras indigenas (ADI, ADIS)
        - Etapas del proceso de consulta
        - Planificacion de la consulta
        - Entrega de informacion
        - Dialogo de buena fe
        - Acuerdos y medidas
        - Cierre del proceso
        """
    },
]


# =============================================================================
# GUIAS SECTORIALES
# =============================================================================

GUIAS_SECTORIALES = [
    # ---------------------------------------------------------------------
    # GUIA SECTORIAL MINERIA
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_proyectos_mineros.pdf",
        "titulo": "Guia para la Evaluacion Ambiental de Proyectos Mineros",
        "tipo": "Guia Sectorial",
        "numero": "GUIA-MINERIA-2021",
        "fecha_publicacion": date(2021, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 2,
        "edicion": "1a Edicion",
        "sectores": ["mineria"],
        "triggers_art11": ["a", "b", "c", "d", "e", "f"],
        "componentes_ambientales": [
            "calidad_aire", "ruido", "geologia", "hidrogeologia", "hidrologia",
            "suelos", "flora_vegetacion", "fauna_terrestre", "medio_humano",
            "arqueologia", "paisaje"
        ],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Guia especifica para proyectos del sector minero.

        Tipologias cubiertas (Art. 3 letra i DS 40):
        - Prospeccion minera (>5.000 t/mes)
        - Explotacion a rajo abierto y subterranea
        - Plantas de beneficio
        - Depositos de relaves
        - Botaderos de esteriles
        - Instalaciones de disposicion de residuos

        Impactos caracteristicos:
        - Emisiones de MP por tronadura, chancado, transito
        - Alteracion de regimen hidrico
        - Drenaje acido de mina (DAM)
        - Perdida de habitat por despeje
        - Vibraciones por tronadura

        PAS criticos:
        - Art. 135: Deposito de relaves
        - Art. 136: Botadero de esteriles
        - Art. 137: Plan de cierre de faena

        OAECA principales: SERNAGEOMIN, DGA, SAG, CONAF, CMN
        """
    },

    # ---------------------------------------------------------------------
    # GUIA SECTORIAL ENERGIA
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_centrales_energia.pdf",
        "titulo": "Guia para la Evaluacion Ambiental de Centrales de Generacion de Energia",
        "tipo": "Guia Sectorial",
        "numero": "GUIA-ENERGIA-2020",
        "fecha_publicacion": date(2020, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 2,
        "edicion": "1a Edicion",
        "sectores": ["energia"],
        "triggers_art11": ["a", "b", "d", "e"],
        "componentes_ambientales": [
            "calidad_aire", "ruido", "hidrologia", "flora_vegetacion",
            "fauna_terrestre", "paisaje", "medio_humano"
        ],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Guia para centrales de generacion de energia electrica.

        Tipologias cubiertas (Art. 3 letras b, c DS 40):
        - Centrales hidroelectricas (>3 MW)
        - Centrales termoelectricas (>3 MW)
        - Parques eolicos
        - Plantas solares fotovoltaicas
        - Centrales geotermicas
        - Centrales de biomasa

        Impactos por subtipo:
        - Termoelectricas: emisiones atmosfericas, vertido termico
        - Hidroelectricas: alteracion caudales, barrera peces
        - Eolicas: colision aves, ruido, impacto visual
        - Solares: ocupacion territorial, efecto isla calor

        PAS frecuentes:
        - Art. 111: Alteracion de cauce
        - Art. 114/115: Corta de bosque
        - Art. 118: Rescate de fauna
        """
    },

    # ---------------------------------------------------------------------
    # GUIA SECTORIAL INMOBILIARIO
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_proyectos_inmobiliarios.pdf",
        "titulo": "Guia para la Evaluacion Ambiental de Proyectos Inmobiliarios",
        "tipo": "Guia Sectorial",
        "numero": "GUIA-INMOBILIARIO-2019",
        "fecha_publicacion": date(2019, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 2,
        "edicion": "1a Edicion",
        "sectores": ["inmobiliario"],
        "triggers_art11": ["a", "c", "e"],
        "componentes_ambientales": [
            "calidad_aire", "ruido", "hidrologia", "suelos",
            "medio_humano", "paisaje"
        ],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Guia para proyectos inmobiliarios y urbanos.

        Tipologias cubiertas (Art. 3 letra g DS 40):
        - Conjuntos habitacionales (>300 viviendas segun ciudad)
        - Edificios de uso publico (>6.000 m2)
        - Proyectos de desarrollo urbano (>7-70 ha segun ciudad)

        Umbrales de ingreso SEIA:
        - Ciudades >1.000.000 hab: >70 ha o >7.000 viviendas
        - Ciudades 500.000-1.000.000: >52 ha o >5.500 viviendas
        - Ciudades <500.000: Umbrales menores

        Impactos caracteristicos:
        - Trafico vehicular inducido
        - Ruido de construccion y operacion
        - Demanda de servicios (agua, energia, alcantarillado)
        - Impermeabilizacion de suelos
        - Perdida de suelo agricola
        """
    },

    # ---------------------------------------------------------------------
    # GUIA SECTORIAL ACUICULTURA
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_proyectos_acuicultura.pdf",
        "titulo": "Guia para la Evaluacion Ambiental de Proyectos de Acuicultura",
        "tipo": "Guia Sectorial",
        "numero": "GUIA-ACUICULTURA-2018",
        "fecha_publicacion": date(2018, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 2,
        "edicion": "1a Edicion",
        "sectores": ["acuicultura"],
        "triggers_art11": ["b", "d"],
        "componentes_ambientales": [
            "ecosistemas_acuaticos", "medio_humano", "paisaje"
        ],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Guia para proyectos de acuicultura y pesca.

        Tipologias cubiertas (Art. 3 letra n DS 40):
        - Centros de cultivo de peces
        - Centros de cultivo de moluscos
        - Hatcheries
        - Plantas de procesamiento

        Impactos caracteristicos:
        - Eutrofizacion de cuerpos de agua
        - Escape de especies exoticas
        - Uso de antibioticos y antiparasitarios
        - Generacion de RILES
        - Impacto en mamiferos marinos

        PAS frecuentes:
        - Art. 116: Concesion acuicola
        - Art. 119: Introduccion fauna acuatica
        """
    },

    # ---------------------------------------------------------------------
    # GUIA SECTORIAL PORTUARIO
    # ---------------------------------------------------------------------
    {
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_proyectos_portuarios.pdf",
        "titulo": "Guia para la Evaluacion Ambiental de Proyectos Portuarios",
        "tipo": "Guia Sectorial",
        "numero": "GUIA-PORTUARIO-2017",
        "fecha_publicacion": date(2017, 1, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 2,
        "edicion": "1a Edicion",
        "sectores": ["portuario"],
        "triggers_art11": ["b", "d", "e"],
        "componentes_ambientales": [
            "ecosistemas_acuaticos", "medio_humano", "paisaje", "ruido"
        ],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Guia para proyectos portuarios y maritimos.

        Tipologias cubiertas (Art. 3 letra f DS 40):
        - Puertos y terminales maritimos
        - Vias de navegacion
        - Dragado de fondos marinos
        - Obras de defensa costera

        Impactos caracteristicos:
        - Alteracion de fondo marino (dragado)
        - Turbidez y suspension de sedimentos
        - Vertido de aguas de lastre
        - Ruido subacuatico
        - Alteracion de corrientes
        """
    },
]


# =============================================================================
# ORDINARIOS Y CRITERIOS DE EVALUACION
# =============================================================================

ORDINARIOS_CRITERIOS = [
    {
        "url": "https://www.sea.gob.cl/sites/default/files/ordinarios/ordinario_nombre_descripcion_proyectos.pdf",
        "titulo": "Ordinario sobre Nombre y Descripcion de Proyectos en el SEIA",
        "tipo": "Ordinario",
        "numero": "ORD-NOMBRE-2023",
        "fecha_publicacion": date(2023, 6, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 3,  # instructivos_sea
        "edicion": None,
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura"],
        "triggers_art11": [],
        "componentes_ambientales": [],
        "etapa_proceso": "ingreso",
        "descripcion": """
        Criterios para nombrar y describir proyectos al ingresar al SEIA.

        El nombre debe ser:
        - Descriptivo y claro
        - En lenguaje sencillo
        - Que refleje la naturaleza del proyecto

        La descripcion breve debe incluir:
        - Principales partes, obras y acciones
        - Objetivo general
        - Ubicacion
        - Tipologia segun Art. 3 DS 40
        """
    },
    {
        "url": "https://www.sea.gob.cl/sites/default/files/criterios/criterios_suficiencia_linea_base.pdf",
        "titulo": "Criterios de Suficiencia Tecnica de Linea de Base",
        "tipo": "Criterio de Evaluacion",
        "numero": "CRIT-LB-2024",
        "fecha_publicacion": date(2024, 3, 1),
        "organismo": "Servicio de Evaluacion Ambiental",
        "categoria_id": 3,
        "edicion": None,
        "sectores": ["mineria", "energia", "infraestructura", "inmobiliario", "acuicultura"],
        "triggers_art11": ["b"],
        "componentes_ambientales": [
            "clima", "calidad_aire", "ruido", "geologia", "suelos",
            "hidrogeologia", "hidrologia", "flora_vegetacion", "fauna_terrestre",
            "ecosistemas_acuaticos", "medio_humano", "paisaje", "arqueologia"
        ],
        "etapa_proceso": "evaluacion",
        "descripcion": """
        Criterios para evaluar la suficiencia de estudios de linea de base.

        Requisitos generales:
        - Actualidad: datos no mayores a 2 anos
        - Representatividad: campanas en epoca apropiada
        - Metodologia: protocolos estandarizados
        - Cobertura espacial: toda el area de influencia

        Requisitos por componente:
        - Flora/Fauna: estacionalidad (primavera + otono/invierno)
        - Calidad aire: campanas de al menos 90 dias
        - Ruido: mediciones 24 horas, dias habiles y fines de semana
        - Hidrologia: al menos 1 ano hidrologico
        """
    },
]


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

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
        return row[0]

    # Crear registro
    ruta_storage = f"legal/guias_sea/{nombre_archivo}"

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
            "subido_por": "ingestar_guias_sea_metodologicas.py",
        }
    )
    return result.scalar()


async def descargar_pdf(url: str, timeout: float = 120.0) -> bytes | None:
    """Descarga un PDF desde una URL."""
    nombre_archivo = unquote(url.split('/')[-1])[:60]
    print(f"  Descargando: {nombre_archivo}...")

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    except httpx.HTTPStatusError as e:
        print(f"  ERROR HTTP {e.response.status_code}: {url}")
        print(f"  NOTA: Verificar URL actualizada en https://www.sea.gob.cl/documentacion/guias-y-criterios")
        return None
    except Exception as e:
        print(f"  ERROR descargando: {e}")
        return None


async def ingestar_guia(
    db,
    ingestor: IngestorLegal,
    guia: dict,
    contenido_pdf: bytes
) -> dict:
    """Ingesta una guia al corpus con vinculacion de PDF."""

    # Crear directorio si no existe
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    # Generar nombre de archivo basado en numero de guia
    nombre_archivo = f"{guia['numero'].lower().replace('-', '_')}.pdf"
    ruta_pdf = PDF_DIR / nombre_archivo

    # Guardar PDF permanentemente
    ruta_pdf.write_bytes(contenido_pdf)

    try:
        texto = extraer_texto_pdf(str(ruta_pdf))

        if len(texto.strip()) < 100:
            return {
                "titulo": guia["titulo"],
                "error": "No se pudo extraer suficiente texto del PDF",
                "exito": False
            }

        # Crear registro en archivos_originales y obtener ID
        archivo_id = await crear_archivo_original(db, ruta_pdf, nombre_archivo)

        # Crear documento para ingesta con archivo_id
        doc = DocumentoAIngestar(
            titulo=guia["titulo"],
            tipo=guia["tipo"],
            numero=guia["numero"],
            fecha_publicacion=guia["fecha_publicacion"],
            organismo=guia["organismo"],
            contenido=texto,
            url_fuente=guia["url"],
            categoria_id=guia["categoria_id"],
            archivo_id=archivo_id,
            sectores=guia["sectores"],
            triggers_art11=guia["triggers_art11"],
            componentes_ambientales=guia["componentes_ambientales"],
            etapa_proceso=guia["etapa_proceso"],
        )

        # Ingestar con clasificacion LLM
        resultado = await ingestor.ingestar_documento(db, doc, clasificar_con_llm=True)

        return {
            "titulo": guia["titulo"],
            "documento_id": resultado.documento_id,
            "archivo_id": archivo_id,
            "fragmentos": resultado.fragmentos_creados,
            "temas": resultado.temas_detectados,
            "tiempo_ms": resultado.tiempo_procesamiento_ms,
            "exito": True
        }

    except Exception as e:
        return {
            "titulo": guia["titulo"],
            "error": str(e),
            "exito": False
        }


async def main():
    """Funcion principal de ingesta."""
    print("=" * 80)
    print("INGESTA DE GUIAS METODOLOGICAS Y SECTORIALES SEA AL CORPUS RAG")
    print("=" * 80)

    # Combinar todas las guias
    todas_guias = GUIAS_METODOLOGICAS + GUIAS_SECTORIALES + ORDINARIOS_CRITERIOS

    print(f"\nDocumentos a procesar:")
    print(f"  - Guias Metodologicas: {len(GUIAS_METODOLOGICAS)}")
    print(f"  - Guias Sectoriales: {len(GUIAS_SECTORIALES)}")
    print(f"  - Ordinarios/Criterios: {len(ORDINARIOS_CRITERIOS)}")
    print(f"  - TOTAL: {len(todas_guias)}")
    print()

    print("NOTA IMPORTANTE:")
    print("  Las URLs de las guias del SEA pueden cambiar con el tiempo.")
    print("  Si una descarga falla, verificar la URL actualizada en:")
    print("  https://www.sea.gob.cl/documentacion/guias-y-criterios")
    print()

    # Inicializar ingestor
    ingestor = get_ingestor_legal(usar_llm=True)

    resultados = []
    exitosos = 0
    fallidos = 0
    existentes = 0

    async with AsyncSessionLocal() as db:
        for i, guia in enumerate(todas_guias, 1):
            print(f"\n[{i}/{len(todas_guias)}] {guia['titulo']}")
            print(f"  Tipo: {guia['tipo']} | Numero: {guia['numero']}")
            print("-" * 60)

            # Verificar si ya existe
            result = await db.execute(
                text("SELECT id FROM legal.documentos WHERE numero = :numero"),
                {"numero": guia["numero"]}
            )
            existente = result.fetchone()

            if existente:
                print(f"  Ya existe en corpus (ID: {existente[0]}). Saltando...")
                resultados.append({
                    "titulo": guia["titulo"],
                    "existente": True,
                    "documento_id": existente[0]
                })
                existentes += 1
                continue

            # Descargar PDF
            contenido = await descargar_pdf(guia["url"])

            if not contenido:
                fallidos += 1
                resultados.append({
                    "titulo": guia["titulo"],
                    "numero": guia["numero"],
                    "url": guia["url"],
                    "error": "Fallo en descarga - verificar URL",
                    "exito": False
                })
                continue

            # Ingestar
            resultado = await ingestar_guia(db, ingestor, guia, contenido)
            resultados.append(resultado)

            if resultado.get("exito"):
                exitosos += 1
                print(f"  OK: {resultado['fragmentos']} fragmentos, {resultado['tiempo_ms']}ms")
            else:
                fallidos += 1
                print(f"  ERROR: {resultado.get('error')}")

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE INGESTA")
    print("=" * 80)
    print(f"Total procesados: {len(todas_guias)}")
    print(f"Exitosos: {exitosos}")
    print(f"Fallidos: {fallidos}")
    print(f"Ya existentes: {existentes}")

    if fallidos > 0:
        print("\n" + "-" * 40)
        print("DOCUMENTOS CON ERROR (verificar URLs):")
        print("-" * 40)
        for r in resultados:
            if not r.get("exito") and not r.get("existente"):
                print(f"  [{r.get('numero', 'N/A')}] {r['titulo']}")
                if r.get("url"):
                    print(f"      URL: {r['url']}")

    print("\n" + "-" * 40)
    print("TODOS LOS RESULTADOS:")
    print("-" * 40)
    for r in resultados:
        status = "EXISTENTE" if r.get("existente") else ("OK" if r.get("exito") else "ERROR")
        print(f"  [{status}] {r['titulo']}")

    return resultados


if __name__ == "__main__":
    asyncio.run(main())
