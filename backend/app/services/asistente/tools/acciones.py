"""
Herramientas de acciones del asistente.
Operaciones que modifican datos y requieren confirmacion del usuario.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.shape import from_shape
from shapely.geometry import shape, MultiPolygon

from .base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)
from app.db.models import Proyecto, Cliente

logger = logging.getLogger(__name__)


# Lista de regiones validas de Chile
REGIONES_CHILE = [
    "Arica y Parinacota",
    "Tarapaca",
    "Antofagasta",
    "Atacama",
    "Coquimbo",
    "Valparaiso",
    "Metropolitana",
    "O'Higgins",
    "Maule",
    "Nuble",
    "Biobio",
    "Araucania",
    "Los Rios",
    "Los Lagos",
    "Aysen",
    "Magallanes",
]

TIPOS_MINERIA = [
    "cielo_abierto",
    "subterranea",
    "mixta",
    "placer",
    "in_situ",
]

FASES_PROYECTO = [
    "exploracion",
    "evaluacion",
    "desarrollo",
    "produccion",
    "cierre",
]


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
        """
        Genera una descripcion legible para el dialogo de confirmacion.
        """
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


@registro_herramientas.registrar
class EjecutarAnalisis(Herramienta):
    """Ejecuta un analisis de prefactibilidad ambiental."""

    nombre = "ejecutar_analisis"
    descripcion = """Ejecuta un analisis de prefactibilidad ambiental para un proyecto.
Usa esta herramienta cuando el usuario quiera:
- Analizar un proyecto
- Evaluar si es DIA o EIA
- Ejecutar el analisis de prefactibilidad
- Ver la clasificacion ambiental de un proyecto

IMPORTANTE: Esta accion requiere confirmacion del usuario.
El proyecto debe tener geometria definida para poder analizarse."""

    categoria = CategoriaHerramienta.ACCION
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
                    "description": "ID del proyecto a analizar",
                },
                "tipo_analisis": {
                    "type": "string",
                    "description": "Tipo de analisis: 'rapido' (sin LLM) o 'completo' (con generacion de informe)",
                    "enum": ["rapido", "completo"],
                    "default": "completo",
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        tipo_analisis: str = "completo",
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta el analisis de prefactibilidad."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
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

            # Verificar que tiene geometria
            if not proyecto.geom:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"El proyecto '{proyecto.nombre}' no tiene geometria definida. "
                          f"Primero debe dibujar el area del proyecto en el mapa."
                )

            # Verificar estado
            if proyecto.estado == "archivado":
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="No se puede analizar un proyecto archivado"
                )

            # Aqui se llamaria al servicio de prefactibilidad
            # Por ahora retornamos un placeholder indicando que la accion fue aceptada
            # La ejecucion real se hara cuando se implemente el AsistenteService

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "proyecto_id": proyecto_id,
                    "proyecto_nombre": proyecto.nombre,
                    "tipo_analisis": tipo_analisis,
                    "estado": "pendiente_ejecucion",
                    "mensaje": f"Analisis '{tipo_analisis}' programado para el proyecto '{proyecto.nombre}'",
                    "nota": "El analisis se ejecutara al confirmar la accion",
                },
                metadata={
                    "proyecto_id": proyecto_id,
                    "tipo_analisis": tipo_analisis,
                    "accion": "ejecutar_analisis",
                }
            )

        except Exception as e:
            logger.error(f"Error preparando analisis: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al preparar el analisis: {str(e)}"
            )

    def generar_descripcion_confirmacion(self, **kwargs) -> str:
        """Genera descripcion para confirmacion."""
        proyecto_id = kwargs.get("proyecto_id", "?")
        tipo = kwargs.get("tipo_analisis", "completo")
        return f"Ejecutar analisis {tipo} para proyecto ID {proyecto_id}"


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
        campos = [k for k, v in kwargs.items() if v is not None and k != "proyecto_id"]
        return f"Actualizar proyecto ID {proyecto_id}: {', '.join(campos) if campos else 'sin cambios'}"
