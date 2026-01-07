# Plan: Auto-llenado de Proyectos mediante Asistente IA

**Fecha:** 2026-01-03
**Versión:** 1.0
**Estado:** Planificación

---

## 1. Objetivo General

Transformar el flujo de creación de proyectos para que:

1. **Los proyectos se creen con información mínima** (nombre + polígono opcional)
2. **El asistente por proyecto recopile información mediante conversación** y determine el tipo de proyecto (minero, inmobiliario, energético, etc.)
3. **Se auto-completen ~10 campos clave del proyecto** desde las respuestas del asistente
4. **El resto de información vaya a la ficha acumulativa** estructurada
5. **Se genere automáticamente una descripción geográfica** al ingresar el polígono en el mapa

---

## 2. Contexto Arquitectónico

### 2.1. Sistemas de Asistente

El sistema cuenta con **DOS asistentes diferentes**:

| Asistente | Schema | Tabla Principal | Uso |
|-----------|--------|-----------------|-----|
| **Global** | `asistente` | `conversaciones` | Chat general, consultas |
| **Por Proyecto** | `proyectos` | `proyecto_conversaciones` | Flujo evaluación EIA, recopilación datos |

**Este plan usa el ASISTENTE POR PROYECTO** (`proyectos.proyecto_conversaciones`)

### 2.2. Modelos Existentes Relevantes

#### Modelo `Proyecto` (proyectos.proyectos)
```python
# Soporte multi-industria (YA EXISTE)
tipo_proyecto_id          # FK a tipos_proyecto (minería, inmobiliario, etc.)
subtipo_proyecto_id       # FK a subtipos_proyecto

# Campos específicos actuales (minería)
tipo_mineria             # Cielo abierto / Subterránea
mineral_principal        # Cobre, Litio, Oro, etc.
fase                     # Exploración, Explotación, Cierre
titular                  # Empresa responsable

# Ubicación (auto-calculado desde geometría)
region                   # Calculado por trigger PostGIS
comuna                   # Calculado por trigger PostGIS
superficie_ha            # Calculada desde geometría

# Recursos y dimensiones
vida_util_anos
inversion_musd
trabajadores_construccion
trabajadores_operacion
uso_agua_lps
fuente_agua
energia_mw

# Descripción
descripcion              # Texto libre
```

#### Modelo `ProyectoCaracteristica` (proyectos.proyecto_caracteristicas)
Ficha acumulativa estructurada:
```python
categoria                # 'identificacion', 'tecnico', 'obras', 'ambiental', etc.
clave                    # Nombre del atributo
valor                    # Valor en texto
valor_numerico           # Valor numérico (si aplica)
unidad                   # Unidad de medida

# Trazabilidad
fuente                   # 'manual' | 'asistente' | 'documento' | 'gis'
pregunta_codigo          # Código de la pregunta que generó este dato
documento_id             # FK si viene de un documento

# Validación
validado                 # Boolean
validado_por
validado_fecha
```

#### Modelo `ProyectoConversacion` (proyectos.proyecto_conversaciones)
Conversación del asistente por proyecto:
```python
estado                   # 'activa' | 'pausada' | 'completada' | 'archivada'
fase                     # 'prefactibilidad' | 'estructuracion' | 'recopilacion' | 'generacion'
progreso_porcentaje
ultima_pregunta_codigo   # Tracking del flujo
resumen_actual           # Resumen acumulativo
tokens_acumulados
```

---

## 3. Campos Auto-Rellenables

### 3.1. Campos del Proyecto (10 campos clave)

Estos campos del modelo `Proyecto` se llenarán automáticamente desde el asistente:

| # | Campo | Tipo | Descripción | Aplica a |
|---|-------|------|-------------|----------|
| 1 | `tipo_proyecto_id` | FK | Tipo: Minería, Inmobiliario, Energía, Industrial, etc. | Todos |
| 2 | `subtipo_proyecto_id` | FK | Subtipo específico según industria | Todos |
| 3 | `titular` | String | Empresa o persona responsable | Todos |
| 4 | `region` | String | **Auto-calculado desde geometría** | Todos |
| 5 | `comuna` | String | **Auto-calculado desde geometría** | Todos |
| 6 | `fase` | String | Fase del proyecto (varía según tipo) | Todos |
| 7 | `superficie_ha` | Numeric | Hectáreas del proyecto | Todos |
| 8 | `vida_util_anos` | Integer | Años de operación estimados | Todos |
| 9 | `inversion_musd` | Numeric | Inversión en millones USD | Todos |
| 10 | `trabajadores_operacion` | Integer | Personal durante operación | Todos |

**Campos específicos de minería** (se llenan SOLO si `tipo_proyecto_id` = Minería):
- `tipo_mineria`: Cielo abierto / Subterránea / Mixta
- `mineral_principal`: Cobre, Litio, Oro, etc.

### 3.2. Datos que van a Ficha Acumulativa

Todo lo demás se almacena en `proyecto_caracteristicas`:

**Categoría: Técnico**
- Método de extracción
- Capacidad de producción
- Tecnologías utilizadas
- Procesos industriales

**Categoría: Recursos**
- Uso de agua (L/s)
- Fuente de agua
- Energía (MW)
- Fuente de energía

**Categoría: Obras**
- Descripción de instalaciones
- Caminos de acceso
- Construcciones principales
- Infraestructura auxiliar

**Categoría: Personal**
- Trabajadores en construcción
- Distribución por especialidad
- Campamentos

**Categoría: Ambiental**
- Emisiones estimadas
- Residuos generados
- Medidas de mitigación previstas

---

## 4. Descripción Geográfica Automática

### 4.1. Objetivo
Al dibujar/importar un polígono en el mapa, generar automáticamente una descripción narrativa del lugar geográfico.

### 4.2. Datos de Entrada (ya disponibles vía GIS)

Análisis espacial automático:
- Región, provincia, comuna
- Altitud media (desde DEM si está disponible)
- Distancia a áreas protegidas
- Distancia a comunidades indígenas
- Distancia a centros poblados
- Afectación a glaciares
- Cuencas hidrográficas
- Tipo de clima (si hay capa disponible)

### 4.3. Generación de Descripción

**Proceso:**
1. Usuario dibuja/importa polígono
2. Trigger actualiza `region`, `comuna`, distancias (ya existe)
3. Backend ejecuta servicio de descripción geográfica:
   - Recopila datos GIS
   - Envía a LLM (Claude) con prompt especializado
   - LLM genera descripción narrativa (150-300 palabras)
4. Se almacena en nuevo campo `descripcion_geografica`

**Ejemplo de salida:**
```
El proyecto se ubica en la Región de Antofagasta, comuna de Calama,
en la zona altiplánica del norte de Chile. El área del proyecto abarca
aproximadamente 450 hectáreas a una altitud promedio de 3,200 msnm,
en un entorno árido de alta montaña.

La ubicación se encuentra a 45 km al noreste de la ciudad de Calama,
en una zona caracterizada por salares y pampas desérticas. El área
protegida más cercana es la Reserva Nacional Los Flamencos, ubicada
a 12 km al sur del proyecto.

No se identifican comunidades indígenas en un radio de 5 km, siendo
la más cercana la comunidad de Caspana a 18 km. El proyecto se
emplaza en la cuenca del río Loa, aunque no intercepta directamente
cursos de agua superficiales.
```

### 4.4. Cambios en el Modelo

```python
# Agregar a modelo Proyecto:
descripcion_geografica = Column(Text, nullable=True)
descripcion_geografica_fecha = Column(DateTime, nullable=True)
descripcion_geografica_fuente = Column(String(20), default='auto')  # 'auto' | 'manual'
```

---

## 5. Fases de Implementación

### FASE 1: Descripción Geográfica Automática
**Prioridad:** Alta
**Complejidad:** Media
**Tiempo estimado:** Inmediato

**Tareas:**
- [ ] Agregar campos `descripcion_geografica` al modelo `Proyecto`
- [ ] Crear migración de base de datos
- [ ] Implementar servicio `generar_descripcion_geografica(proyecto_id)`
- [ ] Crear endpoint `POST /api/v1/proyectos/{id}/generar-descripcion-geografica`
- [ ] Actualizar frontend: mostrar descripción en tab "Ubicación"
- [ ] Agregar botón "Regenerar descripción" (si el usuario quiere actualizarla)
- [ ] Testing

**Criterios de éxito:**
- Al guardar geometría, se genera descripción automáticamente
- Descripción es coherente y útil
- Usuario puede regenerarla manualmente
- Se muestra en la interfaz de forma clara

---

### FASE 2: Auto-llenado por Asistente (Identificación del Proyecto)
**Prioridad:** Alta
**Complejidad:** Alta
**Tiempo estimado:** A definir

#### 2.1. Backend

**Tareas:**
- [ ] Crear endpoint `PUT /api/v1/proyectos/{id}/campos-asistente`
  - Permite al asistente actualizar campos específicos del proyecto
  - Valida que solo actualice campos permitidos
  - Registra en `ProyectoCaracteristica` con `fuente='asistente'`

- [ ] Modificar servicio del asistente por proyecto:
  - Agregar fase inicial "identificacion" antes de "prefactibilidad"
  - Definir flujo de preguntas de identificación
  - Implementar lógica de extracción de información desde respuestas
  - Mapear respuestas a campos del proyecto

- [ ] Crear sistema de preguntas dinámico:
  - Preguntas base para todos los proyectos
  - Preguntas específicas según tipo de proyecto detectado
  - Tree de decisión para optimizar cantidad de preguntas

**Endpoints nuevos:**
```python
PUT  /api/v1/proyectos/{id}/campos-asistente
GET  /api/v1/proyectos/{id}/campos-origen       # Muestra origen de cada campo
POST /api/v1/asistente/proyecto/{id}/iniciar    # Inicia conversación de identificación
```

#### 2.2. Frontend

**Tareas:**
- [ ] Modificar formulario de creación de proyectos:
  - Reducir a campos mínimos (nombre, cliente opcional)
  - Agregar opción "Completar con asistente" o "Completar manualmente"

- [ ] Actualizar `ProyectoFormulario.vue`:
  - Mostrar badge indicando origen de datos (Manual / Asistente / GIS)
  - Campos llenados por asistente en modo read-only con opción "Editar"
  - Visual diferenciado para campos auto-completados

- [ ] Flujo en `ProyectoDetalleView.vue`:
  - Si proyecto tiene campos vacíos, mostrar banner "Completa el proyecto con el asistente"
  - Al hacer clic, abrir tab "Asistente" automáticamente
  - Progreso visual de completado

**Mockup de UI:**
```
┌─────────────────────────────────────────┐
│ Tipo de Proyecto           [Asistente] │
│ Minería                                  │
│                                    [✏️] │
├─────────────────────────────────────────┤
│ Mineral Principal          [Asistente] │
│ Litio                                    │
│                                    [✏️] │
├─────────────────────────────────────────┤
│ Región                            [GIS] │
│ Antofagasta                              │
│                              (calculado) │
└─────────────────────────────────────────┘
```

#### 2.3. Flujo de Preguntas del Asistente

**Secuencia:**

1. **Pregunta inicial:**
   ```
   Asistente: "¡Hola! Voy a ayudarte a configurar el proyecto.
   ¿Qué tipo de proyecto deseas evaluar?"

   Opciones:
   - Minería
   - Inmobiliario / Urbanístico
   - Energía (solar, eólica, etc.)
   - Industrial
   - Infraestructura (carreteras, puertos, etc.)
   - Acuícola / Pesquero
   - Otro
   ```

2. **Preguntas específicas según tipo:**

   **Si es Minería:**
   ```
   - ¿Qué mineral se va a explotar? (Cobre, Litio, Oro, etc.)
   - ¿Qué tipo de minería? (Cielo abierto, Subterránea, Mixta)
   - ¿En qué fase se encuentra? (Exploración, Explotación, Cierre)
   - ¿Cuál es la empresa o titular del proyecto?
   - ¿Cuál es la superficie aproximada en hectáreas?
   - ¿Vida útil estimada del proyecto en años?
   - ¿Inversión estimada en millones de USD?
   - ¿Cuántos trabajadores tendrá durante operación?
   ```

   **Si es Inmobiliario:**
   ```
   - ¿Qué tipo de proyecto inmobiliario? (Edificios, Loteo, Conjunto habitacional, etc.)
   - ¿Cuántas unidades se construirán?
   - ¿Superficie total del terreno en hectáreas?
   - ¿Empresa o titular responsable?
   - ¿Inversión estimada?
   - etc.
   ```

3. **Extracción de información:**
   - El asistente procesa las respuestas con LLM
   - Extrae valores estructurados
   - Actualiza campos del proyecto vía API

4. **Confirmación:**
   ```
   Asistente: "Perfecto, he registrado la siguiente información:

   - Tipo: Proyecto Minero - Litio
   - Método: Minería Subterránea
   - Fase: Explotación
   - Titular: Minera Litio del Norte S.A.
   - Superficie: 450 ha
   - Vida útil: 25 años
   - Inversión: 180 MUSD
   - Trabajadores operación: 120

   ¿Es correcto o necesitas modificar algo?"
   ```

#### 2.4. Sistema de Extracción y Actualización

**Implementación en backend:**

```python
# services/asistente_proyecto_service.py

class AsistenteProyectoService:

    async def procesar_respuesta_identificacion(
        self,
        proyecto_id: int,
        mensaje_usuario: str,
        contexto_pregunta: str
    ) -> dict:
        """
        Procesa respuesta del usuario y extrae información estructurada.
        """
        # 1. Enviar a LLM con prompt de extracción
        prompt = self._construir_prompt_extraccion(
            pregunta=contexto_pregunta,
            respuesta=mensaje_usuario
        )

        # 2. LLM retorna JSON estructurado
        resultado = await self.llm_service.extraer_datos(prompt)

        # 3. Validar y sanitizar
        campos_validados = self._validar_campos(resultado)

        # 4. Actualizar proyecto
        await self._actualizar_campos_proyecto(proyecto_id, campos_validados)

        # 5. Registrar en ficha acumulativa
        await self._registrar_en_ficha(
            proyecto_id=proyecto_id,
            campos=campos_validados,
            fuente='asistente',
            pregunta_codigo=contexto_pregunta
        )

        return {
            'campos_actualizados': campos_validados,
            'siguiente_pregunta': self._siguiente_pregunta(proyecto_id)
        }
```

**Prompt de extracción (ejemplo):**
```python
PROMPT_EXTRACCION = """
Analiza la siguiente conversación y extrae información estructurada.

PREGUNTA DEL ASISTENTE: "{pregunta}"
RESPUESTA DEL USUARIO: "{respuesta}"

Extrae SOLO la información que el usuario proporcionó de forma explícita.
No inventes ni infiera datos que no estén claramente mencionados.

Retorna un JSON con el siguiente formato:
{{
  "tipo_proyecto": "mineria" | "inmobiliario" | "energia" | "industrial" | null,
  "subtipo": "litio" | "cobre" | "edificios" | "solar" | null,
  "titular": "nombre empresa" | null,
  "fase": "exploracion" | "explotacion" | "construccion" | null,
  "superficie_ha": number | null,
  "vida_util_anos": number | null,
  "inversion_musd": number | null,
  "trabajadores_operacion": number | null,
  "confianza": 0.0-1.0,
  "requiere_clarificacion": boolean,
  "pregunta_clarificacion": "texto" | null
}}

Si el usuario no proporcionó un dato, usa null.
Si algo no está claro, marca requiere_clarificacion=true.
"""
```

---

### FASE 3: Refinamiento y Validación
**Prioridad:** Media
**Complejidad:** Media

**Tareas:**
- [ ] Implementar sistema de validación de datos extraídos
- [ ] Permitir al usuario corregir datos auto-completados
- [ ] Historial de cambios (quién modificó qué campo y cuándo)
- [ ] Analytics: % de proyectos completados por asistente vs manual
- [ ] Optimización del flujo de preguntas (reducir cantidad sin perder calidad)
- [ ] A/B testing de diferentes estrategias de preguntas

---

## 6. Consideraciones Técnicas

### 6.1. Seguridad y Validación

- **Validación de permisos:** Solo el asistente del proyecto puede modificar campos
- **Sanitización:** Todos los datos del LLM deben validarse antes de guardar
- **Límites:** No permitir valores fuera de rangos razonables
- **Auditoría:** Registrar todos los cambios automáticos

### 6.2. UX/UI

- **Transparencia:** Usuario siempre sabe qué fue llenado automáticamente
- **Control:** Usuario puede editar/rechazar cualquier campo auto-completado
- **Progreso:** Indicador visual de completitud del proyecto
- **Fallback:** Siempre permitir llenado manual completo

### 6.3. Performance

- **Async:** Generación de descripción geográfica en background
- **Cache:** Cachear análisis GIS para evitar re-cálculos
- **Streaming:** Respuestas del asistente en tiempo real
- **Debouncing:** No regenerar descripción geográfica en cada edición del polígono

### 6.4. Calidad de Datos

- **Confianza:** Almacenar score de confianza de cada extracción
- **Revisión:** Marcar campos que requieren validación humana
- **Feedback loop:** Aprender de correcciones del usuario

---

## 7. Métricas de Éxito

### KPIs
- **% de proyectos con campos auto-completados** (objetivo: >60%)
- **Tiempo promedio de creación de proyecto** (objetivo: reducir 50%)
- **% de campos corregidos manualmente** (objetivo: <15%)
- **Satisfacción del usuario** con descripciones geográficas (objetivo: >4/5)
- **% de usuarios que prefieren asistente vs manual** (objetivo: >70%)

---

## 8. Dependencias y Prerequisitos

### Backend
- ✅ SQLAlchemy async
- ✅ Modelo `Proyecto` con soporte multi-industria
- ✅ Sistema de ficha acumulativa (`ProyectoCaracteristica`)
- ✅ Asistente por proyecto (`ProyectoConversacion`)
- ✅ Análisis GIS automático
- 🔨 Servicio de extracción de datos con LLM
- 🔨 Endpoint de actualización de campos

### Frontend
- ✅ Vue 3 + TypeScript
- ✅ Componente de formulario modular
- ✅ Chat del asistente
- 🔨 UI para campos auto-completados
- 🔨 Indicadores de origen de datos

---

## 9. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| LLM extrae datos incorrectos | Media | Alto | Score de confianza + validación humana |
| Usuario confundido por auto-llenado | Baja | Medio | UI clara con badges y tooltips |
| Descripción geográfica irrelevante | Baja | Bajo | Permitir regenerar/editar manualmente |
| Preguntas del asistente muy largas | Media | Medio | Optimizar flujo, hacer preguntas concisas |
| Tipo de proyecto no soportado | Baja | Medio | Opción "Otro" + llenado manual |

---

## 10. Documentación Adicional Requerida

- [ ] Guía de usuario: Cómo crear proyectos con asistente
- [ ] Documentación técnica: API de auto-llenado
- [ ] Catálogo de preguntas por tipo de proyecto
- [ ] Prompt engineering: Plantillas de extracción
- [ ] Troubleshooting: Qué hacer si el asistente no extrae bien

---

## 11. Próximos Pasos

1. **Validar plan con stakeholders**
2. **Definir exactamente los 10 campos prioritarios**
3. **Decidir: ¿Empezar con Fase 1 o Fase 2?**
4. **Estimar esfuerzo detallado por fase**
5. **Crear tickets/issues en sistema de gestión**

---

## Notas Finales

Este plan es **evolutivo**. Se puede implementar por fases independientes:
- **Fase 1** aporta valor inmediato sin riesgo
- **Fase 2** es el cambio más significativo pero más impactante
- **Fase 3** optimiza basándose en datos reales de uso

La arquitectura actual **ya soporta** la mayoría de estos cambios, lo que reduce significativamente el riesgo técnico.
