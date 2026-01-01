# Pendientes Fase 4 - Frontend

> **Actualizado:** 2025-12-26

## Estado de Pendientes Adicionales

| Tarea | Estado |
|-------|--------|
| Vue Router | COMPLETADO |
| Tests E2E (Playwright) | COMPLETADO |
| Test MapContainer (mocks OpenLayers) | COMPLETADO |
| Coverage tool (@vitest/coverage-v8) | COMPLETADO |

---

## 1. Integración de Capas GIS con GeoServer

**Archivo:** `frontend/src/stores/map.ts`

```typescript
// Agregar función para cargar capas desde la API
async function cargarCapasDesdeAPI() {
  const response = await api.get('/api/v1/gis/capas');
  capas.value = response.data.map(capa => ({
    id: capa.nombre,
    nombre: capa.nombre_display,
    visible: false,
    opacidad: 0.7,
    categoria: capa.categoria,
    url: `${GEOSERVER_URL}/wms?service=WMS&layers=${capa.nombre}`
  }));
}
```

**Archivo:** `frontend/src/components/map/MapContainer.vue`
- Agregar capas WMS de GeoServer usando `ol/source/TileWMS`

---

## 2. Tests de Componentes

**Instalar:**
```bash
npm install -D vitest @vue/test-utils jsdom
```

**Crear:** `frontend/tests/components/ProjectForm.spec.ts`
```typescript
import { mount } from '@vue/test-utils';
import ProjectForm from '@/components/project/ProjectForm.vue';

describe('ProjectForm', () => {
  it('actualiza el nombre del proyecto', async () => {
    const wrapper = mount(ProjectForm);
    await wrapper.find('input[placeholder*="Nombre"]').setValue('Test');
    // verificar store actualizado
  });
});
```

---

## 3. Carpeta Utils

**Crear:** `frontend/src/utils/format.ts`
```typescript
export function formatearFecha(fecha: string): string {
  return new Date(fecha).toLocaleDateString('es-CL');
}

export function formatearNumero(num: number): string {
  return num.toLocaleString('es-CL');
}
```

**Crear:** `frontend/src/utils/validation.ts`
```typescript
export function validarProyecto(datos: DatosProyecto): string[] {
  const errores: string[] = [];
  if (!datos.nombre || datos.nombre.length < 3) {
    errores.push('Nombre debe tener al menos 3 caracteres');
  }
  return errores;
}
```

---

## 4. Campos Dependientes Región/Comuna

**Archivo:** `frontend/src/types/project.ts`
```typescript
export const COMUNAS_POR_REGION: Record<string, string[]> = {
  'Antofagasta': ['Antofagasta', 'Mejillones', 'Calama', ...],
  'Atacama': ['Copiapó', 'Caldera', 'Tierra Amarilla', ...],
  // ...
};
```

**Archivo:** `frontend/src/components/project/ProjectForm.vue`
- Filtrar comunas según región seleccionada

---

## 5. Tooltips en Mapa

**Archivo:** `frontend/src/components/map/MapContainer.vue`
```typescript
// Agregar overlay para tooltip
const tooltip = new Overlay({ element: tooltipEl });
map.addOverlay(tooltip);

map.on('pointermove', (evt) => {
  const feature = map.forEachFeatureAtPixel(evt.pixel, f => f);
  if (feature) {
    tooltip.setPosition(evt.coordinate);
    tooltipEl.innerHTML = feature.get('nombre');
  }
});
```

---

## Prioridad de Implementación

| # | Tarea | Esfuerzo | Impacto |
|---|-------|----------|---------|
| 1 | Capas GIS GeoServer | Alto | Alto |
| 2 | Región/Comuna dependientes | Bajo | Medio |
| 3 | Utils (format/validation) | Bajo | Medio |
| 4 | Tooltips mapa | Medio | Bajo |
| 5 | Tests | Alto | Medio |
