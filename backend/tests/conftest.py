"""
Fixtures compartidos para tests.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db():
    """Mock de sesión de base de datos."""
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def sample_geojson():
    """GeoJSON de ejemplo para pruebas."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [-69.5, -23.5],
            [-69.4, -23.5],
            [-69.4, -23.4],
            [-69.5, -23.4],
            [-69.5, -23.5]
        ]]
    }


@pytest.fixture
def sample_proyecto():
    """Datos de proyecto de ejemplo."""
    return {
        "nombre": "Proyecto Test",
        "geometria": {
            "type": "Polygon",
            "coordinates": [[
                [-69.5, -23.5],
                [-69.4, -23.5],
                [-69.4, -23.4],
                [-69.5, -23.4],
                [-69.5, -23.5]
            ]]
        },
        "tipo_mineria": "Cielo abierto",
        "mineral_principal": "Cobre"
    }


@pytest.fixture
def sample_resultado_gis():
    """Resultado GIS de ejemplo para pruebas."""
    return {
        "areas_protegidas": [
            {
                "id": 1,
                "nombre": "Parque Nacional Test",
                "tipo": "Parque Nacional",
                "categoria": "SNASPE",
                "intersecta": True,
                "distancia_m": 0
            }
        ],
        "glaciares": [
            {
                "id": 1,
                "nombre": "Glaciar Test",
                "tipo": "Glaciar de roca",
                "intersecta": False,
                "distancia_m": 5000
            }
        ],
        "cuerpos_agua": [],
        "comunidades_indigenas": [
            {
                "id": 1,
                "nombre": "Comunidad Test",
                "pueblo": "Atacameño",
                "es_adi": True,
                "nombre_adi": "ADI Atacama",
                "distancia_m": 8000
            }
        ],
        "centros_poblados": [
            {
                "id": 1,
                "nombre": "Pueblo Test",
                "tipo": "Aldea",
                "poblacion": 500,
                "distancia_m": 1500
            }
        ],
        "sitios_patrimoniales": [],
        "alertas": []
    }


@pytest.fixture
def sample_documento_legal():
    """Contenido de documento legal de ejemplo."""
    return """
    Artículo 1°.- La presente ley establece las bases generales del medio ambiente.

    Artículo 2°.- Para todos los efectos legales, se entenderá por:
    a) Biodiversidad o Diversidad Biológica: la variabilidad de los organismos vivos.
    b) Conservación del Patrimonio Ambiental: el uso y aprovechamiento racionales.

    Artículo 11°.- Los proyectos o actividades susceptibles de causar impacto ambiental
    deberán someterse al Sistema de Evaluación de Impacto Ambiental si generan:
    a) Riesgo para la salud de la población.
    b) Efectos adversos significativos sobre recursos naturales renovables.
    c) Reasentamiento de comunidades humanas.
    d) Localización en o próxima a poblaciones, recursos y áreas protegidas.
    """


@pytest.fixture
def mock_embedding_service():
    """Mock del servicio de embeddings."""
    with patch('app.services.rag.embeddings.get_embedding_service') as mock:
        service = MagicMock()
        service.embed_text.return_value = [0.1] * 384
        service.embed_texts.return_value = [[0.1] * 384]
        mock.return_value = service
        yield service
