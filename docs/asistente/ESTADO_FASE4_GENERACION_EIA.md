# Estado de Implementación - Fase 4: Generación de EIA

> **Última actualización:** Enero 2026
> **Estado general:** 40% completado - Backend base implementado, faltan exportación, endpoints y frontend

---

## ✅ Completado

### 1. Base de Datos
- ✅ **Migración 007** (`backend/migrations/007_generacion_eia.sql`)
  - 6 tablas creadas y verificadas
  - Datos iniciales: 11 reglas de validación SEA
  - Templates básicos para 6 capítulos de minería

**Tablas implementadas:**
- `proyectos.documentos_eia` - Documentos EIA con versionado
- `proyectos.versiones_eia` - Historial de versiones
- `proyectos.exportaciones_eia` - Registro de exportaciones
- `asistente_config.reglas_validacion_sea` - Reglas de validación
- `asistente_config.templates_capitulos` - Templates por industria
- `proyectos.observaciones_validacion` - Observaciones detectadas

### 2. Modelos SQLAlchemy
- ✅ **backend/app/db/models/generacion_eia.py**
  - 6 modelos con relaciones completas
  - 5 enums para estados y tipos
  - Integrados en `__init__.py`
  - Relación agregada a modelo `Proyecto`

### 3. Schemas Pydantic
- ✅ **backend/app/schemas/generacion_eia.py**
  - 30+ schemas de request/response
  - Validación completa de datos
  - Schemas para generación, validación y exportación

### 4. Servicios Core
- ✅ **GeneradorTextoService** (`backend/app/services/generacion_eia/generador_texto.py`)
  - Integración con Claude Sonnet 4
  - Generación de capítulos con templates Jinja2
  - Mejora y expansión de texto
  - Post-procesamiento automático

- ✅ **ValidadorSEAService** (`backend/app/services/generacion_eia/validador_sea.py`)
  - Validación contra reglas SEA/ICSARA
  - Validaciones de completitud, formato y longitud
  - Generación de observaciones estructuradas
  - Resultados agrupados por severidad

---

## ⏳ Pendiente - Backend (60%)

### 5. ExportadorService **[CRÍTICO]**
**Archivo:** `backend/app/services/generacion_eia/exportador.py`

**Funcionalidades requeridas:**
```python
class ExportadorService:
    async def exportar_pdf(documento_id: int, config: PDFConfig) -> str
    async def exportar_docx(documento_id: int, config: DOCXConfig) -> str
    async def exportar_eseia(documento_id: int, config: ESEIAConfig) -> str
    async def generar_indice() -> str
    async def generar_anexos() -> List[str]
```

**Dependencias necesarias:**
```bash
# Agregar a backend/requirements.txt
weasyprint>=60.0        # PDF generation
python-docx>=1.0.0      # Word generation
lxml>=4.9.0            # XML para e-SEIA
jinja2>=3.1.0          # Templates (ya instalado)
pillow>=10.0.0         # Imágenes (ya instalado)
```

**Tareas:**
- [ ] Crear templates HTML/CSS para PDF
- [ ] Implementar generación DOCX con estilos SEA
- [ ] Implementar exportación XML según esquema e-SEIA 2.0
- [ ] Gestión de archivos exportados (storage)
- [ ] Generación automática de índices y TOC

---

### 6. GeneracionEIAService **[CRÍTICO - Orquestador]**
**Archivo:** `backend/app/services/generacion_eia/service.py`

**Funcionalidades requeridas:**
```python
class GeneracionEIAService:
    async def compilar_documento(proyecto_id: int, request: CompilarDocumentoRequest) -> DocumentoEIA
    async def generar_capitulo(proyecto_id: int, capitulo: int) -> ContenidoCapitulo
    async def regenerar_seccion(proyecto_id: int, request: RegenerarSeccionRequest) -> str
    async def get_documento(proyecto_id: int, version: int = None) -> DocumentoEIA
    async def crear_version(proyecto_id: int, cambios: str) -> VersionEIA
    async def get_progreso_generacion(proyecto_id: int) -> List[ProgresoGeneracion]
```

**Responsabilidades:**
- Orquestar generación de múltiples capítulos
- Gestionar versionado de documentos
- Integrar GeneradorTextoService y ValidadorSEAService
- Calcular estadísticas y progreso
- Manejo de errores y reintentos

**Complejidad:** Alta - ~400 líneas estimadas

---

### 7. Endpoints API **[CRÍTICO]**
**Archivo:** `backend/app/api/v1/endpoints/generacion.py`

**Endpoints requeridos:**
```python
POST   /api/v1/generacion/{proyecto_id}/compilar           # Compilar documento completo
POST   /api/v1/generacion/{proyecto_id}/capitulo/{num}     # Generar capítulo específico
POST   /api/v1/generacion/{proyecto_id}/regenerar          # Regenerar sección
GET    /api/v1/generacion/{proyecto_id}/documento          # Obtener documento actual
POST   /api/v1/generacion/{proyecto_id}/version            # Crear nueva versión
GET    /api/v1/generacion/{proyecto_id}/versiones          # Listar versiones
POST   /api/v1/generacion/{proyecto_id}/validar            # Validar contra SEA
GET    /api/v1/generacion/{proyecto_id}/validaciones       # Obtener validaciones
POST   /api/v1/generacion/{proyecto_id}/exportar/{formato} # Exportar (pdf/docx/eseia)
GET    /api/v1/generacion/{proyecto_id}/exports            # Listar exportaciones
GET    /api/v1/generacion/{proyecto_id}/export/{id}        # Descargar export
GET    /api/v1/generacion/{proyecto_id}/progreso           # Progreso de generación
```

**Tareas:**
- [ ] Crear router en `backend/app/api/v1/router.py`
- [ ] Implementar 11 endpoints
- [ ] Manejo de errores HTTP
- [ ] Documentación OpenAPI
- [ ] Permisos y autenticación

**Estimación:** ~300 líneas

---

### 8. Herramientas del Asistente
**Archivo:** `backend/app/services/asistente/tools/generacion.py`

**Herramientas requeridas:**

**Acciones:**
- `compilar_documento_eia` - Compila documento completo
- `generar_capitulo_eia` - Genera un capítulo específico
- `regenerar_seccion_eia` - Regenera una sección con instrucciones
- `crear_version_documento` - Crea snapshot de versión
- `exportar_documento_eia` - Exporta a formato específico

**Consultas:**
- `consultar_estado_documento` - Estado actual del documento
- `consultar_validaciones_sea` - Observaciones de validación
- `consultar_progreso_generacion` - % completado por capítulo
- `consultar_versiones_documento` - Historial de versiones

**Tareas:**
- [ ] Crear archivo `generacion.py` en tools/acciones/
- [ ] Registrar herramientas en `tools/__init__.py`
- [ ] Actualizar prompts del asistente para usar las herramientas

**Estimación:** ~250 líneas

---

## ⏳ Pendiente - Frontend (100%)

### 9. Tipos TypeScript
**Archivo:** `frontend/src/types/generacionEia.ts`

**Tipos requeridos:**
- `DocumentoEIA`, `VersionEIA`, `ExportacionEIA`
- `ContenidoCapitulo`, `MetadatosDocumento`, `EstadisticasDocumento`
- `ObservacionValidacion`, `ResultadoValidacion`
- `ProgresoGeneracion`, `GeneracionResponse`
- Enums: `EstadoDocumento`, `FormatoExportacion`, `Severidad`

**Estimación:** ~200 líneas

---

### 10. Store Pinia
**Archivo:** `frontend/src/stores/generacionEia.ts`

**Estado y acciones requeridas:**
```typescript
export const useGeneracionStore = defineStore('generacionEia', () => {
  // Estado
  const documento = ref<DocumentoEIA | null>(null)
  const capituloEditando = ref<number | null>(null)
  const validaciones = ref<Validacion[]>([])
  const versiones = ref<VersionEIA[]>([])
  const progreso = ref<ProgresoGeneracion[]>([])
  const loading = ref(false)

  // Acciones
  async function compilarDocumento(proyectoId: number)
  async function generarCapitulo(proyectoId: number, capitulo: number)
  async function guardarCambios()
  async function validarDocumento()
  async function exportar(formato: 'pdf' | 'docx' | 'eseia')
  async function crearVersion(cambios: string)
  async function cargarVersiones()

  return { documento, validaciones, versiones, ... }
})
```

**Estimación:** ~300 líneas

---

### 11. Componentes Vue **[CRÍTICO]**
**Directorio:** `frontend/src/components/generacion/`

#### 11.1 GeneracionEIA.vue (Vista principal)
- Layout principal con navegación de capítulos
- Toolbar con acciones (compilar, validar, exportar)
- Integración de subcomponentes

#### 11.2 EditorCapitulo.vue
- Editor Markdown con preview
- Toolbar de edición
- Guardado automático
- Indicador de palabras/caracteres

#### 11.3 ValidacionesPanel.vue
- Lista de observaciones agrupadas por severidad
- Filtros por capítulo y severidad
- Acciones: marcar como resuelta, ignorar

#### 11.4 VersionesHistorial.vue
- Timeline de versiones
- Comparación entre versiones (diff)
- Restaurar versión anterior

#### 11.5 ExportadorPanel.vue
- Selección de formato (PDF/DOCX/e-SEIA)
- Configuración de exportación
- Preview de configuración
- Descarga de archivos

#### 11.6 ProgresoGeneracion.vue
- Barra de progreso por capítulo
- Estado de generación (pendiente/generando/completado)
- Estadísticas (palabras, figuras, tablas)

**Estimación total:** ~1200 líneas

---

### 12. Router y Navegación
**Archivos a modificar:**
- `frontend/src/router/index.ts`
- `frontend/src/views/ProyectoDetalleView.vue`

**Tareas:**
- [ ] Agregar ruta `/proyectos/:id/generacion`
- [ ] Crear vista `GeneracionView.vue`
- [ ] Agregar tab "Generación EIA" en detalle de proyecto
- [ ] Breadcrumbs y navegación

---

## 📦 Instalación de Dependencias

### Backend
```bash
cd /var/www/mineria/backend
pip install weasyprint python-docx lxml
# o agregar a requirements.txt y ejecutar:
pip install -r requirements.txt
```

### Frontend
No requiere dependencias adicionales (usa librerías ya instaladas).

---

## 🎯 Prioridades de Implementación

### Fase A - Backend funcional (2-3 horas)
1. ✅ ~~Migración + Modelos + Schemas~~ (completado)
2. ✅ ~~GeneradorTextoService~~ (completado)
3. ✅ ~~ValidadorSEAService~~ (completado)
4. **[SIGUIENTE]** ExportadorService básico (solo PDF)
5. GeneracionEIAService (orquestador)
6. Endpoints API (mínimo 5 endpoints core)

### Fase B - Integración con Asistente (1 hora)
7. Herramientas del asistente (5 acciones + 4 consultas)

### Fase C - Frontend (3-4 horas)
8. Tipos TypeScript
9. Store Pinia
10. Componentes Vue (empezar por GeneracionEIA.vue y EditorCapitulo.vue)
11. Router y navegación

---

## 📊 Métricas de Completitud

| Componente | Archivos | Completado | Pendiente | %    |
|------------|----------|------------|-----------|------|
| Base de datos | 1 | 1 | 0 | 100% |
| Modelos | 1 | 1 | 0 | 100% |
| Schemas | 1 | 1 | 0 | 100% |
| Servicios | 4 | 2 | 2 | 50%  |
| Endpoints | 1 | 0 | 1 | 0%   |
| Herramientas | 1 | 0 | 1 | 0%   |
| Frontend Tipos | 1 | 0 | 1 | 0%   |
| Frontend Store | 1 | 0 | 1 | 0%   |
| Frontend Componentes | 6 | 0 | 6 | 0%   |
| Router | 2 | 0 | 2 | 0%   |
| **TOTAL** | **19** | **6** | **13** | **32%** |

---

## 🚀 Comandos para Continuar

### Verificar migración
```bash
docker exec mineria_postgis psql -U mineria -d mineria -c "\d proyectos.documentos_eia"
```

### Instalar dependencias backend
```bash
docker exec mineria_backend pip install weasyprint python-docx lxml
```

### Reiniciar backend
```bash
cd /var/www/mineria/docker && docker compose restart backend
```

### Ver logs
```bash
docker compose logs -f backend
```

---

## 📝 Notas Importantes

1. **Dependencias de exportación:** WeasyPrint requiere librerías del sistema (cairo, pango). Verificar instalación en contenedor.

2. **Storage de archivos:** Los PDFs/DOCX generados deben almacenarse en volumen persistente (`/app/exports/` o similar).

3. **Límites de Claude:** El GeneradorTextoService usa max_tokens=16000. Capítulos muy largos pueden requerir generación en chunks.

4. **Validaciones personalizables:** Las reglas de validación están en BD y pueden extenderse sin cambios de código.

5. **Templates por industria:** Solo Minería tiene templates. Agregar templates para Energía, Inmobiliario, etc. requiere INSERT en `templates_capitulos`.

---

**Próximo paso recomendado:** Implementar `ExportadorService` básico (PDF) y `GeneracionEIAService` para tener el backend funcional end-to-end.
