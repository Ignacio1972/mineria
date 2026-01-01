# Áreas Protegidas

## Descripción
Capa de áreas bajo protección oficial del Estado de Chile.

## Tipos incluidos
- SNASPE (Parques Nacionales, Reservas Nacionales, Monumentos Naturales)
- Santuarios de la Naturaleza
- Reservas Marinas
- Áreas Marinas Costeras Protegidas
- Bienes Nacionales Protegidos

## Fuentes oficiales

| Fuente | URL | Datos |
|--------|-----|-------|
| CONAF | https://www.conaf.cl/parques-nacionales/snaspe/ | SNASPE completo |
| IDE Chile | https://www.ide.cl/index.php/medio-ambiente | Áreas protegidas |
| MMA | https://mma.gob.cl/biodiversidad/areas-protegidas/ | Santuarios |

## Convención de nombres
```
snaspe_{region|nacional}_{año}.geojson
santuarios_{region|nacional}_{año}.geojson
```

## Campos requeridos
- `nombre`: Nombre del área protegida
- `tipo`: Tipo (Parque Nacional, Reserva, etc.)
- `categoria`: Categoría SNASPE
- `region`: Región administrativa
- `comuna`: Comuna(s)
- `superficie_ha`: Superficie en hectáreas
- `decreto`: Decreto de creación
- `fecha_creacion`: Fecha de creación

## Sistema de referencia
- SRID: 4326 (WGS84)
- Formato: GeoJSON

## Archivos cargados

| Archivo | Fuente | Fecha datos | Registros | Cargado BD |
|---------|--------|-------------|-----------|------------|
| snaspe_arcgis_nacional_2024.geojson | ArcGIS REST Services | 2024 | 2,754 | Sí |
| Areas Protegidas.shp | MMA - Líneas de Base | 2024-07 | 583 | Sí |
| Sitios Prioritarios según Ley 19300.shp | MMA - Líneas de Base | 2024-07 | 63 | Sí |

## Resumen en BD

| Categoría | Registros |
|-----------|-----------|
| SNASPE | 2,754 |
| MMA | 583 |
| Sitio Prioritario Ley 19300 | 63 |
| **Total** | **3,400** |
