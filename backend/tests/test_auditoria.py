"""
Tests para Auditoria de Analisis - Sistema de Prefactibilidad Ambiental Minera.

Tests unitarios para verificar:
- Creacion automatica de registros de auditoria
- Inmutabilidad de registros (sin UPDATE/DELETE)
- Contenido completo de auditoria (capas GIS, normativa, checksums)
- Endpoint GET de auditoria
"""

import pytest
import hashlib
import json
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.db.models.auditoria import AuditoriaAnalisis
from app.schemas.auditoria import (
    AuditoriaAnalisisCreate,
    AuditoriaAnalisisResponse,
    CapaGISUsada,
    NormativaCitada,
    MetricasEjecucion,
)


# === Fixtures ===

@pytest.fixture
def sample_capas_gis():
    """Capas GIS de ejemplo para auditoria."""
    return [
        {
            "nombre": "areas_protegidas",
            "fecha": "2025-01-15",
            "version": "v2024.2",
            "elementos_encontrados": 3
        },
        {
            "nombre": "glaciares",
            "fecha": "2025-01-10",
            "version": "v2024.1",
            "elementos_encontrados": 0
        },
        {
            "nombre": "comunidades_indigenas",
            "fecha": "2025-01-12",
            "version": "v2024.3",
            "elementos_encontrados": 2
        }
    ]


@pytest.fixture
def sample_normativa_citada():
    """Normativa citada de ejemplo."""
    return [
        {
            "tipo": "Ley",
            "numero": "19300",
            "articulo": "11",
            "letra": "d",
            "descripcion": "Areas protegidas y recursos naturales"
        },
        {
            "tipo": "DS",
            "numero": "40",
            "articulo": "3",
            "letra": None,
            "descripcion": "Reglamento SEIA"
        }
    ]


@pytest.fixture
def sample_proyecto_data():
    """Datos de proyecto para calcular checksum."""
    return {
        "id": 1,
        "nombre": "Proyecto Test Auditoria",
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
        "mineral_principal": "Cobre",
        "superficie_ha": 500
    }


@pytest.fixture
def sample_auditoria():
    """Registro de auditoria de ejemplo."""
    return AuditoriaAnalisis(
        id=uuid4(),
        analisis_id=1,
        capas_gis_usadas=[
            {"nombre": "areas_protegidas", "fecha": "2025-01-15", "version": "v2024.2"}
        ],
        documentos_referenciados=[],
        normativa_citada=[
            {"tipo": "Ley", "numero": "19300", "articulo": "11", "letra": "d"}
        ],
        checksum_datos_entrada="abc123def456",
        version_modelo_llm="claude-sonnet-4-20250514",
        version_sistema="1.0.0",
        tiempo_gis_ms=1500,
        tiempo_rag_ms=800,
        tiempo_llm_ms=5000,
        tokens_usados=2500,
        created_at=datetime.utcnow()
    )


def _calcular_checksum_test(datos: dict) -> str:
    """Calcula checksum SHA-256 de datos de entrada."""
    datos_str = json.dumps(datos, sort_keys=True, default=str)
    return hashlib.sha256(datos_str.encode()).hexdigest()


# === Tests de Creacion de Auditoria ===

class TestCreacionAuditoria:
    """Tests para la creacion automatica de registros de auditoria."""

    def test_auditoria_model_tiene_campos_requeridos(self):
        """Verificar que el modelo tiene todos los campos necesarios."""
        auditoria = AuditoriaAnalisis(
            analisis_id=1,
            capas_gis_usadas=[],
            normativa_citada=[],
            checksum_datos_entrada="test_checksum"
        )

        assert hasattr(auditoria, 'id')
        assert hasattr(auditoria, 'analisis_id')
        assert hasattr(auditoria, 'capas_gis_usadas')
        assert hasattr(auditoria, 'documentos_referenciados')
        assert hasattr(auditoria, 'normativa_citada')
        assert hasattr(auditoria, 'checksum_datos_entrada')
        assert hasattr(auditoria, 'version_modelo_llm')
        assert hasattr(auditoria, 'version_sistema')
        assert hasattr(auditoria, 'tiempo_gis_ms')
        assert hasattr(auditoria, 'tiempo_rag_ms')
        assert hasattr(auditoria, 'tiempo_llm_ms')
        assert hasattr(auditoria, 'tokens_usados')
        assert hasattr(auditoria, 'created_at')

    def test_auditoria_schema_create_valido(self, sample_capas_gis, sample_normativa_citada):
        """Verificar que el schema de creacion valida correctamente."""
        capas = [CapaGISUsada(**c) for c in sample_capas_gis]
        normativa = [NormativaCitada(**n) for n in sample_normativa_citada]

        auditoria_data = AuditoriaAnalisisCreate(
            analisis_id=1,
            capas_gis_usadas=capas,
            normativa_citada=normativa,
            checksum_datos_entrada="abc123def456",
            version_modelo_llm="claude-sonnet-4-20250514",
            version_sistema="1.0.0",
            tiempo_gis_ms=1500,
            tiempo_rag_ms=800,
            tiempo_llm_ms=5000,
            tokens_usados=2500
        )

        assert auditoria_data.analisis_id == 1
        assert len(auditoria_data.capas_gis_usadas) == 3
        assert len(auditoria_data.normativa_citada) == 2

    def test_checksum_es_deterministico(self, sample_proyecto_data):
        """Verificar que el checksum es determinsitico para los mismos datos."""
        checksum1 = _calcular_checksum_test(sample_proyecto_data)
        checksum2 = _calcular_checksum_test(sample_proyecto_data)

        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 produce 64 caracteres hex

    def test_checksum_cambia_con_datos_diferentes(self, sample_proyecto_data):
        """Verificar que el checksum cambia cuando cambian los datos."""
        checksum1 = _calcular_checksum_test(sample_proyecto_data)

        datos_modificados = sample_proyecto_data.copy()
        datos_modificados["nombre"] = "Proyecto Modificado"

        checksum2 = _calcular_checksum_test(datos_modificados)

        assert checksum1 != checksum2


# === Tests de Contenido de Auditoria ===

class TestContenidoAuditoria:
    """Tests para verificar que la auditoria contiene la informacion correcta."""

    def test_auditoria_contiene_capas_gis(self, sample_auditoria):
        """Verificar que auditoria registra capas GIS consultadas."""
        assert len(sample_auditoria.capas_gis_usadas) > 0
        assert all("nombre" in capa for capa in sample_auditoria.capas_gis_usadas)

    def test_auditoria_capas_gis_tienen_metadata(self, sample_capas_gis):
        """Verificar que las capas GIS tienen fecha y version."""
        for capa in sample_capas_gis:
            assert "nombre" in capa
            assert "fecha" in capa
            assert "version" in capa or capa.get("version") is None

    def test_auditoria_contiene_normativa_citada(self, sample_auditoria):
        """Verificar que auditoria registra normativa citada."""
        assert len(sample_auditoria.normativa_citada) > 0

        for norma in sample_auditoria.normativa_citada:
            assert "tipo" in norma
            assert "numero" in norma

    def test_auditoria_normativa_estructura_correcta(self, sample_normativa_citada):
        """Verificar estructura de normativa citada."""
        for norma in sample_normativa_citada:
            schema = NormativaCitada(**norma)
            assert schema.tipo in ["Ley", "DS", "Reglamento", "Guia"]
            assert schema.numero is not None

    def test_auditoria_contiene_checksum(self, sample_auditoria):
        """Verificar que auditoria tiene checksum de datos de entrada."""
        assert sample_auditoria.checksum_datos_entrada is not None
        assert len(sample_auditoria.checksum_datos_entrada) > 0

    def test_auditoria_contiene_version_sistema(self, sample_auditoria):
        """Verificar que auditoria registra version del sistema."""
        assert sample_auditoria.version_sistema is not None

    def test_auditoria_contiene_metricas_ejecucion(self, sample_auditoria):
        """Verificar que auditoria registra metricas de ejecucion."""
        assert sample_auditoria.tiempo_gis_ms is not None
        assert sample_auditoria.tiempo_gis_ms > 0

    def test_metricas_ejecucion_schema(self):
        """Verificar schema de metricas de ejecucion."""
        metricas = MetricasEjecucion(
            tiempo_gis_ms=1500,
            tiempo_rag_ms=800,
            tiempo_llm_ms=5000,
            tiempo_total_ms=7300,
            tokens_usados=2500
        )

        assert metricas.tiempo_gis_ms == 1500
        assert metricas.tiempo_total_ms == 7300


# === Tests de Inmutabilidad ===

class TestAuditoriaInmutable:
    """Tests para verificar que la auditoria es inmutable."""

    def test_no_existe_endpoint_update_auditoria(self):
        """Verificar que no existe endpoint PUT/PATCH para auditoria."""
        from app.api.v1.endpoints import prefactibilidad
        import inspect

        # Obtener todos los metodos del modulo
        metodos = inspect.getmembers(prefactibilidad, inspect.isfunction)
        nombres_metodos = [nombre for nombre, _ in metodos]

        # Verificar que no hay metodos de update
        metodos_update = [
            m for m in nombres_metodos
            if ('update' in m.lower() or 'actualizar' in m.lower())
            and 'auditoria' in m.lower()
        ]

        assert len(metodos_update) == 0, \
            f"Se encontraron endpoints de update para auditoria: {metodos_update}"

    def test_no_existe_endpoint_delete_auditoria(self):
        """Verificar que no existe endpoint DELETE para auditoria."""
        from app.api.v1.endpoints import prefactibilidad
        import inspect

        metodos = inspect.getmembers(prefactibilidad, inspect.isfunction)
        nombres_metodos = [nombre for nombre, _ in metodos]

        metodos_delete = [
            m for m in nombres_metodos
            if ('delete' in m.lower() or 'eliminar' in m.lower() or 'borrar' in m.lower())
            and 'auditoria' in m.lower()
        ]

        assert len(metodos_delete) == 0, \
            f"Se encontraron endpoints de delete para auditoria: {metodos_delete}"

    def test_auditoria_solo_tiene_get(self):
        """Verificar que solo existe endpoint GET para auditoria."""
        from app.api.v1.endpoints import prefactibilidad
        import inspect

        metodos = inspect.getmembers(prefactibilidad, inspect.isfunction)
        metodos_auditoria = [
            nombre for nombre, _ in metodos
            if 'auditoria' in nombre.lower()
        ]

        # Solo debe existir 'obtener_auditoria_analisis'
        assert len(metodos_auditoria) == 1
        assert 'obtener' in metodos_auditoria[0].lower()


# === Tests de Endpoint GET ===

class TestEndpointGetAuditoria:
    """Tests para el endpoint GET de auditoria."""

    def test_auditoria_response_schema_valido(self, sample_auditoria):
        """Verificar que el schema de respuesta es valido."""
        response = AuditoriaAnalisisResponse(
            id=sample_auditoria.id,
            analisis_id=sample_auditoria.analisis_id,
            capas_gis_usadas=sample_auditoria.capas_gis_usadas,
            documentos_referenciados=sample_auditoria.documentos_referenciados or [],
            normativa_citada=sample_auditoria.normativa_citada,
            checksum_datos_entrada=sample_auditoria.checksum_datos_entrada,
            version_modelo_llm=sample_auditoria.version_modelo_llm,
            version_sistema=sample_auditoria.version_sistema,
            tiempo_gis_ms=sample_auditoria.tiempo_gis_ms,
            tiempo_rag_ms=sample_auditoria.tiempo_rag_ms,
            tiempo_llm_ms=sample_auditoria.tiempo_llm_ms,
            tokens_usados=sample_auditoria.tokens_usados,
            created_at=sample_auditoria.created_at
        )

        assert response.id == sample_auditoria.id
        assert response.analisis_id == sample_auditoria.analisis_id
        assert response.checksum_datos_entrada == sample_auditoria.checksum_datos_entrada

    @pytest.mark.asyncio
    async def test_get_auditoria_por_analisis_id(self, mock_db, sample_auditoria):
        """Test del endpoint GET /analisis/{id}/auditoria."""
        from app.api.v1.endpoints.prefactibilidad import obtener_auditoria_analisis

        # Configurar mock de resultado de base de datos
        mock_result = MagicMock()
        mock_result.scalar.return_value = sample_auditoria
        mock_db.execute.return_value = mock_result

        # Ejecutar endpoint
        response = await obtener_auditoria_analisis(
            analisis_id=1,
            db=mock_db
        )

        assert response.id == sample_auditoria.id
        assert response.analisis_id == sample_auditoria.analisis_id
        assert len(response.capas_gis_usadas) > 0

    @pytest.mark.asyncio
    async def test_get_auditoria_no_encontrada_retorna_404(self, mock_db):
        """Test que retorna 404 cuando no existe auditoria."""
        from app.api.v1.endpoints.prefactibilidad import obtener_auditoria_analisis
        from fastapi import HTTPException

        # Configurar mock para retornar None
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await obtener_auditoria_analisis(analisis_id=999, db=mock_db)

        assert exc_info.value.status_code == 404


# === Tests de Trazabilidad ===

class TestTrazabilidadAuditoria:
    """Tests para verificar trazabilidad completa."""

    def test_auditoria_incluye_version_llm(self, sample_auditoria):
        """Verificar que se registra version del modelo LLM."""
        assert sample_auditoria.version_modelo_llm is not None
        assert "claude" in sample_auditoria.version_modelo_llm.lower()

    def test_auditoria_timestamp_creacion(self, sample_auditoria):
        """Verificar que se registra timestamp de creacion."""
        assert sample_auditoria.created_at is not None
        assert isinstance(sample_auditoria.created_at, datetime)

    def test_auditoria_tokens_usados(self, sample_auditoria):
        """Verificar que se registran tokens consumidos."""
        # Solo para analisis completos (con LLM)
        if sample_auditoria.version_modelo_llm:
            assert sample_auditoria.tokens_usados is not None
            assert sample_auditoria.tokens_usados > 0

    def test_auditoria_tiempos_coherentes(self, sample_auditoria):
        """Verificar que los tiempos de ejecucion son coherentes."""
        tiempos = [
            sample_auditoria.tiempo_gis_ms or 0,
            sample_auditoria.tiempo_rag_ms or 0,
            sample_auditoria.tiempo_llm_ms or 0
        ]

        # Todos los tiempos deben ser no negativos
        assert all(t >= 0 for t in tiempos)

        # GIS siempre debe tener tiempo (es obligatorio)
        assert sample_auditoria.tiempo_gis_ms > 0


# === Tests de Integracion ===

class TestIntegracionAuditoria:
    """Tests de integracion del sistema de auditoria."""

    def test_capa_gis_usada_schema_completo(self):
        """Test del schema CapaGISUsada con todos los campos."""
        capa = CapaGISUsada(
            nombre="areas_protegidas",
            fecha="2025-01-15",
            version="v2024.2",
            elementos_encontrados=5
        )

        assert capa.nombre == "areas_protegidas"
        assert capa.elementos_encontrados == 5

    def test_normativa_citada_schema_art11(self):
        """Test del schema NormativaCitada para Art. 11."""
        norma = NormativaCitada(
            tipo="Ley",
            numero="19300",
            articulo="11",
            letra="d",
            descripcion="Localizacion en o proxima a areas protegidas"
        )

        assert norma.tipo == "Ley"
        assert norma.numero == "19300"
        assert norma.articulo == "11"
        assert norma.letra == "d"

    def test_flujo_completo_auditoria(self, sample_proyecto_data, sample_capas_gis, sample_normativa_citada):
        """Test del flujo completo de creacion de auditoria."""
        # 1. Calcular checksum
        checksum = _calcular_checksum_test(sample_proyecto_data)

        # 2. Crear schema de capas
        capas = [CapaGISUsada(**c) for c in sample_capas_gis]

        # 3. Crear schema de normativa
        normativa = [NormativaCitada(**n) for n in sample_normativa_citada]

        # 4. Crear schema de auditoria
        auditoria_create = AuditoriaAnalisisCreate(
            analisis_id=1,
            capas_gis_usadas=capas,
            normativa_citada=normativa,
            checksum_datos_entrada=checksum,
            version_modelo_llm="claude-sonnet-4-20250514",
            version_sistema="1.0.0",
            tiempo_gis_ms=1500,
            tiempo_rag_ms=800,
            tiempo_llm_ms=5000,
            tokens_usados=2500
        )

        # 5. Verificar integridad
        assert auditoria_create.checksum_datos_entrada == checksum
        assert len(auditoria_create.capas_gis_usadas) == 3
        assert len(auditoria_create.normativa_citada) == 2
        assert auditoria_create.tiempo_gis_ms == 1500

    def test_auditoria_para_analisis_rapido(self):
        """Test de auditoria para analisis rapido (sin LLM)."""
        auditoria = AuditoriaAnalisis(
            analisis_id=1,
            capas_gis_usadas=[
                {"nombre": "areas_protegidas", "fecha": "2025-01-15"}
            ],
            normativa_citada=[],
            checksum_datos_entrada="test_checksum",
            version_modelo_llm=None,  # Sin LLM
            version_sistema="1.0.0",
            tiempo_gis_ms=500,
            tiempo_rag_ms=0,
            tiempo_llm_ms=None,  # Sin LLM
            tokens_usados=None  # Sin LLM
        )

        assert auditoria.version_modelo_llm is None
        assert auditoria.tiempo_llm_ms is None
        assert auditoria.tokens_usados is None
        assert auditoria.tiempo_gis_ms > 0

    def test_auditoria_para_analisis_completo(self):
        """Test de auditoria para analisis completo (con LLM)."""
        auditoria = AuditoriaAnalisis(
            analisis_id=1,
            capas_gis_usadas=[
                {"nombre": "areas_protegidas", "fecha": "2025-01-15"}
            ],
            normativa_citada=[
                {"tipo": "Ley", "numero": "19300", "articulo": "11"}
            ],
            checksum_datos_entrada="test_checksum",
            version_modelo_llm="claude-sonnet-4-20250514",
            version_sistema="1.0.0",
            tiempo_gis_ms=1500,
            tiempo_rag_ms=800,
            tiempo_llm_ms=5000,
            tokens_usados=2500
        )

        assert auditoria.version_modelo_llm is not None
        assert auditoria.tiempo_llm_ms is not None
        assert auditoria.tiempo_llm_ms > 0
        assert auditoria.tokens_usados is not None
        assert auditoria.tokens_usados > 0
