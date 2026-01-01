"""
Tests para el Motor de Reglas SEIA - Fase 3

Tests unitarios para:
- EvaluadorTriggers
- MotorReglasSSEIA
- SistemaAlertas
"""

import pytest
from app.services.reglas import (
    EvaluadorTriggers,
    MotorReglasSSEIA,
    SistemaAlertas,
    TriggerEIA,
    ClasificacionSEIA,
    Alerta,
    NivelAlerta,
)
from app.services.reglas.triggers import LetraArticulo11, SeveridadTrigger
from app.services.reglas.seia import ViaIngreso, NivelConfianza


# === Fixtures ===

@pytest.fixture
def datos_proyecto_basico():
    """Datos de un proyecto minero básico."""
    return {
        "nombre": "Proyecto Test",
        "tipo_mineria": "Tajo abierto",
        "mineral_principal": "Cobre",
        "region": "Antofagasta",
        "superficie_ha": 200,
        "uso_agua_lps": 50,
        "vida_util_anos": 15,
        "trabajadores_construccion": 300,
    }


@pytest.fixture
def datos_proyecto_grande():
    """Datos de un proyecto minero grande."""
    return {
        "nombre": "Mega Proyecto Minero",
        "tipo_mineria": "Tajo abierto",
        "mineral_principal": "Cobre",
        "region": "Antofagasta",
        "superficie_ha": 1000,
        "uso_agua_lps": 300,
        "vida_util_anos": 30,
        "trabajadores_construccion": 1000,
        "inversion_musd": 5000,
    }


@pytest.fixture
def resultado_gis_sin_impactos():
    """Resultado GIS sin elementos sensibles."""
    return {
        "areas_protegidas": [],
        "glaciares": [],
        "cuerpos_agua": [],
        "comunidades_indigenas": [],
        "centros_poblados": [],
        "sitios_patrimoniales": [],
        "alertas": [],
    }


@pytest.fixture
def resultado_gis_con_area_protegida():
    """Resultado GIS con intersección de área protegida."""
    return {
        "areas_protegidas": [
            {
                "id": 1,
                "nombre": "Parque Nacional Test",
                "tipo": "Parque Nacional",
                "categoria": "SNASPE",
                "intersecta": True,
                "distancia_m": 0,
            }
        ],
        "glaciares": [],
        "cuerpos_agua": [],
        "comunidades_indigenas": [],
        "centros_poblados": [],
        "sitios_patrimoniales": [],
        "alertas": [],
    }


@pytest.fixture
def resultado_gis_con_glaciar():
    """Resultado GIS con intersección de glaciar."""
    return {
        "areas_protegidas": [],
        "glaciares": [
            {
                "id": 1,
                "nombre": "Glaciar Test",
                "tipo": "Glaciar de montaña",
                "intersecta": True,
                "distancia_m": 0,
            }
        ],
        "cuerpos_agua": [],
        "comunidades_indigenas": [],
        "centros_poblados": [],
        "sitios_patrimoniales": [],
        "alertas": [],
    }


@pytest.fixture
def resultado_gis_con_comunidad_indigena():
    """Resultado GIS con comunidad indígena cercana."""
    return {
        "areas_protegidas": [],
        "glaciares": [],
        "cuerpos_agua": [],
        "comunidades_indigenas": [
            {
                "id": 1,
                "nombre": "Comunidad Atacameña Test",
                "pueblo": "Atacameño",
                "es_adi": True,
                "nombre_adi": "ADI Atacama La Grande",
                "distancia_m": 3000,
            }
        ],
        "centros_poblados": [],
        "sitios_patrimoniales": [],
        "alertas": [],
    }


@pytest.fixture
def resultado_gis_complejo():
    """Resultado GIS con múltiples elementos sensibles."""
    return {
        "areas_protegidas": [
            {
                "id": 1,
                "nombre": "Reserva Nacional Test",
                "tipo": "Reserva Nacional",
                "categoria": "SNASPE",
                "intersecta": False,
                "distancia_m": 5000,
            }
        ],
        "glaciares": [
            {
                "id": 1,
                "nombre": "Glaciar Cercano",
                "tipo": "Glaciar de montaña",
                "intersecta": False,
                "distancia_m": 8000,
            }
        ],
        "cuerpos_agua": [
            {
                "id": 1,
                "nombre": "Río Test",
                "tipo": "Río",
                "es_sitio_ramsar": False,
                "intersecta": True,
                "distancia_m": 0,
            }
        ],
        "comunidades_indigenas": [
            {
                "id": 1,
                "nombre": "Comunidad Test",
                "pueblo": "Atacameño",
                "es_adi": False,
                "distancia_m": 8000,
            }
        ],
        "centros_poblados": [
            {
                "id": 1,
                "nombre": "Pueblo Test",
                "tipo": "Pueblo",
                "poblacion": 500,
                "distancia_m": 1500,
            }
        ],
        "sitios_patrimoniales": [],
        "alertas": [],
    }


# === Tests EvaluadorTriggers ===

class TestEvaluadorTriggers:
    """Tests para EvaluadorTriggers."""

    def test_inicializacion(self):
        """Test que el evaluador se inicializa correctamente."""
        evaluador = EvaluadorTriggers()
        assert evaluador.triggers_detectados == []

    def test_sin_triggers(self, resultado_gis_sin_impactos, datos_proyecto_basico):
        """Test evaluación sin triggers detectados."""
        evaluador = EvaluadorTriggers()
        triggers = evaluador.evaluar(resultado_gis_sin_impactos, datos_proyecto_basico)

        assert len(triggers) == 0
        resumen = evaluador.obtener_resumen()
        assert resumen["total_triggers"] == 0
        assert resumen["requiere_eia"] is False

    def test_trigger_area_protegida(self, resultado_gis_con_area_protegida, datos_proyecto_basico):
        """Test detección de trigger por área protegida."""
        evaluador = EvaluadorTriggers()
        triggers = evaluador.evaluar(resultado_gis_con_area_protegida, datos_proyecto_basico)

        assert len(triggers) >= 1
        trigger_d = next((t for t in triggers if t.letra == LetraArticulo11.D), None)
        assert trigger_d is not None
        assert trigger_d.severidad == SeveridadTrigger.CRITICA
        assert "área" in trigger_d.descripcion.lower() or "protegida" in trigger_d.descripcion.lower()

    def test_trigger_glaciar(self, resultado_gis_con_glaciar, datos_proyecto_basico):
        """Test detección de trigger por glaciar."""
        evaluador = EvaluadorTriggers()
        triggers = evaluador.evaluar(resultado_gis_con_glaciar, datos_proyecto_basico)

        assert len(triggers) >= 1
        trigger_b = next((t for t in triggers if t.letra == LetraArticulo11.B), None)
        assert trigger_b is not None
        assert trigger_b.severidad == SeveridadTrigger.CRITICA
        assert "glaciar" in trigger_b.descripcion.lower()

    def test_trigger_comunidad_indigena(self, resultado_gis_con_comunidad_indigena, datos_proyecto_basico):
        """Test detección de trigger por comunidad indígena cercana."""
        evaluador = EvaluadorTriggers()
        triggers = evaluador.evaluar(resultado_gis_con_comunidad_indigena, datos_proyecto_basico)

        assert len(triggers) >= 1
        trigger_c = next((t for t in triggers if t.letra == LetraArticulo11.C), None)
        assert trigger_c is not None
        assert trigger_c.severidad in [SeveridadTrigger.CRITICA, SeveridadTrigger.ALTA]

    def test_multiples_triggers(self, resultado_gis_complejo, datos_proyecto_grande):
        """Test detección de múltiples triggers."""
        evaluador = EvaluadorTriggers()
        triggers = evaluador.evaluar(resultado_gis_complejo, datos_proyecto_grande)

        assert len(triggers) >= 2
        resumen = evaluador.obtener_resumen()
        assert len(resumen["letras_afectadas"]) >= 2

    def test_trigger_to_dict(self, resultado_gis_con_area_protegida, datos_proyecto_basico):
        """Test conversión de trigger a diccionario."""
        evaluador = EvaluadorTriggers()
        triggers = evaluador.evaluar(resultado_gis_con_area_protegida, datos_proyecto_basico)

        assert len(triggers) >= 1
        trigger_dict = triggers[0].to_dict()

        assert "letra" in trigger_dict
        assert "descripcion" in trigger_dict
        assert "severidad" in trigger_dict
        assert "fundamento_legal" in trigger_dict
        assert "peso" in trigger_dict


# === Tests MotorReglasSSEIA ===

class TestMotorReglasSSEIA:
    """Tests para MotorReglasSSEIA."""

    def test_inicializacion(self):
        """Test que el motor se inicializa correctamente."""
        motor = MotorReglasSSEIA()
        assert motor.evaluador_triggers is not None

    def test_clasificacion_dia_sin_triggers(self, resultado_gis_sin_impactos, datos_proyecto_basico):
        """Test clasificación como DIA cuando no hay triggers."""
        motor = MotorReglasSSEIA()
        clasificacion = motor.clasificar_proyecto(resultado_gis_sin_impactos, datos_proyecto_basico)

        assert clasificacion.via_ingreso == ViaIngreso.DIA
        assert clasificacion.confianza >= 0.7
        assert len(clasificacion.triggers) == 0

    def test_clasificacion_eia_por_area_protegida(self, resultado_gis_con_area_protegida, datos_proyecto_basico):
        """Test clasificación como EIA por intersección con área protegida."""
        motor = MotorReglasSSEIA()
        clasificacion = motor.clasificar_proyecto(resultado_gis_con_area_protegida, datos_proyecto_basico)

        assert clasificacion.via_ingreso == ViaIngreso.EIA
        assert clasificacion.confianza >= 0.9

    def test_clasificacion_eia_por_glaciar(self, resultado_gis_con_glaciar, datos_proyecto_basico):
        """Test clasificación como EIA por intersección con glaciar."""
        motor = MotorReglasSSEIA()
        clasificacion = motor.clasificar_proyecto(resultado_gis_con_glaciar, datos_proyecto_basico)

        assert clasificacion.via_ingreso == ViaIngreso.EIA
        assert clasificacion.confianza >= 0.9

    def test_clasificacion_eia_por_comunidad_indigena(self, resultado_gis_con_comunidad_indigena, datos_proyecto_basico):
        """Test clasificación por comunidad indígena cercana en ADI."""
        motor = MotorReglasSSEIA()
        clasificacion = motor.clasificar_proyecto(resultado_gis_con_comunidad_indigena, datos_proyecto_basico)

        # Con ADI debería ser EIA
        assert clasificacion.via_ingreso == ViaIngreso.EIA

    def test_clasificacion_to_dict(self, resultado_gis_con_area_protegida, datos_proyecto_basico):
        """Test conversión de clasificación a diccionario."""
        motor = MotorReglasSSEIA()
        clasificacion = motor.clasificar_proyecto(resultado_gis_con_area_protegida, datos_proyecto_basico)
        resultado = clasificacion.to_dict()

        assert "via_ingreso_recomendada" in resultado
        assert "confianza" in resultado
        assert "triggers" in resultado
        assert "justificacion" in resultado
        assert "puntaje_matriz" in resultado

    def test_recomendaciones_generadas(self, resultado_gis_con_area_protegida, datos_proyecto_basico):
        """Test que se generan recomendaciones."""
        motor = MotorReglasSSEIA()
        clasificacion = motor.clasificar_proyecto(resultado_gis_con_area_protegida, datos_proyecto_basico)

        assert len(clasificacion.recomendaciones_generales) > 0

    def test_matriz_decision(self):
        """Test obtención de configuración de matriz de decisión."""
        motor = MotorReglasSSEIA()
        matriz = motor.obtener_matriz_decision()

        assert "pesos" in matriz
        assert "umbrales" in matriz
        assert "factores_proyecto" in matriz
        assert "reglas" in matriz


# === Tests SistemaAlertas ===

class TestSistemaAlertas:
    """Tests para SistemaAlertas."""

    def test_inicializacion(self):
        """Test que el sistema de alertas se inicializa correctamente."""
        sistema = SistemaAlertas()
        assert sistema.alertas == []

    def test_sin_alertas(self, resultado_gis_sin_impactos, datos_proyecto_basico):
        """Test generación sin alertas cuando no hay impactos."""
        sistema = SistemaAlertas()
        alertas = sistema.generar_alertas(resultado_gis_sin_impactos, datos_proyecto_basico)

        # Pueden generarse alertas por características del proyecto
        resumen = sistema.obtener_resumen()
        assert "total_alertas" in resumen

    def test_alerta_area_protegida(self, resultado_gis_con_area_protegida, datos_proyecto_basico):
        """Test generación de alerta por área protegida."""
        sistema = SistemaAlertas()
        alertas = sistema.generar_alertas(resultado_gis_con_area_protegida, datos_proyecto_basico)

        assert len(alertas) >= 1
        alerta_area = next(
            (a for a in alertas if "protegida" in a.titulo.lower() or "protegida" in a.descripcion.lower()),
            None
        )
        assert alerta_area is not None
        assert alerta_area.nivel == NivelAlerta.CRITICA

    def test_alerta_glaciar(self, resultado_gis_con_glaciar, datos_proyecto_basico):
        """Test generación de alerta por glaciar."""
        sistema = SistemaAlertas()
        alertas = sistema.generar_alertas(resultado_gis_con_glaciar, datos_proyecto_basico)

        assert len(alertas) >= 1
        alerta_glaciar = next(
            (a for a in alertas if "glaciar" in a.titulo.lower()),
            None
        )
        assert alerta_glaciar is not None
        assert alerta_glaciar.nivel == NivelAlerta.CRITICA

    def test_alerta_comunidad_indigena(self, resultado_gis_con_comunidad_indigena, datos_proyecto_basico):
        """Test generación de alerta por comunidad indígena."""
        sistema = SistemaAlertas()
        alertas = sistema.generar_alertas(resultado_gis_con_comunidad_indigena, datos_proyecto_basico)

        assert len(alertas) >= 1
        alerta_indigena = next(
            (a for a in alertas if "indígena" in a.titulo.lower() or "indigena" in a.titulo.lower()),
            None
        )
        assert alerta_indigena is not None

    def test_alertas_ordenadas_por_severidad(self, resultado_gis_complejo, datos_proyecto_grande):
        """Test que las alertas se ordenan por severidad."""
        sistema = SistemaAlertas()
        alertas = sistema.generar_alertas(resultado_gis_complejo, datos_proyecto_grande)

        if len(alertas) >= 2:
            # Las críticas deben estar primero
            niveles_orden = [a.nivel for a in alertas]
            for i in range(len(niveles_orden) - 1):
                if niveles_orden[i] == NivelAlerta.CRITICA:
                    assert niveles_orden[i + 1] != NivelAlerta.BAJA or niveles_orden[i + 1] != NivelAlerta.MEDIA

    def test_alerta_to_dict(self, resultado_gis_con_area_protegida, datos_proyecto_basico):
        """Test conversión de alerta a diccionario."""
        sistema = SistemaAlertas()
        alertas = sistema.generar_alertas(resultado_gis_con_area_protegida, datos_proyecto_basico)

        assert len(alertas) >= 1
        alerta_dict = alertas[0].to_dict()

        assert "id" in alerta_dict
        assert "nivel" in alerta_dict
        assert "categoria" in alerta_dict
        assert "titulo" in alerta_dict
        assert "descripcion" in alerta_dict
        assert "acciones_requeridas" in alerta_dict

    def test_resumen_alertas(self, resultado_gis_complejo, datos_proyecto_grande):
        """Test obtención de resumen de alertas."""
        sistema = SistemaAlertas()
        sistema.generar_alertas(resultado_gis_complejo, datos_proyecto_grande)
        resumen = sistema.obtener_resumen()

        assert "total_alertas" in resumen
        assert "por_nivel" in resumen
        assert "por_categoria" in resumen
        assert "componentes_afectados" in resumen
        assert "permisos_requeridos" in resumen


# === Tests de Integración ===

class TestIntegracionReglas:
    """Tests de integración del motor de reglas."""

    def test_flujo_completo_proyecto_limpio(self, resultado_gis_sin_impactos, datos_proyecto_basico):
        """Test flujo completo para proyecto sin impactos significativos."""
        motor = MotorReglasSSEIA()
        sistema_alertas = SistemaAlertas()

        clasificacion = motor.clasificar_proyecto(resultado_gis_sin_impactos, datos_proyecto_basico)
        alertas = sistema_alertas.generar_alertas(resultado_gis_sin_impactos, datos_proyecto_basico)

        assert clasificacion.via_ingreso == ViaIngreso.DIA
        # El proyecto limpio puede tener pocas o ninguna alerta crítica
        alertas_criticas = [a for a in alertas if a.nivel == NivelAlerta.CRITICA]
        assert len(alertas_criticas) == 0

    def test_flujo_completo_proyecto_critico(self, resultado_gis_con_glaciar, datos_proyecto_grande):
        """Test flujo completo para proyecto con impactos críticos."""
        motor = MotorReglasSSEIA()
        sistema_alertas = SistemaAlertas()

        clasificacion = motor.clasificar_proyecto(resultado_gis_con_glaciar, datos_proyecto_grande)
        alertas = sistema_alertas.generar_alertas(resultado_gis_con_glaciar, datos_proyecto_grande)

        assert clasificacion.via_ingreso == ViaIngreso.EIA
        assert clasificacion.confianza >= 0.9

        # Debe haber alertas críticas
        alertas_criticas = [a for a in alertas if a.nivel == NivelAlerta.CRITICA]
        assert len(alertas_criticas) >= 1

    def test_consistencia_triggers_alertas(self, resultado_gis_con_area_protegida, datos_proyecto_basico):
        """Test que triggers y alertas son consistentes."""
        motor = MotorReglasSSEIA()
        sistema_alertas = SistemaAlertas()

        clasificacion = motor.clasificar_proyecto(resultado_gis_con_area_protegida, datos_proyecto_basico)
        alertas = sistema_alertas.generar_alertas(resultado_gis_con_area_protegida, datos_proyecto_basico)

        # Si hay trigger crítico, debe haber alerta crítica relacionada
        triggers_criticos = [t for t in clasificacion.triggers if t.severidad == SeveridadTrigger.CRITICA]
        alertas_criticas = [a for a in alertas if a.nivel == NivelAlerta.CRITICA]

        if triggers_criticos:
            assert len(alertas_criticas) >= 1
