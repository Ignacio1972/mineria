# Mejoras Pendientes - Sistema de Prefactibilidad Ambiental Minera

**Fecha:** 2025-12-27
**Estado:** Pendiente de implementación
**Prioridad:** Alta

---

## Resumen

Este documento lista las mejoras críticas identificadas en revisión de código que **aún no han sido implementadas**. Se requiere completar estos items antes de pasar a producción.

---

## 1. Backend - Base de Datos

### 1.1 Tabla de Auditoría (OBLIGATORIA)

Para cumplimiento regulatorio SEIA, se debe rastrear exactamente qué datos se usaron en cada análisis:

```sql
-- Archivo: docker/postgis/init/04_auditoria.sql

CREATE TABLE proyectos.auditoria_analisis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analisis_id UUID NOT NULL REFERENCES proyectos.analisis(id) ON DELETE CASCADE,
    capa_gis_usada VARCHAR(100) NOT NULL,  -- 'snaspe', 'glaciares_dga', etc.
    version_capa DATE NOT NULL,             -- Fecha de la capa usada
    documentos_referenciados UUID[],        -- Array de documento_id usados
    normativa_citada JSONB NOT NULL,        -- [{"ley": "19.300", "articulo": "11", "literal": "b"}]
    fragmentos_rag_ids UUID[],              -- IDs de fragmentos RAG citados
    usuario_responsable TEXT,               -- Para firma digital futura
    hash_entrada TEXT,                      -- Hash de datos de entrada (reproducibilidad)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_auditoria_analisis ON proyectos.auditoria_analisis(analisis_id);
CREATE INDEX idx_auditoria_fecha ON proyectos.auditoria_analisis USING BRIN(created_at);

COMMENT ON TABLE proyectos.auditoria_analisis IS
'Registro de auditoría para trazabilidad regulatoria de análisis SEIA';
```

### 1.2 Índices Espaciales y Temporales

```sql
-- Archivo: docker/postgis/init/05_indices.sql

-- Índice espacial para consultas GIS
CREATE INDEX IF NOT EXISTS idx_proyectos_geom
ON proyectos.proyectos USING GIST(geom);

-- Índice BRIN para consultas por fecha (eficiente en tablas grandes)
CREATE INDEX IF NOT EXISTS idx_analisis_fecha
ON proyectos.analisis USING BRIN(created_at);

CREATE INDEX IF NOT EXISTS idx_documentos_fecha
ON proyectos.documentos USING BRIN(created_at);
```

### 1.3 Trigger Automático de Estados

```sql
-- Archivo: docker/postgis/init/06_triggers.sql

CREATE OR REPLACE FUNCTION proyectos.update_estado_proyecto()
RETURNS TRIGGER AS $$
BEGIN
    -- Si se agrega geometría y estaba en 'completo', pasar a 'con_geometria'
    IF NEW.geom IS NOT NULL
       AND OLD.geom IS NULL
       AND OLD.estado = 'completo' THEN
        NEW.estado := 'con_geometria';
    END IF;

    -- Actualizar updated_at
    NEW.updated_at := NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_proyecto_estado
    BEFORE UPDATE ON proyectos.proyectos
    FOR EACH ROW
    EXECUTE FUNCTION proyectos.update_estado_proyecto();

COMMENT ON FUNCTION proyectos.update_estado_proyecto IS
'Actualiza automáticamente el estado del proyecto según cambios en geometría';
```

---

## 2. Backend - Endpoint de Análisis Integrado

El análisis debe orquestar GIS + RAG + LLM en un solo flujo:

```python
# Archivo: backend/app/api/v1/endpoints/prefactibilidad.py

from typing import Literal
from uuid import UUID

@router.post("/analisis-integrado")
async def analisis_integrado(
    proyecto_id: UUID,
    tipo: Literal["rapido", "completo"],
    db: AsyncSession = Depends(get_db)
):
    """
    Ejecuta análisis completo: GIS → RAG → LLM → Auditoría

    - rapido: Solo GIS + reglas, sin LLM
    - completo: GIS + RAG + LLM con generación de informe
    """
    # 1. Obtener proyecto con geometría
    proyecto = await get_proyecto_con_geometria(db, proyecto_id)
    if not proyecto.geom:
        raise HTTPException(400, "Proyecto sin geometría definida")

    # 2. Análisis GIS (cruces espaciales)
    gis_result = await analisis_espacial_service.analizar(proyecto.geom)

    # 3. Evaluar triggers Art. 11
    triggers = await evaluar_triggers_art11(proyecto, gis_result)

    # 4. Clasificación DIA/EIA
    clasificacion = await motor_reglas_seia.clasificar(triggers)

    # 5. Registrar auditoría GIS
    auditoria_gis = await registrar_auditoria_gis(
        analisis_id=...,
        capas_usadas=gis_result.capas_consultadas,
        versiones=gis_result.versiones_capas
    )

    if tipo == "rapido":
        return {
            "gis": gis_result,
            "triggers": triggers,
            "clasificacion": clasificacion,
            "auditoria_id": auditoria_gis.id
        }

    # 6. Búsqueda RAG de normativa relevante
    normativa = await rag_service.buscar_por_triggers(triggers)

    # 7. Generar informe con LLM
    contexto_llm = {
        "proyecto": proyecto.dict(),
        "gis": gis_result.dict(),
        "triggers": triggers,
        "clasificacion": clasificacion,
        "normativa": normativa
    }

    informe = await llm_service.generar_informe(contexto_llm)

    # 8. Registrar auditoría completa
    auditoria = await registrar_auditoria_completa(
        analisis_id=...,
        capas=gis_result.capas_consultadas,
        fragmentos_rag=[n.id for n in normativa],
        normativa_citada=informe.normativa_citada
    )

    return {
        "gis": gis_result,
        "triggers": triggers,
        "clasificacion": clasificacion,
        "normativa": normativa,
        "informe": informe,
        "auditoria_id": auditoria.id
    }
```

---

## 3. Backend - Schema de Auditoría

```python
# Archivo: backend/app/schemas/auditoria.py

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional

class NormativaCitada(BaseModel):
    ley: str              # "19.300"
    articulo: str         # "11"
    literal: Optional[str] # "b"
    descripcion: str      # "Efectos adversos sobre recursos naturales"

class AuditoriaAnalisisCreate(BaseModel):
    analisis_id: UUID
    capa_gis_usada: str
    version_capa: date
    documentos_referenciados: list[UUID] = []
    normativa_citada: list[NormativaCitada]
    fragmentos_rag_ids: list[UUID] = []
    usuario_responsable: Optional[str] = None
    hash_entrada: Optional[str] = None

class AuditoriaAnalisis(AuditoriaAnalisisCreate):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
```

---

## 4. Frontend - Visualización de Auditoría

### 4.1 Componente de Trazabilidad

```vue
<!-- Archivo: frontend/src/components/analysis/AuditoriaTrazabilidad.vue -->

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = defineProps<{
  analisisId: string
}>()

const auditoria = ref<AuditoriaItem[]>([])
const cargando = ref(true)

interface AuditoriaItem {
  id: string
  capa_gis_usada: string
  version_capa: string
  normativa_citada: { ley: string; articulo: string; literal?: string }[]
  created_at: string
}

onMounted(async () => {
  // Cargar datos de auditoría
  auditoria.value = await analisisService.obtenerAuditoria(props.analisisId)
  cargando.value = false
})
</script>

<template>
  <div class="card bg-base-100 shadow-sm">
    <div class="card-body">
      <h3 class="card-title text-sm">Trazabilidad del Análisis</h3>

      <div v-if="cargando" class="flex justify-center py-4">
        <span class="loading loading-spinner"></span>
      </div>

      <div v-else class="space-y-3">
        <!-- Capas GIS usadas -->
        <div>
          <p class="text-xs font-semibold opacity-60 mb-1">Capas GIS consultadas:</p>
          <div class="flex flex-wrap gap-1">
            <span
              v-for="item in auditoria"
              :key="item.id"
              class="badge badge-outline badge-sm"
            >
              {{ item.capa_gis_usada }} ({{ item.version_capa }})
            </span>
          </div>
        </div>

        <!-- Normativa citada -->
        <div>
          <p class="text-xs font-semibold opacity-60 mb-1">Normativa aplicada:</p>
          <ul class="text-xs space-y-1">
            <li v-for="(item, idx) in auditoria[0]?.normativa_citada" :key="idx">
              Ley {{ item.ley }}, Art. {{ item.articulo }}
              <span v-if="item.literal"> letra {{ item.literal }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
```

### 4.2 Integrar en Vista de Análisis

En `ProyectoDetalleView.vue`, agregar el componente de auditoría cuando hay análisis:

```vue
<!-- Dentro del tab de Análisis -->
<AuditoriaTrazabilidad
  v-if="proyecto.ultimo_analisis"
  :analisis-id="proyecto.ultimo_analisis"
/>
```

---

## 5. Checklist de Implementación

### Backend
- [ ] Crear migración SQL para tabla `auditoria_analisis`
- [ ] Crear índices GIST y BRIN
- [ ] Implementar trigger de estados automáticos
- [ ] Crear schema Pydantic `AuditoriaAnalisis`
- [ ] Crear modelo SQLAlchemy `AuditoriaAnalisis`
- [ ] Implementar endpoint `/analisis-integrado`
- [ ] Agregar registro de auditoría en flujo de análisis
- [ ] Endpoint GET `/analisis/{id}/auditoria`

### Frontend
- [ ] Crear tipo `AuditoriaAnalisis` en types
- [ ] Crear servicio `auditoriaService`
- [ ] Crear componente `AuditoriaTrazabilidad.vue`
- [ ] Integrar en vista de análisis
- [ ] Mostrar badge de "Auditable" en análisis completados

---

## 6. Consideraciones de Seguridad

1. **Hash de entrada**: Guardar hash SHA-256 de los datos de entrada para garantizar reproducibilidad.

2. **Usuario responsable**: Campo preparado para futura integración con firma electrónica avanzada (FEA) según Ley 19.799.

3. **Inmutabilidad**: La tabla de auditoría NO debe permitir UPDATE ni DELETE en producción.

```sql
-- Revocar permisos de modificación en producción
REVOKE UPDATE, DELETE ON proyectos.auditoria_analisis FROM app_user;
```

---

## 7. Testing Requerido

```python
# tests/test_auditoria.py

async def test_analisis_genera_auditoria():
    """Verificar que cada análisis genera registro de auditoría"""
    resultado = await analisis_integrado(proyecto_id, "completo")

    assert resultado.auditoria_id is not None

    auditoria = await get_auditoria(resultado.auditoria_id)
    assert len(auditoria.capas_gis) > 0
    assert len(auditoria.normativa_citada) > 0

async def test_auditoria_inmutable():
    """Verificar que auditoría no se puede modificar"""
    with pytest.raises(IntegrityError):
        await update_auditoria(auditoria_id, {"capa": "modificada"})
```

---

## Resumen de Prioridades

| Item | Área | Prioridad | Esfuerzo |
|------|------|-----------|----------|
| Tabla auditoria_analisis | Backend/DB | **CRÍTICA** | 2h |
| Índices GIST/BRIN | Backend/DB | Alta | 30min |
| Trigger estados | Backend/DB | Media | 1h |
| Endpoint integrado | Backend/API | Alta | 4h |
| Componente trazabilidad | Frontend | Media | 2h |

**Total estimado: ~10 horas de desarrollo**
