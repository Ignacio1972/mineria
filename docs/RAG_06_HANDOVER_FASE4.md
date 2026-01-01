# Handover Fase 4 - Frontend Corpus RAG

**Fecha:** 2025-12-31
**Desarrollador anterior:** Claude (Fase 3 - Integracion Ingestor)
**Desarrollador actual:** Claude (Fase 4 - Frontend Corpus)

---

## Resumen Ejecutivo

Se completo la **Fase 4** del sistema RAG: Frontend Vue para gestion del corpus legal. Se implementaron:

- **Store Pinia** `corpus.ts` con estado reactivo y acciones CRUD
- **Servicio API** `corpus.ts` con funciones para todos los endpoints
- **Tipos TypeScript** completos para el sistema de corpus
- **Componentes Vue**:
  - `CorpusManager.vue` - Panel principal de gestion
  - `CategoriaTree.vue` - Arbol de categorias navegable
  - `TemaSelector.vue` - Selector multiple de temas
  - `FragmentosViewer.vue` - Visor de fragmentos indexados

---

## Estado Actual del Desarrollo

### Completado

| Fase | Estado | Descripcion |
|------|--------|-------------|
| 1. Base de Datos | COMPLETADA | Schema SQL + Modelos SQLAlchemy |
| 2. API Endpoints | COMPLETADA | CRUD categorias, corpus, colecciones, temas |
| 3. Integracion Ingestor | COMPLETADA | Ingestor con LLM + relaciones fragmento-tema |
| 4. Frontend Corpus | **COMPLETADA** | Store Pinia + Componentes Vue |
| 5. Tests | PENDIENTE | Tests unitarios y de integracion |

---

## Archivos Creados en esta Sesion

### Tipos TypeScript

| Archivo | Descripcion |
|---------|-------------|
| `frontend/src/types/corpus.ts` | Tipos para Categoria, Tema, Coleccion, Documento, Fragmento |

### Servicios API

| Archivo | Descripcion |
|---------|-------------|
| `frontend/src/services/corpus.ts` | Funciones API para todos los endpoints del corpus |

### Store Pinia

| Archivo | Descripcion |
|---------|-------------|
| `frontend/src/stores/corpus.ts` | Store con estado, computed y acciones |

### Componentes Vue

| Archivo | Descripcion |
|---------|-------------|
| `frontend/src/components/corpus/CorpusManager.vue` | Panel principal de gestion del corpus |
| `frontend/src/components/corpus/CategoriaTree.vue` | Arbol jerarquico de categorias |
| `frontend/src/components/corpus/TemaSelector.vue` | Selector de temas agrupados |
| `frontend/src/components/corpus/FragmentosViewer.vue` | Visor de fragmentos con filtros |
| `frontend/src/components/corpus/index.ts` | Exports centralizados |

---

## Arquitectura del Frontend

### Store `useCorpusStore`

```typescript
// Estado
- categorias, cargandoCategorias
- temas, cargandoTemas
- colecciones, cargandoColecciones
- documentos, documentoActual, totalDocumentos
- fragmentos, totalFragmentos
- filtrosActivos
- error, procesando

// Computed
- categoriasArbol      // Categorias como arbol jerarquico
- temasAgrupados       // Temas agrupados por tipo
- totalPaginas         // Para paginacion
- paginaActual

// Acciones principales
- inicializar()        // Carga todo al montar
- cargarDocumentos(filtros?)
- seleccionarDocumento(id)
- crearNuevoDocumento(data, archivo?)
- eliminarDocumentoActual()
- reprocesarDocumentoActual()
- aplicarFiltro(filtro)
- irAPagina(pagina)
```

### Servicio `corpus.ts`

```typescript
// Agrupado por namespace
corpusService.categorias.listar()
corpusService.categorias.crear(data)

corpusService.temas.listar(grupo?)
corpusService.colecciones.listar()

corpusService.documentos.listar(filtros?)
corpusService.documentos.crear(data, archivo?, procesar?)
corpusService.documentos.obtener(id)
corpusService.documentos.actualizar(id, data)
corpusService.documentos.eliminar(id)

corpusService.fragmentos.obtener(docId, limite, offset)
corpusService.fragmentos.reprocesar(docId)

corpusService.archivos.descargar(docId, nombre)
corpusService.relaciones.crear(origen, destino, tipo)
```

---

## Como Usar los Componentes

### CorpusManager (componente principal)

```vue
<template>
  <CorpusManager />
</template>

<script setup>
import { CorpusManager } from '@/components/corpus'
</script>
```

El componente es autonomo e incluye:
- Sidebar con arbol de categorias
- Lista de documentos con paginacion
- Vista detalle con tabs (info, fragmentos, relaciones)
- Modal para crear documentos
- Filtros expandibles

### Uso individual de componentes

```vue
<template>
  <!-- Arbol de categorias -->
  <CategoriaTree
    :categorias="store.categoriasArbol"
    :seleccionada="categoriaId"
    @seleccionar="onSelectCategoria"
  />

  <!-- Selector de temas -->
  <TemaSelector
    :temas="store.temas"
    :seleccionados="temasSeleccionados"
    :multiselect="true"
    @update:seleccionados="onUpdateTemas"
  />

  <!-- Visor de fragmentos -->
  <FragmentosViewer
    :fragmentos="store.fragmentos"
    :total="store.totalFragmentos"
    :cargando="store.cargandoFragmentos"
    @cargar-mas="cargarMasFragmentos"
    @reprocesar="reprocesarDoc"
  />
</template>
```

---

## Integracion con el Sistema

### Agregar ruta en Vue Router

```typescript
// router/index.ts
{
  path: '/corpus',
  name: 'corpus',
  component: () => import('@/views/CorpusView.vue')
}
```

### Vista wrapper (ejemplo)

```vue
<!-- views/CorpusView.vue -->
<template>
  <div class="h-screen">
    <CorpusManager />
  </div>
</template>

<script setup>
import { CorpusManager } from '@/components/corpus'
</script>
```

### Agregar al menu de navegacion

```vue
<!-- En AppSidebar.vue -->
<router-link to="/corpus" class="...">
  <DocumentIcon />
  Corpus Legal
</router-link>
```

---

## Comandos de Desarrollo

```bash
# Levantar frontend en modo desarrollo
cd /var/www/mineria/frontend
npm run dev

# Build de produccion
npm run build

# Verificar tipos TypeScript
npm run type-check

# Frontend disponible en
http://localhost:5173
```

---

## Pendiente por Desarrollar

### Alta Prioridad

- [ ] **Tests unitarios** para store y servicios
  - `tests/stores/corpus.spec.ts`
  - `tests/services/corpus.spec.ts`

- [ ] **Integracion con router** - Agregar ruta `/corpus`

- [ ] **Agregar al sidebar** - Link de navegacion

### Media Prioridad

- [ ] **Formulario de edicion de documento** - Modal para actualizar metadatos
- [ ] **Drag & drop para upload** - Mejorar UX de subida de archivos
- [ ] **Busqueda avanzada RAG** - Integrar busqueda semantica en el panel
- [ ] **Preview de PDF** - Ver documento original inline

### Baja Prioridad

- [ ] **Gestion de colecciones** - CRUD de colecciones desde frontend
- [ ] **Gestion de categorias** - Crear/editar categorias
- [ ] **Gestion de temas** - Crear/editar temas
- [ ] **Exportar corpus** - Backup/restore desde UI

---

## Notas Tecnicas

### Arbol de Categorias

El store convierte la lista plana de categorias en un arbol jerarquico usando `categoriasArbol`:

```typescript
// Estructura resultante
[
  {
    id: 1,
    nombre: "Normativa Legal",
    hijos: [
      { id: 10, nombre: "Leyes", hijos: [...] },
      { id: 11, nombre: "Reglamentos", hijos: [...] }
    ]
  },
  ...
]
```

### Filtros Reactivos

Los filtros se aplican de forma reactiva y resetean el offset automaticamente:

```typescript
// Aplicar filtro mantiene los demas filtros activos
store.aplicarFiltro({ categoria_id: 5 })  // Reset offset
store.aplicarFiltro({ tipo: 'Ley' })       // Reset offset
store.aplicarFiltro({ offset: 20 })        // NO reset offset (paginacion)
```

### Carga Lazy de Fragmentos

Los fragmentos se cargan solo cuando se selecciona un documento:

```typescript
async function seleccionarDocumento(id: number) {
  documentoActual.value = await obtenerDocumento(id)
  await cargarFragmentosDocumento()  // Carga automatica
}
```

---

## Checklist para Continuar

1. [x] Leer documentacion previa (RAG_01 a RAG_05)
2. [x] Frontend compila sin errores (`npm run build`)
3. [x] Agregar ruta en `router/index.ts`
4. [x] Agregar link en sidebar
5. [x] Crear vista `CorpusView.vue`
6. [ ] Probar flujo completo: listar, filtrar, ver detalle, crear
7. [ ] Escribir tests si es prioritario

---

## Archivos Modificados para Integracion

| Archivo | Cambio |
|---------|--------|
| `frontend/src/router/index.ts` | Agregada ruta `/corpus` |
| `frontend/src/components/layout/AppSidebar.vue` | Agregado item "Corpus Legal" al menu |
| `frontend/src/views/CorpusView.vue` | Nueva vista wrapper del CorpusManager |

---

*Documento actualizado: 2025-12-31*
