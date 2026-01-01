"""
Tests para el servicio de embeddings.
"""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np


class TestEmbeddingService:
    """Tests del servicio de embeddings."""

    def test_embed_text_returns_list(self, mock_embedding_service):
        """Test que embed_text retorna una lista de floats."""
        result = mock_embedding_service.embed_text("texto de prueba")

        assert isinstance(result, list)
        assert len(result) == 384  # Dimensión del modelo
        assert all(isinstance(x, (int, float)) for x in result)

    def test_embed_texts_returns_list_of_lists(self, mock_embedding_service):
        """Test que embed_texts retorna lista de embeddings."""
        textos = ["texto 1", "texto 2", "texto 3"]
        mock_embedding_service.embed_texts.return_value = [[0.1] * 384] * 3

        result = mock_embedding_service.embed_texts(textos)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(len(emb) == 384 for emb in result)

    def test_similarity_calculation(self):
        """Test del cálculo de similitud coseno."""
        from app.services.rag.embeddings import EmbeddingService

        service = EmbeddingService()
        service._model = MagicMock()

        # Vectores idénticos tienen similitud 1
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        similarity = service.similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001

    def test_similarity_orthogonal_vectors(self):
        """Test similitud de vectores ortogonales es 0."""
        from app.services.rag.embeddings import EmbeddingService

        service = EmbeddingService()
        service._model = MagicMock()

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = service.similarity(vec1, vec2)
        assert abs(similarity) < 0.001

    def test_embed_text_handles_empty_string(self, mock_embedding_service):
        """Test que maneja string vacío."""
        mock_embedding_service.embed_text.return_value = [0.0] * 384

        result = mock_embedding_service.embed_text("")
        assert len(result) == 384

    def test_embed_text_handles_long_text(self, mock_embedding_service):
        """Test que maneja textos largos."""
        texto_largo = "palabra " * 10000
        mock_embedding_service.embed_text.return_value = [0.1] * 384

        result = mock_embedding_service.embed_text(texto_largo)
        assert len(result) == 384


class TestEmbeddingServiceSingleton:
    """Tests del patrón singleton."""

    def test_get_embedding_service_returns_same_instance(self):
        """Test que get_embedding_service retorna singleton."""
        from app.services.rag.embeddings import get_embedding_service

        # Limpiar cache
        get_embedding_service.cache_clear()

        with patch('app.services.rag.embeddings.EmbeddingService') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            service1 = get_embedding_service()
            service2 = get_embedding_service()

            # Debe ser la misma instancia (singleton via lru_cache)
            assert service1 is service2
