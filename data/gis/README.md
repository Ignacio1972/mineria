# Sistema GIS - Prefactibilidad Ambiental Minera

## Estructura de Directorios

```
data/gis/
├── fuentes/                    # Datos originales sin procesar
│   ├── ide_chile/              # IDE Chile (geoserver.ide.cl)
│   ├── conaf/                  # SNASPE, áreas protegidas
│   ├── dga/                    # Cuencas, glaciares, derechos agua
│   ├── mop/                    # Infraestructura
│   ├── conadi/                 # ADIs, comunidades indígenas
│   ├── cmn/                    # Patrimonio cultural
│   ├── ine/                    # Censos, división política
│   ├── mma/                    # Medio ambiente, Ramsar
│   └── otros/
│
├── procesados/                 # Datos listos para cargar a BD
│   ├── areas_protegidas/       # SNASPE, santuarios
│   ├── glaciares/              # Inventario glaciares
│   ├── cuerpos_agua/           # Ríos, lagos, humedales
│   ├── comunidades_indigenas/  # Comunidades, ADIs
│   ├── centros_poblados/       # Ciudades, pueblos
│   ├── sitios_patrimoniales/   # Monumentos, arqueología
│   ├── regiones/               # División regional
│   ├── comunas/                # División comunal
│   └── bienes_nacionales/      # Terrenos fiscales
│
├── scripts/                    # Scripts de procesamiento
│
└── catalogo.json               # Inventario de todas las capas
```

## Flujo de Trabajo

```
1. Descargar datos oficiales → fuentes/{origen}/
2. Procesar (reproyectar, limpiar) → procesados/{capa}/
3. Cargar a PostGIS → gis.{tabla}
4. Actualizar catalogo.json
```

## Convención de Nombres

### Archivos de datos
```
{capa}_{fuente}_{region|nacional}_{año}.{formato}
```

Ejemplos:
- `snaspe_conaf_nacional_2024.geojson`
- `glaciares_dga_atacama_2023.geojson`
- `comunas_ine_nacional_2024.geojson`

### Formatos soportados
- **GeoJSON** (preferido) - `.geojson`
- **Shapefile** - `.shp` + archivos asociados
- **GeoPackage** - `.gpkg`

## Sistema de Referencia

Todos los datos deben estar en **EPSG:4326 (WGS84)**.

Si los datos vienen en otro sistema (común en Chile: EPSG:32718 o 32719),
deben ser reproyectados antes de guardar en `/procesados/`.

## Estado Actual de Capas

| Capa | Tabla BD | Registros | Cobertura | Art. 11 |
|------|----------|-----------|-----------|---------|
| Áreas Protegidas | `gis.areas_protegidas` | **3,400** | Nacional | letra d) |
| Glaciares | `gis.glaciares` | **450** | Antofagasta | letra b) |
| Cuerpos de Agua | `gis.cuerpos_agua` | **1,722** | Antofagasta | letra b) |
| Comunidades Indígenas | `gis.comunidades_indigenas` | - | Pendiente | letras c), d) |
| Centros Poblados | `gis.centros_poblados` | - | Pendiente | letra a) |
| Sitios Patrimoniales | `gis.sitios_patrimoniales` | - | Pendiente | letra e) |
| Regiones | `gis.regiones` | - | Pendiente | ubicación |
| Comunas | `gis.comunas` | - | Pendiente | ubicación |

**Total registros en BD:** 5,572 (actualizado 2024-12-26)

## Fuentes de Datos Utilizadas

| Fuente | Datos | URL |
|--------|-------|-----|
| **MMA Líneas de Base** | Áreas protegidas, glaciares, humedales, sitios prioritarios | lineasdebasepublicas.mma.gob.cl |
| **ArcGIS REST** | SNASPE, Ramsar, división política | services7.arcgis.com |
| IDE Chile | División política, capas base | ide.cl |
| CONAF | SNASPE | conaf.cl |
| DGA | Glaciares, cuencas, hidrografía | dga.mop.gob.cl |
| CONADI | Comunidades, ADIs | conadi.gob.cl |
| CMN | Patrimonio | monumentos.gob.cl |
| INE | Censo, localidades | ine.cl |
| BCN | Mapas vectoriales oficiales | bcn.cl/siit/mapas_vectoriales |

## Scripts de Carga

```bash
# Descargar capas desde ArcGIS REST Services
python /var/www/mineria/data/gis/scripts/descargar_arcgis.py --listar
python /var/www/mineria/data/gis/scripts/descargar_arcgis.py --capa snaspe

# Cargar shapefiles con ogr2ogr
ogr2ogr -f "PostgreSQL" "PG:host=localhost port=5433 dbname=mineria user=mineria password=***" \
  archivo.shp -nln gis.tabla_temp -overwrite -nlt PROMOTE_TO_MULTI

# Configurar GeoServer
python /var/www/mineria/data/scripts/configurar_geoserver.py
```

## Catálogo

El archivo `catalogo.json` mantiene un inventario de todas las capas
y archivos cargados. Actualízalo después de cada carga de datos.

## Notas

- Los datos en `/fuentes/` son respaldos originales, no modificar
- Los datos en `/procesados/` deben estar en EPSG:4326
- Cada carpeta en `/procesados/` tiene un README.md con instrucciones
- Documentar siempre: fuente, fecha de descarga, fecha de los datos
