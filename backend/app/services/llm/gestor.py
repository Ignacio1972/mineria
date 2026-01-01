"""
Gestor de Modelos LLM

Administra la selección y configuración de modelos LLM en runtime,
con persistencia en Redis para mantener estado entre reinicios.
"""

import logging
from typing import Any, Optional

import redis

from app.core.config import settings
from app.services.llm.cliente import get_cliente_llm, ModeloLLM

logger = logging.getLogger(__name__)

# Clave Redis para persistencia
REDIS_KEY_MODELO_ACTIVO = "llm:modelo_activo"

# Catálogo de modelos disponibles con metadata
CATALOGO_MODELOS: dict[str, dict[str, Any]] = {
    "claude-sonnet-4-20250514": {
        "nombre": "Claude Sonnet 4",
        "descripcion": "Balance óptimo velocidad/calidad",
        "costo_input_1k": 0.003,
        "costo_output_1k": 0.015,
        "max_tokens": 8192,
        "velocidad": "rápido",
        "recomendado_para": ["análisis", "informes"],
    },
    "claude-3-5-haiku-20241022": {
        "nombre": "Claude 3.5 Haiku",
        "descripcion": "Más rápido y económico",
        "costo_input_1k": 0.0008,
        "costo_output_1k": 0.004,
        "max_tokens": 8192,
        "velocidad": "muy rápido",
        "recomendado_para": ["análisis rápido", "validaciones"],
    },
    "claude-opus-4-20250514": {
        "nombre": "Claude Opus 4",
        "descripcion": "Máxima calidad y razonamiento",
        "costo_input_1k": 0.015,
        "costo_output_1k": 0.075,
        "max_tokens": 8192,
        "velocidad": "lento",
        "recomendado_para": ["informes complejos", "análisis legal"],
    },
}


class GestorModelos:
    """
    Gestor singleton para administrar modelos LLM.

    Permite cambiar el modelo activo en runtime y persiste
    la selección en Redis para mantener estado entre reinicios.
    """

    def __init__(self):
        """Inicializa el gestor cargando el modelo desde Redis o settings."""
        self._redis_client: Optional[redis.Redis] = None
        self._modelo_activo: str = self._cargar_modelo_inicial()
        logger.info(f"GestorModelos inicializado con modelo: {self._modelo_activo}")

    def _get_redis(self) -> Optional[redis.Redis]:
        """Obtiene conexión a Redis con manejo de errores."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                )
                # Verificar conexión
                self._redis_client.ping()
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"No se pudo conectar a Redis: {e}")
                self._redis_client = None
        return self._redis_client

    def _cargar_modelo_inicial(self) -> str:
        """Carga el modelo desde Redis o usa el valor por defecto."""
        redis_client = self._get_redis()
        if redis_client:
            try:
                modelo_guardado = redis_client.get(REDIS_KEY_MODELO_ACTIVO)
                if modelo_guardado and modelo_guardado in CATALOGO_MODELOS:
                    logger.info(f"Modelo cargado desde Redis: {modelo_guardado}")
                    return modelo_guardado
            except redis.RedisError as e:
                logger.warning(f"Error leyendo modelo de Redis: {e}")

        return settings.LLM_MODEL

    def _persistir_modelo(self, modelo: str) -> bool:
        """Persiste el modelo activo en Redis."""
        redis_client = self._get_redis()
        if redis_client:
            try:
                redis_client.set(REDIS_KEY_MODELO_ACTIVO, modelo)
                logger.info(f"Modelo persistido en Redis: {modelo}")
                return True
            except redis.RedisError as e:
                logger.warning(f"Error persistiendo modelo en Redis: {e}")
        return False

    @property
    def modelo_activo(self) -> str:
        """Retorna el ID del modelo activo."""
        return self._modelo_activo

    @property
    def info_modelo_activo(self) -> dict[str, Any]:
        """Retorna la información completa del modelo activo."""
        info = CATALOGO_MODELOS.get(self._modelo_activo, {}).copy()
        info["id"] = self._modelo_activo
        info["activo"] = True
        return info

    def cambiar_modelo(self, modelo: str) -> dict[str, Any]:
        """
        Cambia el modelo activo en runtime.

        Args:
            modelo: ID del modelo a activar

        Returns:
            Dict con modelo anterior, nuevo y estado de persistencia

        Raises:
            ValueError: Si el modelo no está en el catálogo
        """
        if modelo not in CATALOGO_MODELOS:
            modelos_disponibles = list(CATALOGO_MODELOS.keys())
            raise ValueError(
                f"Modelo '{modelo}' no válido. "
                f"Modelos disponibles: {modelos_disponibles}"
            )

        modelo_anterior = self._modelo_activo

        if modelo == modelo_anterior:
            return {
                "anterior": modelo_anterior,
                "nuevo": modelo,
                "mensaje": "El modelo ya estaba activo",
                "persistido": True,
            }

        # Actualizar modelo interno
        self._modelo_activo = modelo

        # Actualizar ClienteLLM singleton
        cliente = get_cliente_llm()
        cliente.config.modelo = modelo

        # Persistir en Redis
        persistido = self._persistir_modelo(modelo)

        logger.info(f"Modelo cambiado: {modelo_anterior} -> {modelo}")

        return {
            "anterior": modelo_anterior,
            "nuevo": modelo,
            "mensaje": "Modelo actualizado correctamente",
            "persistido": persistido,
        }

    def obtener_catalogo(self) -> list[dict[str, Any]]:
        """
        Retorna el catálogo completo de modelos.

        Returns:
            Lista de modelos con su metadata e indicador de activo
        """
        catalogo = []
        for modelo_id, info in CATALOGO_MODELOS.items():
            modelo_info = info.copy()
            modelo_info["id"] = modelo_id
            modelo_info["activo"] = modelo_id == self._modelo_activo
            catalogo.append(modelo_info)
        return catalogo

    def obtener_configuracion_cliente(self) -> dict[str, Any]:
        """Retorna la configuración actual del cliente LLM."""
        cliente = get_cliente_llm()
        config = cliente.obtener_configuracion()
        config["modelo_gestor"] = self._modelo_activo
        return config


# Instancia singleton
_gestor_modelos: Optional[GestorModelos] = None


def get_gestor_modelos() -> GestorModelos:
    """
    Obtiene la instancia singleton del gestor de modelos.

    Returns:
        GestorModelos configurado
    """
    global _gestor_modelos
    if _gestor_modelos is None:
        _gestor_modelos = GestorModelos()
    return _gestor_modelos
