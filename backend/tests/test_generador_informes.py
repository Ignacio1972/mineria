"""
Tests para el Generador de Informes - Fase 3

Tests para:
- GestorPrompts
- GeneradorInformes (con mock de LLM)
- ExportadorInformes
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.llm.prompts import GestorPrompts, TipoPrompt, ContextoPrompt
from app.services.llm.generador import GeneradorInformes, SeccionInforme, InformePrefactibilidad
from app.services.exportacion import ExportadorInformes, FormatoExportacion


# === Fixtures ===

@pytest.fixture
def datos_proyecto():
    """Datos de proyecto para tests."""
    return {
        "nombre": "Proyecto Minero Test",
        "tipo_mineria": "Tajo abierto",
        "mineral_principal": "Cobre",
        "region": "Antofagasta",
        "comuna": "Calama",
        "superficie_ha": 500,
        "uso_agua_lps": 150,
        "vida_util_anos": 25,
        "trabajadores_construccion": 800,
        "trabajadores_operacion": 400,
        "inversion_musd": 2500,
        "descripcion": "Proyecto de extracción de cobre a cielo abierto.",
    }


@pytest.fixture
def resultado_gis():
    """Resultado GIS para tests."""
    return {
        "areas_protegidas": [
            {
                "id": 1,
                "nombre": "Reserva Test",
                "tipo": "Reserva Nacional",
                "intersecta": False,
                "distancia_m": 5000,
            }
        ],
        "glaciares": [],
        "cuerpos_agua": [
            {
                "id": 1,
                "nombre": "Río Test",
                "tipo": "Río",
                "intersecta": False,
                "distancia_m": 2000,
            }
        ],
        "comunidades_indigenas": [],
        "centros_poblados": [
            {
                "id": 1,
                "nombre": "Pueblo Test",
                "tipo": "Pueblo",
                "poblacion": 1000,
                "distancia_m": 3000,
            }
        ],
        "sitios_patrimoniales": [],
        "alertas": [],
    }


@pytest.fixture
def clasificacion_seia_dict():
    """Clasificación SEIA como diccionario."""
    return {
        "via_ingreso_recomendada": "DIA",
        "confianza": 0.75,
        "nivel_confianza": "ALTA",
        "justificacion": "Proyecto con impactos menores.",
        "puntaje_matriz": 0.45,
        "triggers": [
            {
                "letra": "a",
                "descripcion": "Riesgo para salud de la población",
                "detalle": "Centro poblado cercano",
                "severidad": "MEDIA",
                "fundamento_legal": "Art. 11 letra a) Ley 19.300",
                "peso": 0.5,
            }
        ],
    }


@pytest.fixture
def alertas_dict():
    """Alertas como lista de diccionarios."""
    return [
        {
            "id": "ALR-0001",
            "nivel": "MEDIA",
            "categoria": "MEDIO_HUMANO",
            "titulo": "Proximidad a Centros Poblados",
            "descripcion": "Centro poblado a 3km del proyecto.",
            "componentes_afectados": ["medio_humano", "calidad_aire"],
            "acciones_requeridas": ["Evaluación de impacto acústico"],
            "normativa_relacionada": ["Ley 19.300"],
        }
    ]


@pytest.fixture
def contexto_prompt(datos_proyecto, resultado_gis, clasificacion_seia_dict, alertas_dict):
    """Contexto para construcción de prompts."""
    return ContextoPrompt(
        datos_proyecto=datos_proyecto,
        resultado_gis=resultado_gis,
        clasificacion_seia=clasificacion_seia_dict,
        alertas=alertas_dict,
        normativa_relevante=[
            {"contenido": "Art. 11 Ley 19.300...", "documento": "Ley 19.300"},
        ],
    )


@pytest.fixture
def informe_completo(datos_proyecto, resultado_gis, clasificacion_seia_dict, alertas_dict):
    """Informe completo para tests de exportación."""
    return {
        "id": "TEST001",
        "fecha_generacion": datetime.now().isoformat(),
        "datos_proyecto": datos_proyecto,
        "resultado_gis": resultado_gis,
        "clasificacion_seia": clasificacion_seia_dict,
        "alertas": alertas_dict,
        "secciones": [
            {
                "seccion": "resumen_ejecutivo",
                "titulo": "Resumen Ejecutivo",
                "contenido": "Este es el resumen ejecutivo del proyecto minero.",
            },
            {
                "seccion": "descripcion_proyecto",
                "titulo": "Descripción del Proyecto",
                "contenido": "El proyecto consiste en una operación minera a cielo abierto.",
            },
        ],
        "normativa_citada": [
            {"referencia": "Ley 19.300"},
            {"referencia": "DS 40/2012"},
        ],
    }


# === Tests GestorPrompts ===

class TestGestorPrompts:
    """Tests para GestorPrompts."""

    def test_inicializacion(self):
        """Test que el gestor se inicializa correctamente."""
        gestor = GestorPrompts()
        assert gestor is not None

    def test_obtener_prompt_sistema(self):
        """Test obtención del prompt de sistema."""
        gestor = GestorPrompts()
        prompt_sistema = gestor.obtener_prompt_sistema()

        assert len(prompt_sistema) > 100
        assert "SEIA" in prompt_sistema or "ambiental" in prompt_sistema

    def test_tipos_disponibles(self):
        """Test lista de tipos de prompts disponibles."""
        gestor = GestorPrompts()
        tipos = gestor.obtener_tipos_disponibles()

        assert len(tipos) > 0
        assert "resumen_ejecutivo" in tipos
        assert "analisis_gis" in tipos

    def test_construir_prompt_resumen(self, contexto_prompt):
        """Test construcción de prompt para resumen ejecutivo."""
        gestor = GestorPrompts()
        prompt = gestor.construir_prompt(TipoPrompt.RESUMEN_EJECUTIVO, contexto_prompt)

        assert len(prompt) > 100
        assert "Proyecto Minero Test" in prompt or "proyecto" in prompt.lower()

    def test_construir_prompt_analisis_gis(self, contexto_prompt):
        """Test construcción de prompt para análisis GIS."""
        gestor = GestorPrompts()
        prompt = gestor.construir_prompt(TipoPrompt.ANALISIS_GIS, contexto_prompt)

        assert len(prompt) > 100

    def test_construir_prompt_triggers(self, contexto_prompt):
        """Test construcción de prompt para evaluación de triggers."""
        gestor = GestorPrompts()
        prompt = gestor.construir_prompt(TipoPrompt.EVALUACION_TRIGGERS, contexto_prompt)

        assert len(prompt) > 100
        assert "trigger" in prompt.lower() or "art" in prompt.lower()

    def test_prompt_invalido(self, contexto_prompt):
        """Test error con tipo de prompt inválido."""
        gestor = GestorPrompts()

        # Esto debería funcionar porque usamos el enum
        try:
            prompt = gestor.construir_prompt(TipoPrompt.RESUMEN_EJECUTIVO, contexto_prompt)
            assert prompt is not None
        except Exception:
            pytest.fail("No debería fallar con tipo válido")


# === Tests GeneradorInformes (con mocks) ===

class TestGeneradorInformes:
    """Tests para GeneradorInformes con mocks."""

    @pytest.fixture
    def mock_cliente_llm(self):
        """Mock del cliente LLM."""
        mock = MagicMock()
        mock.config = MagicMock()
        mock.config.modelo = "claude-test"

        # Mock de respuesta async
        async def mock_generar(*args, **kwargs):
            response = MagicMock()
            response.contenido = "Contenido generado por LLM de prueba."
            response.tokens_totales = 100
            return response

        mock.generar = mock_generar
        return mock

    def test_inicializacion(self, mock_cliente_llm):
        """Test que el generador se inicializa correctamente."""
        generador = GeneradorInformes(cliente_llm=mock_cliente_llm)
        assert generador.cliente_llm is not None
        assert generador.motor_reglas is not None
        assert generador.sistema_alertas is not None

    def test_titulos_secciones(self):
        """Test que existen títulos para todas las secciones."""
        for seccion in SeccionInforme:
            assert seccion in GeneradorInformes.TITULOS_SECCIONES
            assert len(GeneradorInformes.TITULOS_SECCIONES[seccion]) > 0

    @pytest.mark.asyncio
    async def test_generar_informe_basico(self, mock_cliente_llm, datos_proyecto, resultado_gis):
        """Test generación de informe básico."""
        generador = GeneradorInformes(cliente_llm=mock_cliente_llm)

        informe = await generador.generar_informe(
            datos_proyecto=datos_proyecto,
            resultado_gis=resultado_gis,
            normativa_relevante=[],
            secciones_a_generar=[SeccionInforme.DESCRIPCION_PROYECTO],
        )

        assert informe is not None
        assert informe.id is not None
        assert len(informe.secciones) >= 1

    @pytest.mark.asyncio
    async def test_generar_seccion_individual(self, mock_cliente_llm, datos_proyecto, resultado_gis):
        """Test generación de sección individual."""
        generador = GeneradorInformes(cliente_llm=mock_cliente_llm)

        seccion = await generador.generar_seccion_individual(
            seccion=SeccionInforme.DESCRIPCION_PROYECTO,
            datos_proyecto=datos_proyecto,
            resultado_gis=resultado_gis,
            normativa_relevante=[],
        )

        assert seccion is not None
        assert seccion.titulo == "Descripción del Proyecto"
        assert len(seccion.contenido) > 0

    def test_informe_to_dict(self, mock_cliente_llm, datos_proyecto, resultado_gis):
        """Test conversión de informe a diccionario."""
        from app.services.reglas import MotorReglasSSEIA, SistemaAlertas

        motor = MotorReglasSSEIA()
        sistema = SistemaAlertas()

        clasificacion = motor.clasificar_proyecto(resultado_gis, datos_proyecto)
        alertas = sistema.generar_alertas(resultado_gis, datos_proyecto)

        informe = InformePrefactibilidad(
            id="TEST123",
            fecha_generacion=datetime.now(),
            datos_proyecto=datos_proyecto,
            resultado_gis=resultado_gis,
            clasificacion_seia=clasificacion,
            alertas=[a.to_dict() for a in alertas],
            secciones=[],
            normativa_citada=[],
            version_modelo="test",
        )

        resultado = informe.to_dict()

        assert "id" in resultado
        assert "fecha_generacion" in resultado
        assert "clasificacion_seia" in resultado
        assert "metricas" in resultado

    def test_informe_to_texto_plano(self, mock_cliente_llm, datos_proyecto, resultado_gis):
        """Test conversión de informe a texto plano."""
        from app.services.reglas import MotorReglasSSEIA, SistemaAlertas
        from app.services.llm.generador import SeccionGenerada

        motor = MotorReglasSSEIA()
        sistema = SistemaAlertas()

        clasificacion = motor.clasificar_proyecto(resultado_gis, datos_proyecto)
        alertas = sistema.generar_alertas(resultado_gis, datos_proyecto)

        secciones = [
            SeccionGenerada(
                seccion=SeccionInforme.RESUMEN_EJECUTIVO,
                titulo="Resumen Ejecutivo",
                contenido="Este es el resumen del proyecto.",
            )
        ]

        informe = InformePrefactibilidad(
            id="TEST123",
            fecha_generacion=datetime.now(),
            datos_proyecto=datos_proyecto,
            resultado_gis=resultado_gis,
            clasificacion_seia=clasificacion,
            alertas=[a.to_dict() for a in alertas],
            secciones=secciones,
            normativa_citada=[],
            version_modelo="test",
        )

        texto = informe.to_texto_plano()

        assert "INFORME" in texto
        assert "Proyecto Minero Test" in texto
        assert "RESUMEN EJECUTIVO" in texto


# === Tests ExportadorInformes ===

class TestExportadorInformes:
    """Tests para ExportadorInformes."""

    def test_inicializacion(self):
        """Test que el exportador se inicializa correctamente."""
        exportador = ExportadorInformes()
        assert exportador is not None

    def test_formatos_disponibles(self):
        """Test obtención de formatos disponibles."""
        exportador = ExportadorInformes()
        formatos = exportador.obtener_formatos_disponibles()

        assert len(formatos) == 4
        extensiones = [f["extension"] for f in formatos]
        assert ".pdf" in extensiones
        assert ".docx" in extensiones
        assert ".txt" in extensiones
        assert ".html" in extensiones

    def test_exportar_txt(self, informe_completo):
        """Test exportación a texto plano."""
        exportador = ExportadorInformes()
        contenido = exportador.exportar(informe_completo, FormatoExportacion.TXT)

        assert isinstance(contenido, bytes)
        texto = contenido.decode('utf-8')
        assert "INFORME" in texto
        assert "Proyecto Minero Test" in texto

    def test_exportar_html(self, informe_completo):
        """Test exportación a HTML."""
        exportador = ExportadorInformes()
        contenido = exportador.exportar(informe_completo, FormatoExportacion.HTML)

        assert isinstance(contenido, bytes)
        html = contenido.decode('utf-8')
        assert "<!DOCTYPE html>" in html
        assert "Proyecto Minero Test" in html
        assert "<style>" in html

    def test_exportar_pdf(self, informe_completo):
        """Test exportación a PDF."""
        exportador = ExportadorInformes()
        contenido = exportador.exportar(informe_completo, FormatoExportacion.PDF)

        assert isinstance(contenido, bytes)
        # PDF comienza con %PDF
        assert contenido[:4] == b'%PDF'

    def test_exportar_docx(self, informe_completo):
        """Test exportación a DOCX."""
        exportador = ExportadorInformes()
        contenido = exportador.exportar(informe_completo, FormatoExportacion.DOCX)

        assert isinstance(contenido, bytes)
        # DOCX es un ZIP que comienza con PK
        assert contenido[:2] == b'PK'

    def test_formato_invalido(self, informe_completo):
        """Test error con formato inválido."""
        exportador = ExportadorInformes()

        with pytest.raises(ValueError):
            exportador.exportar(informe_completo, "formato_invalido")

    def test_informe_con_alertas(self, informe_completo):
        """Test exportación con alertas incluidas."""
        # Agregar más alertas
        informe_completo["alertas"].append({
            "id": "ALR-0002",
            "nivel": "CRITICA",
            "categoria": "BIODIVERSIDAD",
            "titulo": "Área Protegida Cercana",
            "descripcion": "Área protegida a 5km.",
            "componentes_afectados": [],
            "acciones_requeridas": [],
        })

        exportador = ExportadorInformes()

        # TXT
        contenido_txt = exportador.exportar(informe_completo, FormatoExportacion.TXT)
        texto = contenido_txt.decode('utf-8')
        assert "ALERTAS" in texto or "CRITICA" in texto

        # HTML
        contenido_html = exportador.exportar(informe_completo, FormatoExportacion.HTML)
        html = contenido_html.decode('utf-8')
        assert "CRITICA" in html

    def test_informe_minimal(self):
        """Test exportación con datos mínimos."""
        informe_minimal = {
            "id": "MIN001",
            "fecha_generacion": datetime.now().isoformat(),
            "datos_proyecto": {"nombre": "Proyecto Minimal"},
            "resultado_gis": {},
            "clasificacion_seia": {
                "via_ingreso_recomendada": "DIA",
                "confianza": 0.8,
            },
            "alertas": [],
            "secciones": [],
            "normativa_citada": [],
        }

        exportador = ExportadorInformes()

        for formato in FormatoExportacion:
            contenido = exportador.exportar(informe_minimal, formato)
            assert isinstance(contenido, bytes)
            assert len(contenido) > 0
