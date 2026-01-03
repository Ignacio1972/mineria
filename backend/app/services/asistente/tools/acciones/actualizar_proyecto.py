"""
Herramienta para actualizar proyectos mineros existentes.
"""
import logging
from typing import Any, Dict, Optional

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
from .constantes import TIPOS_MINERIA, FASES_PROYECTO

logger = logging.getLogger(__name__)


@registro_herramientas.registrar
class ActualizarProyecto(Herramienta):
    """Actualiza datos de un proyecto existente."""

    nombre = "actualizar_proyecto"
    descripcion = """Actualiza los datos de un proyecto existente.
Usa esta herramienta cuando el usuario quiera:
- Modificar datos de un proyecto
- Actualizar informacion del proyecto
- Cambiar parametros del proyecto

IMPORTANTE: Esta accion requiere confirmacion del usuario."""

    categoria = CategoriaHerramienta.ACCION
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = True
    permisos = [PermisoHerramienta.ESCRITURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "proyecto_id": {
                    "type": "integer",
                    "description": "ID del proyecto a actualizar",
                },
                "nombre": {
                    "type": "string",
                    "description": "Nuevo nombre del proyecto",
                },
                "comuna": {
                    "type": "string",
                    "description": "Nueva comuna",
                },
                "tipo_mineria": {
                    "type": "string",
                    "enum": TIPOS_MINERIA,
                },
                "mineral_principal": {
                    "type": "string",
                },
                "fase": {
                    "type": "string",
                    "enum": FASES_PROYECTO,
                },
                "titular": {
                    "type": "string",
                },
                "superficie_ha": {
                    "type": "number",
                    "minimum": 0,
                },
                "vida_util_anos": {
                    "type": "integer",
                    "minimum": 0,
                },
                "uso_agua_lps": {
                    "type": "number",
                    "minimum": 0,
                },
                "fuente_agua": {
                    "type": "string",
                },
                "energia_mw": {
                    "type": "number",
                    "minimum": 0,
                },
                "trabajadores_construccion": {
                    "type": "integer",
                    "minimum": 0,
                },
                "trabajadores_operacion": {
                    "type": "integer",
                    "minimum": 0,
                },
                "inversion_musd": {
                    "type": "number",
                    "minimum": 0,
                },
                "descripcion": {
                    "type": "string",
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        nombre: Optional[str] = None,
        comuna: Optional[str] = None,
        tipo_mineria: Optional[str] = None,
        mineral_principal: Optional[str] = None,
        fase: Optional[str] = None,
        titular: Optional[str] = None,
        superficie_ha: Optional[float] = None,
        vida_util_anos: Optional[int] = None,
        uso_agua_lps: Optional[float] = None,
        fuente_agua: Optional[str] = None,
        energia_mw: Optional[float] = None,
        trabajadores_construccion: Optional[int] = None,
        trabajadores_operacion: Optional[int] = None,
        inversion_musd: Optional[float] = None,
        descripcion: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Actualiza el proyecto."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            # Obtener proyecto
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

            if proyecto.estado == "archivado":
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="No se puede modificar un proyecto archivado"
                )

            # Construir diccionario de cambios
            cambios = {}
            campos_actualizables = {
                "nombre": nombre,
                "comuna": comuna,
                "tipo_mineria": tipo_mineria,
                "mineral_principal": mineral_principal,
                "fase": fase,
                "titular": titular,
                "superficie_ha": superficie_ha,
                "vida_util_anos": vida_util_anos,
                "uso_agua_lps": uso_agua_lps,
                "fuente_agua": fuente_agua,
                "energia_mw": energia_mw,
                "trabajadores_construccion": trabajadores_construccion,
                "trabajadores_operacion": trabajadores_operacion,
                "inversion_musd": inversion_musd,
                "descripcion": descripcion,
            }

            for campo, valor in campos_actualizables.items():
                if valor is not None:
                    cambios[campo] = valor

            if not cambios:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="No se proporcionaron campos para actualizar"
                )

            # Validaciones
            if tipo_mineria and tipo_mineria not in TIPOS_MINERIA:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Tipo de mineria invalido. Valores validos: {', '.join(TIPOS_MINERIA)}"
                )

            if fase and fase not in FASES_PROYECTO:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Fase invalida. Valores validos: {', '.join(FASES_PROYECTO)}"
                )

            # Aplicar cambios
            for campo, valor in cambios.items():
                setattr(proyecto, campo, valor)

            await db.commit()
            await db.refresh(proyecto)

            logger.info(f"Proyecto actualizado: {proyecto.id} - Campos: {list(cambios.keys())}")

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto.id,
                    "nombre": proyecto.nombre,
                    "campos_actualizados": list(cambios.keys()),
                    "mensaje": f"Proyecto '{proyecto.nombre}' actualizado exitosamente",
                },
                metadata={
                    "proyecto_id": proyecto.id,
                    "cambios": cambios,
                    "accion": "actualizar_proyecto",
                }
            )

        except Exception as e:
            logger.error(f"Error actualizando proyecto: {e}")
            await db.rollback()
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al actualizar el proyecto: {str(e)}"
            )

    def generar_descripcion_confirmacion(self, **kwargs) -> str:
        """Genera descripcion para confirmacion."""
        proyecto_id = kwargs.get("proyecto_id", "?")
        proyecto_nombre = kwargs.get("_proyecto_nombre")
        campos = [k for k, v in kwargs.items() if v is not None and k not in ("proyecto_id", "_proyecto_nombre")]

        if proyecto_nombre:
            return f"Actualizar proyecto '{proyecto_nombre}': {', '.join(campos) if campos else 'sin cambios'}"
        return f"Actualizar proyecto ID {proyecto_id}: {', '.join(campos) if campos else 'sin cambios'}"
