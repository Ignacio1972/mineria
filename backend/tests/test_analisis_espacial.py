"""
Tests para el análisis espacial GIS.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.gis.analisis import analizar_proyecto_espacial, evaluar_triggers_eia


class TestAnalizarProyectoEspacial:
    """Tests del análisis espacial de proyectos."""

    @pytest.mark.asyncio
    async def test_analizar_proyecto_usa_funcion_sql(self, mock_db, sample_geojson):
        """Test que usa la función SQL cuando está disponible."""
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.resultado = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "sitios_patrimoniales": [],
            "alertas": []
        }
        mock_result.fetchone.return_value = mock_row
        mock_db.execute.return_value = mock_result

        resultado = await analizar_proyecto_espacial(mock_db, sample_geojson)

        assert "areas_protegidas" in resultado
        assert "glaciares" in resultado
        assert "alertas" in resultado

    @pytest.mark.asyncio
    async def test_analizar_proyecto_fallback_manual(self, mock_db, sample_geojson):
        """Test que usa análisis manual cuando no hay función SQL."""
        # Primera llamada retorna None (sin función SQL)
        mock_result_none = MagicMock()
        mock_result_none.fetchone.return_value = None

        # Llamadas siguientes para análisis manual
        mock_result_empty = MagicMock()
        mock_result_empty.fetchall.return_value = []

        mock_db.execute.side_effect = [
            mock_result_none,  # Función SQL no disponible
            mock_result_empty,  # áreas protegidas
            mock_result_empty,  # glaciares
            mock_result_empty,  # comunidades
            mock_result_empty,  # cuerpos agua
            mock_result_empty,  # centros poblados
        ]

        resultado = await analizar_proyecto_espacial(mock_db, sample_geojson)

        assert "areas_protegidas" in resultado
        assert resultado["areas_protegidas"] == []


class TestEvaluarTriggersEIA:
    """Tests de evaluación de triggers SEIA."""

    def test_evaluar_sin_triggers(self):
        """Test clasificación sin triggers detectados."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        assert clasificacion["via_ingreso_recomendada"] == "DIA"
        assert clasificacion["confianza"] == 0.8
        assert len(clasificacion["triggers"]) == 0

    def test_evaluar_con_area_protegida_intersectada(self):
        """Test que intersección con área protegida dispara EIA."""
        resultado_gis = {
            "areas_protegidas": [
                {
                    "id": 1,
                    "nombre": "Parque Nacional Test",
                    "tipo": "Parque Nacional",
                    "intersecta": True,
                    "distancia_m": 0
                }
            ],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        assert clasificacion["via_ingreso_recomendada"] == "EIA"
        assert clasificacion["confianza"] >= 0.9
        assert any(t["letra"] == "d" for t in clasificacion["triggers"])

    def test_evaluar_con_glaciar_intersectado(self):
        """Test que intersección con glaciar dispara EIA."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [
                {
                    "id": 1,
                    "nombre": "Glaciar Test",
                    "intersecta": True,
                    "distancia_m": 0
                }
            ],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        assert clasificacion["via_ingreso_recomendada"] == "EIA"
        assert any(t["letra"] == "b" for t in clasificacion["triggers"])

    def test_evaluar_con_comunidad_cercana(self):
        """Test que comunidad cercana genera trigger."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [
                {
                    "id": 1,
                    "nombre": "Comunidad Test",
                    "pueblo": "Atacameño",
                    "distancia_m": 5000
                }
            ],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        assert any(t["letra"] == "c/d" for t in clasificacion["triggers"])

    def test_evaluar_con_centro_poblado_cercano(self):
        """Test que centro poblado cercano genera trigger."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [
                {
                    "id": 1,
                    "nombre": "Pueblo Test",
                    "tipo": "Ciudad",
                    "poblacion": 10000,
                    "distancia_m": 1500
                }
            ],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        assert any(t["letra"] == "a" for t in clasificacion["triggers"])

    def test_evaluar_con_cuerpo_agua_intersectado(self):
        """Test que intersección con cuerpo de agua genera trigger."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [
                {
                    "id": 1,
                    "nombre": "Río Test",
                    "tipo": "Río",
                    "intersecta": True,
                    "distancia_m": 0
                }
            ],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        assert any(t["letra"] == "b" for t in clasificacion["triggers"])

    def test_evaluar_multiples_triggers(self):
        """Test con múltiples triggers detectados."""
        resultado_gis = {
            "areas_protegidas": [
                {"id": 1, "nombre": "PN Test", "intersecta": True, "distancia_m": 0}
            ],
            "glaciares": [
                {"id": 1, "nombre": "Glaciar", "intersecta": True, "distancia_m": 0}
            ],
            "cuerpos_agua": [],
            "comunidades_indigenas": [
                {"id": 1, "nombre": "Comunidad", "pueblo": "Aymara", "distancia_m": 3000}
            ],
            "centros_poblados": [
                {"id": 1, "nombre": "Pueblo", "poblacion": 500, "distancia_m": 1000}
            ],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        assert clasificacion["via_ingreso_recomendada"] == "EIA"
        assert clasificacion["confianza"] >= 0.9
        assert len(clasificacion["triggers"]) >= 3

    def test_clasificacion_resumen(self):
        """Test que el resumen refleja cantidad de triggers."""
        resultado_gis = {
            "areas_protegidas": [
                {"id": 1, "nombre": "PN Test", "intersecta": True, "distancia_m": 0}
            ],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        assert "trigger" in clasificacion["resumen"].lower()
        assert "1" in clasificacion["resumen"]


class TestAnalizarProyectoAlertas:
    """Tests de generación de alertas en análisis espacial."""

    @pytest.mark.asyncio
    async def test_genera_alerta_area_protegida_intersectada(self, mock_db, sample_geojson):
        """Test que genera alerta cuando intersecta área protegida."""
        # Simular resultado con intersección
        mock_result_none = MagicMock()
        mock_result_none.fetchone.return_value = None

        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.nombre = "Parque Nacional"
        mock_row.tipo = "Parque Nacional"
        mock_row.categoria = "SNASPE"
        mock_row.intersecta = True
        mock_row.distancia_m = 0

        mock_result_areas = MagicMock()
        mock_result_areas.fetchall.return_value = [mock_row]

        mock_result_empty = MagicMock()
        mock_result_empty.fetchall.return_value = []

        mock_db.execute.side_effect = [
            mock_result_none,  # Función SQL
            mock_result_areas,  # áreas protegidas
            mock_result_empty,  # glaciares
            mock_result_empty,  # comunidades
            mock_result_empty,  # cuerpos agua
            mock_result_empty,  # centros poblados
        ]

        resultado = await analizar_proyecto_espacial(mock_db, sample_geojson)

        assert len(resultado["alertas"]) >= 1
        alerta = resultado["alertas"][0]
        assert alerta["tipo"] == "CRITICA"
        assert "área protegida" in alerta["categoria"] or "intersecta" in alerta["mensaje"].lower()
