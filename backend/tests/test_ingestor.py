"""
Tests para el ingestor de documentos legales.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

from app.services.rag.ingestor import IngestorLegal, DocumentoLegal, Fragmento


class TestIngestorLegal:
    """Tests del ingestor de documentos."""

    @pytest.fixture
    def ingestor(self, mock_embedding_service):
        """Fixture del ingestor con mock de embeddings."""
        with patch('app.services.rag.ingestor.get_embedding_service', return_value=mock_embedding_service):
            return IngestorLegal()

    def test_detectar_temas_agua(self, ingestor):
        """Test detección de tema agua."""
        texto = "El proyecto afecta recursos hídricos y el caudal del río."
        temas = ingestor.detectar_temas(texto)

        assert "agua" in temas

    def test_detectar_temas_glaciares(self, ingestor):
        """Test detección de tema glaciares."""
        texto = "Zona de ambiente periglaciar con presencia de permafrost."
        temas = ingestor.detectar_temas(texto)

        assert "glaciares" in temas

    def test_detectar_temas_comunidades_indigenas(self, ingestor):
        """Test detección de tema comunidades indígenas."""
        texto = "Consulta indígena con el pueblo originario atacameño."
        temas = ingestor.detectar_temas(texto)

        assert "comunidades_indigenas" in temas

    def test_detectar_temas_multiples(self, ingestor):
        """Test detección de múltiples temas."""
        texto = "El proyecto minero afecta el río y está cerca de un parque nacional SNASPE."
        temas = ingestor.detectar_temas(texto)

        assert "agua" in temas
        assert "areas_protegidas" in temas
        assert "mineria" in temas

    def test_detectar_temas_sin_keywords(self, ingestor):
        """Test que retorna 'general' cuando no hay keywords."""
        texto = "Este es un texto genérico sin palabras clave específicas."
        temas = ingestor.detectar_temas(texto)

        assert temas == ["general"]

    def test_segmentar_documento_con_articulos(self, ingestor, sample_documento_legal):
        """Test segmentación de documento con artículos."""
        doc = DocumentoLegal(
            titulo="Ley Test",
            tipo="Ley",
            numero="123",
            fecha_publicacion=date(2024, 1, 1),
            organismo="Test",
            contenido=sample_documento_legal
        )

        fragmentos = ingestor.segmentar_documento(doc)

        assert len(fragmentos) >= 1
        assert any("Artículo" in f.seccion for f in fragmentos)

    def test_segmentar_documento_sin_articulos(self, ingestor):
        """Test segmentación de documento sin artículos."""
        contenido = """
        Este es un documento que no tiene artículos formales.
        Contiene información sobre medio ambiente y recursos naturales.
        Se divide en párrafos normales sin numeración legal.
        """

        doc = DocumentoLegal(
            titulo="Guía Test",
            tipo="Guía SEA",
            numero=None,
            fecha_publicacion=None,
            organismo="SEA",
            contenido=contenido
        )

        fragmentos = ingestor.segmentar_documento(doc)

        assert len(fragmentos) >= 1
        assert any("Sección" in f.seccion for f in fragmentos)

    def test_limpiar_texto(self, ingestor):
        """Test limpieza de texto."""
        texto_sucio = "Texto    con   espacios\n\n\n\nmúltiples"
        texto_limpio = ingestor._limpiar_texto(texto_sucio)

        assert "    " not in texto_limpio
        assert "\n\n\n\n" not in texto_limpio

    def test_dividir_en_chunks_texto_corto(self, ingestor):
        """Test que texto corto no se divide."""
        texto = "Texto corto"
        chunks = ingestor._dividir_en_chunks(texto, max_chars=1000)

        assert len(chunks) == 1
        assert chunks[0] == texto

    def test_dividir_en_chunks_texto_largo(self, ingestor):
        """Test división de texto largo."""
        texto = "Esta es una oración. " * 100  # ~2100 caracteres
        chunks = ingestor._dividir_en_chunks(texto, max_chars=500)

        assert len(chunks) > 1
        assert all(len(c) <= 500 for c in chunks)


class TestIngestorLegalAsync:
    """Tests asíncronos del ingestor."""

    @pytest.fixture
    def ingestor(self, mock_embedding_service):
        """Fixture del ingestor."""
        with patch('app.services.rag.ingestor.get_embedding_service', return_value=mock_embedding_service):
            return IngestorLegal()

    @pytest.mark.asyncio
    async def test_ingestar_documento(self, ingestor, mock_db, sample_documento_legal):
        """Test ingestión completa de documento."""
        # Mock del INSERT RETURNING id
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_db.execute.return_value = mock_result

        doc = DocumentoLegal(
            titulo="Ley 19.300",
            tipo="Ley",
            numero="19.300",
            fecha_publicacion=date(1994, 3, 9),
            organismo="Congreso Nacional",
            contenido=sample_documento_legal
        )

        resultado = await ingestor.ingestar_documento(mock_db, doc)

        assert resultado["documento_id"] == 1
        assert resultado["titulo"] == "Ley 19.300"
        assert resultado["fragmentos_creados"] >= 1
        assert isinstance(resultado["temas_detectados"], list)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingestar_documento_detecta_temas(self, ingestor, mock_db):
        """Test que ingestión detecta temas correctamente."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_db.execute.return_value = mock_result

        contenido = """
        Artículo 1°.- Los proyectos mineros que afecten glaciares y recursos hídricos
        deberán someterse a evaluación de impacto ambiental.
        """

        doc = DocumentoLegal(
            titulo="Test",
            tipo="Ley",
            numero="1",
            fecha_publicacion=None,
            organismo="Test",
            contenido=contenido
        )

        resultado = await ingestor.ingestar_documento(mock_db, doc)

        assert "mineria" in resultado["temas_detectados"] or "glaciares" in resultado["temas_detectados"]


class TestDocumentoLegal:
    """Tests del dataclass DocumentoLegal."""

    def test_documento_legal_creation(self):
        """Test creación de DocumentoLegal."""
        doc = DocumentoLegal(
            titulo="Ley 19.300",
            tipo="Ley",
            numero="19.300",
            fecha_publicacion=date(1994, 3, 9),
            organismo="Congreso Nacional",
            contenido="Contenido de la ley",
            url_fuente="https://bcn.cl/ley19300"
        )

        assert doc.titulo == "Ley 19.300"
        assert doc.tipo == "Ley"
        assert doc.fecha_publicacion == date(1994, 3, 9)

    def test_documento_legal_optional_fields(self):
        """Test campos opcionales de DocumentoLegal."""
        doc = DocumentoLegal(
            titulo="Test",
            tipo="Guía SEA",
            numero=None,
            fecha_publicacion=None,
            organismo="SEA",
            contenido="Contenido"
        )

        assert doc.numero is None
        assert doc.fecha_publicacion is None
        assert doc.url_fuente is None


class TestFragmento:
    """Tests del dataclass Fragmento."""

    def test_fragmento_creation(self):
        """Test creación de Fragmento."""
        fragmento = Fragmento(
            seccion="Artículo 11",
            numero_seccion="11",
            contenido="Los proyectos susceptibles de causar impacto...",
            temas=["eia", "seia"]
        )

        assert fragmento.seccion == "Artículo 11"
        assert fragmento.numero_seccion == "11"
        assert "eia" in fragmento.temas
