# Glaciares

## Descripción
Inventario de glaciares y ambiente periglaciar de Chile.

## Tipos incluidos
- Glaciares descubiertos
- Glaciares cubiertos
- Glaciares rocosos
- Campos de nieve

## Fuentes oficiales

| Fuente | URL | Datos |
|--------|-----|-------|
| DGA | https://dga.mop.gob.cl/productosyservicios/mapas/Paginas/default.aspx | Inventario Nacional de Glaciares |
| IDE Chile | https://www.ide.cl/ | Capas glaciares |

## Convención de nombres
```
glaciares_dga_{region|nacional}_{año}.geojson
```

## Campos requeridos
- `nombre`: Nombre del glaciar (si tiene)
- `tipo`: Tipo de glaciar
- `cuenca`: Cuenca hidrográfica
- `subcuenca`: Subcuenca
- `superficie_km2`: Superficie en km²
- `altitud_min`: Altitud mínima (m.s.n.m.)
- `altitud_max`: Altitud máxima (m.s.n.m.)

## Sistema de referencia
- SRID: 4326 (WGS84)
- Formato: GeoJSON

## Notas
Los glaciares son especialmente relevantes para el Art. 11 letra b) de la Ley 19.300.
Buffer de análisis: 20 km

## Archivos cargados

| Archivo | Fuente | Fecha datos | Registros | Cargado BD |
|---------|--------|-------------|-----------|------------|
| Inventario de Glaciares.shp | DGA via MMA | 2024-07 | 450 | Sí |

**Nota:** Actualmente solo región de Antofagasta. Pendiente obtener inventario nacional completo.
