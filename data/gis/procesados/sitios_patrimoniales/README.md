# Sitios Patrimoniales

## Descripción
Patrimonio cultural, arqueológico e histórico de Chile.

## Tipos incluidos
- Monumentos Históricos
- Monumentos Arqueológicos
- Zonas Típicas
- Santuarios de la Naturaleza (aspecto patrimonial)
- Sitios del Patrimonio Mundial UNESCO

## Fuentes oficiales

| Fuente | URL | Datos |
|--------|-----|-------|
| CMN | https://www.monumentos.gob.cl/ | Monumentos Nacionales |
| UNESCO | https://whc.unesco.org/ | Patrimonio Mundial |
| IDE Chile | https://www.ide.cl/ | Capas patrimonio |

## Convención de nombres
```
monumentos_historicos_{region|nacional}_{año}.geojson
sitios_arqueologicos_{region|nacional}_{año}.geojson
zonas_tipicas_{año}.geojson
patrimonio_unesco_{año}.geojson
```

## Campos requeridos
- `nombre`: Nombre del sitio
- `tipo`: Tipo de patrimonio
- `categoria`: Categoría CMN
- `decreto`: Decreto de protección
- `fecha_declaracion`: Fecha de declaración

## Sistema de referencia
- SRID: 4326 (WGS84)
- Formato: GeoJSON

## Notas
Relevante para Art. 11 letra e) - alteración del patrimonio cultural.
Buffer de análisis: 10 km

## Archivos cargados
| Archivo | Fuente | Fecha datos | Registros | Cargado BD |
|---------|--------|-------------|-----------|------------|
| - | - | - | - | - |
