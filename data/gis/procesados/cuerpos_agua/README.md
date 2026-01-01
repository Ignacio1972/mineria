# Cuerpos de Agua

## Descripción
Red hidrográfica y cuerpos de agua de Chile.

## Tipos incluidos
- Ríos y esteros
- Lagos y lagunas
- Humedales
- Sitios Ramsar
- Salares
- Embalses

## Fuentes oficiales

| Fuente | URL | Datos |
|--------|-----|-------|
| DGA | https://dga.mop.gob.cl/ | Red hidrográfica, cuencas |
| IDE Chile | https://www.ide.cl/ | Hidrografía nacional |
| MMA | https://mma.gob.cl/ | Sitios Ramsar, humedales |

## Convención de nombres
```
rios_{region|nacional}_{año}.geojson
lagos_{region|nacional}_{año}.geojson
humedales_{region|nacional}_{año}.geojson
sitios_ramsar_{año}.geojson
cuencas_{año}.geojson
```

## Campos requeridos
- `nombre`: Nombre del cuerpo de agua
- `tipo`: Tipo (río, lago, humedal, etc.)
- `cuenca`: Cuenca hidrográfica
- `es_sitio_ramsar`: Boolean
- `superficie_ha`: Superficie (para polígonos)

## Sistema de referencia
- SRID: 4326 (WGS84)
- Formato: GeoJSON

## Notas
Relevante para Art. 11 letra b) - recursos naturales renovables.
Buffer de análisis: 10 km

## Archivos cargados

| Archivo | Fuente | Fecha datos | Registros | Cargado BD |
|---------|--------|-------------|-----------|------------|
| Inventario de Humedales.shp | MMA - Inventario Nacional | 2024-07 | 1,722 | Sí |

**Nota:** Actualmente solo región de Antofagasta. Pendiente obtener datos nacionales de ríos, lagos y sitios Ramsar.
