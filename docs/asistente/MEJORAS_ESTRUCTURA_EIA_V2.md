# Mejoras Estructura EIA/DIA - Versión 2.0

> **Versión:** 2.0 | **Fecha:** Enero 2026 | **Estado:** Especificación para implementación
> **Objetivo:** Llevar el sistema al 100% de cobertura de requisitos oficiales SEIA

---

## Resumen Ejecutivo

Este documento especifica las mejoras necesarias para completar la implementación del sistema de estructura EIA/DIA conforme a:

- **Decreto Supremo 40/2012** (Reglamento del SEIA)
- **Ley 19.300** sobre Bases Generales del Medio Ambiente
- **Guías y documentos oficiales del SEA**

### Gaps Identificados (Alta Prioridad)

| # | Mejora | Impacto | Esfuerzo |
|---|--------|---------|----------|
| 1 | Gestor de ICSARA/Adendas | Alto | Medio |
| 2 | Estructura DIA diferenciada | Alto | Bajo |
| 3 | Módulo de medidas de mitigación | Alto | Alto |
| 4 | Dimensiones detalladas medio humano | Medio | Medio |
| 5 | Referencias a guías SEA | Medio | Bajo |
| 6 | Generador de resumen ejecutivo | Medio | Medio |
| 7 | Validadores de calidad | Bajo | Alto |

---

## Parte I: Referencias Normativas Oficiales

### 1.1 Documentos Legales Base

| Documento | Artículos Clave | Estado en Sistema |
|-----------|-----------------|-------------------|
| **Ley 19.300** | Art. 10 (ingreso SEIA), Art. 11 (triggers EIA), Art. 12-16 (evaluación) | ✅ Ingestado |
| **D.S. 40/2012** | Art. 3 (tipologías), Art. 18 (contenido EIA), Art. 19 (contenido DIA), Art. 85-86 (PAC/CPLI) | ✅ Ingestado |
| **D.S. 40/2012** | Art. 100-160 (Permisos Ambientales Sectoriales) | ✅ Configurado |

### 1.2 Guías SEA Oficiales (Requeridas para Ingesta)

#### Guías Metodológicas Generales

| Guía | Año | Edición | URL | Estado |
|------|-----|---------|-----|--------|
| Guía de Área de Influencia en el SEIA | 2017 | 1ª | [sea.gob.cl/guias](https://www.sea.gob.cl/documentacion/guias-y-criterios) | ⚠️ Pendiente |
| Guía de Ecosistemas Terrestres en el SEIA | 2025 | 2ª | [sea.gob.cl/guias](https://www.sea.gob.cl/documentacion/guias-y-criterios) | ⚠️ Pendiente |
| Guía de Ecosistemas Acuáticos Continentales | 2022 | 1ª | [sea.gob.cl/guias](https://www.sea.gob.cl/documentacion/guias-y-criterios) | ⚠️ Pendiente |
| Guía de Sistemas de Vida y Costumbres de Grupos Humanos | 2020 | 2ª | [sea.gob.cl/guias](https://www.sea.gob.cl/documentacion/guias-y-criterios) | ⚠️ Pendiente |
| Guía de Evaluación de Impactos en Paisaje | 2019 | 1ª | [sea.gob.cl/guias](https://www.sea.gob.cl/documentacion/guias-y-criterios) | ⚠️ Pendiente |
| Guía de Participación Ciudadana | 2023 | 2ª | [sea.gob.cl/guias](https://www.sea.gob.cl/documentacion/guias-y-criterios) | ⚠️ Pendiente |
| Guía de Consulta Indígena (CPLI) | 2023 | 2ª | [sea.gob.cl/guias](https://www.sea.gob.cl/documentacion/guias-y-criterios) | ⚠️ Pendiente |
| Manual Técnico de Geoinformación en SEIA | 2025 | 3ª | [sea.gob.cl/guias](https://www.sea.gob.cl/documentacion/guias-y-criterios) | ✅ Ingestado |

#### Guías Sectoriales Específicas

| Guía | Sector | Año | Estado |
|------|--------|-----|--------|
| Guía para la Evaluación Ambiental de Proyectos Mineros | Minería | 2021 | ⚠️ Pendiente |
| Guía para Centrales de Generación de Energía | Energía | 2020 | ⚠️ Pendiente |
| Guía para Proyectos Inmobiliarios | Inmobiliario | 2019 | ⚠️ Pendiente |
| Guía para Proyectos de Acuicultura | Acuicultura | 2018 | ⚠️ Pendiente |
| Guía para Proyectos Portuarios | Portuario | 2017 | ⚠️ Pendiente |

#### Instructivos Vigentes (2024-2025)

| Instructivo | Código | Fecha | Estado |
|-------------|--------|-------|--------|
| Proceso de Consulta a Pueblos Indígenas | PCPI-2025 | Ene 2025 | ✅ Ingestado |
| Documentación Participación Ciudadana | PAC-2025 | Ene 2025 | ✅ Ingestado |
| Procedimientos Administrativos e-SEIA | PROC-ADM-2025 | Feb 2025 | ✅ Ingestado |
| Competencias Municipales en SEIA | MUN-2025 | Mar 2025 | ✅ Ingestado |
| Ley de Lobby en SEIA | LOBBY-2025 | Abr 2025 | ✅ Ingestado |
| Uso de Geoinformación en SEIA | GEO-2025 | Sep 2025 | ✅ Ingestado |

### 1.3 Ordinarios y Criterios de Evaluación

| Ordinario | Tema | Fecha | Estado |
|-----------|------|-------|--------|
| Ordinario sobre nombre y descripción de proyectos | Redacción EIA/DIA | 2023 | ⚠️ Pendiente |
| Criterios de evaluación de línea de base | Suficiencia técnica | 2024 | ⚠️ Pendiente |
| Criterios para definición de área de influencia | AI por componente | 2024 | ⚠️ Pendiente |

---

## Parte II: Gestor de ICSARA/Adendas

### 2.1 Contexto Legal

El proceso de evaluación ambiental incluye solicitudes de información complementaria:

- **ICSARA**: Informe Consolidado de Solicitud de Aclaraciones, Rectificaciones y Ampliaciones
- **Adenda**: Documento de respuesta del titular a las observaciones del ICSARA
- **Límite legal**: Máximo 2 ICSARA (salvo excepciones Art. 36 D.S. 40)

### 2.2 Modelo de Datos

#### Nueva Tabla: `proyectos.proceso_evaluacion`

```sql
CREATE TABLE proyectos.proceso_evaluacion (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id),

    -- Estado administrativo
    estado_evaluacion estado_evaluacion_enum NOT NULL DEFAULT 'no_ingresado',
    fecha_ingreso DATE,
    fecha_admisibilidad DATE,
    fecha_rca DATE,
    resultado_rca resultado_rca_enum,

    -- Plazos
    plazo_legal_dias INTEGER DEFAULT 120,  -- EIA=120, DIA=60
    dias_transcurridos INTEGER DEFAULT 0,
    dias_suspension INTEGER DEFAULT 0,     -- Por Adendas

    -- Resolución
    numero_rca VARCHAR(50),
    url_rca TEXT,
    condiciones_rca JSONB,  -- Array de condiciones

    -- Metadatos
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TYPE estado_evaluacion_enum AS ENUM (
    'no_ingresado',        -- Proyecto en preparación
    'ingresado',           -- Enviado a e-SEIA
    'en_admisibilidad',    -- 5 días hábiles
    'admitido',            -- Pasa a evaluación
    'inadmitido',          -- Rechazado formalmente
    'en_evaluacion',       -- Análisis OAECA
    'icsara_emitido',      -- Esperando respuesta
    'adenda_en_revision',  -- Adenda presentada
    'ice_emitido',         -- Informe Consolidado de Evaluación
    'en_comision',         -- Votación regional
    'rca_aprobada',        -- Favorable
    'rca_rechazada',       -- Desfavorable
    'desistido',           -- Titular retira
    'caducado'             -- Sin actividad por plazo
);

CREATE TYPE resultado_rca_enum AS ENUM (
    'favorable',
    'favorable_con_condiciones',
    'desfavorable',
    'desistimiento',
    'caducidad'
);
```

#### Nueva Tabla: `proyectos.icsara`

```sql
CREATE TABLE proyectos.icsara (
    id SERIAL PRIMARY KEY,
    proceso_evaluacion_id INTEGER NOT NULL REFERENCES proyectos.proceso_evaluacion(id),

    -- Identificación
    numero_icsara INTEGER NOT NULL,  -- 1, 2, (3 excepcional)
    fecha_emision DATE NOT NULL,
    fecha_limite_respuesta DATE NOT NULL,

    -- Contenido
    observaciones JSONB NOT NULL,  -- Array de ObservacionICSARA
    total_observaciones INTEGER DEFAULT 0,
    observaciones_por_oaeca JSONB,  -- { "SAG": 5, "DGA": 3, ... }

    -- Estado
    estado estado_icsara_enum NOT NULL DEFAULT 'emitido',

    -- Metadatos
    archivo_id INTEGER REFERENCES archivos.archivos(id),  -- PDF original
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TYPE estado_icsara_enum AS ENUM (
    'emitido',
    'respondido',
    'parcialmente_respondido',
    'vencido'
);

-- Estructura de observación individual
COMMENT ON COLUMN proyectos.icsara.observaciones IS 'Array de:
{
    "id": "OBS-001",
    "oaeca": "SERNAGEOMIN",
    "capitulo_eia": 3,
    "componente": "hidrogeologia",
    "tipo": "ampliacion|aclaracion|rectificacion",
    "texto": "Se requiere ampliar información sobre...",
    "prioridad": "critica|importante|menor",
    "estado": "pendiente|respondida|parcial"
}';
```

#### Nueva Tabla: `proyectos.adenda`

```sql
CREATE TABLE proyectos.adenda (
    id SERIAL PRIMARY KEY,
    icsara_id INTEGER NOT NULL REFERENCES proyectos.icsara(id),

    -- Identificación
    numero_adenda INTEGER NOT NULL,  -- 1, 2, 3...
    fecha_presentacion DATE NOT NULL,

    -- Contenido
    respuestas JSONB NOT NULL,  -- Array de RespuestaAdenda
    total_respuestas INTEGER DEFAULT 0,
    observaciones_resueltas INTEGER DEFAULT 0,
    observaciones_pendientes INTEGER DEFAULT 0,

    -- Evaluación de la Adenda
    estado estado_adenda_enum NOT NULL DEFAULT 'presentada',
    fecha_revision DATE,
    resultado_revision resultado_revision_enum,

    -- Metadatos
    archivo_id INTEGER REFERENCES archivos.archivos(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TYPE estado_adenda_enum AS ENUM (
    'en_elaboracion',
    'presentada',
    'en_revision',
    'aceptada',
    'con_observaciones',
    'rechazada'
);

CREATE TYPE resultado_revision_enum AS ENUM (
    'suficiente',
    'insuficiente',
    'parcialmente_suficiente'
);

-- Estructura de respuesta individual
COMMENT ON COLUMN proyectos.adenda.respuestas IS 'Array de:
{
    "observacion_id": "OBS-001",
    "respuesta": "Se adjunta Anexo A5-bis con modelación...",
    "anexos_referenciados": ["A5-bis", "A7-bis"],
    "estado": "respondida|parcial|no_respondida",
    "calificacion_sea": "suficiente|insuficiente|null"
}';
```

### 2.3 Servicio de Negocio

```python
# backend/app/services/proceso_evaluacion/service.py

class ProcesoEvaluacionService:
    """Gestiona el ciclo de vida de evaluación SEIA."""

    async def iniciar_proceso(
        self,
        proyecto_id: int,
        fecha_ingreso: date
    ) -> ProcesoEvaluacion:
        """Marca proyecto como ingresado al SEIA."""

    async def registrar_admisibilidad(
        self,
        proceso_id: int,
        resultado: Literal["admitido", "inadmitido"],
        fecha: date,
        observaciones: Optional[str] = None
    ) -> ProcesoEvaluacion:
        """Registra resultado de admisibilidad (5 días hábiles)."""

    async def registrar_icsara(
        self,
        proceso_id: int,
        numero: int,
        fecha_emision: date,
        observaciones: List[ObservacionICSARA],
        archivo_pdf: Optional[UploadFile] = None
    ) -> ICSARA:
        """Registra nuevo ICSARA con observaciones parseadas."""

    async def registrar_adenda(
        self,
        icsara_id: int,
        numero: int,
        fecha_presentacion: date,
        respuestas: List[RespuestaAdenda],
        archivo_pdf: Optional[UploadFile] = None
    ) -> Adenda:
        """Registra Adenda con respuestas a observaciones."""

    async def actualizar_estado_observacion(
        self,
        adenda_id: int,
        observacion_id: str,
        estado: Literal["respondida", "parcial", "pendiente"],
        calificacion: Optional[str] = None
    ) -> Adenda:
        """Actualiza estado de una observación específica."""

    async def registrar_rca(
        self,
        proceso_id: int,
        resultado: ResultadoRCA,
        numero_rca: str,
        fecha: date,
        condiciones: Optional[List[CondicionRCA]] = None,
        url: Optional[str] = None
    ) -> ProcesoEvaluacion:
        """Registra resolución final (RCA)."""

    async def get_resumen_proceso(
        self,
        proyecto_id: int
    ) -> ResumenProcesoEvaluacion:
        """Retorna estado completo del proceso de evaluación."""

    async def calcular_plazo_restante(
        self,
        proceso_id: int
    ) -> PlazoEvaluacion:
        """Calcula días restantes considerando suspensiones."""
```

### 2.4 Schemas Pydantic

```python
# backend/app/schemas/proceso_evaluacion.py

class ObservacionICSARA(BaseModel):
    id: str                          # "OBS-001"
    oaeca: str                       # "SERNAGEOMIN"
    capitulo_eia: int                # 1-11
    componente: Optional[str]        # "hidrogeologia"
    tipo: Literal["ampliacion", "aclaracion", "rectificacion"]
    texto: str
    prioridad: Literal["critica", "importante", "menor"]
    estado: Literal["pendiente", "respondida", "parcial"] = "pendiente"

class RespuestaAdenda(BaseModel):
    observacion_id: str
    respuesta: str
    anexos_referenciados: List[str] = []
    estado: Literal["respondida", "parcial", "no_respondida"]
    calificacion_sea: Optional[Literal["suficiente", "insuficiente"]] = None

class ResumenProcesoEvaluacion(BaseModel):
    proyecto_id: int
    estado_actual: str
    fecha_ingreso: Optional[date]
    dias_transcurridos: int
    dias_restantes: int

    # ICSARA
    total_icsara: int
    icsara_actual: Optional[int]
    observaciones_totales: int
    observaciones_pendientes: int
    observaciones_resueltas: int

    # Por OAECA
    observaciones_por_oaeca: Dict[str, int]
    oaeca_criticos: List[str]  # Organismos con más observaciones

    # Adendas
    total_adendas: int
    ultima_adenda_fecha: Optional[date]

    # Próximos pasos
    proxima_accion: str
    fecha_limite: Optional[date]
    alerta: Optional[str]
```

### 2.5 Herramienta del Asistente

```python
# backend/app/services/asistente/tools/proceso_evaluacion.py

class ConsultarProcesoEvaluacion(HerramientaBase):
    """Consulta estado del proceso de evaluación SEIA."""

    nombre = "consultar_proceso_evaluacion"
    descripcion = """
    Consulta el estado del proceso de evaluación ambiental del proyecto.

    Retorna:
    - Estado administrativo actual (ingresado, en evaluación, RCA, etc.)
    - Plazos legales y días transcurridos
    - ICSARA emitidos y observaciones pendientes
    - Adendas presentadas y su estado
    - Próximos pasos y fechas límite
    """
    contexto_requerido = ContextoHerramienta.PROYECTO
    categoria = CategoriaHerramienta.CONSULTA

class RegistrarObservacionICSARA(HerramientaBase):
    """Registra observaciones de un ICSARA."""

    nombre = "registrar_observacion_icsara"
    descripcion = """
    Registra una nueva observación del ICSARA para su seguimiento.
    Permite categorizar por OAECA, capítulo del EIA y prioridad.
    """
    contexto_requerido = ContextoHerramienta.PROYECTO
    categoria = CategoriaHerramienta.ACCION
    requiere_confirmacion = True
```

### 2.6 Componente Frontend

```vue
<!-- frontend/src/components/asistente/ProcesoEvaluacion.vue -->

<template>
  <div class="proceso-evaluacion">
    <!-- Timeline de estados -->
    <div class="timeline">
      <div
        v-for="estado in estadosTimeline"
        :key="estado.id"
        :class="['estado', estado.clase]"
      >
        <div class="estado-icono">{{ estado.icono }}</div>
        <div class="estado-info">
          <span class="estado-nombre">{{ estado.nombre }}</span>
          <span class="estado-fecha" v-if="estado.fecha">
            {{ formatDate(estado.fecha) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Resumen de plazos -->
    <div class="plazos card">
      <h3>Plazos de Evaluación</h3>
      <div class="plazo-barra">
        <div
          class="plazo-progreso"
          :style="{ width: porcentajePlazo + '%' }"
          :class="clasePlazo"
        />
      </div>
      <div class="plazo-info">
        <span>{{ diasTranscurridos }} días transcurridos</span>
        <span>{{ diasRestantes }} días restantes</span>
      </div>
    </div>

    <!-- ICSARA y Observaciones -->
    <div class="icsara-section" v-if="tieneICSARA">
      <h3>Observaciones (ICSARA {{ numeroICSARA }})</h3>

      <!-- Stats por OAECA -->
      <div class="oaeca-stats">
        <div
          v-for="(count, oaeca) in observacionesPorOAECA"
          :key="oaeca"
          class="oaeca-badge"
        >
          {{ oaeca }}: {{ count }}
        </div>
      </div>

      <!-- Lista de observaciones -->
      <div class="observaciones-lista">
        <ObservacionCard
          v-for="obs in observaciones"
          :key="obs.id"
          :observacion="obs"
          @responder="abrirRespuesta(obs)"
        />
      </div>

      <!-- Progreso de respuestas -->
      <div class="progreso-adenda">
        <span>{{ observacionesResueltas }}/{{ totalObservaciones }} resueltas</span>
        <progress
          :value="observacionesResueltas"
          :max="totalObservaciones"
        />
      </div>
    </div>
  </div>
</template>
```

---

## Parte III: Estructura DIA Diferenciada

### 3.1 Contexto Legal

Según **Art. 19 del D.S. 40/2012**, una DIA tiene estructura más simple que un EIA:

| Sección DIA | Equivalente EIA | Obligatoria |
|-------------|-----------------|-------------|
| 1. Descripción del Proyecto | Cap. 1 (simplificado) | Sí |
| 2. Justificación inexistencia Art. 11 | N/A (específico DIA) | Sí |
| 3. Plan cumplimiento legislación | Cap. 8 | Sí |
| 4. PAS aplicables | Cap. 9 | Sí |
| 5. Compromisos voluntarios | Cap. 11 | No |
| 6. Ficha resumen por fase | Similar EIA | Sí |
| 7. Resumen (<20 páginas) | <30 páginas en EIA | Sí |
| 8. Equipo elaborador | Igual | Sí |

### 3.2 Modelo de Datos

#### Modificación Tabla: `asistente_config.capitulos_eia`

```sql
-- Agregar campo para diferenciar EIA vs DIA
ALTER TABLE asistente_config.capitulos_eia
ADD COLUMN aplica_instrumento instrumento_ambiental[] DEFAULT ARRAY['EIA'::instrumento_ambiental];

CREATE TYPE instrumento_ambiental AS ENUM ('EIA', 'DIA');

-- Insertar capítulos específicos DIA
INSERT INTO asistente_config.capitulos_eia (
    tipo_proyecto_id, numero, titulo, descripcion,
    contenido_requerido, es_obligatorio, aplica_instrumento
) VALUES
-- Cap. específico DIA: Justificación inexistencia Art. 11
(1, 2, 'Justificación de Inexistencia de Efectos Art. 11',
 'Demostración punto por punto de que el proyecto NO genera efectos significativos',
 '[
    "Análisis literal a) - Riesgo para salud de población",
    "Análisis literal b) - Recursos naturales renovables",
    "Análisis literal c) - Reasentamiento o alteración sistemas de vida",
    "Análisis literal d) - Áreas protegidas o sitios prioritarios",
    "Análisis literal e) - Valor paisajístico o turístico",
    "Análisis literal f) - Patrimonio cultural",
    "Conclusión general de inexistencia de efectos"
 ]'::jsonb,
 true,
 ARRAY['DIA']
);
```

#### Nueva Tabla: `asistente_config.estructura_por_instrumento`

```sql
CREATE TABLE asistente_config.estructura_por_instrumento (
    id SERIAL PRIMARY KEY,
    instrumento instrumento_ambiental NOT NULL,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),

    -- Configuración de estructura
    capitulos_requeridos INTEGER[] NOT NULL,  -- Números de capítulo
    max_paginas_resumen INTEGER NOT NULL,     -- 30 para EIA, 20 para DIA
    requiere_linea_base BOOLEAN DEFAULT true,
    requiere_prediccion_impactos BOOLEAN DEFAULT true,
    requiere_plan_mitigacion BOOLEAN DEFAULT true,

    -- Plazos legales
    plazo_evaluacion_dias INTEGER NOT NULL,   -- 120 EIA, 60 DIA
    plazo_prorroga_dias INTEGER NOT NULL,     -- 60 EIA, 30 DIA
    max_icsara INTEGER DEFAULT 2,

    -- Metadatos
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Datos iniciales
INSERT INTO asistente_config.estructura_por_instrumento
(instrumento, tipo_proyecto_id, capitulos_requeridos, max_paginas_resumen,
 requiere_linea_base, requiere_prediccion_impactos, requiere_plan_mitigacion,
 plazo_evaluacion_dias, plazo_prorroga_dias)
VALUES
-- EIA Minería
('EIA', 1, ARRAY[1,2,3,4,5,6,7,8,9,10,11], 30, true, true, true, 120, 60),
-- DIA Minería
('DIA', 1, ARRAY[1,2,8,9,11], 20, false, false, false, 60, 30);
```

### 3.3 Servicio de Negocio

```python
# backend/app/services/estructura_eia/service.py (modificación)

class EstructuraEIAService:

    async def generar_estructura(
        self,
        proyecto_id: int,
        instrumento: Literal["EIA", "DIA"],  # NUEVO parámetro
        forzar_regenerar: bool = False
    ) -> EstructuraEIAResponse:
        """Genera estructura según instrumento (EIA o DIA)."""

        # Obtener configuración por instrumento
        config_instrumento = await self._get_config_instrumento(
            instrumento,
            tipo_proyecto_id
        )

        # Filtrar capítulos según instrumento
        capitulos = await self._generar_capitulos(
            tipo_proyecto_id,
            instrumento=instrumento,
            capitulos_requeridos=config_instrumento.capitulos_requeridos
        )

        # DIA no requiere línea base completa
        plan_linea_base = None
        if config_instrumento.requiere_linea_base:
            plan_linea_base = await self._generar_plan_linea_base(tipo_proyecto_id)

        # DIA no requiere predicción de impactos formal
        # pero sí justificación de inexistencia
        ...

        return EstructuraEIAResponse(
            instrumento=instrumento,
            capitulos=capitulos,
            max_paginas_resumen=config_instrumento.max_paginas_resumen,
            plazo_evaluacion_dias=config_instrumento.plazo_evaluacion_dias,
            ...
        )

    async def _generar_capitulo_justificacion_art11(
        self,
        proyecto_id: int
    ) -> CapituloConEstado:
        """Genera capítulo específico DIA con análisis por literal."""

        # Obtener análisis Art. 11 del proyecto
        analisis_art11 = await self.prefactibilidad_service.get_analisis_art11(
            proyecto_id
        )

        # Generar secciones por cada literal
        secciones = []
        for literal in ['a', 'b', 'c', 'd', 'e', 'f']:
            secciones.append({
                "literal": literal,
                "descripcion": DESCRIPCIONES_ART11[literal],
                "aplica": analisis_art11.get(f"literal_{literal}", {}).get("aplica", False),
                "justificacion_requerida": not analisis_art11.get(f"literal_{literal}", {}).get("aplica", False),
                "estado": "pendiente"
            })

        return CapituloConEstado(
            numero=2,
            titulo="Justificación de Inexistencia de Efectos Art. 11",
            descripcion="Demostración de que el proyecto NO genera efectos significativos",
            contenido_requerido=[s["descripcion"] for s in secciones],
            es_obligatorio=True,
            estado="pendiente",
            progreso_porcentaje=0,
            secciones_detalle=secciones
        )
```

### 3.4 Herramienta del Asistente

```python
class GenerarEstructuraDIA(HerramientaBase):
    """Genera estructura específica para DIA."""

    nombre = "generar_estructura_dia"
    descripcion = """
    Genera la estructura de una Declaración de Impacto Ambiental (DIA).

    Una DIA es más simple que un EIA y requiere:
    1. Descripción del proyecto (simplificada)
    2. Justificación de inexistencia de efectos Art. 11 (OBLIGATORIO)
    3. Plan de cumplimiento de legislación
    4. PAS aplicables
    5. Compromisos voluntarios (opcional)
    6. Resumen ejecutivo (<20 páginas)

    La DIA NO requiere:
    - Línea de base completa
    - Predicción formal de impactos
    - Plan de mitigación
    - Plan de contingencias

    Úsala cuando el análisis de prefactibilidad recomiende DIA.
    """
    contexto_requerido = ContextoHerramienta.PROYECTO
    categoria = CategoriaHerramienta.ACCION
    requiere_confirmacion = True
```

---

## Parte IV: Módulo de Medidas de Mitigación

### 4.1 Contexto Legal

Según **Art. 18 letra e) del D.S. 40/2012**, el EIA debe incluir:

> "Una descripción pormenorizada de aquellas medidas que se adoptarán para eliminar o minimizar los efectos adversos del proyecto o actividad y las acciones de reparación que se realizarán, cuando ello sea procedente, así como las medidas de compensación..."

La jerarquía de mitigación es:
1. **Prevención**: Evitar el impacto
2. **Minimización**: Reducir magnitud o duración
3. **Restauración/Reparación**: Reparar el daño causado
4. **Compensación**: Sustituir lo perdido (última opción)

### 4.2 Modelo de Datos

#### Nueva Tabla: `proyectos.medidas_mitigacion`

```sql
CREATE TABLE proyectos.medidas_mitigacion (
    id SERIAL PRIMARY KEY,
    estructura_eia_id INTEGER NOT NULL REFERENCES proyectos.estructura_eia(id),

    -- Identificación
    codigo VARCHAR(20) NOT NULL,  -- "MIT-001", "REP-001", "COMP-001"
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,

    -- Clasificación
    tipo_medida tipo_medida_enum NOT NULL,
    jerarquia_mitigacion INTEGER NOT NULL,  -- 1=Prevención, 2=Minimización, 3=Reparación, 4=Compensación

    -- Vinculación a impactos
    impactos_asociados JSONB NOT NULL,  -- Array de { impacto_id, componente, descripcion }
    capitulo_eia INTEGER DEFAULT 5,      -- Capítulo donde se documenta

    -- Aplicación
    fase_aplicacion fase_proyecto_enum[] NOT NULL,  -- [construccion, operacion, cierre]
    lugar_aplicacion TEXT,
    coordenadas_utm JSONB,  -- { "este": 123456, "norte": 654321, "huso": 19 }
    superficie_intervenida_ha DECIMAL(10,2),

    -- Indicadores
    indicador_cumplimiento TEXT NOT NULL,
    meta_o_estandar TEXT NOT NULL,
    forma_control TEXT NOT NULL,
    oportunidad_control TEXT NOT NULL,  -- "Mensual", "Trimestral", etc.

    -- Responsabilidad
    responsable_ejecucion VARCHAR(100),
    responsable_verificacion VARCHAR(100),
    costo_estimado_usd DECIMAL(12,2),

    -- Estado
    estado estado_medida_enum NOT NULL DEFAULT 'propuesta',

    -- Metadatos
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TYPE tipo_medida_enum AS ENUM (
    'prevencion',
    'minimizacion',
    'restauracion',
    'reparacion',
    'compensacion'
);

CREATE TYPE fase_proyecto_enum AS ENUM (
    'construccion',
    'operacion',
    'cierre'
);

CREATE TYPE estado_medida_enum AS ENUM (
    'propuesta',
    'en_revision',
    'aprobada',
    'rechazada',
    'en_ejecucion',
    'completada',
    'verificada'
);

-- Índices
CREATE INDEX idx_medidas_estructura ON proyectos.medidas_mitigacion(estructura_eia_id);
CREATE INDEX idx_medidas_tipo ON proyectos.medidas_mitigacion(tipo_medida);
CREATE INDEX idx_medidas_fase ON proyectos.medidas_mitigacion USING GIN(fase_aplicacion);
```

#### Nueva Tabla: `proyectos.impactos_ambientales`

```sql
CREATE TABLE proyectos.impactos_ambientales (
    id SERIAL PRIMARY KEY,
    estructura_eia_id INTEGER NOT NULL REFERENCES proyectos.estructura_eia(id),

    -- Identificación
    codigo VARCHAR(20) NOT NULL,  -- "IMP-001"
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,

    -- Clasificación
    tipo_impacto tipo_impacto_enum NOT NULL,
    componente_ambiental VARCHAR(50) NOT NULL,  -- "calidad_aire", "flora", "medio_humano"
    fase_generacion fase_proyecto_enum[] NOT NULL,

    -- Caracterización
    caracter caracter_impacto_enum NOT NULL,  -- Positivo, Negativo
    probabilidad probabilidad_enum NOT NULL,
    extension extension_enum NOT NULL,
    duracion duracion_enum NOT NULL,
    reversibilidad reversibilidad_enum NOT NULL,

    -- Evaluación
    magnitud magnitud_enum NOT NULL,
    significancia significancia_enum NOT NULL,
    requiere_mitigacion BOOLEAN DEFAULT false,

    -- Vinculación Art. 11
    literal_art11 CHAR(1),  -- a, b, c, d, e, f (si aplica)

    -- Estado
    estado estado_impacto_enum NOT NULL DEFAULT 'identificado',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enums de caracterización (según metodologías estándar)
CREATE TYPE tipo_impacto_enum AS ENUM ('directo', 'indirecto', 'acumulativo', 'sinergico');
CREATE TYPE caracter_impacto_enum AS ENUM ('positivo', 'negativo', 'neutro');
CREATE TYPE probabilidad_enum AS ENUM ('cierta', 'probable', 'poco_probable', 'improbable');
CREATE TYPE extension_enum AS ENUM ('puntual', 'local', 'regional', 'extensa');
CREATE TYPE duracion_enum AS ENUM ('temporal', 'permanente', 'periodica');
CREATE TYPE reversibilidad_enum AS ENUM ('reversible', 'parcialmente_reversible', 'irreversible');
CREATE TYPE magnitud_enum AS ENUM ('baja', 'media', 'alta', 'muy_alta');
CREATE TYPE significancia_enum AS ENUM ('no_significativo', 'poco_significativo', 'significativo', 'muy_significativo');
CREATE TYPE estado_impacto_enum AS ENUM ('identificado', 'evaluado', 'mitigado', 'residual');
```

#### Tabla de Vinculación: `proyectos.medida_impacto`

```sql
CREATE TABLE proyectos.medida_impacto (
    id SERIAL PRIMARY KEY,
    medida_id INTEGER NOT NULL REFERENCES proyectos.medidas_mitigacion(id),
    impacto_id INTEGER NOT NULL REFERENCES proyectos.impactos_ambientales(id),

    -- Efectividad
    reduccion_esperada_porcentaje INTEGER,  -- 0-100
    impacto_residual_esperado significancia_enum,

    UNIQUE(medida_id, impacto_id)
);
```

### 4.3 Servicio de Negocio

```python
# backend/app/services/medidas_mitigacion/service.py

class MedidasMitigacionService:
    """Gestiona medidas de mitigación, reparación y compensación."""

    async def crear_medida(
        self,
        estructura_eia_id: int,
        medida: MedidaCreate
    ) -> MedidaMitigacion:
        """Crea nueva medida de mitigación."""

    async def vincular_impacto(
        self,
        medida_id: int,
        impacto_id: int,
        reduccion_esperada: int
    ) -> MedidaImpacto:
        """Vincula medida a impacto con reducción esperada."""

    async def get_matriz_impactos_medidas(
        self,
        estructura_eia_id: int
    ) -> MatrizImpactosMedidas:
        """Genera matriz de impactos vs medidas."""

    async def validar_cobertura(
        self,
        estructura_eia_id: int
    ) -> ValidacionCobertura:
        """Valida que todos los impactos significativos tienen medidas."""

    async def calcular_impacto_residual(
        self,
        impacto_id: int
    ) -> ImpactoResidual:
        """Calcula impacto residual después de aplicar medidas."""

    async def generar_plan_seguimiento(
        self,
        estructura_eia_id: int
    ) -> PlanSeguimiento:
        """Genera plan de seguimiento basado en medidas."""

    async def sugerir_medidas_tipo(
        self,
        componente: str,
        tipo_impacto: str,
        tipo_proyecto: str
    ) -> List[MedidaSugerida]:
        """Sugiere medidas típicas para un tipo de impacto."""
```

### 4.4 Schemas Pydantic

```python
# backend/app/schemas/medidas_mitigacion.py

class MedidaCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: str
    tipo_medida: TipoMedida
    jerarquia_mitigacion: int = Field(ge=1, le=4)

    impactos_asociados: List[ImpactoAsociado]
    fase_aplicacion: List[FaseProyecto]
    lugar_aplicacion: Optional[str]

    indicador_cumplimiento: str
    meta_o_estandar: str
    forma_control: str
    oportunidad_control: str

    responsable_ejecucion: Optional[str]
    costo_estimado_usd: Optional[Decimal]

class MatrizImpactosMedidas(BaseModel):
    """Matriz de relación impactos-medidas."""

    impactos: List[ImpactoResumen]
    medidas: List[MedidaResumen]
    relaciones: List[RelacionImpactoMedida]

    # Validación
    impactos_sin_medida: List[str]
    impactos_significativos_cubiertos: int
    impactos_significativos_total: int
    cobertura_porcentaje: float

class PlanSeguimiento(BaseModel):
    """Plan de seguimiento ambiental derivado de medidas."""

    variables: List[VariableMonitoreo]
    frecuencias: Dict[str, str]  # { "calidad_aire": "mensual", ... }
    puntos_control: List[PuntoControl]
    responsables: List[ResponsableMonitoreo]
    cronograma: List[ActividadCronograma]
    presupuesto_anual_estimado_usd: Decimal
```

### 4.5 Herramienta del Asistente

```python
class GestionarMedidasMitigacion(HerramientaBase):
    """Gestiona medidas de mitigación del proyecto."""

    nombre = "gestionar_medidas_mitigacion"
    descripcion = """
    Permite crear, consultar y gestionar medidas de mitigación, reparación
    y compensación del proyecto.

    Acciones disponibles:
    - crear: Crea nueva medida vinculada a impactos
    - consultar: Lista medidas existentes
    - matriz: Genera matriz impactos-medidas
    - validar: Verifica cobertura de impactos significativos
    - sugerir: Sugiere medidas típicas para un tipo de impacto

    Jerarquía de mitigación:
    1. Prevención (evitar el impacto)
    2. Minimización (reducir magnitud/duración)
    3. Restauración/Reparación (reparar el daño)
    4. Compensación (sustituir lo perdido) - última opción

    Cada medida debe tener:
    - Indicador de cumplimiento
    - Meta o estándar
    - Forma y oportunidad de control
    - Responsable
    """
    contexto_requerido = ContextoHerramienta.PROYECTO
    categoria = CategoriaHerramienta.ACCION
    requiere_confirmacion = True
```

### 4.6 Componente Frontend

```vue
<!-- frontend/src/components/asistente/MedidasMitigacion.vue -->

<template>
  <div class="medidas-mitigacion">
    <!-- Tabs: Lista / Matriz / Plan -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="{ active: tabActual === tab.id }"
        @click="tabActual = tab.id"
      >
        {{ tab.nombre }}
      </button>
    </div>

    <!-- Tab: Lista de Medidas -->
    <div v-if="tabActual === 'lista'" class="lista-medidas">
      <div class="filtros">
        <select v-model="filtroTipo">
          <option value="">Todos los tipos</option>
          <option value="prevencion">Prevención</option>
          <option value="minimizacion">Minimización</option>
          <option value="restauracion">Restauración</option>
          <option value="compensacion">Compensación</option>
        </select>
        <select v-model="filtroFase">
          <option value="">Todas las fases</option>
          <option value="construccion">Construcción</option>
          <option value="operacion">Operación</option>
          <option value="cierre">Cierre</option>
        </select>
      </div>

      <MedidaCard
        v-for="medida in medidasFiltradas"
        :key="medida.id"
        :medida="medida"
        @editar="editarMedida(medida)"
        @eliminar="eliminarMedida(medida)"
      />

      <button class="btn-agregar" @click="mostrarFormulario = true">
        + Agregar Medida
      </button>
    </div>

    <!-- Tab: Matriz Impactos-Medidas -->
    <div v-if="tabActual === 'matriz'" class="matriz">
      <MatrizImpactosMedidas
        :impactos="impactos"
        :medidas="medidas"
        :relaciones="relaciones"
      />

      <div class="validacion" :class="validacion.clase">
        <span v-if="validacion.completa">
          ✅ Todos los impactos significativos tienen medidas
        </span>
        <span v-else>
          ⚠️ {{ validacion.impactosSinMedida }} impactos significativos sin medidas
        </span>
      </div>
    </div>

    <!-- Tab: Plan de Seguimiento -->
    <div v-if="tabActual === 'plan'" class="plan-seguimiento">
      <PlanSeguimientoView :plan="planSeguimiento" />
    </div>
  </div>
</template>
```

---

## Parte V: Dimensiones Detalladas del Medio Humano

### 5.1 Contexto Legal

Según la **Guía de Sistemas de Vida y Costumbres de Grupos Humanos (SEA 2020, 2ª ed.)**, el medio humano debe caracterizarse en 5 dimensiones:

| Dimensión | Descripción | Variables Clave |
|-----------|-------------|-----------------|
| **Geográfica** | Distribución espacial de la población | Asentamientos, conectividad, accesibilidad |
| **Demográfica** | Estructura poblacional | Población total, densidad, pirámide etaria, migración |
| **Antropológica** | Cultura e identidad | Valores, tradiciones, costumbres, sistemas de creencias |
| **Socioeconómica** | Actividades productivas | Empleo, ingresos, actividades económicas, pobreza |
| **Bienestar Social** | Calidad de vida | Salud, educación, vivienda, servicios básicos |

Adicionalmente, si hay **pueblos indígenas**, se debe caracterizar:
- Sistemas de vida y costumbres
- Uso del territorio
- Prácticas culturales y religiosas
- Organización social

### 5.2 Modelo de Datos

#### Modificación: `asistente_config.componentes_linea_base`

```sql
-- Expandir componente "medio_humano" en 5 dimensiones

-- Dimensión Geográfica
INSERT INTO asistente_config.componentes_linea_base (
    tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
    metodologia, variables_monitorear, estudios_requeridos,
    duracion_estimada_dias, es_obligatorio
) VALUES (
    1, 3, 'medio_humano_geografico',
    'Medio Humano - Dimensión Geográfica',
    'Distribución espacial de la población en el área de influencia',
    'Análisis cartográfico, censos, encuestas territoriales',
    '["Localidades y asentamientos", "Distancias a centros urbanos", "Vías de acceso", "Conectividad territorial", "Zonificación territorial"]'::jsonb,
    '["Mapa de localidades", "Análisis de accesibilidad", "Caracterización territorial"]'::jsonb,
    30, true
);

-- Dimensión Demográfica
INSERT INTO asistente_config.componentes_linea_base (
    tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
    metodologia, variables_monitorear, estudios_requeridos,
    duracion_estimada_dias, es_obligatorio
) VALUES (
    1, 3, 'medio_humano_demografico',
    'Medio Humano - Dimensión Demográfica',
    'Estructura y dinámica poblacional del área de influencia',
    'Análisis de datos censales INE, encuestas sociodemográficas',
    '["Población total", "Densidad poblacional", "Estructura etaria", "Distribución por sexo", "Tasas de natalidad/mortalidad", "Migración", "Proyección poblacional"]'::jsonb,
    '["Informe demográfico", "Pirámide poblacional", "Análisis de tendencias"]'::jsonb,
    30, true
);

-- Dimensión Antropológica
INSERT INTO asistente_config.componentes_linea_base (
    tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
    metodologia, variables_monitorear, estudios_requeridos,
    duracion_estimada_dias, es_obligatorio
) VALUES (
    1, 3, 'medio_humano_antropologico',
    'Medio Humano - Dimensión Antropológica',
    'Cultura, identidad y sistemas de creencias de las comunidades',
    'Etnografía, entrevistas en profundidad, observación participante',
    '["Identidad territorial", "Valores y creencias", "Tradiciones y costumbres", "Festividades", "Prácticas religiosas", "Historia local", "Percepción del territorio"]'::jsonb,
    '["Estudio antropológico", "Mapeo cultural", "Entrevistas cualitativas"]'::jsonb,
    60, true
);

-- Dimensión Socioeconómica
INSERT INTO asistente_config.componentes_linea_base (
    tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
    metodologia, variables_monitorear, estudios_requeridos,
    duracion_estimada_dias, es_obligatorio
) VALUES (
    1, 3, 'medio_humano_socioeconomico',
    'Medio Humano - Dimensión Socioeconómica',
    'Actividades productivas, empleo e ingresos de la población',
    'Encuestas socioeconómicas, análisis de datos CASEN, entrevistas',
    '["Actividades económicas principales", "Tasas de empleo/desempleo", "Niveles de ingreso", "Pobreza multidimensional", "Estructura productiva", "Cadenas de valor locales", "Economías de subsistencia"]'::jsonb,
    '["Estudio socioeconómico", "Caracterización productiva", "Análisis de empleo local"]'::jsonb,
    45, true
);

-- Dimensión Bienestar Social
INSERT INTO asistente_config.componentes_linea_base (
    tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
    metodologia, variables_monitorear, estudios_requeridos,
    duracion_estimada_dias, es_obligatorio
) VALUES (
    1, 3, 'medio_humano_bienestar',
    'Medio Humano - Dimensión Bienestar Social',
    'Calidad de vida y acceso a servicios de la población',
    'Análisis de coberturas, encuestas de satisfacción, datos sectoriales',
    '["Cobertura de salud", "Establecimientos educacionales", "Calidad de vivienda", "Servicios básicos (agua, luz, alcantarillado)", "Transporte público", "Espacios públicos", "Seguridad ciudadana", "Organizaciones comunitarias"]'::jsonb,
    '["Informe de bienestar social", "Análisis de coberturas", "Mapeo de servicios"]'::jsonb,
    45, true
);

-- Grupos Vulnerables (transversal)
INSERT INTO asistente_config.componentes_linea_base (
    tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
    metodologia, variables_monitorear, estudios_requeridos,
    duracion_estimada_dias, es_obligatorio
) VALUES (
    1, 3, 'grupos_vulnerables',
    'Identificación de Grupos Vulnerables',
    'Caracterización de grupos especialmente vulnerables a impactos del proyecto',
    'Mapeo de vulnerabilidad, análisis de riesgos sociales',
    '["Adultos mayores", "Niños y adolescentes", "Personas en situación de discapacidad", "Mujeres jefas de hogar", "Comunidades aisladas", "Población en pobreza extrema"]'::jsonb,
    '["Mapa de vulnerabilidad", "Análisis de riesgos sociales"]'::jsonb,
    30, true
);
```

### 5.3 Estructura de Datos para Pueblos Indígenas

```sql
-- Expandir componente "pueblos_indigenas" con requisitos CPLI

INSERT INTO asistente_config.componentes_linea_base (
    tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
    metodologia, variables_monitorear, estudios_requeridos,
    duracion_estimada_dias, es_obligatorio, condicion_activacion
) VALUES (
    1, 3, 'pueblos_indigenas_detalle',
    'Pueblos Indígenas - Caracterización Completa',
    'Caracterización de pueblos originarios según Convenio 169 OIT y Ley 19.253',
    'Etnografía participativa, consulta previa, mapeo territorial indígena',
    '[
        "Pueblos presentes (mapuche, aymara, atacameño, etc.)",
        "Comunidades y asociaciones indígenas",
        "Tierras indígenas (ADI, ADIS)",
        "Sitios de significación cultural",
        "Prácticas ceremoniales y religiosas",
        "Sistemas de vida y costumbres",
        "Uso del territorio y recursos naturales",
        "Economías tradicionales",
        "Organización social y autoridades tradicionales",
        "Lengua y transmisión cultural",
        "Relación con el agua y la tierra",
        "Rutas de trashumancia (si aplica)"
    ]'::jsonb,
    '[
        "Estudio de pertinencia indígena (CONADI)",
        "Caracterización antropológica de pueblos",
        "Mapeo territorial participativo",
        "Actas de reuniones con comunidades",
        "Informe de susceptibilidad CPLI"
    ]'::jsonb,
    90, false,
    '{"presencia_indigena": true}'::jsonb
);
```

### 5.4 Herramienta del Asistente

```python
class CaracterizarMedioHumano(HerramientaBase):
    """Guía la caracterización del medio humano en 5 dimensiones."""

    nombre = "caracterizar_medio_humano"
    descripcion = """
    Guía la caracterización del medio humano según la Guía SEA 2020.

    El medio humano debe caracterizarse en 5 DIMENSIONES:

    1. GEOGRÁFICA: Distribución espacial de la población
       - Localidades y asentamientos
       - Conectividad y accesibilidad
       - Zonificación territorial

    2. DEMOGRÁFICA: Estructura poblacional
       - Población total y densidad
       - Estructura etaria (pirámide)
       - Tasas vitales y migración

    3. ANTROPOLÓGICA: Cultura e identidad
       - Valores y tradiciones
       - Prácticas culturales
       - Historia e identidad territorial

    4. SOCIOECONÓMICA: Actividades productivas
       - Empleo e ingresos
       - Actividades económicas
       - Pobreza y vulnerabilidad

    5. BIENESTAR SOCIAL: Calidad de vida
       - Salud y educación
       - Vivienda y servicios básicos
       - Organizaciones comunitarias

    Si hay PUEBLOS INDÍGENAS, se activa caracterización adicional según
    Convenio 169 OIT y se evalúa susceptibilidad de CPLI (Art. 85 DS 40).

    Acciones:
    - consultar: Estado actual de caracterización por dimensión
    - guiar: Siguiente paso en la caracterización
    - validar: Verifica completitud según guía SEA
    """
    contexto_requerido = ContextoHerramienta.PROYECTO
    categoria = CategoriaHerramienta.CONSULTA
```

---

## Parte VI: Generador de Resumen Ejecutivo

### 6.1 Requisitos Legales

| Instrumento | Máximo Páginas | Requisitos |
|-------------|----------------|------------|
| EIA | 30 páginas | Lenguaje sencillo y accesible al público no técnico |
| DIA | 20 páginas | Declaración jurada, lenguaje claro |

El resumen debe ser **autosuficiente** e incluir los puntos clave de todos los capítulos.

### 6.2 Estructura del Generador

```python
# backend/app/services/generador_resumen/service.py

class GeneradorResumenService:
    """Genera resumen ejecutivo automático."""

    SECCIONES_RESUMEN_EIA = [
        "antecedentes_generales",      # Titular, nombre, tipología
        "descripcion_proyecto",         # Fases, partes principales
        "localizacion",                 # Ubicación, superficie
        "inversion_vida_util",          # Monto, duración
        "area_influencia",              # Resumen por componente
        "linea_base",                   # Principales hallazgos
        "impactos_principales",         # Impactos significativos
        "medidas_principales",          # Medidas clave
        "plan_seguimiento",             # Variables monitoreadas
        "normativa_aplicable",          # Principales normas
        "pas_requeridos",               # Lista de PAS
        "compromisos_voluntarios",      # Si aplica
        "conclusiones"                  # Viabilidad ambiental
    ]

    async def generar_resumen(
        self,
        proyecto_id: int,
        instrumento: Literal["EIA", "DIA"],
        max_paginas: int = None
    ) -> ResumenEjecutivo:
        """Genera resumen ejecutivo del EIA/DIA."""

        max_paginas = max_paginas or (30 if instrumento == "EIA" else 20)

        # Obtener datos del proyecto
        proyecto = await self.proyecto_repo.get(proyecto_id)
        estructura = await self.estructura_repo.get_by_proyecto(proyecto_id)

        # Generar cada sección
        secciones = []
        for seccion_id in self.SECCIONES_RESUMEN_EIA:
            contenido = await self._generar_seccion(
                seccion_id,
                proyecto,
                estructura
            )
            secciones.append(contenido)

        # Validar longitud
        texto_completo = self._compilar_secciones(secciones)
        paginas_estimadas = self._estimar_paginas(texto_completo)

        if paginas_estimadas > max_paginas:
            # Resumir con LLM
            texto_completo = await self._resumir_con_llm(
                texto_completo,
                max_paginas
            )

        # Validar legibilidad
        score_legibilidad = self._calcular_legibilidad(texto_completo)

        return ResumenEjecutivo(
            contenido=texto_completo,
            paginas_estimadas=paginas_estimadas,
            score_legibilidad=score_legibilidad,
            advertencias=self._generar_advertencias(score_legibilidad),
            secciones=secciones
        )

    async def _generar_seccion(
        self,
        seccion_id: str,
        proyecto: Proyecto,
        estructura: EstructuraEIA
    ) -> SeccionResumen:
        """Genera contenido de una sección específica."""

        generadores = {
            "antecedentes_generales": self._gen_antecedentes,
            "descripcion_proyecto": self._gen_descripcion,
            "localizacion": self._gen_localizacion,
            # ...
        }

        return await generadores[seccion_id](proyecto, estructura)

    def _calcular_legibilidad(self, texto: str) -> float:
        """Calcula score de legibilidad (Fernández-Huerta para español)."""
        # Fórmula Fernández-Huerta
        # L = 206.84 - 0.60P - 1.02F
        # P = promedio sílabas por palabra
        # F = promedio palabras por frase
        ...
```

### 6.3 Herramienta del Asistente

```python
class GenerarResumenEjecutivo(HerramientaBase):
    """Genera resumen ejecutivo del EIA/DIA."""

    nombre = "generar_resumen_ejecutivo"
    descripcion = """
    Genera el resumen ejecutivo del EIA o DIA.

    Requisitos legales:
    - EIA: Máximo 30 páginas
    - DIA: Máximo 20 páginas
    - Lenguaje sencillo y accesible al público no técnico
    - Debe ser autosuficiente

    El resumen incluye:
    1. Antecedentes generales (titular, nombre, tipología)
    2. Descripción resumida del proyecto
    3. Localización e inversión
    4. Área de influencia
    5. Principales hallazgos línea de base
    6. Impactos significativos identificados
    7. Medidas de mitigación principales
    8. Plan de seguimiento
    9. Normativa y PAS aplicables
    10. Conclusiones de viabilidad ambiental

    El sistema valida:
    - Longitud máxima
    - Legibilidad del texto (score Fernández-Huerta)
    - Completitud de secciones
    """
    contexto_requerido = ContextoHerramienta.PROYECTO
    categoria = CategoriaHerramienta.ACCION
    requiere_confirmacion = True
```

---

## Parte VII: Referencias de Guías SEA para Ingesta

### 7.1 Script de Ingesta de Guías SEA

```python
# data/scripts/ingestar_guias_sea.py

GUIAS_SEA_PENDIENTES = {
    # Guías Metodológicas Generales
    "GUIA-AI-2017": {
        "titulo": "Guía de Área de Influencia en el SEIA",
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_area_influencia.pdf",
        "año": 2017,
        "edicion": "1ª",
        "categoria": "Guías Metodológicas",
        "tipo": "guia_metodologica",
        "triggers_art11": ["b", "c", "d"],
        "componentes": ["todos"],
        "descripcion": "Criterios para definir áreas de influencia por cada elemento ambiental"
    },

    "GUIA-ET-2025": {
        "titulo": "Guía de Ecosistemas Terrestres en el SEIA",
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_ecosistemas_terrestres.pdf",
        "año": 2025,
        "edicion": "2ª",
        "categoria": "Guías Metodológicas",
        "tipo": "guia_metodologica",
        "triggers_art11": ["b"],
        "componentes": ["flora_vegetacion", "fauna_terrestre", "ecosistemas"],
        "descripcion": "Metodologías para caracterizar y evaluar impactos en ecosistemas terrestres"
    },

    "GUIA-EAC-2022": {
        "titulo": "Guía de Ecosistemas Acuáticos Continentales en el SEIA",
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_ecosistemas_acuaticos.pdf",
        "año": 2022,
        "edicion": "1ª",
        "categoria": "Guías Metodológicas",
        "tipo": "guia_metodologica",
        "triggers_art11": ["b"],
        "componentes": ["ecosistemas_acuaticos", "hidrologia", "hidrogeologia"],
        "descripcion": "Metodologías para ríos, lagos, humedales y aguas subterráneas"
    },

    "GUIA-SVG-2020": {
        "titulo": "Guía de Sistemas de Vida y Costumbres de Grupos Humanos",
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_medio_humano.pdf",
        "año": 2020,
        "edicion": "2ª",
        "categoria": "Guías Metodológicas",
        "tipo": "guia_metodologica",
        "triggers_art11": ["c"],
        "componentes": ["medio_humano", "pueblos_indigenas"],
        "descripcion": "Las 5 dimensiones del medio humano: geográfica, demográfica, antropológica, socioeconómica, bienestar social"
    },

    "GUIA-PAISAJE-2019": {
        "titulo": "Guía de Evaluación de Impactos en el Valor Paisajístico",
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_paisaje.pdf",
        "año": 2019,
        "edicion": "1ª",
        "categoria": "Guías Metodológicas",
        "tipo": "guia_metodologica",
        "triggers_art11": ["e"],
        "componentes": ["paisaje"],
        "descripcion": "Metodología para evaluar alteración de valor paisajístico o turístico"
    },

    "GUIA-PAC-2023": {
        "titulo": "Guía de Participación Ciudadana en el SEIA",
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_pac.pdf",
        "año": 2023,
        "edicion": "2ª",
        "categoria": "Guías Metodológicas",
        "tipo": "guia_metodologica",
        "triggers_art11": ["a", "c"],
        "componentes": ["medio_humano"],
        "descripcion": "Procedimiento de participación ciudadana en evaluación ambiental"
    },

    "GUIA-CPLI-2023": {
        "titulo": "Guía de Consulta Indígena (CPLI) en el SEIA",
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_cpli.pdf",
        "año": 2023,
        "edicion": "2ª",
        "categoria": "Guías Metodológicas",
        "tipo": "guia_metodologica",
        "triggers_art11": ["c", "d"],
        "componentes": ["pueblos_indigenas"],
        "descripcion": "Procedimiento de consulta a pueblos indígenas según Art. 85 DS 40"
    },

    # Guías Sectoriales
    "GUIA-MINERIA-2021": {
        "titulo": "Guía para la Evaluación Ambiental de Proyectos Mineros",
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_mineria.pdf",
        "año": 2021,
        "edicion": "1ª",
        "categoria": "Guías Sectoriales",
        "tipo": "guia_sectorial",
        "sector": "mineria",
        "descripcion": "Criterios específicos para evaluación de proyectos mineros"
    },

    "GUIA-ENERGIA-2020": {
        "titulo": "Guía para Centrales de Generación de Energía",
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_energia.pdf",
        "año": 2020,
        "edicion": "1ª",
        "categoria": "Guías Sectoriales",
        "tipo": "guia_sectorial",
        "sector": "energia",
        "descripcion": "Criterios para hidroeléctricas, termoeléctricas, eólicas, solares"
    },

    "GUIA-INMOBILIARIO-2019": {
        "titulo": "Guía para Proyectos Inmobiliarios",
        "url": "https://www.sea.gob.cl/sites/default/files/guias/guia_inmobiliario.pdf",
        "año": 2019,
        "edicion": "1ª",
        "categoria": "Guías Sectoriales",
        "tipo": "guia_sectorial",
        "sector": "inmobiliario",
        "descripcion": "Criterios para proyectos inmobiliarios y urbanos"
    },

    # Ordinarios y Criterios
    "ORD-NOMBRE-2023": {
        "titulo": "Ordinario sobre nombre y descripción de proyectos",
        "url": "https://www.sea.gob.cl/sites/default/files/ordinarios/ord_nombre_proyecto.pdf",
        "año": 2023,
        "categoria": "Ordinarios",
        "tipo": "ordinario",
        "descripcion": "Criterios para nombrar y describir proyectos en el SEIA"
    },

    "CRIT-LB-2024": {
        "titulo": "Criterios de evaluación de línea de base",
        "url": "https://www.sea.gob.cl/sites/default/files/criterios/criterios_linea_base.pdf",
        "año": 2024,
        "categoria": "Criterios",
        "tipo": "criterio_evaluacion",
        "descripcion": "Suficiencia técnica de estudios de línea de base"
    }
}
```

### 7.2 Actualización de Tabla de Documentos

```sql
-- Agregar campos para guías SEA
ALTER TABLE legal.documentos ADD COLUMN IF NOT EXISTS
    sector VARCHAR(50);

ALTER TABLE legal.documentos ADD COLUMN IF NOT EXISTS
    edicion VARCHAR(20);

ALTER TABLE legal.documentos ADD COLUMN IF NOT EXISTS
    url_fuente_oficial TEXT;

-- Vista para búsqueda de guías
CREATE OR REPLACE VIEW legal.v_guias_sea AS
SELECT
    d.id,
    d.titulo,
    d.numero AS codigo,
    d.tipo,
    d.categoria,
    d.sector,
    d.edicion,
    d.fecha_publicacion,
    d.url_fuente_oficial,
    d.triggers_art11,
    d.componentes_ambientales,
    d.estado
FROM legal.documentos d
WHERE d.tipo IN ('guia_metodologica', 'guia_sectorial', 'instructivo', 'ordinario', 'criterio_evaluacion')
ORDER BY d.fecha_publicacion DESC;
```

---

## Parte VIII: Plan de Implementación

### 8.1 Priorización

| Fase | Mejora | Semanas | Dependencias |
|------|--------|---------|--------------|
| **1** | Estructura DIA diferenciada | 2 | Ninguna |
| **1** | Ingesta guías SEA | 2 | Ninguna |
| **2** | Dimensiones medio humano | 3 | Guías SEA |
| **2** | Gestor ICSARA/Adendas | 4 | Ninguna |
| **3** | Módulo medidas mitigación | 4 | Estructura EIA |
| **3** | Generador resumen ejecutivo | 3 | Todas las anteriores |
| **4** | Validadores de calidad | 3 | Generador resumen |

### 8.2 Migraciones de BD

```sql
-- Archivo: backend/migrations/007_mejoras_estructura_eia_v2.sql

-- Parte 1: Tipos enumerados
CREATE TYPE estado_evaluacion_enum AS ENUM (...);
CREATE TYPE instrumento_ambiental AS ENUM ('EIA', 'DIA');
-- ... (todos los tipos definidos arriba)

-- Parte 2: Tablas de proceso de evaluación
CREATE TABLE proyectos.proceso_evaluacion (...);
CREATE TABLE proyectos.icsara (...);
CREATE TABLE proyectos.adenda (...);

-- Parte 3: Tablas de medidas e impactos
CREATE TABLE proyectos.impactos_ambientales (...);
CREATE TABLE proyectos.medidas_mitigacion (...);
CREATE TABLE proyectos.medida_impacto (...);

-- Parte 4: Modificaciones a tablas existentes
ALTER TABLE asistente_config.capitulos_eia ADD COLUMN aplica_instrumento ...;
CREATE TABLE asistente_config.estructura_por_instrumento (...);

-- Parte 5: Datos iniciales
INSERT INTO asistente_config.componentes_linea_base ... -- Dimensiones medio humano
INSERT INTO asistente_config.estructura_por_instrumento ... -- Config EIA vs DIA
```

### 8.3 Archivos a Crear

```
backend/
├── app/
│   ├── db/models/
│   │   ├── proceso_evaluacion.py      # NUEVO
│   │   ├── medidas_mitigacion.py      # NUEVO
│   │   └── impactos_ambientales.py    # NUEVO
│   │
│   ├── schemas/
│   │   ├── proceso_evaluacion.py      # NUEVO
│   │   ├── medidas_mitigacion.py      # NUEVO
│   │   └── impactos_ambientales.py    # NUEVO
│   │
│   ├── services/
│   │   ├── proceso_evaluacion/
│   │   │   └── service.py             # NUEVO
│   │   ├── medidas_mitigacion/
│   │   │   └── service.py             # NUEVO
│   │   └── generador_resumen/
│   │       └── service.py             # NUEVO
│   │
│   ├── services/asistente/tools/
│   │   ├── proceso_evaluacion.py      # NUEVO
│   │   ├── medidas_mitigacion.py      # NUEVO
│   │   ├── medio_humano.py            # NUEVO
│   │   └── generador_resumen.py       # NUEVO
│   │
│   └── api/v1/endpoints/
│       ├── proceso_evaluacion.py      # NUEVO
│       └── medidas_mitigacion.py      # NUEVO
│
├── migrations/
│   └── 007_mejoras_estructura_eia_v2.sql  # NUEVO
│
└── data/scripts/
    └── ingestar_guias_sea.py          # ACTUALIZAR

frontend/
├── src/
│   ├── components/asistente/
│   │   ├── ProcesoEvaluacion.vue      # NUEVO
│   │   ├── MedidasMitigacion.vue      # NUEVO
│   │   └── MedioHumano.vue            # NUEVO
│   │
│   ├── stores/
│   │   ├── procesoEvaluacion.ts       # NUEVO
│   │   └── medidasMitigacion.ts       # NUEVO
│   │
│   └── types/
│       ├── procesoEvaluacion.ts       # NUEVO
│       └── medidasMitigacion.ts       # NUEVO
```

---

## Parte IX: Checklist de Validación

### 9.1 Validación Pre-Presentación (Automatizable)

```python
class ValidadorEIA:
    """Valida completitud del EIA antes de presentación."""

    CHECKS = [
        # Estructura
        ("estructura_completa", "Todos los capítulos obligatorios completados"),
        ("capitulos_progreso_100", "Todos los capítulos al 100%"),

        # Contenido
        ("resumen_max_paginas", "Resumen no excede límite de páginas"),
        ("resumen_legibilidad", "Resumen tiene legibilidad adecuada"),
        ("linea_base_actualizada", "Línea de base tiene menos de 2 años"),

        # Art. 11
        ("art11_justificado", "Todos los efectos Art. 11 están justificados"),

        # PAS
        ("pas_identificados", "Todos los PAS aplicables identificados"),
        ("pas_documentados", "Requisitos de PAS documentados"),

        # Medidas
        ("impactos_cubiertos", "Todos los impactos significativos tienen medidas"),
        ("jerarquia_respetada", "Se respeta jerarquía de mitigación"),

        # Plan de seguimiento
        ("variables_monitoreadas", "Todas las variables clave tienen monitoreo"),
        ("indicadores_definidos", "Todos los indicadores de cumplimiento definidos"),

        # Cartografía
        ("cartografia_wgs84", "Cartografía en datum WGS84"),
        ("area_influencia_justificada", "AI justificada por componente"),

        # Equipo
        ("equipo_identificado", "Equipo elaborador identificado con títulos"),

        # Coherencia
        ("coherencia_interna", "Datos coherentes entre capítulos"),
    ]

    async def validar(self, proyecto_id: int) -> ResultadoValidacion:
        """Ejecuta todos los checks y retorna resultado."""
```

---

## Anexos

### A. Organismos con Competencia Ambiental (OAECA)

| Organismo | Sigla | Competencias Principales |
|-----------|-------|--------------------------|
| Servicio Agrícola y Ganadero | SAG | Flora, fauna, suelos, subdivisión |
| Corporación Nacional Forestal | CONAF | Bosques, áreas silvestres protegidas |
| Dirección General de Aguas | DGA | Recursos hídricos, derechos de agua |
| Servicio Nacional de Geología y Minería | SERNAGEOMIN | Geología, relaves, botaderos, cierre |
| Secretaría Regional Ministerial de Salud | SEREMI Salud | Residuos, aguas servidas, ruido, aire |
| Consejo de Monumentos Nacionales | CMN | Patrimonio arqueológico, histórico |
| Secretaría Regional Ministerial de Medio Ambiente | SEREMI MMA | Coordinación, biodiversidad |
| Municipalidades | MUNICIPIO | Uso de suelo, planificación |
| Corporación Nacional de Desarrollo Indígena | CONADI | Pueblos indígenas |
| Servicio Nacional de Turismo | SERNATUR | Turismo, ZOIT |
| Subsecretaría de Pesca y Acuicultura | SUBPESCA | Recursos marinos, acuicultura |
| Gobernación Marítima | DIRECTEMAR | Borde costero |

### B. Normas de Referencia

| Norma | Componente | Parámetro Principal |
|-------|------------|---------------------|
| D.S. 59/1998 | Aire | MP10 (130 µg/m³N) |
| D.S. 12/2011 | Aire | MP2.5 (35 µg/m³N) |
| D.S. 113/2002 | Aire | SO2 |
| D.S. 114/2002 | Aire | NO2 |
| NCh 1333 | Agua | Riego, recreación |
| D.S. 143/2009 | Suelos | Contaminantes |
| D.S. 38/2011 | Ruido | Niveles máximos |
| D.S. 148/2003 | Residuos | Peligrosos |
| D.S. 90/2000 | Emisión | RILES |
| D.S. 46/2002 | Emisión | Aguas servidas |

---

*Documento generado: Enero 2026*
*Versión: 2.0*
*Próxima revisión: Con implementación de mejoras*
