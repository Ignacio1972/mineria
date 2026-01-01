# Comunidades Indígenas

## Descripción
Comunidades y pueblos indígenas reconocidos por la Ley 19.253.

## Tipos incluidos
- Comunidades indígenas
- Áreas de Desarrollo Indígena (ADI)
- Tierras indígenas

## Fuentes oficiales

| Fuente | URL | Datos |
|--------|-----|-------|
| CONADI | https://www.conadi.gob.cl/ | Comunidades, ADIs |
| IDE Chile | https://www.ide.cl/ | Capas comunidades |

## Convención de nombres
```
comunidades_{pueblo}_{region|nacional}_{año}.geojson
adis_{año}.geojson
tierras_indigenas_{año}.geojson
```

## Campos requeridos
- `nombre`: Nombre de la comunidad
- `pueblo`: Pueblo originario (Mapuche, Aymara, Atacameño, etc.)
- `es_adi`: Boolean - si está en un ADI
- `nombre_adi`: Nombre del ADI (si aplica)
- `region`: Región administrativa
- `comuna`: Comuna

## Pueblos originarios reconocidos
1. Mapuche
2. Aymara
3. Rapa Nui
4. Atacameño (Lickanantay)
5. Quechua
6. Colla
7. Diaguita
8. Kawésqar
9. Yagán
10. Chango

## Sistema de referencia
- SRID: 4326 (WGS84)
- Formato: GeoJSON

## Notas
Especialmente relevante para Art. 11 letras c) y d) - reasentamiento y alteración de sistemas de vida.
Buffer de análisis: 30 km

## Archivos cargados
| Archivo | Fuente | Fecha datos | Registros | Cargado BD |
|---------|--------|-------------|-----------|------------|
| - | - | - | - | - |
