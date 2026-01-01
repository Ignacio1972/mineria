# Documento 2: Taxonomía Documental y Proceso SEIA

## Introducción

Este documento describe en detalle el proceso de Evaluación de Impacto Ambiental en Chile y la taxonomía completa de documentos que el sistema RAG debe gestionar. Es fundamental que el desarrollador comprenda este proceso porque **la estructura del corpus RAG refleja directamente la estructura del proceso regulatorio**.

Cada categoría de documento existe porque cumple un rol específico en el proceso SEIA. Entender ese rol permite:
- Diseñar metadatos relevantes
- Crear filtros de búsqueda útiles
- Vincular resultados RAG con etapas del proceso
- Priorizar qué documentos ingestar primero

---

## Parte 1: El Proceso SEIA en Detalle

### 1.1 Marco Legal Fundamental

El Sistema de Evaluación de Impacto Ambiental (SEIA) está regulado por:

| Norma | Contenido | Relevancia |
|-------|-----------|------------|
| **Ley 19.300** | Bases Generales del Medio Ambiente | Define qué proyectos ingresan (Art. 10) y cuándo requieren EIA (Art. 11) |
| **DS 40/2012** | Reglamento del SEIA | Detalla procedimientos, plazos, contenidos mínimos |
| **DS 66/2018** | Reglamento de Consulta Indígena | Proceso de consulta a pueblos originarios |

### 1.2 Decisión de Ingreso al SEIA

El primer paso es determinar si un proyecto **debe** ingresar al SEIA. Esto se define en el **Artículo 10 de la Ley 19.300**, que lista las tipologías de proyectos que requieren evaluación ambiental. El **Artículo 3 del DS 40/2012** detalla cada tipología.

Para proyectos mineros, las tipologías relevantes incluyen:

```
Art. 3 DS 40/2012 - Tipologías Mineras:
├── Letra i.1) Explotación de yacimientos > 5.000 ton/mes
├── Letra i.2) Plantas procesadoras > 1.000 ton/día
├── Letra i.3) Depósitos de relaves
├── Letra i.4) Depósitos de estériles > 1.000.000 m³
├── Letra i.5) Extracción industrial de áridos > 500.000 ton/año
└── Letra o.7) Proyectos en áreas protegidas
```

**Importante**: Un proyecto puede ingresar voluntariamente al SEIA aunque no esté obligado. Esto le otorga la "certificación ambiental" que facilita permisos sectoriales.

### 1.3 Los Triggers del Artículo 11: DIA vs EIA

Una vez determinado que el proyecto debe ingresar al SEIA, la pregunta crítica es: **¿Con qué instrumento?**

El **Artículo 11 de la Ley 19.300** establece 6 "efectos, características o circunstancias" (ECC) que, de presentarse, obligan a presentar un EIA en lugar de una DIA:

#### Letra a) Riesgo para la Salud de la Población

Se activa cuando el proyecto genera:
- Emisiones atmosféricas que exceden normas de calidad
- Contaminación de aguas de consumo humano
- Generación de residuos peligrosos cerca de poblaciones
- Ruido que supera normas en zonas habitadas

**Documentos RAG relevantes**:
- Criterios de evaluación de calidad del aire (MP10, MP2.5)
- Guías sobre ruido y salud
- Normas de calidad de aguas

#### Letra b) Efectos Adversos sobre Recursos Naturales Renovables

Se activa cuando el proyecto afecta significativamente:
- Calidad y cantidad de aguas superficiales o subterráneas
- Suelo (erosión, contaminación, cambio de uso)
- Aire (más allá de normas)
- Flora y fauna nativa
- **Glaciares y ambiente periglaciar** (muy relevante para minería de altura)

**Documentos RAG relevantes**:
- Criterios de evaluación del recurso hídrico
- Guías sobre glaciares y permafrost
- Criterios de fauna y flora
- Guías sobre línea base de biodiversidad

#### Letra c) Reasentamiento de Comunidades Humanas

Se activa cuando el proyecto implica:
- Relocalización de grupos humanos
- Alteración significativa de sistemas de vida
- Modificación de accesos a recursos básicos

**Documentos RAG relevantes**:
- Guías sobre comunidades humanas
- Criterios de área de influencia social
- Instructivos sobre participación ciudadana

#### Letra d) Localización en o Próxima a Áreas Protegidas

Se activa cuando el proyecto se ubica en o cerca de:
- SNASPE (Parques Nacionales, Reservas, Monumentos Naturales)
- Santuarios de la Naturaleza
- Humedales Ramsar
- Reservas de la Biósfera
- Áreas de Desarrollo Indígena (ADI)
- Sitios prioritarios para la conservación
- Glaciares (protección especial)
- **Áreas colocadas bajo protección oficial** (concepto amplio)

**Documentos RAG relevantes**:
- Instructivos sobre áreas protegidas (hay múltiples)
- Guías sobre proyectos en/cerca de áreas protegidas
- Criterios específicos por tipo de área
- Jurisprudencia sobre "proximidad" (¿cuántos km?)

#### Letra e) Alteración del Patrimonio Cultural

Se activa cuando el proyecto afecta:
- Sitios arqueológicos
- Sitios paleontológicos
- Monumentos históricos
- Patrimonio cultural inmaterial de pueblos originarios

**Documentos RAG relevantes**:
- Criterios de patrimonio arqueológico (2024)
- Criterios de patrimonio paleontológico (2025)
- Guías del Consejo de Monumentos Nacionales
- Instructivos sobre consulta indígena (Convenio 169 OIT)

#### Letra f) Alteración de Paisaje o Sitios con Valor Turístico

Se activa cuando el proyecto modifica significativamente:
- Paisajes con valor estético reconocido
- Zonas de interés turístico (ZOIT)
- Áreas con potencial turístico declarado

**Documentos RAG relevantes**:
- Guías sobre evaluación de paisaje
- Criterios de impacto visual
- Criterios de efecto sombra (parques eólicos)

### 1.4 Flujo del Proceso DIA

Cuando un proyecto NO genera ninguno de los efectos del Art. 11, ingresa mediante **Declaración de Impacto Ambiental**:

```
FLUJO DIA (Declaración de Impacto Ambiental)
═══════════════════════════════════════════

[1] INGRESO
    │
    │  Titular presenta DIA en plataforma e-SEIA
    │  Contenido: descripción proyecto, área influencia,
    │  justificación de ausencia de efectos Art. 11,
    │  plan de emergencias, normativa aplicable
    │
    ▼
[2] TEST DE ADMISIBILIDAD (5 días)
    │
    │  SEA verifica que DIA esté completa
    │
    ├──► NO ADMISIBLE ──► Resolución de Inadmisibilidad
    │                     (Titular puede corregir y reingresar)
    │
    ▼
[3] RESOLUCIÓN DE ADMISIBILIDAD
    │
    │  Se inicia formalmente la evaluación
    │  Se publican antecedentes para consulta
    │
    ▼
[4] EVALUACIÓN POR OAECA (15 días)
    │
    │  Órganos con Competencia Ambiental evalúan:
    │  - SAG (fauna, flora, suelo agrícola)
    │  - DGA (aguas)
    │  - CONAF (áreas protegidas, bosques)
    │  - CMN (patrimonio)
    │  - SERNAGEOMIN (geología, minería)
    │  - Municipalidades
    │  - Otros según proyecto
    │
    │  Cada órgano emite INFORME SECTORIAL
    │
    ▼
[5] SEA ELABORA ICSARA
    │
    │  Informe Consolidado de Solicitud de Aclaraciones,
    │  Rectificaciones o Ampliaciones
    │
    │  Consolida todas las observaciones de OAECA
    │
    ▼
[6] ¿ERRORES, OMISIONES O INEXACTITUDES?
    │
    ├──► NO ──────────────────────────────────────┐
    │                                              │
    ▼                                              │
[7] SEA SOLICITA ADENDA (10 días)                 │
    │                                              │
    │  OAECA revisan y confirman qué falta        │
    │                                              │
    ▼                                              │
[8] TITULAR PRESENTA ADENDA                        │
    │                                              │
    │  Responde a cada observación del ICSARA     │
    │  Puede haber múltiples rondas de Adenda     │
    │                                              │
    ▼                                              │
[9] SEA ELABORA ICSARA COMPLEMENTARIO             │
    │  (si hay nuevas observaciones)              │
    │                                              │
    └──► Vuelve a paso [6]                        │
                                                   │
    ◄──────────────────────────────────────────────┘
    │
    ▼
[10] SEA ELABORA ICE (10 días)
    │
    │  Informe Consolidado de Evaluación
    │  Resume toda la evaluación técnica
    │  Recomienda aprobar o rechazar
    │
    ▼
[11] CALIFICACIÓN (5 días)
    │
    │  Comisión de Evaluación Regional
    │  (o Director Ejecutivo SEA si es interregional)
    │
    │  Vota aprobar/rechazar basándose en ICE
    │
    ▼
[12] RCA (Resolución de Calificación Ambiental)
    │
    ├──► APROBATORIA: Proyecto puede ejecutarse
    │    (puede incluir condiciones y compromisos)
    │
    └──► RECHAZO: Proyecto no puede ejecutarse
         (Titular puede recurrir o modificar y reingresar)
```

**Plazo total base DIA**: ~60 días hábiles (extensible a 90 con Adendas)

### 1.5 Flujo del Proceso EIA

Cuando un proyecto SÍ genera al menos uno de los efectos del Art. 11:

```
FLUJO EIA (Estudio de Impacto Ambiental)
════════════════════════════════════════

[1] INGRESO
    │
    │  Contenido adicional vs DIA:
    │  - Línea base detallada del área de influencia
    │  - Predicción y evaluación de impactos
    │  - Plan de medidas de mitigación, reparación, compensación
    │  - Plan de seguimiento ambiental
    │  - Plan de cumplimiento de normativa
    │
    ▼
[2] TEST DE ADMISIBILIDAD (5 días)
    │
    ▼
[3] RESOLUCIÓN DE ADMISIBILIDAD
    │
    │  *** PARTICIPACIÓN CIUDADANA OBLIGATORIA ***
    │  Se abre período de 60 días para observaciones
    │
    │  *** CONSULTA INDÍGENA (si aplica) ***
    │  Si proyecto afecta pueblos indígenas,
    │  se inicia proceso de consulta Convenio 169 OIT
    │
    ▼
[4] EVALUACIÓN POR OAECA (30 días)
    │
    │  Evaluación más exhaustiva que DIA
    │  Incluye revisión de línea base y predicción de impactos
    │
    ▼
[5] SEA ELABORA ICSARA
    │
    ▼
[6] ¿ERRORES, OMISIONES O INEXACTITUDES?
    │
    ├──► NO ──────────────────────────────────────┐
    │                                              │
    ▼                                              │
[7] SEA SOLICITA ADENDA (15 días)                 │
    │                                              │
    ▼                                              │
[8] TITULAR PRESENTA ADENDA                        │
    │                                              │
    ▼                                              │
[9] ICSARA COMPLEMENTARIO (si necesario)          │
    │                                              │
    └──► Vuelve a paso [6]                        │
                                                   │
    ◄──────────────────────────────────────────────┘
    │
    ▼
[10] SEA ELABORA ICE (15 días)
    │
    ▼
[11] OAECA VISA ICE (5 días)
    │
    │  Paso adicional en EIA:
    │  Cada OAECA confirma que sus observaciones
    │  fueron adecuadamente respondidas
    │
    ▼
[12] CALIFICACIÓN (4 días)
    │
    ▼
[13] RCA
```

**Plazo total base EIA**: ~120 días hábiles (extensible a 180+ con Adendas y consulta indígena)

### 1.6 Actores del Proceso

| Sigla | Nombre Completo | Rol en el Proceso |
|-------|-----------------|-------------------|
| **SEA** | Servicio de Evaluación Ambiental | Administra el SEIA, coordina evaluación, elabora informes consolidados |
| **OAECA** | Órganos de la Administración del Estado con Competencia Ambiental | Evalúan técnicamente según su especialidad |
| **SAG** | Servicio Agrícola y Ganadero | Fauna, flora, suelo agrícola |
| **DGA** | Dirección General de Aguas | Recursos hídricos, derechos de agua |
| **CONAF** | Corporación Nacional Forestal | Bosques, SNASPE |
| **CMN** | Consejo de Monumentos Nacionales | Patrimonio arqueológico, paleontológico, histórico |
| **SERNAGEOMIN** | Servicio Nacional de Geología y Minería | Aspectos geológicos, seguridad minera |
| **CONADI** | Corporación Nacional de Desarrollo Indígena | Pueblos originarios, ADI |
| **SMA** | Superintendencia del Medio Ambiente | Fiscalización post-RCA |
| **Titular** | Empresa o persona natural | Presenta proyecto, responde observaciones |

### 1.7 Documentos Generados en el Proceso

Cada etapa del proceso genera documentos específicos que pueden ser parte del corpus RAG:

| Documento | Generado por | Etapa | Contenido |
|-----------|--------------|-------|-----------|
| DIA/EIA | Titular | Ingreso | Descripción completa del proyecto |
| Resolución Admisibilidad | SEA | Admisión | Acepta/rechaza a trámite |
| Informes Sectoriales | OAECA | Evaluación | Observaciones técnicas por materia |
| ICSARA | SEA | Evaluación | Consolidado de observaciones |
| Adenda | Titular | Respuesta | Respuestas a observaciones |
| ICE | SEA | Pre-calificación | Evaluación técnica final |
| Acta PAC | SEA | Participación | Observaciones ciudadanas |
| Acta Consulta Indígena | SEA | Consulta | Proceso con pueblos originarios |
| RCA | Comisión/DE | Calificación | Resolución final |

---

## Parte 2: Taxonomía del Corpus Documental

### 2.1 Estructura Jerárquica Completa

La siguiente taxonomía organiza todos los tipos de documentos que el sistema debe gestionar:

```
📁 CORPUS RAG - SISTEMA DE GESTIÓN DOCUMENTAL
│
│
├── 📁 1. NORMATIVA LEGAL
│   │
│   │   Documentos con fuerza de ley que establecen obligaciones.
│   │   Son la base del sistema y raramente cambian.
│   │
│   ├── 📁 1.1 Leyes
│   │   │   Aprobadas por el Congreso Nacional
│   │   │
│   │   ├── Ley 19.300 - Bases Generales del Medio Ambiente (1994)
│   │   │   └── Artículos clave: 2, 8, 10, 11, 12, 13, 18bis, 19, 25, 34, 35
│   │   │
│   │   ├── Ley 20.417 - Crea Institucionalidad Ambiental (2010)
│   │   │   └── Crea SEA, SMA, Tribunales Ambientales
│   │   │
│   │   ├── Ley 20.600 - Tribunales Ambientales (2012)
│   │   │
│   │   ├── Ley 20.730 - Regula el Lobby (2014)
│   │   │   └── Aplicable a reuniones con SEA
│   │   │
│   │   └── Ley 21.455 - Ley Marco de Cambio Climático (2022)
│   │
│   ├── 📁 1.2 Reglamentos (Decretos Supremos)
│   │   │   Detallan la aplicación de las leyes
│   │   │
│   │   ├── DS 40/2012 - Reglamento del SEIA
│   │   │   └── 120+ artículos detallando procedimientos
│   │   │
│   │   ├── DS 66/2018 - Reglamento Consulta Indígena
│   │   │   └── Procedimiento Convenio 169 OIT
│   │   │
│   │   ├── DS 38/2012 - Reglamento de Clasificación de Especies
│   │   │
│   │   └── DS 39/2012 - Normas de Calidad Secundaria
│   │
│   └── 📁 1.3 Decretos y Resoluciones
│       │   Normas específicas de aplicación
│       │
│       ├── Normas de Calidad Primaria (aire, agua)
│       ├── Normas de Emisión
│       └── Planes de Descontaminación
│
│
├── 📁 2. GUÍAS SEA
│   │
│   │   Documentos orientadores del SEA. No son obligatorios pero
│   │   representan el "estado del arte" para la evaluación.
│   │   Se actualizan frecuentemente.
│   │
│   ├── 📁 2.1 Guías de Descripción de Proyecto
│   │   │
│   │   │   Explican cómo describir proyectos por sector.
│   │   │   Muy útiles para entender qué evaluar.
│   │   │
│   │   ├── 📁 Por Sector Productivo
│   │   │   ├── Minería de Cobre y Metales Preciosos
│   │   │   ├── Explotación de Litio desde Salares (2ª ed. 2025)
│   │   │   ├── Plantas Desalinizadoras (2023)
│   │   │   ├── Generación Eólica (2ª ed. 2020)
│   │   │   ├── Generación Solar Fotovoltaica
│   │   │   ├── Generación Geotérmica (2ª ed. 2022)
│   │   │   ├── Generación Biomasa/Biogás (2ª ed. 2022)
│   │   │   ├── Pequeñas Centrales Hidroeléctricas (<20MW) (2021)
│   │   │   ├── Desarrollo Inmobiliario (2019)
│   │   │   ├── Salmonicultura en Mar (2021)
│   │   │   ├── Desarrollo de Petróleo y Gas (2ª ed. 2021)
│   │   │   ├── Transporte Terrestre
│   │   │   ├── Planteles Avícolas
│   │   │   └── [otros sectores]
│   │   │
│   │   └── 📁 Por Fase de Proyecto
│   │       ├── Fase de Construcción
│   │       ├── Fase de Operación
│   │       └── Fase de Cierre
│   │
│   ├── 📁 2.2 Guías Artículo 11 (Triggers EIA)
│   │   │
│   │   │   Explican cómo evaluar cada literal del Art. 11.
│   │   │   CRÍTICAS para el motor de reglas del sistema.
│   │   │
│   │   ├── Letra a) Riesgo para Salud de la Población
│   │   ├── Letra b) Efectos Adversos en Recursos Naturales
│   │   │   ├── Recurso Hídrico
│   │   │   ├── Suelo
│   │   │   ├── Aire
│   │   │   ├── Flora y Fauna
│   │   │   └── Glaciares
│   │   ├── Letra c) Reasentamiento de Comunidades
│   │   ├── Letra d) Áreas Protegidas y Sitios Prioritarios
│   │   ├── Letra e) Patrimonio Cultural
│   │   │   ├── Arqueológico
│   │   │   ├── Paleontológico
│   │   │   └── Histórico
│   │   └── Letra f) Paisaje y Turismo
│   │
│   ├── 📁 2.3 Guías de Área de Influencia
│   │   │
│   │   │   Metodologías para delimitar el área de estudio
│   │   │
│   │   ├── Área de Influencia General
│   │   ├── Área de Influencia por Componente
│   │   └── Enfoque de Género en Área de Influencia
│   │
│   ├── 📁 2.4 Guías de Participación Ciudadana
│   │   │
│   │   ├── PAC en DIA (cuando aplica)
│   │   ├── PAC en EIA (obligatoria)
│   │   ├── Observaciones Ciudadanas
│   │   └── Monitoreos Participativos (2025)
│   │
│   ├── 📁 2.5 Guías de Metodologías y Modelos
│   │   │
│   │   ├── Modelación de Calidad del Aire
│   │   ├── Modelación Hidrogeológica
│   │   ├── Evaluación de Impactos
│   │   └── Línea Base
│   │
│   ├── 📁 2.6 Guías de Permisos Ambientales Sectoriales (PAS)
│   │   │
│   │   │   Los PAS son permisos que se tramitan dentro del SEIA.
│   │   │   El Art. 111+ del DS 40/2012 lista todos los PAS.
│   │   │
│   │   ├── PAS relacionados con aguas
│   │   ├── PAS relacionados con suelo
│   │   ├── PAS relacionados con fauna
│   │   ├── PAS relacionados con patrimonio
│   │   └── [otros PAS por materia]
│   │
│   └── 📁 2.7 Guías No Vigentes (Histórico)
│       │
│       │   Guías reemplazadas por versiones nuevas.
│       │   Útiles para proyectos evaluados bajo normativa anterior.
│       │
│       └── [guías archivadas con fecha de derogación]
│
│
├── 📁 3. INSTRUCTIVOS SEA
│   │
│   │   Directrices operativas del SEA (Ordinarios).
│   │   Establecen cómo interpretar y aplicar la normativa.
│   │   Muy importantes para entender la práctica real.
│   │
│   ├── 📁 3.1 Consulta a Pueblos Indígenas
│   │   │
│   │   ├── Convenio 169 OIT - Procedimiento general (2025)
│   │   ├── Art. 86 - Reuniones con GHPPI (2024)
│   │   ├── Art. 27 - Afectación directa a pueblos indígenas (2014)
│   │   └── [otros instructivos indígenas]
│   │
│   ├── 📁 3.2 Procedimientos Administrativos
│   │   │
│   │   ├── e-SEIA - Uso de plataforma electrónica
│   │   ├── Firma electrónica avanzada
│   │   ├── Foliación y expedientes
│   │   ├── Cambio de titularidad
│   │   ├── Competencias de municipalidades
│   │   └── Lobby (Ley 20.730)
│   │
│   ├── 📁 3.3 Pertinencia de Ingreso
│   │   │
│   │   │   Cómo determinar si un proyecto debe ingresar al SEIA
│   │   │
│   │   ├── Consultas de pertinencia (múltiples instructivos)
│   │   ├── Modificación de proyectos calificados
│   │   └── Literales específicos del Art. 3 DS 40
│   │
│   ├── 📁 3.4 Áreas Protegidas
│   │   │
│   │   │   Múltiples instructivos sobre este tema crítico
│   │   │
│   │   ├── Áreas colocadas bajo protección oficial (2023)
│   │   ├── Sitios prioritarios para conservación
│   │   ├── Proyectos acuícolas en/cerca de áreas protegidas
│   │   └── [otros]
│   │
│   ├── 📁 3.5 Seguimiento Ambiental
│   │   │
│   │   ├── Seguimiento de RCA
│   │   ├── Auditorías ambientales independientes
│   │   └── Uso de geoinformación (2025)
│   │
│   ├── 📁 3.6 Participación Ciudadana
│   │   │
│   │   ├── Documentación de respaldo PAC (2025)
│   │   ├── Admisibilidad de observaciones
│   │   └── Consideración de observaciones en evaluación
│   │
│   └── 📁 3.7 Aplicación Normativa
│       │
│       ├── Aplicabilidad de guías y criterios (2024)
│       ├── Vigencia y observancia de guías
│       ├── Concepto de impacto ambiental y riesgo
│       └── Concepto de cargas ambientales
│
│
├── 📁 4. CRITERIOS DE EVALUACIÓN
│   │
│   │   Documentos técnicos específicos que establecen estándares
│   │   para evaluar componentes ambientales particulares.
│   │   Alta especificidad técnica.
│   │
│   ├── 📁 4.1 Componentes Ambientales
│   │   │
│   │   ├── 📁 Recursos Hídricos
│   │   │   ├── Contenidos técnicos para evaluación (2022)
│   │   │   ├── Cambio climático y recurso hídrico (2023)
│   │   │   ├── Alteración del régimen sedimentológico (2024)
│   │   │   └── Uso de normas de referencia (2024)
│   │   │
│   │   ├── 📁 Calidad del Aire
│   │   │   └── Impacto de emisiones en zonas saturadas MP10/MP2.5 (2023)
│   │   │
│   │   ├── 📁 Ruido
│   │   │   ├── Ruido sobre fauna nativa (2022)
│   │   │   ├── Ruido submarino (2022)
│   │   │   ├── Efecto sinérgico ruido y salud (2022)
│   │   │   ├── Ruido efecto corona en transmisión eléctrica (2023)
│   │   │   └── Radiación electromagnética (2023)
│   │   │
│   │   └── 📁 Fauna y Flora
│   │       ├── Campañas de terreno y validación de datos (2022)
│   │       ├── Golondrinas de mar (2ª ed. 2025)
│   │       ├── Perturbación controlada (2022)
│   │       └── Rescate y relocalización (2022)
│   │
│   ├── 📁 4.2 Patrimonio Cultural
│   │   │
│   │   ├── Patrimonio arqueológico (2024)
│   │   └── Patrimonio paleontológico (2025)
│   │
│   ├── 📁 4.3 Impactos Especiales
│   │   │
│   │   ├── Impactos acumulativos y sinérgicos (2024)
│   │   ├── Alcances y principios metodológicos (2023)
│   │   ├── Efecto sombra intermitente en parques eólicos (2021)
│   │   └── Áreas astronómicas (2024)
│   │
│   ├── 📁 4.4 Proyectos Específicos
│   │   │
│   │   ├── Hidrógeno verde - Introducción (2022)
│   │   ├── Hidrógeno verde - Descripción integrada (2023)
│   │   ├── Almacenamiento de energía (2023)
│   │   ├── Salmonicultura en/cerca áreas protegidas (2023)
│   │   └── Proyectos inmobiliarios - Transporte (2022)
│   │
│   └── 📁 4.5 Objetos de Protección
│       │
│       └── Criterio general de objetos de protección (2022)
│
│
├── 📁 5. JURISPRUDENCIA
│   │
│   │   Sentencias y dictámenes que interpretan la normativa.
│   │   Establecen precedentes importantes.
│   │
│   ├── 📁 5.1 Tribunales Ambientales
│   │   │
│   │   │   Chile tiene 3 Tribunales Ambientales:
│   │   │   - 1° TA: Antofagasta (norte, zona minera)
│   │   │   - 2° TA: Santiago (centro)
│   │   │   - 3° TA: Valdivia (sur)
│   │   │
│   │   ├── 📁 Por Tribunal
│   │   │   ├── Primer Tribunal Ambiental
│   │   │   ├── Segundo Tribunal Ambiental
│   │   │   └── Tercer Tribunal Ambiental
│   │   │
│   │   └── 📁 Por Materia
│   │       ├── Reclamaciones contra RCA
│   │       ├── Demandas por daño ambiental
│   │       └── Solicitudes de medidas cautelares
│   │
│   ├── 📁 5.2 Corte Suprema
│   │   │
│   │   │   Recursos de casación contra sentencias de TA
│   │   │
│   │   └── Sentencias relevantes en materia ambiental
│   │
│   └── 📁 5.3 Contraloría General de la República
│       │
│       │   Dictámenes sobre interpretación de normativa
│       │
│       └── Dictámenes en materia ambiental
│
│
├── 📁 6. DOCUMENTOS DE PROCESO
│   │
│   │   Modelos y ejemplos de documentos generados durante
│   │   el proceso de evaluación. Útiles como referencia.
│   │
│   ├── 📁 6.1 Modelos y Templates
│   │   │
│   │   ├── Estructura tipo de DIA
│   │   ├── Estructura tipo de EIA
│   │   ├── Formato de Adendas
│   │   └── Contenidos mínimos por tipología
│   │
│   ├── 📁 6.2 Ejemplos de RCA
│   │   │
│   │   │   RCAs de proyectos similares como referencia
│   │   │
│   │   ├── 📁 Por Sector
│   │   │   ├── RCAs Minería
│   │   │   ├── RCAs Energía
│   │   │   └── [otros sectores]
│   │   │
│   │   └── 📁 Por Resultado
│   │       ├── RCAs Aprobatorias
│   │       ├── RCAs con Condiciones Especiales
│   │       └── RCAs de Rechazo
│   │
│   └── 📁 6.3 Ejemplos de ICSARA
│       │
│       │   Para entender qué observaciones son típicas
│       │
│       └── ICSARAs de proyectos por sector
│
│
└── 📁 7. RECURSOS ADICIONALES
    │
    ├── 📁 7.1 Normas de Calidad Ambiental
    │   │
    │   ├── Normas primarias (protección salud)
    │   ├── Normas secundarias (protección recursos)
    │   └── Valores de referencia (cuando no hay norma)
    │
    ├── 📁 7.2 Estadísticas SEIA
    │   │
    │   └── Reportes estadísticos mensuales del SEA
    │
    └── 📁 7.3 Publicaciones Técnicas
        │
        └── Revista técnica del SEA
```

### 2.2 Metadatos por Tipo de Documento

Cada tipo de documento requiere metadatos específicos para ser útil en búsquedas:

#### Documentos de Normativa Legal

```yaml
documento_legal:
  # Identificación
  tipo: "Ley" | "Reglamento" | "Decreto" | "Resolución"
  numero: "19.300"
  titulo: "Bases Generales del Medio Ambiente"

  # Temporalidad
  fecha_publicacion: "1994-03-09"
  fecha_vigencia: "1994-03-09"
  fecha_ultima_modificacion: "2023-06-15"
  estado: "vigente" | "modificado" | "derogado"

  # Emisor
  organismo: "Congreso Nacional" | "Ministerio del Medio Ambiente" | ...

  # Contenido
  articulos_clave: ["10", "11", "12"]
  materias: ["SEIA", "evaluación ambiental", "tipologías"]

  # Trazabilidad
  url_bcn: "https://bcn.cl/..."  # Biblioteca del Congreso
  url_diario_oficial: "https://..."
  archivo_original_hash: "sha256:..."
```

#### Guías SEA

```yaml
guia_sea:
  # Identificación
  tipo: "Guía de Descripción" | "Guía Art. 11" | "Guía PAS" | ...
  categoria: "Descripción de Proyectos"
  subcategoria: "Por Sector"
  titulo: "Minería de Cobre y Metales Preciosos"
  edicion: 1

  # Temporalidad
  fecha_publicacion: "2017-05-15"
  resolucion_aprobatoria: "Exenta N° 201799101234"
  estado: "vigente" | "no vigente"
  reemplaza_a: null | "guia_id_anterior"

  # Aplicabilidad
  sectores: ["Minería"]
  tipologias_art3: ["i.1", "i.2", "i.3", "i.4"]
  componentes_ambientales: ["agua", "aire", "suelo", "fauna"]
  triggers_art11: ["a", "b", "d", "e"]

  # Trazabilidad
  url_sea: "https://sea.gob.cl/..."
  archivo_original_hash: "sha256:..."
```

#### Instructivos SEA

```yaml
instructivo_sea:
  # Identificación
  tipo: "Ordinario" | "Memorandum" | "Resolución Exenta"
  numero: "202599102506"
  titulo: "Documentación de respaldo de actividades de PAC"

  # Temporalidad
  fecha: "2025-06-06"
  estado: "vigente" | "modificado" | "derogado"

  # Temática
  categoria: "Participación Ciudadana"
  materias: ["PAC", "documentación", "respaldo"]

  # Aplicabilidad
  aplica_a: ["DIA", "EIA"]
  etapa_proceso: "evaluación"

  # Trazabilidad
  url_sea: "https://sea.gob.cl/..."
  archivo_original_hash: "sha256:..."
```

#### Criterios de Evaluación

```yaml
criterio_evaluacion:
  # Identificación
  titulo: "Metodologías para Impactos Acumulativos y Sinérgicos"
  resolucion: "Exenta N° 202499101937"

  # Temporalidad
  fecha_publicacion: "2024-11-25"
  estado: "vigente"

  # Temática
  categoria: "Impactos Especiales"
  componente_ambiental: ["múltiple"]

  # Aplicabilidad
  sectores: ["todos"]
  triggers_art11: ["a", "b", "c", "d", "e", "f"]

  # Técnico
  requiere_especialista: true
  nivel_complejidad: "alto"

  # Trazabilidad
  url_sea: "https://sea.gob.cl/..."
  archivo_original_hash: "sha256:..."
```

### 2.3 Relaciones entre Documentos

Los documentos del corpus tienen relaciones importantes que el sistema debe modelar:

```
┌─────────────────────────────────────────────────────────────────┐
│                    RELACIONES DOCUMENTALES                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Ley 19.300 ──────────────────┐                                 │
│      │                        │                                  │
│      │ reglamenta             │ desarrolla                       │
│      ▼                        ▼                                  │
│  DS 40/2012 ◄────────────── Guías SEA                           │
│      │                        │                                  │
│      │ interpreta             │ aplica                           │
│      ▼                        ▼                                  │
│  Instructivos ◄───────────► Criterios de Evaluación             │
│      │                        │                                  │
│      │                        │                                  │
│      └────────────┬───────────┘                                  │
│                   │                                              │
│                   │ fundamenta                                   │
│                   ▼                                              │
│              Jurisprudencia                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Tipos de relaciones:
- reglamenta: Norma inferior desarrolla norma superior
- interpreta: Documento aclara cómo aplicar norma
- reemplaza: Documento nuevo deja sin efecto anterior
- complementa: Documento agrega información a otro
- cita: Documento referencia a otro
- aplica_en: Documento se usa en etapa específica del proceso
```

---

## Parte 3: Priorización de Ingestión

### 3.1 Documentos Críticos (Fase 1)

Documentos que el sistema DEBE tener para funcionar:

| Prioridad | Documento | Razón |
|-----------|-----------|-------|
| 1 | Ley 19.300 completa | Base legal de todo el sistema |
| 2 | DS 40/2012 completo | Detalla todos los procedimientos |
| 3 | Guías Art. 11 (todas las letras) | Motor de reglas DIA/EIA |
| 4 | Guía Descripción Minería | Sector objetivo del sistema |
| 5 | Instructivos Áreas Protegidas | Trigger más común en minería |
| 6 | Criterios Recurso Hídrico | Componente crítico para minería |

### 3.2 Documentos Importantes (Fase 2)

Mejoran significativamente la calidad de respuestas:

- Todas las Guías de Descripción de Proyecto por sector
- Criterios de Evaluación de componentes ambientales
- Instructivos de Consulta Indígena
- Guías de Participación Ciudadana
- Criterios de Patrimonio

### 3.3 Documentos Complementarios (Fase 3)

Agregan profundidad y casos específicos:

- Jurisprudencia relevante
- Ejemplos de RCA por sector
- Normas de calidad ambiental
- Estadísticas SEIA

---

## Siguiente Documento

El **Documento 3** detalla la arquitectura técnica: modelo de datos, endpoints API, sistema de storage, y flujo de ingestión.
