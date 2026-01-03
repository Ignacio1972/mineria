"""
Herramientas del asistente para Recopilacion Guiada (Fase 3).
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    Herramienta, ResultadoHerramienta, CategoriaHerramienta,
    ContextoHerramienta, PermisoHerramienta, registro_herramientas
)
from app.services.recopilacion import RecopilacionService, ExtraccionDocumentosService

logger = logging.getLogger(__name__)


@registro_herramientas.registrar
class IniciarRecopilacionCapitulo(Herramienta):
    """Inicia o retoma la recopilacion de un capitulo del EIA."""

    nombre = "iniciar_recopilacion_capitulo"
    descripcion = """Inicia la recopilacion guiada de un capitulo del EIA.

    Usa esta herramienta cuando:
    - El usuario quiera trabajar en un capitulo especifico del EIA
    - Se haya completado la estructura del EIA (Fase 2)
    - El usuario pregunte "que informacion necesito para el capitulo X"

    Retorna: Lista de secciones con preguntas pendientes, progreso actual
    y mensaje de bienvenida.

    IMPORTANTE: Al iniciar un capitulo, presenta las preguntas de la primera
    seccion pendiente y guia al usuario paso a paso."""

    categoria = CategoriaHerramienta.ACCION
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "capitulo_numero": {
                    "type": "integer",
                    "description": "Numero del capitulo a trabajar (1-11)",
                    "minimum": 1,
                    "maximum": 11
                }
            },
            "required": ["capitulo_numero"]
        }

    async def ejecutar(
        self,
        db: AsyncSession,
        proyecto_id: int,
        capitulo_numero: int,
        **kwargs
    ) -> ResultadoHerramienta:
        try:
            service = RecopilacionService(db)
            resultado = await service.iniciar_capitulo(proyecto_id, capitulo_numero)

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "capitulo_numero": resultado.capitulo_numero,
                    "titulo": resultado.titulo,
                    "secciones": [s.model_dump() for s in resultado.secciones],
                    "total_preguntas": resultado.total_preguntas,
                    "preguntas_obligatorias": resultado.preguntas_obligatorias,
                    "mensaje": resultado.mensaje_bienvenida
                },
                metadata={"accion": "iniciar_capitulo"}
            )
        except Exception as e:
            logger.error(f"Error iniciando capitulo {capitulo_numero}: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class GuardarContenidoSeccion(Herramienta):
    """Guarda respuestas de una seccion del EIA."""

    nombre = "guardar_contenido_seccion"
    descripcion = """Guarda las respuestas del usuario en una seccion del EIA.

    Usa esta herramienta cuando:
    - El usuario proporcione informacion para una seccion
    - Se necesite persistir respuestas recopiladas
    - El usuario confirme datos extraidos de documentos

    Puede guardar una o multiples respuestas a la vez.

    IMPORTANTE: Despues de guardar, informa al usuario el progreso
    de la seccion y sugiere la siguiente pregunta o seccion."""

    categoria = CategoriaHerramienta.ACCION
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.ESCRITURA]

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "capitulo_numero": {
                    "type": "integer",
                    "description": "Numero del capitulo"
                },
                "seccion_codigo": {
                    "type": "string",
                    "description": "Codigo de la seccion (ej: 'antecedentes', 'localizacion')"
                },
                "respuestas": {
                    "type": "object",
                    "description": "Diccionario de respuestas {codigo_pregunta: valor}",
                    "additionalProperties": True
                }
            },
            "required": ["capitulo_numero", "seccion_codigo", "respuestas"]
        }

    async def ejecutar(
        self,
        db: AsyncSession,
        proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str,
        respuestas: Dict[str, Any],
        **kwargs
    ) -> ResultadoHerramienta:
        try:
            service = RecopilacionService(db)
            contenido = await service.guardar_respuestas(
                proyecto_id, capitulo_numero, seccion_codigo, respuestas
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "seccion": seccion_codigo,
                    "estado": contenido.estado,
                    "progreso": contenido.progreso,
                    "respuestas_guardadas": len(respuestas),
                    "mensaje": f"Se guardaron {len(respuestas)} respuestas. Progreso de la seccion: {contenido.progreso}%"
                },
                metadata={"accion": "guardar_respuestas"}
            )
        except Exception as e:
            logger.error(f"Error guardando respuestas: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ConsultarProgresoCapitulo(Herramienta):
    """Consulta el progreso de un capitulo o del EIA completo."""

    nombre = "consultar_progreso_capitulo"
    descripcion = """Consulta el estado y progreso de recopilacion.

    Usa esta herramienta cuando:
    - El usuario pregunte "cuanto falta", "como voy", "que me falta"
    - Se necesite mostrar el estado general del EIA
    - Antes de sugerir la siguiente seccion a trabajar

    Si se especifica capitulo_numero, retorna progreso de ese capitulo.
    Si no, retorna progreso general del EIA completo."""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "capitulo_numero": {
                    "type": "integer",
                    "description": "Numero del capitulo (opcional, si no se especifica retorna progreso general)",
                    "minimum": 1,
                    "maximum": 11
                }
            },
            "required": []
        }

    async def ejecutar(
        self,
        db: AsyncSession,
        proyecto_id: int,
        capitulo_numero: Optional[int] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        try:
            service = RecopilacionService(db)

            if capitulo_numero:
                progreso = await service.get_progreso_capitulo(proyecto_id, capitulo_numero)
                return ResultadoHerramienta(
                    exito=True,
                    contenido=progreso.model_dump(),
                    metadata={"tipo": "progreso_capitulo"}
                )
            else:
                progreso = await service.get_progreso_general(proyecto_id)
                return ResultadoHerramienta(
                    exito=True,
                    contenido=progreso.model_dump(),
                    metadata={"tipo": "progreso_general"}
                )
        except Exception as e:
            logger.error(f"Error consultando progreso: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ExtraerDatosDocumento(Herramienta):
    """Extrae datos de un documento tecnico usando IA."""

    nombre = "extraer_datos_documento"
    descripcion = """Extrae datos estructurados de un documento tecnico usando Claude Vision.

    Usa esta herramienta cuando:
    - El usuario suba un documento tecnico (PDF, imagen)
    - Se necesite extraer informacion de un informe de linea base
    - El usuario mencione que tiene un estudio listo

    Tipos de documentos soportados:
    - Informes climatologicos
    - Informes de calidad del aire
    - Informes hidrogeologicos
    - Informes de flora/fauna
    - Informes arqueologicos
    - Fichas de proyecto

    IMPORTANTE: Despues de extraer, muestra los datos y pregunta al usuario
    si desea aplicarlos a las secciones correspondientes."""

    categoria = CategoriaHerramienta.ACCION
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = True
    permisos = [PermisoHerramienta.ESCRITURA]

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "documento_id": {
                    "type": "integer",
                    "description": "ID del documento a procesar"
                },
                "tipo_documento": {
                    "type": "string",
                    "description": "Tipo de documento (opcional, se detecta automaticamente)",
                    "enum": [
                        "informe_climatologico", "informe_calidad_aire",
                        "informe_hidrogeologico", "informe_flora", "informe_fauna",
                        "informe_arqueologico", "informe_medio_humano", "ficha_proyecto"
                    ]
                }
            },
            "required": ["documento_id"]
        }

    async def ejecutar(
        self,
        db: AsyncSession,
        proyecto_id: int,
        documento_id: int,
        tipo_documento: Optional[str] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        try:
            service = ExtraccionDocumentosService(db)
            extraccion = await service.extraer_datos_documento(
                proyecto_id, documento_id, tipo_documento
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "extraccion_id": extraccion.id,
                    "tipo_documento": extraccion.tipo_documento,
                    "datos_extraidos": extraccion.datos_extraidos,
                    "mapeo_sugerido": [m.model_dump() for m in extraccion.mapeo_secciones],
                    "confianza": extraccion.confianza_extraccion,
                    "mensaje": f"Se extrajeron {len(extraccion.datos_extraidos)} campos con {extraccion.confianza_extraccion*100:.0f}% de confianza"
                },
                metadata={"accion": "extraer_documento"}
            )
        except Exception as e:
            logger.error(f"Error extrayendo datos de documento {documento_id}: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ValidarConsistenciaEIA(Herramienta):
    """Valida la consistencia entre capitulos del EIA."""

    nombre = "validar_consistencia_eia"
    descripcion = """Detecta inconsistencias entre capitulos del EIA.

    Usa esta herramienta cuando:
    - El usuario pregunte si hay errores o inconsistencias
    - Se complete un capitulo y se quiera verificar coherencia
    - Antes de generar el documento final

    Valida reglas como:
    - Coordenadas consistentes entre capitulos
    - Superficie coherente con area de influencia
    - Especies en conservacion tienen medidas asociadas
    - Sitios arqueologicos tienen proteccion

    IMPORTANTE: Si detecta inconsistencias de severidad "error",
    el usuario DEBE corregirlas antes de continuar."""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "capitulos": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Lista de capitulos a validar (opcional, si no se especifica valida todos)"
                }
            },
            "required": []
        }

    async def ejecutar(
        self,
        db: AsyncSession,
        proyecto_id: int,
        capitulos: Optional[List[int]] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        try:
            service = RecopilacionService(db)
            resultado = await service.validar_consistencia(proyecto_id, capitulos)

            mensaje = "El EIA es consistente." if resultado.es_consistente else \
                f"Se detectaron {len(resultado.inconsistencias)} inconsistencias ({resultado.errores} errores, {resultado.warnings} advertencias)"

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "es_consistente": resultado.es_consistente,
                    "total_reglas": resultado.total_reglas_evaluadas,
                    "errores": resultado.errores,
                    "warnings": resultado.warnings,
                    "inconsistencias": [i.model_dump() for i in resultado.inconsistencias],
                    "mensaje": mensaje
                },
                metadata={"accion": "validar_consistencia"}
            )
        except Exception as e:
            logger.error(f"Error validando consistencia: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class SugerirRedaccion(Herramienta):
    """Sugiere redaccion para una seccion basada en corpus SEA."""

    nombre = "sugerir_redaccion"
    descripcion = """Genera sugerencias de redaccion basadas en EIAs aprobados.

    Usa esta herramienta cuando:
    - El usuario no sepa como redactar una seccion
    - Se necesite ejemplo de redaccion tecnica
    - El usuario pida ayuda con el texto

    Busca en el corpus de EIAs aprobados y documentos SEA
    para sugerir redaccion apropiada.

    IMPORTANTE: Las sugerencias son referencias, el usuario debe
    adaptar el texto a su proyecto especifico."""

    categoria = CategoriaHerramienta.CONSULTA
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "capitulo_numero": {
                    "type": "integer",
                    "description": "Numero del capitulo"
                },
                "seccion_codigo": {
                    "type": "string",
                    "description": "Codigo de la seccion"
                },
                "campo": {
                    "type": "string",
                    "description": "Campo especifico (opcional)"
                },
                "contexto": {
                    "type": "string",
                    "description": "Contexto adicional para mejorar la sugerencia"
                }
            },
            "required": ["capitulo_numero", "seccion_codigo"]
        }

    async def ejecutar(
        self,
        db: AsyncSession,
        proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str,
        campo: Optional[str] = None,
        contexto: Optional[str] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        # Por ahora retornamos sugerencia basica
        # TODO: Integrar con RAG para buscar en corpus
        try:
            sugerencias = self._generar_sugerencias_basicas(
                capitulo_numero, seccion_codigo, campo
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "sugerencias": sugerencias,
                    "total": len(sugerencias),
                    "mensaje": f"Se encontraron {len(sugerencias)} sugerencias de redaccion"
                },
                metadata={"accion": "sugerir_redaccion"}
            )
        except Exception as e:
            logger.error(f"Error generando sugerencias: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )

    def _generar_sugerencias_basicas(
        self,
        capitulo: int,
        seccion: str,
        campo: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Genera sugerencias basicas de redaccion."""
        # Templates basicos por seccion
        templates = {
            (1, "antecedentes"): [
                {
                    "campo": "objetivo_proyecto",
                    "texto": "El objetivo del presente proyecto es [describir objetivo principal], mediante [descripcion de actividades principales], con el fin de [beneficio esperado].",
                    "fuente": "template_eia_mineria",
                    "confianza": 0.7
                }
            ],
            (3, "clima"): [
                {
                    "campo": "tipo_clima",
                    "texto": "Segun la clasificacion climatica de Koppen, el area del proyecto corresponde a un clima [tipo], caracterizado por [descripcion de caracteristicas principales].",
                    "fuente": "corpus_sea",
                    "confianza": 0.8
                }
            ],
            (3, "flora"): [
                {
                    "campo": "metodologia_flora",
                    "texto": "La caracterizacion de flora y vegetacion se realizo mediante transectos de [longitud] m y parcelas de [dimension] m2, distribuidos de manera representativa en el area de influencia. Se realizaron campanas en [estaciones], cubriendo la variabilidad estacional del area.",
                    "fuente": "corpus_sea",
                    "confianza": 0.85
                }
            ]
        }

        key = (capitulo, seccion)
        sugerencias = templates.get(key, [])

        if campo:
            sugerencias = [s for s in sugerencias if s.get("campo") == campo]

        return sugerencias


@registro_herramientas.registrar
class VincularDocumentoSeccion(Herramienta):
    """Vincula un documento a una seccion del EIA."""

    nombre = "vincular_documento_seccion"
    descripcion = """Vincula un documento tecnico a una seccion del EIA.

    Usa esta herramienta cuando:
    - El usuario indique que un documento corresponde a una seccion
    - Se necesite asociar estudios a capitulos especificos
    - Despues de subir un documento se quiera asociar

    La vinculacion permite trackear que documentos sustentan
    cada seccion del EIA."""

    categoria = CategoriaHerramienta.ACCION
    contexto_requerido = ContextoHerramienta.PROYECTO
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.ESCRITURA]

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "documento_id": {
                    "type": "integer",
                    "description": "ID del documento a vincular"
                },
                "capitulo_numero": {
                    "type": "integer",
                    "description": "Numero del capitulo"
                },
                "seccion_codigo": {
                    "type": "string",
                    "description": "Codigo de la seccion"
                }
            },
            "required": ["documento_id", "capitulo_numero", "seccion_codigo"]
        }

    async def ejecutar(
        self,
        db: AsyncSession,
        proyecto_id: int,
        documento_id: int,
        capitulo_numero: int,
        seccion_codigo: str,
        **kwargs
    ) -> ResultadoHerramienta:
        try:
            service = RecopilacionService(db)
            contenido = await service.vincular_documento(
                proyecto_id, documento_id, capitulo_numero, seccion_codigo
            )

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "documento_id": documento_id,
                    "seccion": seccion_codigo,
                    "total_documentos": len(contenido.documentos_vinculados),
                    "mensaje": f"Documento {documento_id} vinculado a seccion {seccion_codigo}"
                },
                metadata={"accion": "vincular_documento"}
            )
        except Exception as e:
            logger.error(f"Error vinculando documento: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )
