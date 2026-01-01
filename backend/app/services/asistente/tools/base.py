"""
Clase base para herramientas del agente.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from enum import Enum

logger = logging.getLogger(__name__)


class CategoriaHerramienta(str, Enum):
    """Categorias de herramientas."""
    RAG = "rag"
    CONSULTA = "consulta"
    ACCION = "accion"
    EXTERNA = "externa"
    SISTEMA = "sistema"


class PermisoHerramienta(str, Enum):
    """Permisos requeridos para herramientas."""
    LECTURA = "lectura"
    ESCRITURA = "escritura"
    ADMIN = "admin"


@dataclass
class ResultadoHerramienta:
    """Resultado de la ejecucion de una herramienta."""
    exito: bool
    contenido: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para el LLM."""
        if self.exito:
            return {
                "success": True,
                "result": self.contenido,
                "metadata": self.metadata,
            }
        return {
            "success": False,
            "error": self.error or "Error desconocido",
        }


@dataclass
class DefinicionHerramienta:
    """Definicion de una herramienta en formato Anthropic."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    categoria: CategoriaHerramienta = CategoriaHerramienta.CONSULTA
    requiere_confirmacion: bool = False
    permisos: List[PermisoHerramienta] = field(default_factory=lambda: [PermisoHerramienta.LECTURA])

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convierte al formato de Anthropic Tool Use."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class Herramienta(ABC):
    """Clase base abstracta para herramientas del agente."""

    # Atributos que deben definir las subclases
    nombre: str = ""
    descripcion: str = ""
    categoria: CategoriaHerramienta = CategoriaHerramienta.CONSULTA
    requiere_confirmacion: bool = False
    permisos: List[PermisoHerramienta] = [PermisoHerramienta.LECTURA]

    @classmethod
    @abstractmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Retorna el JSON Schema de los parametros de entrada.

        Returns:
            JSON Schema para input_schema de Anthropic
        """
        pass

    @abstractmethod
    async def ejecutar(self, **kwargs) -> ResultadoHerramienta:
        """
        Ejecuta la herramienta con los parametros dados.

        Args:
            **kwargs: Parametros de la herramienta

        Returns:
            ResultadoHerramienta con el resultado o error
        """
        pass

    @classmethod
    def get_definicion(cls) -> DefinicionHerramienta:
        """Obtiene la definicion completa de la herramienta."""
        return DefinicionHerramienta(
            name=cls.nombre,
            description=cls.descripcion,
            input_schema=cls.get_schema(),
            categoria=cls.categoria,
            requiere_confirmacion=cls.requiere_confirmacion,
            permisos=cls.permisos,
        )

    def __repr__(self) -> str:
        return f"<Herramienta {self.nombre}>"


class RegistroHerramientas:
    """Registro central de herramientas disponibles."""

    def __init__(self):
        self._herramientas: Dict[str, Type[Herramienta]] = {}
        self._instancias: Dict[str, Herramienta] = {}

    def registrar(self, herramienta_class: Type[Herramienta]) -> Type[Herramienta]:
        """
        Decorador para registrar una herramienta.

        Uso:
            @registro.registrar
            class MiHerramienta(Herramienta):
                ...
        """
        nombre = herramienta_class.nombre
        if not nombre:
            raise ValueError(f"La herramienta {herramienta_class.__name__} debe definir 'nombre'")

        self._herramientas[nombre] = herramienta_class
        logger.debug(f"Herramienta registrada: {nombre}")
        return herramienta_class

    def obtener(self, nombre: str) -> Optional[Herramienta]:
        """
        Obtiene una instancia de herramienta por nombre.

        Args:
            nombre: Nombre de la herramienta

        Returns:
            Instancia de la herramienta o None
        """
        if nombre not in self._instancias:
            herramienta_class = self._herramientas.get(nombre)
            if herramienta_class:
                self._instancias[nombre] = herramienta_class()
        return self._instancias.get(nombre)

    def listar(
        self,
        categoria: Optional[CategoriaHerramienta] = None,
        permisos_usuario: Optional[List[PermisoHerramienta]] = None
    ) -> List[DefinicionHerramienta]:
        """
        Lista las herramientas disponibles.

        Args:
            categoria: Filtrar por categoria
            permisos_usuario: Permisos del usuario para filtrar

        Returns:
            Lista de definiciones de herramientas
        """
        resultado = []

        for nombre, herramienta_class in self._herramientas.items():
            definicion = herramienta_class.get_definicion()

            # Filtrar por categoria
            if categoria and definicion.categoria != categoria:
                continue

            # Filtrar por permisos
            if permisos_usuario is not None:
                if not all(p in permisos_usuario for p in definicion.permisos):
                    continue

            resultado.append(definicion)

        return resultado

    def obtener_tools_anthropic(
        self,
        permisos_usuario: Optional[List[PermisoHerramienta]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las herramientas en formato Anthropic Tool Use.

        Args:
            permisos_usuario: Permisos del usuario para filtrar

        Returns:
            Lista de herramientas en formato Anthropic
        """
        definiciones = self.listar(permisos_usuario=permisos_usuario)
        return [d.to_anthropic_format() for d in definiciones]

    async def ejecutar(self, nombre: str, **kwargs) -> ResultadoHerramienta:
        """
        Ejecuta una herramienta por nombre.

        Args:
            nombre: Nombre de la herramienta
            **kwargs: Parametros de la herramienta

        Returns:
            ResultadoHerramienta
        """
        herramienta = self.obtener(nombre)
        if not herramienta:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Herramienta '{nombre}' no encontrada"
            )

        try:
            logger.info(f"Ejecutando herramienta: {nombre}")
            resultado = await herramienta.ejecutar(**kwargs)
            logger.info(f"Herramienta {nombre} completada: exito={resultado.exito}")
            return resultado
        except Exception as e:
            logger.error(f"Error ejecutando herramienta {nombre}: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


# Instancia global del registro
registro_herramientas = RegistroHerramientas()
