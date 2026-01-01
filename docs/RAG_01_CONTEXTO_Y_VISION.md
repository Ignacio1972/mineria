# Documento 1: Contexto y Visión del Sistema de Gestión Documental RAG

## El Problema que Resolvemos

En Chile, determinar si un proyecto minero requiere una **DIA** (Declaración de Impacto Ambiental) o un **EIA** (Estudio de Impacto Ambiental) es un proceso complejo que involucra:

- Cientos de documentos normativos dispersos
- Guías técnicas que se actualizan constantemente
- Criterios de evaluación específicos por componente ambiental
- Jurisprudencia que establece precedentes importantes

Un consultor ambiental puede tardar semanas en recopilar y analizar toda la normativa aplicable a un proyecto específico. **Nuestro sistema automatiza este proceso.**

---

## Qué es el SEIA (en simple)

El **Sistema de Evaluación de Impacto Ambiental** es la puerta de entrada obligatoria para proyectos que pueden afectar el medio ambiente en Chile.

```
Proyecto Minero
      │
      ▼
┌─────────────────────────────────────┐
│  ¿Genera efectos del Art. 11?       │
│  (los "triggers")                   │
│                                     │
│  a) Riesgo para salud población     │
│  b) Efectos en recursos naturales   │
│  c) Reasentamiento de comunidades   │
│  d) Cercanía a áreas protegidas     │
│  e) Alteración de patrimonio        │
│  f) Alteración de paisaje/turismo   │
└─────────────────────────────────────┘
      │
      ├─► SÍ (cualquiera) ──► EIA (120+ días, más complejo)
      │
      └─► NO (ninguno) ────► DIA (60+ días, más simple)
```

**Nuestro sistema predice esta clasificación** analizando la ubicación geográfica del proyecto contra capas GIS sensibles, y fundamenta la recomendación con normativa relevante extraída mediante RAG.

---

## El Rol del Corpus RAG

El corpus RAG es el **cerebro normativo** del sistema. Cuando el análisis GIS detecta que un proyecto está cerca de un glaciar, el sistema RAG debe poder responder:

> "¿Qué dice la normativa chilena sobre proyectos mineros cerca de glaciares?"

Y entregar fragmentos específicos de:
- Ley 19.300, Art. 11 letra b)
- DS 40/2012, criterios de glaciares
- Guías SEA sobre ambiente periglaciar
- Jurisprudencia relevante del Tribunal Ambiental

---

## Por Qué Necesitamos un Sistema de Gestión Documental

### Situación Actual
- 3 documentos base en el corpus (Ley 19.300, DS 40, Guía Minería)
- Ingestión manual mediante scripts
- Sin categorización real
- Sin trazabilidad a fuentes originales

### Situación Objetivo
- **Cientos de documentos** organizados jerárquicamente
- **Upload fácil** con categorización guiada
- **Trazabilidad completa**: del fragmento RAG al PDF original
- **Escalabilidad**: preparado para crecer indefinidamente

---

## Principios de Diseño

### 1. Trazabilidad Total
Cada resultado RAG debe poder rastrearse hasta:
- El documento original (PDF/DOCX)
- La sección específica (Artículo X, Título Y)
- La fecha de vigencia
- La URL oficial de la fuente

### 2. Categorización Inteligente
No basta con "tipo = Ley". Necesitamos saber:
- ¿A qué sector aplica? (Minería, Energía, etc.)
- ¿Qué componente ambiental aborda? (Agua, Aire, Fauna)
- ¿Qué trigger del Art. 11 es relevante?
- ¿En qué etapa del proceso SEIA se usa?

### 3. Crecimiento Orgánico
El corpus crecerá de 3 a 300+ documentos. La arquitectura debe:
- Soportar búsquedas rápidas en millones de fragmentos
- Permitir agregar nuevas categorías sin reestructurar
- Mantener índices vectoriales optimizados

### 4. Fuente de Verdad
Cuando un usuario ve una recomendación del sistema, debe poder:
- Ver el fragmento exacto que la sustenta
- Descargar el documento original
- Verificar la vigencia de la norma

---

## Usuarios del Sistema

| Usuario | Necesidad |
|---------|-----------|
| **Administrador** | Subir documentos, categorizar, mantener corpus actualizado |
| **Consultor** | Obtener normativa relevante para su proyecto |
| **Sistema LLM** | Recibir contexto normativo preciso para generar informes |

---

## Métricas de Éxito

1. **Cobertura**: % de consultas RAG que retornan resultados relevantes
2. **Precisión**: Relevancia de los fragmentos retornados (feedback usuarios)
3. **Trazabilidad**: 100% de fragmentos con fuente verificable
4. **Actualización**: Tiempo desde publicación SEA hasta disponibilidad en sistema

---

## Siguiente Documento

El **Documento 2** detalla la taxonomía completa de documentos del SEA y el flujo del proceso SEIA que el sistema debe modelar.
