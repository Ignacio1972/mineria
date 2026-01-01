"""
Tests específicos para evaluación de triggers del Art. 11 Ley 19.300.
"""

import pytest
from app.services.gis.analisis import evaluar_triggers_eia


class TestTriggerLetraA:
    """Tests del trigger letra a) - Riesgo para salud de la población."""

    def test_centro_poblado_menor_2km_activa_trigger(self):
        """Centro poblado a menos de 2km activa trigger."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [
                {"id": 1, "nombre": "Ciudad", "distancia_m": 1500, "poblacion": 5000}
            ],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        triggers_a = [t for t in clasificacion["triggers"] if t["letra"] == "a"]
        assert len(triggers_a) == 1
        assert triggers_a[0]["severidad"] == "MEDIA"

    def test_centro_poblado_mayor_2km_no_activa_trigger(self):
        """Centro poblado a más de 2km no activa trigger a)."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [
                {"id": 1, "nombre": "Ciudad", "distancia_m": 3000, "poblacion": 5000}
            ],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        triggers_a = [t for t in clasificacion["triggers"] if t["letra"] == "a"]
        assert len(triggers_a) == 0


class TestTriggerLetraB:
    """Tests del trigger letra b) - Efectos adversos sobre recursos naturales."""

    def test_glaciar_intersectado_activa_trigger_critico(self):
        """Intersección con glaciar activa trigger crítico."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [
                {"id": 1, "nombre": "Glaciar", "intersecta": True, "distancia_m": 0}
            ],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        triggers_b = [t for t in clasificacion["triggers"] if t["letra"] == "b"]
        assert len(triggers_b) >= 1
        assert any(t["severidad"] == "CRITICA" for t in triggers_b)

    def test_glaciar_cercano_no_activa_trigger_b(self):
        """Glaciar cercano pero no intersectado no activa trigger b)."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [
                {"id": 1, "nombre": "Glaciar", "intersecta": False, "distancia_m": 5000}
            ],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        triggers_b_glaciar = [
            t for t in clasificacion["triggers"]
            if t["letra"] == "b" and "glaciar" in t["detalle"].lower()
        ]
        assert len(triggers_b_glaciar) == 0

    def test_cuerpo_agua_intersectado_activa_trigger(self):
        """Intersección con cuerpo de agua activa trigger."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [
                {"id": 1, "nombre": "Río", "tipo": "Río", "intersecta": True}
            ],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        triggers_b = [t for t in clasificacion["triggers"] if t["letra"] == "b"]
        assert len(triggers_b) >= 1


class TestTriggerLetraD:
    """Tests del trigger letra d) - Localización en áreas protegidas."""

    def test_area_protegida_intersectada_activa_trigger_critico(self):
        """Intersección con área protegida activa trigger crítico."""
        resultado_gis = {
            "areas_protegidas": [
                {"id": 1, "nombre": "Parque Nacional", "intersecta": True, "distancia_m": 0}
            ],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        triggers_d = [t for t in clasificacion["triggers"] if t["letra"] == "d"]
        assert len(triggers_d) == 1
        assert triggers_d[0]["severidad"] == "CRITICA"

    def test_area_protegida_cercana_no_activa_trigger_d(self):
        """Área protegida cercana pero no intersectada no activa trigger d)."""
        resultado_gis = {
            "areas_protegidas": [
                {"id": 1, "nombre": "Parque Nacional", "intersecta": False, "distancia_m": 500}
            ],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        triggers_d = [t for t in clasificacion["triggers"] if t["letra"] == "d"]
        assert len(triggers_d) == 0


class TestTriggerLetraCyD:
    """Tests del trigger letra c) y d) - Comunidades indígenas."""

    def test_comunidad_menor_10km_activa_trigger(self):
        """Comunidad indígena a menos de 10km activa trigger c/d."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [
                {"id": 1, "nombre": "Comunidad", "pueblo": "Atacameño", "distancia_m": 5000}
            ],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        triggers_cd = [t for t in clasificacion["triggers"] if t["letra"] == "c/d"]
        assert len(triggers_cd) == 1
        assert triggers_cd[0]["severidad"] == "ALTA"

    def test_comunidad_mayor_10km_no_activa_trigger(self):
        """Comunidad indígena a más de 10km no activa trigger c/d."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [
                {"id": 1, "nombre": "Comunidad", "pueblo": "Atacameño", "distancia_m": 15000}
            ],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        triggers_cd = [t for t in clasificacion["triggers"] if t["letra"] == "c/d"]
        assert len(triggers_cd) == 0


class TestClasificacionFinal:
    """Tests de la clasificación final DIA/EIA."""

    def test_trigger_critico_fuerza_eia(self):
        """Cualquier trigger crítico fuerza clasificación EIA."""
        resultado_gis = {
            "areas_protegidas": [
                {"id": 1, "nombre": "PN", "intersecta": True, "distancia_m": 0}
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

    def test_trigger_alto_sugiere_eia(self):
        """Trigger de severidad alta sugiere EIA."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [
                {"id": 1, "nombre": "Comunidad", "pueblo": "Diaguita", "distancia_m": 5000}
            ],
            "centros_poblados": [],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        assert clasificacion["via_ingreso_recomendada"] == "EIA"
        assert clasificacion["confianza"] >= 0.7

    def test_solo_trigger_medio_sugiere_dia(self):
        """Solo trigger de severidad media sugiere DIA."""
        resultado_gis = {
            "areas_protegidas": [],
            "glaciares": [],
            "cuerpos_agua": [],
            "comunidades_indigenas": [],
            "centros_poblados": [
                {"id": 1, "nombre": "Pueblo", "distancia_m": 1500, "poblacion": 100}
            ],
            "alertas": []
        }

        clasificacion = evaluar_triggers_eia(resultado_gis, {})

        assert clasificacion["via_ingreso_recomendada"] == "DIA"
        assert clasificacion["confianza"] >= 0.6

    def test_sin_triggers_sugiere_dia_alta_confianza(self):
        """Sin triggers sugiere DIA con alta confianza."""
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
