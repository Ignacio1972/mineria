"""
Herramientas del asistente para Generación de EIA (Fase 4).

Incluye acciones y consultas para:
- Compilar documento EIA completo
- Generar capítulos individuales
- Regenerar secciones específicas
- Gestionar versiones
- Exportar a diferentes formatos
- Validar contra reglas SEA
"""
import logging
from typing import Any, Dict, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    ContextoHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)
from app.services.generacion_eia import GeneracionEIAService
from app.schemas.generacion_eia import (
    CompilarDocumentoRequest,
    RegenerarSeccionRequest,
    SeveridadEnum,
)

logger = logging.getLogger(__name__)

# Servicio singleton
_generacion_service: Optional[GeneracionEIAService] = None


def get_generacion_service() -> GeneracionEIAService:
    """Obtiene instancia del servicio de generación."""
    global _generacion_service
    if _generacion_service is None:
        _generacion_service = GeneracionEIAService()
    return _generacion_service


# =============================================================================
# ACCIONES - Requieren confirmación
# =============================================================================

@registro_herramientas.registrar
class CompilarDocumentoEIA(Herramienta):
    """Compila el documento EIA completo generando todos los capítulos."""

    nombre = "compilar_documento_eia"
    descripcion = """Compila el documento EIA completo generando todos los capítulos con IA.

Usa esta herramienta cuando:
- El usuario quiera generar el documento EIA completo
- La estructura EIA ya esté definida (Fase 2 completada)
- Se haya recopilado suficiente información (Fase 3 con progreso significativo)

Genera los 11 capítulos del EIA según Art. 18 DS 40:
1. Descripción del Proyecto
2. Área de Influencia
3. Línea de Base
4. Predicción de Impactos
5. Plan de Medidas
6. Plan de Contingencias
7. Plan de Seguimiento
8. Participación Ciudadana
9. Políticas, Planes y Programas
10. Compromisos Voluntarios
11. Ficha Resumen

IMPORTANTE: Este proceso puede tomar varios minutos. Se recomienda generar
capítulos individuales si solo se necesitan algunos específicos.

NOTA: Esta acción requiere confirmación del usuario."""

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
                    "description": "ID del proyecto para el cual generar el EIA",
                },
                "capitulos": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Lista de capítulos a generar (1-11). Si no se especifica, genera todos.",
                },
                "regenerar_existentes": {
                    "type": "boolean",
                    "description": "Si es true, regenera capítulos que ya existen",
                    "default": False,
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        capitulos: Optional[List[int]] = None,
        regenerar_existentes: bool = False,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta la compilación del documento EIA."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay conexión a base de datos disponible"
            )

        try:
            service = get_generacion_service()
            request = CompilarDocumentoRequest(
                incluir_capitulos=capitulos,
                regenerar_existentes=regenerar_existentes
            )

            resultado = await service.compilar_documento(
                db=db,
                proyecto_id=proyecto_id,
                request=request
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "mensaje": f"Documento EIA compilado exitosamente",
                    "documento_id": resultado.documento_id,
                    "capitulos_generados": resultado.capitulos_generados,
                    "capitulos_con_error": resultado.capitulos_con_error,
                    "tiempo_total_segundos": resultado.tiempo_total_segundos,
                    "estadisticas": {
                        "palabras": resultado.estadisticas.total_palabras,
                        "paginas_estimadas": resultado.estadisticas.total_paginas,
                        "completitud": resultado.estadisticas.porcentaje_completitud,
                    }
                },
                metadata={"proyecto_id": proyecto_id}
            )

        except Exception as e:
            logger.error(f"Error compilando documento EIA: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al compilar documento: {str(e)}"
            )


@registro_herramientas.registrar
class GenerarCapituloEIA(Herramienta):
    """Genera un capítulo específico del EIA."""

    nombre = "generar_capitulo_eia"
    descripcion = """Genera un capítulo específico del EIA usando IA.

Usa esta herramienta cuando:
- El usuario quiera generar o regenerar un capítulo específico
- Se necesite actualizar el contenido de un capítulo existente
- El usuario proporcione instrucciones adicionales para la generación

Capítulos disponibles (1-11):
1. Descripción del Proyecto
2. Determinación y Justificación del Área de Influencia
3. Línea de Base
4. Predicción y Evaluación de Impactos Ambientales
5. Plan de Medidas de Mitigación, Reparación y Compensación
6. Plan de Prevención de Contingencias y Emergencias
7. Plan de Seguimiento Ambiental
8. Descripción de la Participación Ciudadana
9. Relación con Políticas, Planes y Programas
10. Compromisos Ambientales Voluntarios
11. Ficha Resumen del EIA

NOTA: Esta acción requiere confirmación del usuario."""

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
                    "description": "ID del proyecto",
                },
                "capitulo_numero": {
                    "type": "integer",
                    "description": "Número del capítulo a generar (1-11)",
                    "minimum": 1,
                    "maximum": 11,
                },
                "instrucciones": {
                    "type": "string",
                    "description": "Instrucciones adicionales para la generación del capítulo",
                },
                "regenerar": {
                    "type": "boolean",
                    "description": "Si es true, regenera el capítulo aunque ya exista",
                    "default": False,
                },
            },
            "required": ["proyecto_id", "capitulo_numero"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        capitulo_numero: int,
        instrucciones: Optional[str] = None,
        regenerar: bool = False,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta la generación del capítulo."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay conexión a base de datos disponible"
            )

        if capitulo_numero < 1 or capitulo_numero > 11:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="El número de capítulo debe estar entre 1 y 11"
            )

        try:
            service = get_generacion_service()

            resultado = await service.generar_capitulo(
                db=db,
                proyecto_id=proyecto_id,
                capitulo_numero=capitulo_numero,
                instrucciones_adicionales=instrucciones,
                regenerar=regenerar
            )

            palabras = len(resultado.contenido.split()) if resultado.contenido else 0

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "mensaje": f"Capítulo {capitulo_numero} generado exitosamente",
                    "capitulo": {
                        "numero": resultado.numero,
                        "titulo": resultado.titulo,
                        "palabras": palabras,
                        "subsecciones": len(resultado.subsecciones),
                    },
                    "preview": resultado.contenido[:500] + "..." if len(resultado.contenido) > 500 else resultado.contenido,
                },
                metadata={"proyecto_id": proyecto_id, "capitulo": capitulo_numero}
            )

        except Exception as e:
            logger.error(f"Error generando capítulo {capitulo_numero}: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al generar capítulo: {str(e)}"
            )


@registro_herramientas.registrar
class RegenerarSeccionEIA(Herramienta):
    """Regenera una sección específica de un capítulo con instrucciones personalizadas."""

    nombre = "regenerar_seccion_eia"
    descripcion = """Regenera una sección específica de un capítulo del EIA.

Usa esta herramienta cuando:
- El usuario quiera mejorar o expandir una sección específica
- Se necesite reescribir una sección con instrucciones diferentes
- El contenido de una sección necesite ser más detallado o técnico

Permite dar instrucciones específicas como:
- "Agregar más detalle técnico sobre..."
- "Expandir la descripción de..."
- "Reformular para incluir..."

NOTA: Esta acción requiere confirmación del usuario."""

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
                    "description": "ID del proyecto",
                },
                "capitulo_numero": {
                    "type": "integer",
                    "description": "Número del capítulo (1-11)",
                    "minimum": 1,
                    "maximum": 11,
                },
                "seccion_codigo": {
                    "type": "string",
                    "description": "Código o nombre de la sección a regenerar",
                },
                "instrucciones": {
                    "type": "string",
                    "description": "Instrucciones específicas para la regeneración",
                },
            },
            "required": ["proyecto_id", "capitulo_numero", "seccion_codigo", "instrucciones"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str,
        instrucciones: str,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta la regeneración de la sección."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay conexión a base de datos disponible"
            )

        try:
            service = get_generacion_service()
            request = RegenerarSeccionRequest(
                capitulo_numero=capitulo_numero,
                seccion_codigo=seccion_codigo,
                instrucciones=instrucciones
            )

            texto = await service.regenerar_seccion(
                db=db,
                proyecto_id=proyecto_id,
                request=request
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "mensaje": f"Sección '{seccion_codigo}' regenerada exitosamente",
                    "capitulo": capitulo_numero,
                    "seccion": seccion_codigo,
                    "palabras": len(texto.split()),
                    "preview": texto[:500] + "..." if len(texto) > 500 else texto,
                },
                metadata={"proyecto_id": proyecto_id}
            )

        except Exception as e:
            logger.error(f"Error regenerando sección: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al regenerar sección: {str(e)}"
            )


@registro_herramientas.registrar
class CrearVersionDocumento(Herramienta):
    """Crea una nueva versión (snapshot) del documento EIA."""

    nombre = "crear_version_documento"
    descripcion = """Crea un snapshot del documento EIA actual como nueva versión.

Usa esta herramienta cuando:
- El usuario quiera guardar el estado actual antes de hacer cambios
- Se haya completado una fase importante del documento
- El usuario quiera crear un punto de restauración

Las versiones permiten:
- Mantener historial de cambios
- Restaurar versiones anteriores
- Comparar diferentes estados del documento

NOTA: Esta acción requiere confirmación del usuario."""

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
                    "description": "ID del proyecto",
                },
                "descripcion_cambios": {
                    "type": "string",
                    "description": "Descripción de los cambios realizados en esta versión",
                },
            },
            "required": ["proyecto_id", "descripcion_cambios"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        descripcion_cambios: str,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta la creación de versión."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay conexión a base de datos disponible"
            )

        try:
            service = get_generacion_service()

            version = await service.crear_version(
                db=db,
                proyecto_id=proyecto_id,
                cambios=descripcion_cambios,
                creado_por="asistente"
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "mensaje": f"Versión {version.version} creada exitosamente",
                    "version_id": version.id,
                    "numero_version": version.version,
                    "descripcion": version.cambios,
                    "fecha": version.created_at.isoformat(),
                },
                metadata={"proyecto_id": proyecto_id}
            )

        except Exception as e:
            logger.error(f"Error creando versión: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al crear versión: {str(e)}"
            )


@registro_herramientas.registrar
class ExportarDocumentoEIA(Herramienta):
    """Exporta el documento EIA a un formato específico (PDF, DOCX, e-SEIA)."""

    nombre = "exportar_documento_eia"
    descripcion = """Exporta el documento EIA a un formato específico.

Formatos disponibles:
- **pdf**: Documento PDF listo para impresión con portada e índice
- **docx**: Documento Word editable con estilos SEA
- **eseia_xml**: XML para carga en plataforma e-SEIA del SEA

Usa esta herramienta cuando:
- El usuario quiera descargar el documento en algún formato
- Se necesite preparar el documento para envío o revisión
- Se quiera generar la versión final para ingreso al SEA

NOTA: Esta acción requiere confirmación del usuario."""

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
                    "description": "ID del proyecto",
                },
                "formato": {
                    "type": "string",
                    "description": "Formato de exportación",
                    "enum": ["pdf", "docx", "eseia_xml"],
                },
                "incluir_portada": {
                    "type": "boolean",
                    "description": "Incluir portada en el documento",
                    "default": True,
                },
                "incluir_indice": {
                    "type": "boolean",
                    "description": "Incluir índice de contenidos",
                    "default": True,
                },
            },
            "required": ["proyecto_id", "formato"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        formato: str,
        incluir_portada: bool = True,
        incluir_indice: bool = True,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta la exportación del documento."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay conexión a base de datos disponible"
            )

        formatos_validos = ["pdf", "docx", "eseia_xml"]
        if formato.lower() not in formatos_validos:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Formato inválido. Formatos disponibles: {', '.join(formatos_validos)}"
            )

        try:
            service = get_generacion_service()

            config = {
                "incluir_portada": incluir_portada,
                "incluir_indice": incluir_indice,
            }

            resultado = await service.exportar(
                db=db,
                proyecto_id=proyecto_id,
                formato=formato,
                config=config
            )

            if resultado.generado_exitoso:
                return ResultadoHerramienta(
                    exito=True,
                    contenido={
                        "mensaje": f"Documento exportado exitosamente a {formato.upper()}",
                        "exportacion_id": resultado.id,
                        "formato": resultado.formato,
                        "tamano_bytes": resultado.tamano_bytes,
                        "url_descarga": resultado.url_descarga,
                    },
                    metadata={"proyecto_id": proyecto_id}
                )
            else:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error=f"Error en exportación: {resultado.error_mensaje}"
                )

        except Exception as e:
            logger.error(f"Error exportando documento: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al exportar documento: {str(e)}"
            )


# =============================================================================
# CONSULTAS - No requieren confirmación
# =============================================================================

@registro_herramientas.registrar
class ConsultarEstadoDocumento(Herramienta):
    """Consulta el estado actual del documento EIA."""

    nombre = "consultar_estado_documento"
    descripcion = """Consulta el estado actual del documento EIA del proyecto.

Retorna información sobre:
- Estado general del documento (borrador, en revisión, validado, final)
- Versión actual
- Capítulos generados y su estado
- Estadísticas (palabras, páginas estimadas, completitud)
- Última fecha de modificación

Usa esta herramienta cuando:
- El usuario pregunte por el estado del documento
- Se necesite saber qué capítulos ya están generados
- Se quiera conocer el progreso general del EIA"""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

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
                    "description": "ID del proyecto",
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta la consulta del estado."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay conexión a base de datos disponible"
            )

        try:
            service = get_generacion_service()

            documento = await service.get_documento(
                db=db,
                proyecto_id=proyecto_id
            )

            if not documento:
                return ResultadoHerramienta(
                    exito=True,
                    contenido={
                        "existe_documento": False,
                        "mensaje": "No existe documento EIA para este proyecto. Use 'compilar_documento_eia' o 'generar_capitulo_eia' para comenzar.",
                    },
                    metadata={"proyecto_id": proyecto_id}
                )

            # Obtener progreso por capítulo
            progreso = await service.get_progreso_generacion(db, proyecto_id)
            capitulos_completados = [p for p in progreso if p.estado == 'completado']
            capitulos_pendientes = [p for p in progreso if p.estado == 'pendiente']

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "existe_documento": True,
                    "documento": {
                        "id": documento.id,
                        "titulo": documento.titulo,
                        "estado": documento.estado,
                        "version": documento.version,
                        "updated_at": documento.updated_at.isoformat(),
                    },
                    "progreso": {
                        "capitulos_completados": len(capitulos_completados),
                        "capitulos_pendientes": len(capitulos_pendientes),
                        "completitud": f"{(len(capitulos_completados) / 11) * 100:.1f}%",
                    },
                    "estadisticas": documento.estadisticas,
                    "capitulos_listos": [
                        {"numero": p.capitulo_numero, "titulo": p.titulo, "palabras": p.palabras_generadas}
                        for p in capitulos_completados
                    ],
                },
                metadata={"proyecto_id": proyecto_id}
            )

        except Exception as e:
            logger.error(f"Error consultando estado: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al consultar estado: {str(e)}"
            )


@registro_herramientas.registrar
class ConsultarValidacionesSEA(Herramienta):
    """Consulta las validaciones del documento contra reglas SEA."""

    nombre = "consultar_validaciones_sea"
    descripcion = """Consulta las observaciones de validación del documento EIA.

Valida el documento contra reglas del SEA e ICSARA, detectando:
- Errores de contenido (información faltante o incorrecta)
- Errores de formato (estructura, referencias)
- Advertencias de completitud
- Sugerencias de mejora

Usa esta herramienta cuando:
- El usuario quiera revisar la calidad del documento
- Se necesite verificar cumplimiento antes de enviar
- Haya preguntas sobre observaciones o errores detectados"""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

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
                    "description": "ID del proyecto",
                },
                "nivel_minimo": {
                    "type": "string",
                    "description": "Nivel mínimo de severidad a incluir",
                    "enum": ["error", "warning", "info"],
                    "default": "info",
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        nivel_minimo: str = "info",
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta la validación y retorna resultados."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay conexión a base de datos disponible"
            )

        try:
            service = get_generacion_service()

            severidad_map = {
                "error": SeveridadEnum.ERROR,
                "warning": SeveridadEnum.WARNING,
                "info": SeveridadEnum.INFO,
            }
            severidad = severidad_map.get(nivel_minimo, SeveridadEnum.INFO)

            resultado = await service.validar_documento(
                db=db,
                proyecto_id=proyecto_id,
                nivel_severidad_minima=severidad
            )

            # Agrupar observaciones por severidad
            por_severidad = {}
            for obs in resultado.observaciones:
                sev = obs.severidad
                if sev not in por_severidad:
                    por_severidad[sev] = []
                por_severidad[sev].append({
                    "capitulo": obs.capitulo_numero,
                    "seccion": obs.seccion,
                    "mensaje": obs.mensaje,
                    "sugerencia": obs.sugerencia,
                })

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "es_valido": resultado.es_valido,
                    "mensaje_resumen": resultado.mensaje_resumen,
                    "total_observaciones": resultado.total_observaciones,
                    "por_severidad": resultado.observaciones_por_severidad,
                    "observaciones": por_severidad,
                },
                metadata={"proyecto_id": proyecto_id}
            )

        except ValueError as e:
            # No existe documento
            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "es_valido": False,
                    "mensaje_resumen": str(e),
                    "total_observaciones": 0,
                },
                metadata={"proyecto_id": proyecto_id}
            )
        except Exception as e:
            logger.error(f"Error en validación: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al validar documento: {str(e)}"
            )


@registro_herramientas.registrar
class ConsultarProgresoGeneracion(Herramienta):
    """Consulta el progreso de generación por capítulo."""

    nombre = "consultar_progreso_generacion"
    descripcion = """Consulta el progreso de generación de cada capítulo del EIA.

Retorna para cada capítulo (1-11):
- Estado (pendiente, generando, completado, error)
- Porcentaje de progreso
- Palabras generadas
- Tiempo estimado si está pendiente

Usa esta herramienta cuando:
- El usuario pregunte qué capítulos faltan
- Se necesite planificar qué generar primero
- Haya preguntas sobre el avance del documento"""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

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
                    "description": "ID del proyecto",
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta la consulta de progreso."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay conexión a base de datos disponible"
            )

        try:
            service = get_generacion_service()

            progreso = await service.get_progreso_generacion(
                db=db,
                proyecto_id=proyecto_id
            )

            completados = sum(1 for p in progreso if p.estado == 'completado')
            total_palabras = sum(p.palabras_generadas for p in progreso)

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "resumen": {
                        "completados": completados,
                        "total": 11,
                        "porcentaje": f"{(completados / 11) * 100:.1f}%",
                        "total_palabras": total_palabras,
                    },
                    "capitulos": [
                        {
                            "numero": p.capitulo_numero,
                            "titulo": p.titulo,
                            "estado": p.estado,
                            "palabras": p.palabras_generadas,
                        }
                        for p in progreso
                    ],
                },
                metadata={"proyecto_id": proyecto_id}
            )

        except Exception as e:
            logger.error(f"Error consultando progreso: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al consultar progreso: {str(e)}"
            )


@registro_herramientas.registrar
class ConsultarVersionesDocumento(Herramienta):
    """Consulta el historial de versiones del documento EIA."""

    nombre = "consultar_versiones_documento"
    descripcion = """Consulta el historial de versiones guardadas del documento EIA.

Retorna:
- Lista de todas las versiones con fecha y descripción
- Quién creó cada versión
- Permite identificar versiones para restaurar

Usa esta herramienta cuando:
- El usuario pregunte por versiones anteriores
- Se necesite revisar el historial de cambios
- Haya intención de restaurar una versión anterior"""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

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
                    "description": "ID del proyecto",
                },
            },
            "required": ["proyecto_id"],
        }

    async def ejecutar(
        self,
        proyecto_id: int,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta la consulta de versiones."""
        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay conexión a base de datos disponible"
            )

        try:
            service = get_generacion_service()

            versiones = await service.listar_versiones(
                db=db,
                proyecto_id=proyecto_id
            )

            if not versiones:
                return ResultadoHerramienta(
                    exito=True,
                    contenido={
                        "mensaje": "No hay versiones guardadas del documento. Use 'crear_version_documento' para crear snapshots.",
                        "versiones": [],
                    },
                    metadata={"proyecto_id": proyecto_id}
                )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "total_versiones": len(versiones),
                    "versiones": [
                        {
                            "version": v.version,
                            "cambios": v.cambios,
                            "creado_por": v.creado_por,
                            "fecha": v.created_at.isoformat(),
                        }
                        for v in versiones
                    ],
                },
                metadata={"proyecto_id": proyecto_id}
            )

        except Exception as e:
            logger.error(f"Error consultando versiones: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Error al consultar versiones: {str(e)}"
            )
