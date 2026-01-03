"""
Herramienta para guardar informacion en la ficha acumulativa del proyecto.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    ContextoHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)
from app.db.models import Proyecto
from .constantes import CATEGORIAS_FICHA

logger = logging.getLogger(__name__)


@registro_herramientas.registrar
class GuardarFicha(Herramienta):
    """Guarda informacion en la ficha acumulativa del proyecto."""

    nombre = "guardar_ficha"
    descripcion = """Guarda informacion recopilada en la ficha acumulativa del proyecto.
Usa esta herramienta cuando el usuario proporcione informacion sobre su proyecto que debe
ser persistida en la ficha, como:
- Datos de identificacion (nombre del titular, contacto, etc.)
- Parametros tecnicos (tonelaje, tipo de extraccion, minerales, etc.)
- Informacion sobre obras (plantas, depositos, caminos, etc.)
- Fases del proyecto (construccion, operacion, cierre)
- Insumos (agua, energia, combustibles)
- Emisiones y residuos
- Aspectos sociales (comunidades, trabajadores)
- Aspectos ambientales (flora, fauna, areas sensibles)

Esta herramienta NO requiere confirmacion porque solo guarda informacion que el usuario
ya proporciono durante la conversacion.

IMPORTANTE: Extrae los datos estructurados de la respuesta del usuario y guardalos
con la categoria y clave apropiadas."""

    categoria = CategoriaHerramienta.ACCION
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.ESCRITURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None
        self._proyecto_id: Optional[int] = None

    def set_db(self, db: AsyncSession):
        """Establece la sesion de base de datos."""
        self._db = db

    def set_proyecto_id(self, proyecto_id: int):
        """Establece el ID del proyecto contexto."""
        self._proyecto_id = proyecto_id

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "proyecto_id": {
                    "type": "integer",
                    "description": "ID del proyecto donde guardar (opcional si hay contexto)",
                },
                "datos": {
                    "type": "array",
                    "description": "Lista de datos a guardar en la ficha",
                    "items": {
                        "type": "object",
                        "properties": {
                            "categoria": {
                                "type": "string",
                                "description": "Categoria del dato",
                                "enum": [
                                    "identificacion", "tecnico", "obras", "fases",
                                    "insumos", "emisiones", "social", "ambiental"
                                ],
                            },
                            "clave": {
                                "type": "string",
                                "description": "Clave identificadora del dato (ej: tonelaje_mensual)",
                            },
                            "valor": {
                                "type": "string",
                                "description": "Valor textual del dato",
                            },
                            "valor_numerico": {
                                "type": "number",
                                "description": "Valor numerico si aplica (para comparaciones de umbral)",
                            },
                            "unidad": {
                                "type": "string",
                                "description": "Unidad de medida (ej: ton/mes, l/s, MW)",
                            },
                        },
                        "required": ["categoria", "clave"],
                    },
                    "minItems": 1,
                },
            },
            "required": ["datos"],
        }

    async def ejecutar(
        self,
        datos: List[Dict[str, Any]],
        proyecto_id: Optional[int] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Guarda datos en la ficha acumulativa del proyecto."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        # Determinar proyecto_id
        proyecto_id = proyecto_id or self._proyecto_id
        if not proyecto_id:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No se especifico proyecto_id y no hay proyecto en contexto"
            )

        try:
            # Verificar que el proyecto existe
            result = await db.execute(
                select(Proyecto).where(Proyecto.id == proyecto_id)
            )
            proyecto = result.scalar()

            if not proyecto:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Proyecto con ID {proyecto_id} no encontrado"
                )

            # Validar y preparar datos
            respuestas, errores_validacion = self._validar_datos(datos)

            if not respuestas:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"No hay datos validos para guardar. Errores: {errores_validacion}"
                )

            # Guardar respuestas
            resultado = await self._guardar_respuestas(db, proyecto_id, respuestas)
            await db.commit()

            logger.info(
                f"Ficha actualizada: proyecto_id={proyecto_id}, "
                f"guardadas={resultado['guardadas']}, actualizadas={resultado['actualizadas']}"
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto_id,
                    "proyecto_nombre": proyecto.nombre,
                    "guardadas": resultado["guardadas"],
                    "actualizadas": resultado["actualizadas"],
                    "errores": resultado["errores"] + errores_validacion,
                    "datos_guardados": resultado["datos_guardados"],
                    "mensaje": f"Se guardaron {resultado['guardadas'] + resultado['actualizadas']} datos en la ficha del proyecto '{proyecto.nombre}'",
                },
                metadata={
                    "proyecto_id": proyecto_id,
                    "accion": "guardar_ficha",
                    "total_guardados": resultado["guardadas"] + resultado["actualizadas"],
                }
            )

        except Exception as e:
            logger.error(f"Error guardando ficha: {e}")
            await db.rollback()
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al guardar en la ficha: {str(e)}"
            )

    def _validar_datos(self, datos: List[Dict[str, Any]]) -> tuple:
        """Valida los datos y retorna respuestas validadas y errores."""
        from app.schemas.ficha import GuardarRespuestaAsistente, CategoriaCaracteristica

        respuestas = []
        errores_validacion = []

        for dato in datos:
            categoria_str = dato.get("categoria", "").lower()
            clave = dato.get("clave", "")
            valor = dato.get("valor")
            valor_numerico = dato.get("valor_numerico")
            unidad = dato.get("unidad")

            # Validar categoria
            if categoria_str not in CATEGORIAS_FICHA:
                errores_validacion.append({
                    "clave": clave,
                    "error": f"Categoria '{categoria_str}' no valida"
                })
                continue

            # Validar que hay al menos un valor
            if valor is None and valor_numerico is None:
                errores_validacion.append({
                    "clave": clave,
                    "error": "Debe proporcionar valor o valor_numerico"
                })
                continue

            try:
                categoria_enum = CategoriaCaracteristica(categoria_str)
                respuestas.append(GuardarRespuestaAsistente(
                    categoria=categoria_enum,
                    clave=clave,
                    valor=str(valor) if valor else None,
                    valor_numerico=float(valor_numerico) if valor_numerico is not None else None,
                    unidad=unidad,
                ))
            except Exception as e:
                errores_validacion.append({
                    "clave": clave,
                    "error": str(e)
                })

        return respuestas, errores_validacion

    async def _guardar_respuestas(
        self,
        db: AsyncSession,
        proyecto_id: int,
        respuestas: list
    ) -> dict:
        """Guarda las respuestas usando el servicio de ficha."""
        from app.services.asistente.ficha import get_ficha_service

        ficha_service = get_ficha_service(db)
        resultado = await ficha_service.guardar_respuestas_asistente(
            proyecto_id,
            respuestas
        )

        # Preparar resumen para el LLM
        datos_guardados = []
        for c in resultado.caracteristicas:
            datos_guardados.append({
                "categoria": c.categoria.value if hasattr(c.categoria, 'value') else c.categoria,
                "clave": c.clave,
                "valor": c.valor or c.valor_numerico,
                "unidad": c.unidad,
            })

        return {
            "guardadas": resultado.guardadas,
            "actualizadas": resultado.actualizadas,
            "errores": resultado.errores,
            "datos_guardados": datos_guardados,
        }

    def generar_descripcion_confirmacion(self, **kwargs) -> str:
        """Genera descripcion para confirmacion (aunque no la usa)."""
        datos = kwargs.get("datos", [])
        return f"Guardar {len(datos)} datos en la ficha del proyecto"
