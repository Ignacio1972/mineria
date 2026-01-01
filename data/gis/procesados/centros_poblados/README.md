# Centros Poblados

## Descripción
Ciudades, pueblos y localidades habitadas de Chile.

## Tipos incluidos
- Ciudades
- Pueblos
- Aldeas
- Caseríos

## Fuentes oficiales

| Fuente | URL | Datos |
|--------|-----|-------|
| INE | https://www.ine.cl/ | Censo, entidades pobladas |
| IDE Chile | https://www.ide.cl/ | Localidades |

## Convención de nombres
```
centros_poblados_{region|nacional}_{año}.geojson
ciudades_{año}.geojson
```

## Campos requeridos
- `nombre`: Nombre del centro poblado
- `tipo`: Tipo (Ciudad, Pueblo, Aldea, Caserío)
- `region`: Región administrativa
- `comuna`: Comuna
- `poblacion`: Población según último censo

## Categorías por población
- **Ciudad**: > 5.000 habitantes
- **Pueblo**: 2.001 - 5.000 habitantes
- **Aldea**: 301 - 2.000 habitantes
- **Caserío**: < 300 habitantes

## Sistema de referencia
- SRID: 4326 (WGS84)
- Formato: GeoJSON (Point)

## Notas
Relevante para Art. 11 letra a) - riesgo para la salud de la población.
Buffer de análisis: 20 km

## Archivos cargados
| Archivo | Fuente | Fecha datos | Registros | Cargado BD |
|---------|--------|-------------|-----------|------------|
| - | - | - | - | - |
