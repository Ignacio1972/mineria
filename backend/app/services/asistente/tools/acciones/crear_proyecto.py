"""
Herramienta para crear proyectos mineros.
"""
import logging
from typing import Any, Dict, Optional
from uuid import UUID

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
from app.db.models import Proyecto, Cliente
from .constantes import REGIONES_CHILE, TIPOS_MINERIA, FASES_PROYECTO

logger = logging.getLogger(__name__)


@registro_herramientas.registrar
class CrearProyecto(Herramienta):
    """Crea un nuevo proyecto minero en el sistema."""

    nombre = "crear_proyecto"
    descripcion = """Crea un nuevo proyecto minero en el sistema.
Usa esta herramienta cuando el usuario quiera:
- Crear un nuevo proyecto
- Registrar un proyecto minero
- Agregar un proyecto al sistema

IMPORTANTE: Esta accion requiere confirmacion del usuario antes de ejecutarse.
Los campos minimos requeridos son: nombre y region.
Otros campos opcionales mejoran el analisis posterior."""

    categoria = CategoriaHerramienta.ACCION
    contexto_requerido = ContextoHerramienta.GLOBAL
    requiere_confirmacion = True
    permisos = [PermisoHerramienta.ESCRITURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        """Establece la sesion de base de datos."""
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Nombre del proyecto minero (obligatorio)",
                    "minLength": 2,
                    "maxLength": 200,
                },
                "region": {
                    "type": "string",
                    "description": "Region de Chile donde se ubica el proyecto",
                    "enum": REGIONES_CHILE,
                },
                "comuna": {
                    "type": "string",
                    "description": "Comuna donde se ubica el proyecto",
                },
                "tipo_mineria": {
                    "type": "string",
                    "description": "Tipo de mineria del proyecto",
                    "enum": TIPOS_MINERIA,
                },
                "mineral_principal": {
                    "type": "string",
                    "description": "Mineral principal a extraer (ej: cobre, litio, oro)",
                },
                "fase": {
                    "type": "string",
                    "description": "Fase actual del proyecto",
                    "enum": FASES_PROYECTO,
                },
                "titular": {
                    "type": "string",
                    "description": "Nombre del titular o empresa responsable",
                },
                "cliente_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "ID del cliente asociado (si existe en el sistema)",
                },
                "superficie_ha": {
                    "type": "number",
                    "description": "Superficie del proyecto en hectareas",
                    "minimum": 0,
                },
                "vida_util_anos": {
                    "type": "integer",
                    "description": "Vida util estimada del proyecto en anos",
                    "minimum": 0,
                },
                "uso_agua_lps": {
                    "type": "number",
                    "description": "Uso de agua estimado en litros por segundo",
                    "minimum": 0,
                },
                "fuente_agua": {
                    "type": "string",
                    "description": "Fuente de agua (ej: subterranea, superficial, mar)",
                },
                "energia_mw": {
                    "type": "number",
                    "description": "Consumo de energia estimado en MW",
                    "minimum": 0,
                },
                "trabajadores_construccion": {
                    "type": "integer",
                    "description": "Numero de trabajadores en fase de construccion",
                    "minimum": 0,
                },
                "trabajadores_operacion": {
                    "type": "integer",
                    "description": "Numero de trabajadores en fase de operacion",
                    "minimum": 0,
                },
                "inversion_musd": {
                    "type": "number",
                    "description": "Inversion estimada en millones de USD",
                    "minimum": 0,
                },
                "descripcion": {
                    "type": "string",
                    "description": "Descripcion general del proyecto",
                },
            },
            "required": ["nombre", "region"],
        }

    async def ejecutar(
        self,
        nombre: str,
        region: str,
        comuna: Optional[str] = None,
        tipo_mineria: Optional[str] = None,
        mineral_principal: Optional[str] = None,
        fase: Optional[str] = None,
        titular: Optional[str] = None,
        cliente_id: Optional[str] = None,
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
        """Crea un nuevo proyecto en la base de datos."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        # Validar nombre
        if not nombre or len(nombre.strip()) < 2:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="El nombre del proyecto debe tener al menos 2 caracteres"
            )

        # Validar region
        if region not in REGIONES_CHILE:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Region invalida. Regiones validas: {', '.join(REGIONES_CHILE)}"
            )

        # Validar tipo_mineria si se proporciona
        if tipo_mineria and tipo_mineria not in TIPOS_MINERIA:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Tipo de mineria invalido. Tipos validos: {', '.join(TIPOS_MINERIA)}"
            )

        # Validar fase si se proporciona
        if fase and fase not in FASES_PROYECTO:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Fase invalida. Fases validas: {', '.join(FASES_PROYECTO)}"
            )

        try:
            # Verificar cliente si se proporciona
            cliente = None
            cliente_uuid = None
            if cliente_id:
                try:
                    cliente_uuid = UUID(cliente_id)
                    result = await db.execute(
                        select(Cliente).where(
                            Cliente.id == cliente_uuid,
                            Cliente.activo == True
                        )
                    )
                    cliente = result.scalar()
                    if not cliente:
                        return ResultadoHerramienta(
                            exito=False,
                            contenido=None,
                            error=f"Cliente con ID {cliente_id} no encontrado o inactivo"
                        )
                except ValueError:
                    return ResultadoHerramienta(
                        exito=False,
                        contenido=None,
                        error=f"ID de cliente invalido: {cliente_id}"
                    )

            # Verificar si ya existe un proyecto con el mismo nombre
            existing = await db.execute(
                select(Proyecto).where(Proyecto.nombre == nombre.strip())
            )
            if existing.scalar():
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Ya existe un proyecto con el nombre '{nombre}'"
                )

            # Crear proyecto
            proyecto = Proyecto(
                nombre=nombre.strip(),
                region=region,
                comuna=comuna,
                tipo_mineria=tipo_mineria,
                mineral_principal=mineral_principal,
                fase=fase,
                titular=titular,
                cliente_id=cliente_uuid,
                superficie_ha=superficie_ha,
                vida_util_anos=vida_util_anos,
                uso_agua_lps=uso_agua_lps,
                fuente_agua=fuente_agua,
                energia_mw=energia_mw,
                trabajadores_construccion=trabajadores_construccion,
                trabajadores_operacion=trabajadores_operacion,
                inversion_musd=inversion_musd,
                descripcion=descripcion,
                estado="borrador",
            )

            db.add(proyecto)
            await db.commit()
            await db.refresh(proyecto)

            logger.info(f"Proyecto creado: {proyecto.id} - {proyecto.nombre}")

            # Construir respuesta
            resultado = {
                "proyecto_id": proyecto.id,
                "nombre": proyecto.nombre,
                "region": proyecto.region,
                "comuna": proyecto.comuna,
                "estado": proyecto.estado,
                "tipo_mineria": proyecto.tipo_mineria,
                "mineral_principal": proyecto.mineral_principal,
                "fase": proyecto.fase,
                "titular": proyecto.titular,
                "cliente": {
                    "id": str(cliente.id),
                    "razon_social": cliente.razon_social,
                } if cliente else None,
                "parametros_tecnicos": {
                    "superficie_ha": proyecto.superficie_ha,
                    "vida_util_anos": proyecto.vida_util_anos,
                    "uso_agua_lps": proyecto.uso_agua_lps,
                    "fuente_agua": proyecto.fuente_agua,
                    "energia_mw": proyecto.energia_mw,
                    "trabajadores_construccion": proyecto.trabajadores_construccion,
                    "trabajadores_operacion": proyecto.trabajadores_operacion,
                    "inversion_musd": proyecto.inversion_musd,
                },
                "tiene_geometria": False,
                "puede_analizar": False,
                "mensaje": f"Proyecto '{proyecto.nombre}' creado exitosamente con ID {proyecto.id}",
                "siguiente_paso": "Para ejecutar el analisis de prefactibilidad, primero debe definir la geometria del proyecto en el mapa.",
            }

            return ResultadoHerramienta(
                exito=True,
                contenido=resultado,
                metadata={
                    "proyecto_id": proyecto.id,
                    "accion": "crear_proyecto",
                }
            )

        except Exception as e:
            logger.error(f"Error creando proyecto: {e}")
            await db.rollback()
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al crear el proyecto: {str(e)}"
            )

    def generar_descripcion_confirmacion(self, **kwargs) -> str:
        """Genera una descripcion legible para el dialogo de confirmacion."""
        nombre = kwargs.get("nombre", "Sin nombre")
        region = kwargs.get("region", "Sin region")
        tipo = kwargs.get("tipo_mineria", "No especificado")
        mineral = kwargs.get("mineral_principal", "No especificado")

        descripcion = f"Crear proyecto '{nombre}' en {region}"

        detalles = []
        if tipo and tipo != "No especificado":
            detalles.append(f"Tipo: {tipo}")
        if mineral and mineral != "No especificado":
            detalles.append(f"Mineral: {mineral}")
        if kwargs.get("superficie_ha"):
            detalles.append(f"Superficie: {kwargs['superficie_ha']} ha")
        if kwargs.get("inversion_musd"):
            detalles.append(f"Inversion: {kwargs['inversion_musd']} MUSD")

        if detalles:
            descripcion += f" ({', '.join(detalles)})"

        return descripcion
