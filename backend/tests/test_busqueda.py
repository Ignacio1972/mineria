"""
Tests para el buscador semántico legal.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.rag.busqueda import BuscadorLegal, ResultadoBusqueda


class TestBuscadorLegal:
    """Tests del buscador semántico."""

    @pytest.fixture
    def buscador(self, mock_embedding_service):
        """Fixture del buscador con mock de embeddings."""
        with patch('app.services.rag.busqueda.get_embedding_service', return_value=mock_embedding_service):
            return BuscadorLegal()

    @pytest.mark.asyncio
    async def test_buscar_returns_empty_list_when_no_results(self, buscador, mock_db):
        """Test búsqueda sin resultados."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        resultados = await buscador.buscar(mock_db, "consulta sin resultados")

        assert resultados == []

    @pytest.mark.asyncio
    async def test_buscar_filters_by_umbral_similitud(self, buscador, mock_db):
        """Test que filtra por umbral de similitud."""
        mock_row = MagicMock()
        mock_row.fragmento_id = 1
        mock_row.documento_id = 1
        mock_row.documento_titulo = "Test"
        mock_row.documento_tipo = "Ley"
        mock_row.seccion = "Art. 1"
        mock_row.contenido = "Contenido test"
        mock_row.temas = ["agua"]
        mock_row.similitud = 0.2  # Menor que umbral default 0.3

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute.return_value = mock_result

        resultados = await buscador.buscar(mock_db, "agua recursos")

        assert len(resultados) == 0  # Filtrado por umbral

    @pytest.mark.asyncio
    async def test_buscar_includes_results_above_umbral(self, buscador, mock_db):
        """Test que incluye resultados sobre el umbral."""
        mock_row = MagicMock()
        mock_row.fragmento_id = 1
        mock_row.documento_id = 1
        mock_row.documento_titulo = "Ley 19.300"
        mock_row.documento_tipo = "Ley"
        mock_row.seccion = "Artículo 11"
        mock_row.contenido = "Contenido sobre medio ambiente"
        mock_row.temas = ["eia", "agua"]
        mock_row.similitud = 0.85

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute.return_value = mock_result

        resultados = await buscador.buscar(mock_db, "evaluación impacto ambiental")

        assert len(resultados) == 1
        assert resultados[0].documento_titulo == "Ley 19.300"
        assert resultados[0].similitud == 0.85

    @pytest.mark.asyncio
    async def test_buscar_with_tipo_filter(self, buscador, mock_db):
        """Test búsqueda con filtro por tipo."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        await buscador.buscar(
            mock_db,
            "requisitos minería",
            filtro_tipo="Ley"
        )

        # Verificar que se llamó execute con el filtro
        call_args = mock_db.execute.call_args
        sql = str(call_args[0][0])
        assert "d.tipo = :tipo" in sql

    @pytest.mark.asyncio
    async def test_buscar_with_temas_filter(self, buscador, mock_db):
        """Test búsqueda con filtro por temas."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        await buscador.buscar(
            mock_db,
            "requisitos agua",
            filtro_temas=["agua", "mineria"]
        )

        call_args = mock_db.execute.call_args
        sql = str(call_args[0][0])
        assert "f.temas && :temas" in sql


class TestBuscarPorContextoGIS:
    """Tests de búsqueda por contexto GIS."""

    @pytest.fixture
    def buscador(self, mock_embedding_service):
        """Fixture del buscador."""
        with patch('app.services.rag.busqueda.get_embedding_service', return_value=mock_embedding_service):
            return BuscadorLegal()

    @pytest.mark.asyncio
    async def test_busca_normativa_areas_protegidas(self, buscador, mock_db, sample_resultado_gis):
        """Test que busca normativa cuando hay áreas protegidas."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        resultado = await buscador.buscar_por_contexto_gis(mock_db, sample_resultado_gis)

        assert "areas_protegidas" in resultado
        assert "seia_general" in resultado

    @pytest.mark.asyncio
    async def test_busca_normativa_comunidades_cercanas(self, buscador, mock_db, sample_resultado_gis):
        """Test que busca normativa cuando hay comunidades cercanas."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        resultado = await buscador.buscar_por_contexto_gis(mock_db, sample_resultado_gis)

        assert "comunidades_indigenas" in resultado


class TestObtenerEstadisticas:
    """Tests de estadísticas del corpus."""

    @pytest.fixture
    def buscador(self, mock_embedding_service):
        """Fixture del buscador."""
        with patch('app.services.rag.busqueda.get_embedding_service', return_value=mock_embedding_service):
            return BuscadorLegal()

    @pytest.mark.asyncio
    async def test_obtener_estadisticas_estructura(self, buscador, mock_db):
        """Test que estadísticas tienen estructura correcta."""
        # Mock para las diferentes queries
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=10)),  # total docs
            MagicMock(scalar=MagicMock(return_value=100)),  # total fragmentos
            MagicMock(fetchall=MagicMock(return_value=[])),  # por tipo
            MagicMock(fetchall=MagicMock(return_value=[])),  # temas
        ]

        stats = await buscador.obtener_estadisticas(mock_db)

        assert "total_documentos" in stats
        assert "total_fragmentos" in stats
        assert "documentos_por_tipo" in stats
        assert "temas_mas_comunes" in stats


class TestResultadoBusqueda:
    """Tests del dataclass ResultadoBusqueda."""

    def test_resultado_busqueda_creation(self):
        """Test creación de ResultadoBusqueda."""
        resultado = ResultadoBusqueda(
            fragmento_id=1,
            documento_id=1,
            documento_titulo="Ley 19.300",
            documento_tipo="Ley",
            seccion="Artículo 11",
            contenido="Contenido test",
            temas=["eia", "agua"],
            similitud=0.85
        )

        assert resultado.fragmento_id == 1
        assert resultado.documento_titulo == "Ley 19.300"
        assert resultado.similitud == 0.85
        assert "eia" in resultado.temas
