"""
Servicio de embeddings para el sistema RAG.
Usa sentence-transformers con modelo multilingüe optimizado para español.
"""

import logging
from functools import lru_cache
from typing import List
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Servicio para generar embeddings de texto."""

    def __init__(self):
        self._model = None

    @property
    def model(self):
        """Carga lazy del modelo de embeddings."""
        if self._model is None:
            logger.info(f"Cargando modelo de embeddings: {settings.EMBEDDING_MODEL}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Modelo de embeddings cargado exitosamente")
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """
        Genera embedding para un texto.

        Args:
            text: Texto a convertir en embedding

        Returns:
            Lista de floats representando el embedding
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para múltiples textos.

        Args:
            texts: Lista de textos

        Returns:
            Lista de embeddings
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcula similitud coseno entre dos embeddings.

        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding

        Returns:
            Similitud coseno (0 a 1)
        """
        a = np.array(embedding1)
        b = np.array(embedding2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Singleton del servicio de embeddings."""
    return EmbeddingService()
