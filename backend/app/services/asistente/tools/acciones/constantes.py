"""
Constantes compartidas para las herramientas de accion.
"""

# Lista de regiones validas de Chile
REGIONES_CHILE = [
    "Arica y Parinacota",
    "Tarapaca",
    "Antofagasta",
    "Atacama",
    "Coquimbo",
    "Valparaiso",
    "Metropolitana",
    "O'Higgins",
    "Maule",
    "Nuble",
    "Biobio",
    "Araucania",
    "Los Rios",
    "Los Lagos",
    "Aysen",
    "Magallanes",
]

TIPOS_MINERIA = [
    "cielo_abierto",
    "subterranea",
    "mixta",
    "placer",
    "in_situ",
]

FASES_PROYECTO = [
    "exploracion",
    "evaluacion",
    "desarrollo",
    "produccion",
    "cierre",
]

# Categorias validas para ficha y sus claves tipicas
CATEGORIAS_FICHA = {
    "identificacion": [
        "nombre_proyecto", "titular", "rut_titular", "representante_legal",
        "direccion", "telefono", "email", "tipo_titular", "razon_social"
    ],
    "tecnico": [
        "tipo_extraccion", "mineral_principal", "minerales_secundarios",
        "tonelaje_mensual", "tonelaje_anual", "ley_mineral", "vida_util_anos",
        "produccion_estimada", "metodo_explotacion", "profundidad_rajo",
        "profundidad_mina", "razon_esteril_mineral"
    ],
    "obras": [
        "planta_beneficio", "deposito_relaves", "botadero_esteriles",
        "caminos_acceso", "linea_transmision", "subestacion", "campamento",
        "piscinas", "tanques_combustible", "polvorin", "talleres",
        "oficinas", "laboratorio", "patio_acopio"
    ],
    "fases": [
        "fecha_inicio_construccion", "duracion_construccion_meses",
        "fecha_inicio_operacion", "duracion_operacion_anos",
        "fecha_inicio_cierre", "duracion_cierre_anos",
        "trabajadores_construccion", "trabajadores_operacion"
    ],
    "insumos": [
        "uso_agua_lps", "fuente_agua", "tipo_agua", "derechos_agua",
        "energia_mw", "fuente_energia", "combustible_tipo",
        "combustible_consumo", "explosivos_tipo", "explosivos_consumo",
        "reactivos", "acido_sulfurico"
    ],
    "emisiones": [
        "emisiones_mp", "emisiones_so2", "emisiones_nox",
        "ruido_diurno", "ruido_nocturno", "vibraciones",
        "residuos_solidos", "residuos_peligrosos", "efluentes",
        "drenaje_acido", "manejo_aguas_contacto"
    ],
    "social": [
        "comunidades_cercanas", "distancia_poblados", "poblacion_afectada",
        "comunidades_indigenas", "patrimonio_cultural", "sitios_arqueologicos",
        "participacion_ciudadana", "compromisos_sociales"
    ],
    "ambiental": [
        "areas_protegidas_cercanas", "distancia_areas_protegidas",
        "glaciares_cercanos", "humedales_cercanos", "cuerpos_agua",
        "flora_protegida", "fauna_protegida", "vegetacion_nativa",
        "especies_peligro", "habitat_critico"
    ],
}
