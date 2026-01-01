# Documento 3: Arquitectura Técnica del Sistema de Gestión Documental RAG

## Resumen Ejecutivo para el Desarrollador

Este documento te guía en la implementación de un sistema de gestión documental que alimenta el motor RAG del proyecto Minería Ambiental. Al finalizar, habrás construido:

1. **Nuevo modelo de datos** con categorías jerárquicas, colecciones y trazabilidad completa
2. **Sistema de storage** para archivos originales (PDF, DOCX) con hash de integridad
3. **API REST completa** para CRUD de documentos, categorías y búsquedas
4. **Pipeline de ingestión** mejorado con detección de temas por LLM
5. **Interfaz de administración** en Vue 3 para gestionar el corpus

El sistema actual tiene 2 tablas (`legal.documentos` y `legal.fragmentos`). Lo evolucionarás a 7+ tablas con relaciones apropiadas.

---

## Parte 1: Modelo de Datos

### 1.1 Diagnóstico del Modelo Actual

El sistema actual en `/var/www/mineria/backend/app/db/models/legal.py` tiene:

```python
# Modelo actual (simplificado)
class Documento(Base):
    __tablename__ = "documentos"
    __table_args__ = {"schema": "legal"}

    id: int
    titulo: str
    tipo: str              # Solo un string plano: "Ley", "Reglamento", etc.
    numero: str
    fecha_publicacion: date
    organismo: str
    url_fuente: str
    contenido_completo: text
    estado: str
    metadata: JSONB        # No se usa en la práctica

class Fragmento(Base):
    __tablename__ = "fragmentos"
    __table_args__ = {"schema": "legal"}

    id: int
    documento_id: FK
    seccion: str
    contenido: text
    temas: ARRAY(String)   # Detección por keywords, no semántica
    embedding: Vector(384)
```

**Limitaciones identificadas:**
- Sin categorización jerárquica
- Sin almacenamiento de archivo original
- Sin versionado de documentos
- Sin relaciones entre documentos
- Sin colecciones temáticas
- Detección de temas primitiva

### 1.2 Nuevo Modelo de Datos

Debes crear las siguientes tablas en el esquema `legal`:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DIAGRAMA ENTIDAD-RELACIÓN                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐            │
│  │  categorias  │──────<│  documentos  │>──────│  archivos    │            │
│  │  (árbol)     │ 1   N │              │ 1   1 │  _originales │            │
│  └──────────────┘       └──────────────┘       └──────────────┘            │
│         │                      │                                            │
│         │ self-ref             │ 1                                          │
│         │ (parent)             │                                            │
│         ▼                      ▼ N                                          │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐            │
│  │  categorias  │       │  fragmentos  │       │  versiones   │            │
│  │  (hijos)     │       │              │       │  _documento  │            │
│  └──────────────┘       └──────────────┘       └──────────────┘            │
│                                │                      │                     │
│                                │ N                    │                     │
│                                ▼                      │                     │
│                         ┌──────────────┐              │                     │
│                         │   temas      │              │                     │
│                         │  (many2many) │◄─────────────┘                     │
│                         └──────────────┘                                    │
│                                                                             │
│  ┌──────────────┐       ┌──────────────────────┐                           │
│  │ colecciones  │──────<│ documentos_coleccion │                           │
│  │              │ N   M │    (junction)        │                           │
│  └──────────────┘       └──────────────────────┘                           │
│                                                                             │
│  ┌──────────────┐       ┌──────────────────────┐                           │
│  │ relaciones   │       │  Tipos de relación:  │                           │
│  │ _documentos  │       │  - reglamenta        │                           │
│  │              │       │  - interpreta        │                           │
│  └──────────────┘       │  - reemplaza         │                           │
│                         │  - complementa       │                           │
│                         │  - cita              │                           │
│                         └──────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Definición de Tablas

#### Tabla: `legal.categorias`

Almacena la taxonomía jerárquica de documentos (árbol con auto-referencia).

```sql
CREATE TABLE legal.categorias (
    id SERIAL PRIMARY KEY,

    -- Jerarquía
    parent_id INTEGER REFERENCES legal.categorias(id) ON DELETE CASCADE,
    nivel INTEGER NOT NULL DEFAULT 1,  -- 1=raíz, 2=subcategoría, etc.
    orden INTEGER NOT NULL DEFAULT 0,  -- Para ordenar siblings

    -- Identificación
    codigo VARCHAR(50) UNIQUE NOT NULL,  -- Ej: "guias.art11.letra_a"
    nombre VARCHAR(255) NOT NULL,        -- Ej: "Letra a) Riesgo Salud"
    descripcion TEXT,

    -- Configuración
    tipo_documentos_permitidos VARCHAR(100)[],  -- ["Guía SEA", "Criterio"]
    icono VARCHAR(50),                          -- Para UI: "folder", "file-text"
    color VARCHAR(7),                           -- Hex color para UI

    -- Metadatos
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices útiles
    CONSTRAINT nivel_valido CHECK (nivel >= 1 AND nivel <= 5)
);

-- Índice para búsquedas jerárquicas
CREATE INDEX idx_categorias_parent ON legal.categorias(parent_id);
CREATE INDEX idx_categorias_codigo ON legal.categorias(codigo);

-- Función para obtener path completo de categoría
CREATE OR REPLACE FUNCTION legal.get_categoria_path(categoria_id INTEGER)
RETURNS TEXT AS $$
    WITH RECURSIVE path AS (
        SELECT id, nombre, parent_id, nombre::TEXT as full_path
        FROM legal.categorias WHERE id = categoria_id
        UNION ALL
        SELECT c.id, c.nombre, c.parent_id, c.nombre || ' > ' || p.full_path
        FROM legal.categorias c
        JOIN path p ON c.id = p.parent_id
    )
    SELECT full_path FROM path WHERE parent_id IS NULL;
$$ LANGUAGE SQL;
```

#### Tabla: `legal.archivos_originales`

Almacena referencias a archivos físicos con hash de integridad.

```sql
CREATE TABLE legal.archivos_originales (
    id SERIAL PRIMARY KEY,

    -- Archivo físico
    nombre_original VARCHAR(500) NOT NULL,      -- "DS_40_2012.pdf"
    nombre_storage VARCHAR(255) NOT NULL,       -- UUID generado
    ruta_storage VARCHAR(1000) NOT NULL,        -- "/storage/legal/2024/12/uuid.pdf"
    mime_type VARCHAR(100) NOT NULL,            -- "application/pdf"
    tamano_bytes BIGINT NOT NULL,

    -- Integridad
    hash_sha256 VARCHAR(64) NOT NULL UNIQUE,    -- Para detectar duplicados

    -- Procesamiento
    texto_extraido TEXT,                        -- Texto raw extraído del PDF
    paginas INTEGER,                            -- Número de páginas (si aplica)
    procesado_at TIMESTAMP,

    -- Auditoría
    subido_por VARCHAR(255),                    -- Usuario que subió
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índice para detectar duplicados
    CONSTRAINT archivo_unico UNIQUE (hash_sha256)
);

CREATE INDEX idx_archivos_hash ON legal.archivos_originales(hash_sha256);
```

#### Tabla: `legal.documentos` (modificada)

Versión mejorada del modelo actual.

```sql
-- Primero, agregar columnas nuevas a tabla existente
ALTER TABLE legal.documentos
    ADD COLUMN categoria_id INTEGER REFERENCES legal.categorias(id),
    ADD COLUMN archivo_id INTEGER REFERENCES legal.archivos_originales(id),
    ADD COLUMN version INTEGER DEFAULT 1,
    ADD COLUMN version_anterior_id INTEGER REFERENCES legal.documentos(id),

    -- Metadatos enriquecidos
    ADD COLUMN resolucion_aprobatoria VARCHAR(100),
    ADD COLUMN fecha_vigencia_fin DATE,
    ADD COLUMN sectores VARCHAR(100)[] DEFAULT '{}',
    ADD COLUMN tipologias_art3 VARCHAR(20)[] DEFAULT '{}',
    ADD COLUMN triggers_art11 CHAR(1)[] DEFAULT '{}',
    ADD COLUMN componentes_ambientales VARCHAR(50)[] DEFAULT '{}',
    ADD COLUMN regiones_aplicables VARCHAR(50)[] DEFAULT '{}',

    -- Búsqueda
    ADD COLUMN palabras_clave VARCHAR(100)[] DEFAULT '{}',
    ADD COLUMN resumen TEXT,

    -- Auditoría mejorada
    ADD COLUMN creado_por VARCHAR(255),
    ADD COLUMN modificado_por VARCHAR(255);

-- Índices para búsquedas frecuentes
CREATE INDEX idx_documentos_categoria ON legal.documentos(categoria_id);
CREATE INDEX idx_documentos_tipo ON legal.documentos(tipo);
CREATE INDEX idx_documentos_estado ON legal.documentos(estado);
CREATE INDEX idx_documentos_sectores ON legal.documentos USING GIN(sectores);
CREATE INDEX idx_documentos_triggers ON legal.documentos USING GIN(triggers_art11);
CREATE INDEX idx_documentos_componentes ON legal.documentos USING GIN(componentes_ambientales);

-- Búsqueda full-text en título y resumen
CREATE INDEX idx_documentos_fts ON legal.documentos
    USING GIN(to_tsvector('spanish', coalesce(titulo, '') || ' ' || coalesce(resumen, '')));
```

#### Tabla: `legal.temas`

Catálogo de temas para clasificación consistente.

```sql
CREATE TABLE legal.temas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,    -- "agua", "glaciares", "patrimonio_arqueologico"
    nombre VARCHAR(100) NOT NULL,          -- "Recursos Hídricos"
    descripcion TEXT,

    -- Agrupación
    grupo VARCHAR(50),                     -- "componente_ambiental", "procedimiento", etc.

    -- Keywords para detección automática (respaldo)
    keywords TEXT[] DEFAULT '{}',

    -- UI
    color VARCHAR(7),
    icono VARCHAR(50),

    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Temas predefinidos basados en el sistema actual + expansión
INSERT INTO legal.temas (codigo, nombre, grupo, keywords) VALUES
    ('agua', 'Recursos Hídricos', 'componente_ambiental',
     ARRAY['agua', 'hídrico', 'río', 'lago', 'humedal', 'acuífero', 'caudal', 'DGA']),
    ('aire', 'Calidad del Aire', 'componente_ambiental',
     ARRAY['aire', 'emisión', 'atmosférico', 'material particulado', 'MP10', 'MP2.5']),
    ('suelo', 'Suelo', 'componente_ambiental',
     ARRAY['suelo', 'erosión', 'contaminación del suelo']),
    ('flora_fauna', 'Flora y Fauna', 'componente_ambiental',
     ARRAY['flora', 'fauna', 'especie', 'biodiversidad', 'hábitat', 'SAG']),
    ('glaciares', 'Glaciares y Criósfera', 'componente_ambiental',
     ARRAY['glaciar', 'criósfera', 'permafrost', 'periglaciar']),
    ('ruido', 'Ruido', 'componente_ambiental',
     ARRAY['ruido', 'acústico', 'decibeles', 'sonido']),
    ('patrimonio_arqueologico', 'Patrimonio Arqueológico', 'patrimonio',
     ARRAY['arqueológico', 'arqueología', 'sitio arqueológico']),
    ('patrimonio_paleontologico', 'Patrimonio Paleontológico', 'patrimonio',
     ARRAY['paleontológico', 'fósil', 'paleontología']),
    ('comunidades_indigenas', 'Pueblos Indígenas', 'social',
     ARRAY['indígena', 'pueblo originario', 'consulta', 'CONADI', 'ADI', 'Convenio 169']),
    ('participacion_ciudadana', 'Participación Ciudadana', 'procedimiento',
     ARRAY['participación ciudadana', 'PAC', 'observación ciudadana']),
    ('areas_protegidas', 'Áreas Protegidas', 'territorio',
     ARRAY['área protegida', 'SNASPE', 'parque nacional', 'reserva', 'santuario']),
    ('eia', 'Estudio de Impacto Ambiental', 'instrumento',
     ARRAY['EIA', 'estudio de impacto']),
    ('dia', 'Declaración de Impacto Ambiental', 'instrumento',
     ARRAY['DIA', 'declaración de impacto']),
    ('rca', 'Resolución de Calificación Ambiental', 'instrumento',
     ARRAY['RCA', 'resolución de calificación']),
    ('mineria', 'Minería', 'sector',
     ARRAY['minería', 'minero', 'faena minera', 'SERNAGEOMIN', 'relaves', 'botadero']),
    ('energia', 'Energía', 'sector',
     ARRAY['energía', 'eléctrico', 'generación', 'transmisión']),
    ('impactos_acumulativos', 'Impactos Acumulativos', 'metodologia',
     ARRAY['acumulativo', 'sinérgico', 'impacto acumulativo']);
```

#### Tabla: `legal.fragmentos_temas` (junction)

Relación many-to-many entre fragmentos y temas.

```sql
CREATE TABLE legal.fragmentos_temas (
    fragmento_id INTEGER REFERENCES legal.fragmentos(id) ON DELETE CASCADE,
    tema_id INTEGER REFERENCES legal.temas(id) ON DELETE CASCADE,

    -- Metadatos de la relación
    confianza FLOAT DEFAULT 1.0,           -- 0-1, qué tan seguro es el match
    detectado_por VARCHAR(20) DEFAULT 'manual',  -- 'manual', 'keyword', 'llm'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (fragmento_id, tema_id)
);

CREATE INDEX idx_fragmentos_temas_tema ON legal.fragmentos_temas(tema_id);
```

#### Tabla: `legal.colecciones`

Agrupaciones temáticas transversales de documentos.

```sql
CREATE TABLE legal.colecciones (
    id SERIAL PRIMARY KEY,

    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,

    -- Configuración
    es_publica BOOLEAN DEFAULT true,
    orden INTEGER DEFAULT 0,

    -- UI
    color VARCHAR(7),
    icono VARCHAR(50),

    -- Auditoría
    creado_por VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Colecciones sugeridas
INSERT INTO legal.colecciones (codigo, nombre, descripcion) VALUES
    ('art11_triggers', 'Triggers Artículo 11', 'Documentación sobre las 6 letras del Art. 11'),
    ('normativa_aguas', 'Normativa de Aguas', 'Todo sobre recursos hídricos y DGA'),
    ('consulta_indigena', 'Consulta Indígena', 'Convenio 169 y procedimientos'),
    ('mineria_altura', 'Minería de Altura', 'Glaciares, criósfera, proyectos cordilleranos'),
    ('patrimonio', 'Patrimonio Cultural', 'Arqueológico, paleontológico, histórico'),
    ('nuevas_tecnologias', 'Nuevas Tecnologías', 'Hidrógeno verde, almacenamiento energía');
```

#### Tabla: `legal.documentos_colecciones` (junction)

```sql
CREATE TABLE legal.documentos_colecciones (
    documento_id INTEGER REFERENCES legal.documentos(id) ON DELETE CASCADE,
    coleccion_id INTEGER REFERENCES legal.colecciones(id) ON DELETE CASCADE,

    orden INTEGER DEFAULT 0,
    notas TEXT,
    agregado_por VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (documento_id, coleccion_id)
);
```

#### Tabla: `legal.relaciones_documentos`

Relaciones entre documentos.

```sql
CREATE TABLE legal.relaciones_documentos (
    id SERIAL PRIMARY KEY,

    documento_origen_id INTEGER REFERENCES legal.documentos(id) ON DELETE CASCADE,
    documento_destino_id INTEGER REFERENCES legal.documentos(id) ON DELETE CASCADE,

    tipo_relacion VARCHAR(50) NOT NULL,
    -- Valores: 'reglamenta', 'interpreta', 'reemplaza', 'complementa', 'cita', 'modifica'

    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT relacion_unica UNIQUE (documento_origen_id, documento_destino_id, tipo_relacion),
    CONSTRAINT no_auto_relacion CHECK (documento_origen_id != documento_destino_id)
);

CREATE INDEX idx_relaciones_origen ON legal.relaciones_documentos(documento_origen_id);
CREATE INDEX idx_relaciones_destino ON legal.relaciones_documentos(documento_destino_id);
CREATE INDEX idx_relaciones_tipo ON legal.relaciones_documentos(tipo_relacion);
```

#### Tabla: `legal.historial_versiones`

Auditoría de cambios en documentos.

```sql
CREATE TABLE legal.historial_versiones (
    id SERIAL PRIMARY KEY,

    documento_id INTEGER REFERENCES legal.documentos(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,

    -- Snapshot del documento en esa versión
    datos_documento JSONB NOT NULL,

    -- Cambio
    tipo_cambio VARCHAR(50) NOT NULL,  -- 'creacion', 'edicion', 'reindexacion'
    descripcion_cambio TEXT,

    -- Auditoría
    realizado_por VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_historial_documento ON legal.historial_versiones(documento_id);
```

### 1.4 Migración de Datos Existentes

Script para migrar datos del modelo actual al nuevo:

```sql
-- 1. Crear categorías base desde tipos existentes
INSERT INTO legal.categorias (codigo, nombre, nivel, orden)
SELECT DISTINCT
    LOWER(REPLACE(tipo, ' ', '_')),
    tipo,
    1,
    ROW_NUMBER() OVER (ORDER BY tipo)
FROM legal.documentos
WHERE tipo IS NOT NULL;

-- 2. Actualizar documentos con categoria_id
UPDATE legal.documentos d
SET categoria_id = c.id
FROM legal.categorias c
WHERE LOWER(REPLACE(d.tipo, ' ', '_')) = c.codigo;

-- 3. Migrar temas de array a tabla junction
INSERT INTO legal.fragmentos_temas (fragmento_id, tema_id, detectado_por)
SELECT f.id, t.id, 'keyword'
FROM legal.fragmentos f
CROSS JOIN LATERAL unnest(f.temas) AS tema_texto
JOIN legal.temas t ON t.codigo = tema_texto;

-- 4. Verificar integridad
SELECT
    'Documentos sin categoría' as check,
    COUNT(*) as cantidad
FROM legal.documentos WHERE categoria_id IS NULL
UNION ALL
SELECT
    'Fragmentos sin temas migrados',
    COUNT(DISTINCT f.id)
FROM legal.fragmentos f
LEFT JOIN legal.fragmentos_temas ft ON f.id = ft.fragmento_id
WHERE ft.fragmento_id IS NULL AND array_length(f.temas, 1) > 0;
```

---

## Parte 2: Sistema de Storage

### 2.1 Arquitectura de Almacenamiento

Los archivos originales (PDF, DOCX) se almacenan en el filesystem con la siguiente estructura:

```
/var/www/mineria/storage/
└── legal/
    ├── 2024/
    │   ├── 01/
    │   │   ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf
    │   │   └── b2c3d4e5-f6a7-8901-bcde-f12345678901.docx
    │   └── 12/
    │       └── ...
    └── 2025/
        └── ...
```

### 2.2 Servicio de Storage

Crear `/var/www/mineria/backend/app/services/storage/archivo_service.py`:

```python
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Optional, Tuple
import aiofiles
from fastapi import UploadFile

class ArchivoService:
    """
    Servicio para gestión de archivos originales del corpus RAG.

    Responsabilidades:
    - Almacenar archivos con estructura año/mes/uuid
    - Calcular hash SHA-256 para integridad y deduplicación
    - Extraer texto de PDFs y DOCX
    - Gestionar eliminación segura
    """

    def __init__(self, base_path: str = "/var/www/mineria/storage/legal"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def guardar_archivo(
        self,
        archivo: UploadFile,
        subido_por: Optional[str] = None
    ) -> Tuple[str, str, int, str]:
        """
        Guarda un archivo y retorna (ruta_storage, hash_sha256, tamano, nombre_storage).

        Detecta duplicados por hash antes de guardar.
        """
        # Leer contenido para calcular hash
        contenido = await archivo.read()
        hash_sha256 = hashlib.sha256(contenido).hexdigest()

        # Verificar si ya existe (deduplicación)
        # Esta verificación se hace en el endpoint, aquí solo guardamos

        # Generar ruta: año/mes/uuid.extension
        ahora = datetime.now()
        extension = Path(archivo.filename).suffix.lower()
        nombre_storage = f"{uuid4()}{extension}"

        ruta_relativa = f"{ahora.year}/{ahora.month:02d}/{nombre_storage}"
        ruta_completa = self.base_path / ruta_relativa

        # Crear directorio si no existe
        ruta_completa.parent.mkdir(parents=True, exist_ok=True)

        # Guardar archivo
        async with aiofiles.open(ruta_completa, 'wb') as f:
            await f.write(contenido)

        return (
            str(ruta_relativa),
            hash_sha256,
            len(contenido),
            nombre_storage
        )

    async def obtener_ruta_completa(self, ruta_storage: str) -> Path:
        """Retorna la ruta absoluta de un archivo."""
        return self.base_path / ruta_storage

    async def eliminar_archivo(self, ruta_storage: str) -> bool:
        """Elimina un archivo del storage."""
        ruta = self.base_path / ruta_storage
        if ruta.exists():
            ruta.unlink()
            return True
        return False

    async def extraer_texto_pdf(self, ruta_storage: str) -> Tuple[str, int]:
        """
        Extrae texto de un PDF usando PyMuPDF.
        Retorna (texto, num_paginas).
        """
        import fitz  # PyMuPDF

        ruta = self.base_path / ruta_storage
        texto_completo = []

        with fitz.open(str(ruta)) as doc:
            num_paginas = len(doc)
            for pagina in doc:
                texto_completo.append(pagina.get_text())

        return "\n\n".join(texto_completo), num_paginas

    async def extraer_texto_docx(self, ruta_storage: str) -> str:
        """Extrae texto de un archivo DOCX."""
        from docx import Document

        ruta = self.base_path / ruta_storage
        doc = Document(str(ruta))

        texto_completo = []
        for parrafo in doc.paragraphs:
            if parrafo.text.strip():
                texto_completo.append(parrafo.text)

        return "\n\n".join(texto_completo)
```

### 2.3 Configuración Docker

Agregar volumen para storage en `docker/docker-compose.yml`:

```yaml
services:
  backend:
    # ... configuración existente ...
    volumes:
      - ../backend:/app
      - ../storage:/var/www/mineria/storage  # Nuevo volumen para archivos
    environment:
      - STORAGE_PATH=/var/www/mineria/storage/legal
```

---

## Parte 3: API REST

### 3.1 Estructura de Endpoints

Crear nuevos routers en `/var/www/mineria/backend/app/api/v1/endpoints/`:

```
endpoints/
├── categorias.py      # CRUD de categorías
├── documentos.py      # CRUD de documentos (mejorado)
├── colecciones.py     # CRUD de colecciones
├── temas.py           # CRUD de temas
├── archivos.py        # Upload/download de archivos
├── buscar_normativa.py  # (existente, mejorar)
└── ingestor.py        # (existente, mejorar)
```

### 3.2 Endpoints de Categorías

`/var/www/mineria/backend/app/api/v1/endpoints/categorias.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/categorias", tags=["Categorías"])

# === SCHEMAS ===

class CategoriaBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    tipo_documentos_permitidos: Optional[List[str]] = None
    icono: Optional[str] = None
    color: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    parent_id: Optional[int] = None

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    icono: Optional[str] = None
    color: Optional[str] = None
    activo: Optional[bool] = None

class CategoriaResponse(CategoriaBase):
    id: int
    parent_id: Optional[int]
    nivel: int
    orden: int
    activo: bool
    cantidad_documentos: int = 0

    class Config:
        from_attributes = True

class CategoriaArbol(CategoriaResponse):
    """Categoría con sus hijos anidados."""
    hijos: List["CategoriaArbol"] = []

# === ENDPOINTS ===

@router.get("/", response_model=List[CategoriaResponse])
async def listar_categorias(
    solo_raiz: bool = False,
    incluir_inactivas: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas las categorías.

    - **solo_raiz**: Si true, solo retorna categorías de nivel 1
    - **incluir_inactivas**: Si true, incluye categorías desactivadas
    """
    query = select(Categoria)

    if solo_raiz:
        query = query.where(Categoria.parent_id.is_(None))

    if not incluir_inactivas:
        query = query.where(Categoria.activo == True)

    query = query.order_by(Categoria.nivel, Categoria.orden, Categoria.nombre)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/arbol", response_model=List[CategoriaArbol])
async def obtener_arbol_categorias(
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna la taxonomía completa como árbol jerárquico.
    Útil para renderizar el sidebar de navegación.
    """
    # Obtener todas las categorías activas
    query = select(Categoria).where(Categoria.activo == True)
    result = await db.execute(query)
    categorias = result.scalars().all()

    # Construir árbol
    categorias_por_id = {c.id: c for c in categorias}
    raices = []

    for cat in categorias:
        cat_dict = CategoriaArbol.from_orm(cat)
        cat_dict.hijos = []

        if cat.parent_id is None:
            raices.append(cat_dict)
        else:
            parent = categorias_por_id.get(cat.parent_id)
            if parent:
                # Agregar como hijo del padre
                # (esto requiere lógica adicional para construir recursivamente)
                pass

    return _construir_arbol(categorias)


@router.post("/", response_model=CategoriaResponse, status_code=201)
async def crear_categoria(
    categoria: CategoriaCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crea una nueva categoría.

    Si se especifica parent_id, la categoría será hija de esa categoría.
    El nivel se calcula automáticamente basado en el padre.
    """
    # Verificar que el código no existe
    existe = await db.execute(
        select(Categoria).where(Categoria.codigo == categoria.codigo)
    )
    if existe.scalar_one_or_none():
        raise HTTPException(400, f"Ya existe una categoría con código '{categoria.codigo}'")

    # Calcular nivel
    nivel = 1
    if categoria.parent_id:
        parent = await db.get(Categoria, categoria.parent_id)
        if not parent:
            raise HTTPException(404, "Categoría padre no encontrada")
        nivel = parent.nivel + 1

    # Calcular orden (al final de los siblings)
    orden_query = select(func.coalesce(func.max(Categoria.orden), 0) + 1).where(
        Categoria.parent_id == categoria.parent_id
    )
    orden = (await db.execute(orden_query)).scalar()

    nueva = Categoria(
        **categoria.dict(),
        nivel=nivel,
        orden=orden
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)

    return nueva


@router.get("/{categoria_id}", response_model=CategoriaResponse)
async def obtener_categoria(
    categoria_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene una categoría por ID."""
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(404, "Categoría no encontrada")
    return categoria


@router.put("/{categoria_id}", response_model=CategoriaResponse)
async def actualizar_categoria(
    categoria_id: int,
    datos: CategoriaUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Actualiza una categoría existente."""
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(404, "Categoría no encontrada")

    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(categoria, campo, valor)

    await db.commit()
    await db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}")
async def eliminar_categoria(
    categoria_id: int,
    forzar: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina una categoría.

    - Si tiene documentos asociados, falla (a menos que forzar=True)
    - Si tiene subcategorías, estas se eliminan en cascada
    """
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(404, "Categoría no encontrada")

    # Verificar documentos asociados
    docs_count = await db.execute(
        select(func.count(Documento.id)).where(Documento.categoria_id == categoria_id)
    )
    if docs_count.scalar() > 0 and not forzar:
        raise HTTPException(
            400,
            "La categoría tiene documentos asociados. Use forzar=True para eliminar de todos modos."
        )

    await db.delete(categoria)
    await db.commit()

    return {"mensaje": "Categoría eliminada", "id": categoria_id}


@router.get("/{categoria_id}/documentos", response_model=List[DocumentoResumen])
async def listar_documentos_categoria(
    categoria_id: int,
    incluir_subcategorias: bool = True,
    limite: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista documentos de una categoría.

    - **incluir_subcategorias**: Si true, incluye documentos de categorías hijas
    """
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(404, "Categoría no encontrada")

    if incluir_subcategorias:
        # Obtener IDs de esta categoría y todas sus descendientes
        categoria_ids = await _obtener_ids_descendientes(db, categoria_id)
        query = select(Documento).where(Documento.categoria_id.in_(categoria_ids))
    else:
        query = select(Documento).where(Documento.categoria_id == categoria_id)

    query = query.order_by(Documento.created_at.desc()).limit(limite).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()
```

### 3.3 Endpoints de Documentos (Mejorado)

`/var/www/mineria/backend/app/api/v1/endpoints/documentos.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

router = APIRouter(prefix="/documentos", tags=["Documentos"])

# === SCHEMAS ===

class DocumentoCreate(BaseModel):
    """Schema para crear documento con metadata."""
    titulo: str
    tipo: str
    numero: Optional[str] = None
    fecha_publicacion: Optional[date] = None
    fecha_vigencia: Optional[date] = None
    organismo: Optional[str] = None
    url_fuente: Optional[str] = None
    resolucion_aprobatoria: Optional[str] = None

    # Categorización
    categoria_id: int
    coleccion_ids: Optional[List[int]] = None

    # Aplicabilidad
    sectores: Optional[List[str]] = None
    tipologias_art3: Optional[List[str]] = None
    triggers_art11: Optional[List[str]] = None  # ["a", "b", "d"]
    componentes_ambientales: Optional[List[str]] = None
    regiones_aplicables: Optional[List[str]] = None

    # Contenido (si no se sube archivo)
    contenido: Optional[str] = None
    resumen: Optional[str] = None
    palabras_clave: Optional[List[str]] = None

class DocumentoResponse(BaseModel):
    id: int
    titulo: str
    tipo: str
    numero: Optional[str]
    fecha_publicacion: Optional[date]
    estado: str

    # Categoría
    categoria_id: int
    categoria_nombre: Optional[str] = None
    categoria_path: Optional[str] = None

    # Archivo
    tiene_archivo: bool = False
    archivo_nombre: Optional[str] = None

    # Estadísticas
    fragmentos_count: int = 0

    class Config:
        from_attributes = True

class DocumentoDetalle(DocumentoResponse):
    """Respuesta completa con todos los campos."""
    fecha_vigencia: Optional[date]
    fecha_vigencia_fin: Optional[date]
    organismo: Optional[str]
    url_fuente: Optional[str]
    resolucion_aprobatoria: Optional[str]

    sectores: List[str]
    tipologias_art3: List[str]
    triggers_art11: List[str]
    componentes_ambientales: List[str]
    regiones_aplicables: List[str]

    resumen: Optional[str]
    palabras_clave: List[str]

    # Relaciones
    colecciones: List[dict] = []
    documentos_relacionados: List[dict] = []

    # Archivo original
    archivo: Optional[dict] = None

    # Auditoría
    version: int
    created_at: datetime
    updated_at: Optional[datetime]
    creado_por: Optional[str]

# === ENDPOINTS ===

@router.post("/", response_model=DocumentoResponse, status_code=201)
async def crear_documento(
    datos: str = Form(...),  # JSON string con DocumentoCreate
    archivo: Optional[UploadFile] = File(None),
    procesar_automaticamente: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    archivo_service: ArchivoService = Depends(get_archivo_service)
):
    """
    Crea un nuevo documento en el corpus.

    **Flujo:**
    1. Si se sube archivo PDF/DOCX:
       - Se guarda en storage
       - Se extrae texto automáticamente
       - Se calcula hash para detectar duplicados
    2. Se crea registro en BD
    3. Si procesar_automaticamente=True:
       - Se segmenta el contenido
       - Se detectan temas (LLM o keywords)
       - Se generan embeddings
       - Se crean fragmentos

    **Parámetros:**
    - **datos**: JSON con metadatos del documento (ver DocumentoCreate)
    - **archivo**: Archivo PDF o DOCX opcional
    - **procesar_automaticamente**: Si True, genera fragmentos y embeddings
    """
    import json
    documento_data = DocumentoCreate(**json.loads(datos))

    # Verificar categoría existe
    categoria = await db.get(Categoria, documento_data.categoria_id)
    if not categoria:
        raise HTTPException(404, "Categoría no encontrada")

    archivo_id = None
    contenido = documento_data.contenido

    # Procesar archivo si se subió
    if archivo:
        # Verificar tipo de archivo
        if archivo.content_type not in ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            raise HTTPException(400, "Solo se permiten archivos PDF o DOCX")

        # Guardar archivo
        ruta, hash_sha256, tamano, nombre_storage = await archivo_service.guardar_archivo(archivo)

        # Verificar duplicado
        existe_hash = await db.execute(
            select(ArchivoOriginal).where(ArchivoOriginal.hash_sha256 == hash_sha256)
        )
        if existe_hash.scalar_one_or_none():
            # Eliminar archivo recién subido (es duplicado)
            await archivo_service.eliminar_archivo(ruta)
            raise HTTPException(400, "Este archivo ya existe en el sistema (duplicado detectado por hash)")

        # Extraer texto
        if archivo.content_type == 'application/pdf':
            texto, paginas = await archivo_service.extraer_texto_pdf(ruta)
        else:
            texto = await archivo_service.extraer_texto_docx(ruta)
            paginas = None

        # Crear registro de archivo
        archivo_original = ArchivoOriginal(
            nombre_original=archivo.filename,
            nombre_storage=nombre_storage,
            ruta_storage=ruta,
            mime_type=archivo.content_type,
            tamano_bytes=tamano,
            hash_sha256=hash_sha256,
            texto_extraido=texto,
            paginas=paginas,
            procesado_at=datetime.utcnow()
        )
        db.add(archivo_original)
        await db.flush()

        archivo_id = archivo_original.id
        contenido = texto

    if not contenido:
        raise HTTPException(400, "Debe proporcionar contenido o subir un archivo")

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
        resumen=documento_data.resumen,
        palabras_clave=documento_data.palabras_clave or [],
        version=1
    )
    db.add(documento)
    await db.flush()

    # Agregar a colecciones
    if documento_data.coleccion_ids:
        for col_id in documento_data.coleccion_ids:
            db.add(DocumentoColeccion(
                documento_id=documento.id,
                coleccion_id=col_id
            ))

    await db.commit()

    # Procesar fragmentos si está habilitado
    if procesar_automaticamente:
        from app.services.rag.ingestor import IngestorLegal
        ingestor = IngestorLegal()
        await ingestor.procesar_documento(db, documento.id)

    await db.refresh(documento)
    return documento


@router.get("/", response_model=List[DocumentoResponse])
async def listar_documentos(
    # Filtros
    categoria_id: Optional[int] = None,
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    sector: Optional[str] = None,
    trigger_art11: Optional[str] = None,
    componente: Optional[str] = None,
    coleccion_id: Optional[int] = None,

    # Búsqueda
    q: Optional[str] = None,  # Búsqueda en título y resumen

    # Paginación
    limite: int = 50,
    offset: int = 0,

    # Ordenamiento
    orden: str = "fecha_desc",  # fecha_desc, fecha_asc, titulo_asc, titulo_desc

    db: AsyncSession = Depends(get_db)
):
    """
    Lista documentos con filtros avanzados.

    **Filtros disponibles:**
    - categoria_id: Filtrar por categoría
    - tipo: "Ley", "Reglamento", "Guía SEA", etc.
    - estado: "vigente", "no vigente", "modificado"
    - sector: "Minería", "Energía", etc.
    - trigger_art11: "a", "b", "c", "d", "e", "f"
    - componente: "agua", "aire", "fauna", etc.
    - coleccion_id: Documentos de una colección específica
    - q: Búsqueda full-text en título y resumen
    """
    query = select(Documento)

    # Aplicar filtros
    if categoria_id:
        query = query.where(Documento.categoria_id == categoria_id)
    if tipo:
        query = query.where(Documento.tipo == tipo)
    if estado:
        query = query.where(Documento.estado == estado)
    if sector:
        query = query.where(Documento.sectores.contains([sector]))
    if trigger_art11:
        query = query.where(Documento.triggers_art11.contains([trigger_art11]))
    if componente:
        query = query.where(Documento.componentes_ambientales.contains([componente]))
    if coleccion_id:
        query = query.join(DocumentoColeccion).where(
            DocumentoColeccion.coleccion_id == coleccion_id
        )

    # Búsqueda full-text
    if q:
        query = query.where(
            func.to_tsvector('spanish',
                func.coalesce(Documento.titulo, '') + ' ' +
                func.coalesce(Documento.resumen, '')
            ).match(q)
        )

    # Ordenamiento
    orden_map = {
        "fecha_desc": Documento.created_at.desc(),
        "fecha_asc": Documento.created_at.asc(),
        "titulo_asc": Documento.titulo.asc(),
        "titulo_desc": Documento.titulo.desc(),
    }
    query = query.order_by(orden_map.get(orden, Documento.created_at.desc()))

    # Paginación
    query = query.limit(limite).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{documento_id}", response_model=DocumentoDetalle)
async def obtener_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un documento con todos sus detalles.

    Incluye:
    - Metadata completa
    - Información del archivo original
    - Colecciones a las que pertenece
    - Documentos relacionados
    - Estadísticas de fragmentos
    """
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(404, "Documento no encontrado")

    # Cargar relaciones
    # ... (implementar carga de colecciones, relaciones, etc.)

    return documento


@router.get("/{documento_id}/fragmentos")
async def obtener_fragmentos_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los fragmentos de un documento.

    Útil para verificar cómo se segmentó el documento
    y qué temas se detectaron en cada fragmento.
    """
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(404, "Documento no encontrado")

    query = select(Fragmento).where(
        Fragmento.documento_id == documento_id
    ).order_by(Fragmento.id)

    result = await db.execute(query)
    fragmentos = result.scalars().all()

    return {
        "documento_id": documento_id,
        "documento_titulo": documento.titulo,
        "total_fragmentos": len(fragmentos),
        "fragmentos": [
            {
                "id": f.id,
                "seccion": f.seccion,
                "contenido": f.contenido[:500] + "..." if len(f.contenido) > 500 else f.contenido,
                "temas": f.temas,
                "tiene_embedding": f.embedding is not None
            }
            for f in fragmentos
        ]
    }


@router.get("/{documento_id}/archivo")
async def descargar_archivo_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_db),
    archivo_service: ArchivoService = Depends(get_archivo_service)
):
    """
    Descarga el archivo original de un documento.

    Retorna el PDF o DOCX original que se subió al crear el documento.
    Permite trazabilidad completa: del fragmento RAG al documento fuente.
    """
    from fastapi.responses import FileResponse

    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(404, "Documento no encontrado")

    if not documento.archivo_id:
        raise HTTPException(404, "Este documento no tiene archivo original asociado")

    archivo = await db.get(ArchivoOriginal, documento.archivo_id)
    if not archivo:
        raise HTTPException(404, "Archivo no encontrado")

    ruta = await archivo_service.obtener_ruta_completa(archivo.ruta_storage)

    if not ruta.exists():
        raise HTTPException(500, "El archivo físico no existe")

    return FileResponse(
        path=str(ruta),
        filename=archivo.nombre_original,
        media_type=archivo.mime_type
    )


@router.post("/{documento_id}/reprocesar")
async def reprocesar_documento(
    documento_id: int,
    regenerar_embeddings: bool = True,
    detectar_temas_llm: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Reprocesa un documento existente.

    Útil cuando:
    - Se actualizó el algoritmo de segmentación
    - Se quiere usar detección de temas por LLM
    - Se cambió el modelo de embeddings

    **Parámetros:**
    - regenerar_embeddings: Si True, regenera todos los embeddings
    - detectar_temas_llm: Si True, usa Claude para detectar temas (más preciso)
    """
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(404, "Documento no encontrado")

    # Eliminar fragmentos existentes
    await db.execute(
        delete(Fragmento).where(Fragmento.documento_id == documento_id)
    )

    # Reprocesar
    from app.services.rag.ingestor import IngestorLegal
    ingestor = IngestorLegal()
    resultado = await ingestor.procesar_documento(
        db,
        documento_id,
        usar_llm_para_temas=detectar_temas_llm
    )

    return {
        "mensaje": "Documento reprocesado",
        "fragmentos_creados": resultado["fragmentos_creados"],
        "temas_detectados": resultado["temas_detectados"]
    }


@router.delete("/{documento_id}")
async def eliminar_documento(
    documento_id: int,
    eliminar_archivo: bool = True,
    db: AsyncSession = Depends(get_db),
    archivo_service: ArchivoService = Depends(get_archivo_service)
):
    """
    Elimina un documento y opcionalmente su archivo original.

    Los fragmentos se eliminan automáticamente (CASCADE).
    """
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(404, "Documento no encontrado")

    archivo_eliminado = False
    if eliminar_archivo and documento.archivo_id:
        archivo = await db.get(ArchivoOriginal, documento.archivo_id)
        if archivo:
            await archivo_service.eliminar_archivo(archivo.ruta_storage)
            await db.delete(archivo)
            archivo_eliminado = True

    await db.delete(documento)
    await db.commit()

    return {
        "mensaje": "Documento eliminado",
        "id": documento_id,
        "archivo_eliminado": archivo_eliminado
    }
```

### 3.4 Endpoints de Búsqueda (Mejorado)

Mejorar `/var/www/mineria/backend/app/api/v1/endpoints/buscar_normativa.py`:

```python
@router.post("/buscar-avanzado")
async def buscar_normativa_avanzado(
    request: BusquedaAvanzadaRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Búsqueda avanzada con filtros y facetas.

    **Características:**
    - Búsqueda semántica por embeddings
    - Filtros por categoría, tipo, sector, triggers, etc.
    - Facetas para refinar resultados
    - Highlighting de términos encontrados
    - Trazabilidad completa a documento fuente
    """
    # ... implementación

    return {
        "query": request.query,
        "total_resultados": len(resultados),
        "tiempo_ms": tiempo,

        # Resultados con trazabilidad
        "resultados": [
            {
                "fragmento_id": r.id,
                "contenido": r.contenido,
                "similitud": r.similitud,
                "temas": r.temas,

                # Trazabilidad completa
                "documento": {
                    "id": r.documento.id,
                    "titulo": r.documento.titulo,
                    "tipo": r.documento.tipo,
                    "seccion": r.seccion,
                    "tiene_archivo": r.documento.archivo_id is not None,
                    "url_descarga": f"/api/v1/documentos/{r.documento.id}/archivo"
                },

                # Ubicación en taxonomía
                "categoria": {
                    "id": r.documento.categoria.id,
                    "nombre": r.documento.categoria.nombre,
                    "path": get_categoria_path(r.documento.categoria_id)
                }
            }
            for r in resultados
        ],

        # Facetas para filtrar
        "facetas": {
            "tipos": [{"valor": "Ley", "count": 5}, ...],
            "categorias": [...],
            "temas": [...],
            "triggers_art11": [...]
        }
    }
```

---

## Parte 4: Pipeline de Ingestión Mejorado

### 4.1 Flujo de Ingestión

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PIPELINE DE INGESTIÓN                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [1] UPLOAD                                                                 │
│       │                                                                     │
│       ├── Archivo PDF/DOCX                                                  │
│       │   ├── Calcular hash SHA-256                                        │
│       │   ├── Verificar duplicados                                         │
│       │   ├── Guardar en storage                                           │
│       │   └── Extraer texto (PyMuPDF / python-docx)                        │
│       │                                                                     │
│       └── Texto directo                                                     │
│           └── Usar contenido proporcionado                                  │
│                                                                             │
│       ▼                                                                     │
│  [2] SEGMENTACIÓN                                                           │
│       │                                                                     │
│       ├── Detectar estructura del documento                                │
│       │   ├── ¿Tiene artículos? → Segmentar por artículos                  │
│       │   ├── ¿Tiene secciones numeradas? → Segmentar por secciones        │
│       │   └── Fallback → Segmentar por párrafos (chunk ~1500 chars)        │
│       │                                                                     │
│       └── Validar fragmentos                                               │
│           ├── Descartar < 50 caracteres                                    │
│           └── Subdividir > 2000 caracteres                                 │
│                                                                             │
│       ▼                                                                     │
│  [3] DETECCIÓN DE TEMAS                                                     │
│       │                                                                     │
│       ├── Método Keywords (rápido, menos preciso)                          │
│       │   └── Buscar keywords de cada tema en el texto                     │
│       │                                                                     │
│       └── Método LLM (lento, más preciso) [NUEVO]                          │
│           └── Enviar fragmento a Claude para clasificación                 │
│                                                                             │
│       ▼                                                                     │
│  [4] GENERACIÓN DE EMBEDDINGS                                               │
│       │                                                                     │
│       ├── Batch de fragmentos al modelo                                    │
│       │   └── sentence-transformers (paraphrase-multilingual-MiniLM-L12)   │
│       │                                                                     │
│       └── Vector de 384 dimensiones por fragmento                          │
│                                                                             │
│       ▼                                                                     │
│  [5] ALMACENAMIENTO                                                         │
│       │                                                                     │
│       ├── Insertar documento en legal.documentos                           │
│       ├── Insertar fragmentos en legal.fragmentos                          │
│       ├── Insertar relaciones en legal.fragmentos_temas                    │
│       └── Crear registro en legal.historial_versiones                      │
│                                                                             │
│       ▼                                                                     │
│  [6] POST-PROCESAMIENTO                                                     │
│       │                                                                     │
│       ├── Detectar relaciones con otros documentos                         │
│       ├── Actualizar estadísticas de categoría                             │
│       └── Invalidar cachés relevantes                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Detección de Temas con LLM

Agregar a `/var/www/mineria/backend/app/services/rag/ingestor.py`:

```python
async def detectar_temas_llm(self, fragmento: str, temas_disponibles: List[dict]) -> List[str]:
    """
    Usa Claude para detectar temas de un fragmento.

    Más preciso que keywords porque entiende contexto y sinónimos.
    """
    from app.services.llm.cliente import cliente_anthropic

    temas_lista = "\n".join([
        f"- {t['codigo']}: {t['nombre']} - {t['descripcion']}"
        for t in temas_disponibles
    ])

    prompt = f"""Analiza el siguiente fragmento de normativa ambiental chilena y determina qué temas aplican.

TEMAS DISPONIBLES:
{temas_lista}

FRAGMENTO:
{fragmento}

Responde SOLO con los códigos de los temas que aplican, separados por comas.
Si ningún tema aplica claramente, responde "ninguno".
No incluyas explicaciones, solo los códigos.

Ejemplo de respuesta: agua, glaciares, mineria"""

    response = await cliente_anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )

    temas_detectados = []
    respuesta = response.content[0].text.strip().lower()

    if respuesta != "ninguno":
        codigos = [c.strip() for c in respuesta.split(",")]
        codigos_validos = {t['codigo'] for t in temas_disponibles}
        temas_detectados = [c for c in codigos if c in codigos_validos]

    return temas_detectados
```

---

## Parte 5: Optimización de Búsqueda

### 5.1 Índices pgvector

Para corpus grandes (>100k fragmentos), crear índice IVFFlat:

```sql
-- Crear índice IVFFlat para búsquedas vectoriales rápidas
-- lists = sqrt(num_fragmentos), pero mínimo 100
CREATE INDEX idx_fragmentos_embedding_ivfflat
ON legal.fragmentos
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Para corpus muy grandes, considerar HNSW (más rápido pero más memoria)
CREATE INDEX idx_fragmentos_embedding_hnsw
ON legal.fragmentos
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### 5.2 Caché de Embeddings Frecuentes

```python
from functools import lru_cache
import hashlib

class BuscadorLegalOptimizado:
    def __init__(self):
        self._cache_embeddings = {}  # query_hash -> embedding

    def _get_query_hash(self, query: str) -> str:
        return hashlib.md5(query.lower().strip().encode()).hexdigest()

    async def buscar(self, query: str, ...) -> List[ResultadoBusqueda]:
        query_hash = self._get_query_hash(query)

        # Verificar caché
        if query_hash in self._cache_embeddings:
            embedding = self._cache_embeddings[query_hash]
        else:
            embedding = self.embedding_service.embed_text(query)
            self._cache_embeddings[query_hash] = embedding

            # Limitar tamaño de caché
            if len(self._cache_embeddings) > 1000:
                # Eliminar más antiguos (simplificado)
                self._cache_embeddings.clear()

        # Continuar con búsqueda...
```

---

## Parte 6: Frontend de Gestión

### 6.1 Componentes Vue Necesarios

Crear en `/var/www/mineria/frontend/src/components/corpus/`:

```
corpus/
├── CorpusLayout.vue           # Layout principal con sidebar de categorías
├── CategoriasTree.vue         # Árbol de navegación de categorías
├── DocumentosList.vue         # Lista de documentos con filtros
├── DocumentoCard.vue          # Tarjeta resumen de documento
├── DocumentoDetalle.vue       # Vista detallada de documento
├── DocumentoForm.vue          # Formulario crear/editar documento
├── UploadDocumento.vue        # Componente de upload con drag&drop
├── FragmentosViewer.vue       # Visualizador de fragmentos
├── BuscadorAvanzado.vue       # Búsqueda con filtros
├── ColeccionesManager.vue     # Gestión de colecciones
└── TemasSelector.vue          # Selector múltiple de temas
```

### 6.2 Store Pinia

`/var/www/mineria/frontend/src/stores/corpus.ts`:

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { corpusApi } from '@/services/corpusApi'

interface Categoria {
  id: number
  codigo: string
  nombre: string
  parent_id: number | null
  nivel: number
  hijos: Categoria[]
  cantidad_documentos: number
}

interface Documento {
  id: number
  titulo: string
  tipo: string
  categoria_id: number
  estado: string
  tiene_archivo: boolean
  fragmentos_count: number
}

export const useCorpusStore = defineStore('corpus', () => {
  // Estado
  const categorias = ref<Categoria[]>([])
  const categoriaSeleccionada = ref<number | null>(null)
  const documentos = ref<Documento[]>([])
  const documentoSeleccionado = ref<Documento | null>(null)
  const cargando = ref(false)
  const filtros = ref({
    tipo: null as string | null,
    sector: null as string | null,
    trigger: null as string | null,
    busqueda: ''
  })

  // Getters
  const categoriasArbol = computed(() => {
    return construirArbol(categorias.value)
  })

  const documentosFiltrados = computed(() => {
    return documentos.value.filter(doc => {
      if (filtros.value.tipo && doc.tipo !== filtros.value.tipo) return false
      if (filtros.value.busqueda) {
        const busqueda = filtros.value.busqueda.toLowerCase()
        if (!doc.titulo.toLowerCase().includes(busqueda)) return false
      }
      return true
    })
  })

  // Acciones
  async function cargarCategorias() {
    cargando.value = true
    try {
      const response = await corpusApi.getCategorias()
      categorias.value = response.data
    } finally {
      cargando.value = false
    }
  }

  async function cargarDocumentos(categoriaId?: number) {
    cargando.value = true
    try {
      const params = {
        categoria_id: categoriaId,
        ...filtros.value
      }
      const response = await corpusApi.getDocumentos(params)
      documentos.value = response.data
    } finally {
      cargando.value = false
    }
  }

  async function subirDocumento(formData: FormData) {
    const response = await corpusApi.crearDocumento(formData)
    // Recargar documentos de la categoría actual
    await cargarDocumentos(categoriaSeleccionada.value || undefined)
    return response.data
  }

  function seleccionarCategoria(id: number) {
    categoriaSeleccionada.value = id
    cargarDocumentos(id)
  }

  return {
    // Estado
    categorias,
    categoriaSeleccionada,
    documentos,
    documentoSeleccionado,
    cargando,
    filtros,

    // Getters
    categoriasArbol,
    documentosFiltrados,

    // Acciones
    cargarCategorias,
    cargarDocumentos,
    subirDocumento,
    seleccionarCategoria
  }
})
```

### 6.3 Componente de Upload

`/var/www/mineria/frontend/src/components/corpus/UploadDocumento.vue`:

```vue
<template>
  <div class="upload-documento">
    <!-- Zona de Drop -->
    <div
      class="drop-zone"
      :class="{ 'drag-over': isDragging, 'has-file': archivo }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="handleDrop"
      @click="$refs.fileInput.click()"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".pdf,.docx"
        @change="handleFileSelect"
        class="hidden"
      />

      <div v-if="!archivo" class="drop-content">
        <IconUpload class="w-12 h-12 text-base-content/50" />
        <p class="mt-2">Arrastra un PDF o DOCX aquí</p>
        <p class="text-sm text-base-content/50">o haz clic para seleccionar</p>
      </div>

      <div v-else class="file-preview">
        <IconFile class="w-8 h-8" />
        <span>{{ archivo.name }}</span>
        <button @click.stop="archivo = null" class="btn btn-ghost btn-xs">
          <IconX />
        </button>
      </div>
    </div>

    <!-- Formulario de Metadata -->
    <form @submit.prevent="handleSubmit" class="mt-6 space-y-4">
      <!-- Título -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">Título *</span>
        </label>
        <input
          v-model="form.titulo"
          type="text"
          class="input input-bordered"
          required
        />
      </div>

      <!-- Tipo y Categoría en grid -->
      <div class="grid grid-cols-2 gap-4">
        <div class="form-control">
          <label class="label">
            <span class="label-text">Tipo de documento *</span>
          </label>
          <select v-model="form.tipo" class="select select-bordered" required>
            <option value="">Seleccionar...</option>
            <option value="Ley">Ley</option>
            <option value="Reglamento">Reglamento</option>
            <option value="Guía SEA">Guía SEA</option>
            <option value="Instructivo">Instructivo</option>
            <option value="Criterio de Evaluación">Criterio de Evaluación</option>
          </select>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Categoría *</span>
          </label>
          <select v-model="form.categoria_id" class="select select-bordered" required>
            <option value="">Seleccionar...</option>
            <option
              v-for="cat in categoriasFlat"
              :key="cat.id"
              :value="cat.id"
            >
              {{ '—'.repeat(cat.nivel - 1) }} {{ cat.nombre }}
            </option>
          </select>
        </div>
      </div>

      <!-- Triggers Art. 11 -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">Triggers Art. 11 aplicables</span>
        </label>
        <div class="flex flex-wrap gap-2">
          <label
            v-for="trigger in triggersOptions"
            :key="trigger.value"
            class="label cursor-pointer gap-2"
          >
            <input
              type="checkbox"
              :value="trigger.value"
              v-model="form.triggers_art11"
              class="checkbox checkbox-sm"
            />
            <span class="label-text">{{ trigger.label }}</span>
          </label>
        </div>
      </div>

      <!-- Componentes Ambientales -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">Componentes ambientales</span>
        </label>
        <TemasSelector v-model="form.componentes_ambientales" />
      </div>

      <!-- URL Fuente -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">URL de la fuente oficial</span>
        </label>
        <input
          v-model="form.url_fuente"
          type="url"
          class="input input-bordered"
          placeholder="https://sea.gob.cl/..."
        />
      </div>

      <!-- Opciones de procesamiento -->
      <div class="divider">Opciones de procesamiento</div>

      <label class="label cursor-pointer justify-start gap-4">
        <input
          type="checkbox"
          v-model="form.procesar_automaticamente"
          class="checkbox"
        />
        <span class="label-text">
          Procesar automáticamente (segmentar y generar embeddings)
        </span>
      </label>

      <!-- Botón Submit -->
      <div class="flex justify-end gap-2 mt-6">
        <button type="button" class="btn btn-ghost" @click="$emit('cancel')">
          Cancelar
        </button>
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="!isValid || uploading"
        >
          <span v-if="uploading" class="loading loading-spinner"></span>
          {{ uploading ? 'Subiendo...' : 'Subir documento' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useCorpusStore } from '@/stores/corpus'

const corpusStore = useCorpusStore()
const emit = defineEmits(['success', 'cancel'])

const archivo = ref<File | null>(null)
const isDragging = ref(false)
const uploading = ref(false)

const form = ref({
  titulo: '',
  tipo: '',
  categoria_id: '',
  triggers_art11: [] as string[],
  componentes_ambientales: [] as string[],
  url_fuente: '',
  procesar_automaticamente: true
})

const triggersOptions = [
  { value: 'a', label: 'a) Riesgo salud' },
  { value: 'b', label: 'b) Recursos naturales' },
  { value: 'c', label: 'c) Comunidades' },
  { value: 'd', label: 'd) Áreas protegidas' },
  { value: 'e', label: 'e) Patrimonio' },
  { value: 'f', label: 'f) Paisaje' },
]

const isValid = computed(() => {
  return form.value.titulo &&
         form.value.tipo &&
         form.value.categoria_id &&
         (archivo.value || form.value.contenido)
})

function handleDrop(e: DragEvent) {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files?.length) {
    archivo.value = files[0]
    // Auto-completar título desde nombre de archivo
    if (!form.value.titulo) {
      form.value.titulo = files[0].name.replace(/\.[^/.]+$/, '')
    }
  }
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    archivo.value = input.files[0]
  }
}

async function handleSubmit() {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('datos', JSON.stringify(form.value))
    if (archivo.value) {
      formData.append('archivo', archivo.value)
    }
    formData.append('procesar_automaticamente', String(form.value.procesar_automaticamente))

    const resultado = await corpusStore.subirDocumento(formData)
    emit('success', resultado)
  } catch (error) {
    console.error('Error subiendo documento:', error)
  } finally {
    uploading.value = false
  }
}
</script>
```

---

## Parte 7: Rutas y Registro

### 7.1 Registrar Routers en FastAPI

Modificar `/var/www/mineria/backend/app/main.py`:

```python
from app.api.v1.endpoints import (
    categorias,
    documentos,
    colecciones,
    temas,
    buscar_normativa,
    # ... otros
)

# Registrar nuevos routers
app.include_router(categorias.router, prefix="/api/v1")
app.include_router(documentos.router, prefix="/api/v1")
app.include_router(colecciones.router, prefix="/api/v1")
app.include_router(temas.router, prefix="/api/v1")
```

### 7.2 Rutas Vue Router

Agregar en `/var/www/mineria/frontend/src/router/index.ts`:

```typescript
{
  path: '/corpus',
  component: () => import('@/views/CorpusView.vue'),
  children: [
    {
      path: '',
      name: 'corpus-home',
      component: () => import('@/components/corpus/DocumentosList.vue')
    },
    {
      path: 'categoria/:id',
      name: 'corpus-categoria',
      component: () => import('@/components/corpus/DocumentosList.vue')
    },
    {
      path: 'documento/:id',
      name: 'corpus-documento',
      component: () => import('@/components/corpus/DocumentoDetalle.vue')
    },
    {
      path: 'nuevo',
      name: 'corpus-nuevo',
      component: () => import('@/components/corpus/DocumentoForm.vue')
    },
    {
      path: 'colecciones',
      name: 'corpus-colecciones',
      component: () => import('@/components/corpus/ColeccionesManager.vue')
    }
  ]
}
```

---

## Parte 8: Plan de Implementación

### 8.1 Orden de Desarrollo Recomendado

| Fase | Tareas | Dependencias |
|------|--------|--------------|
| **1. Base de datos** | Crear tablas, migrar datos existentes | Ninguna |
| **2. Storage** | Implementar ArchivoService, configurar Docker | Fase 1 |
| **3. API Categorías** | CRUD completo de categorías | Fase 1 |
| **4. API Documentos** | CRUD con upload de archivos | Fases 1, 2, 3 |
| **5. Ingestor mejorado** | Detección temas LLM, pipeline completo | Fase 4 |
| **6. API Búsqueda** | Búsqueda avanzada con facetas | Fase 5 |
| **7. Frontend Store** | Pinia store para corpus | Ninguna |
| **8. Frontend Categorías** | Árbol de navegación | Fases 3, 7 |
| **9. Frontend Upload** | Componente de subida | Fases 4, 7 |
| **10. Frontend Lista** | Lista con filtros | Fases 6, 8 |
| **11. Frontend Detalle** | Vista de documento | Fase 10 |
| **12. Optimización** | Índices pgvector, caché | Todas |

### 8.2 Archivos a Crear/Modificar

**Backend (crear):**
```
backend/app/
├── db/models/
│   ├── categoria.py
│   ├── archivo.py
│   ├── coleccion.py
│   └── tema.py
├── services/
│   └── storage/
│       └── archivo_service.py
└── api/v1/endpoints/
    ├── categorias.py
    ├── documentos.py
    ├── colecciones.py
    └── temas.py
```

**Backend (modificar):**
```
backend/app/
├── db/models/legal.py          # Agregar campos a Documento
├── services/rag/ingestor.py    # Agregar detección LLM
├── services/rag/busqueda.py    # Mejorar búsqueda
└── main.py                     # Registrar routers
```

**Frontend (crear):**
```
frontend/src/
├── components/corpus/          # Todos los componentes listados
├── stores/corpus.ts
├── services/corpusApi.ts
└── views/CorpusView.vue
```

**SQL (crear):**
```
docker/postgis/init/
└── 02_corpus_schema.sql        # Nuevas tablas y migraciones
```

---

## Resumen

Este documento te ha proporcionado:

1. **Modelo de datos completo** con 7+ tablas para categorías, documentos, archivos, temas, colecciones y relaciones
2. **Sistema de storage** para archivos originales con deduplicación por hash
3. **API REST completa** con endpoints para gestión del corpus
4. **Pipeline de ingestión mejorado** con detección de temas por LLM
5. **Optimizaciones de búsqueda** con índices pgvector
6. **Componentes frontend** para la interfaz de gestión
7. **Plan de implementación** ordenado por dependencias

El sistema resultante permitirá:
- Subir documentos fácilmente con categorización guiada
- Mantener trazabilidad completa desde fragmentos RAG hasta PDFs originales
- Escalar a miles de documentos sin degradar rendimiento
- Buscar normativa con filtros avanzados y facetas
