"""
Servicio de Extraccion de Documentos con IA.
Extrae datos estructurados de documentos tecnicos usando Claude Vision.
"""
import logging
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.recopilacion import (
    ExtraccionDocumento, ContenidoEIA, PreguntaRecopilacion
)
from app.db.models.proyecto import Proyecto
from app.schemas.recopilacion import (
    ExtraccionDocumentoResponse, MapeoSeccionSugerido
)
from app.core.config import settings

logger = logging.getLogger(__name__)


# Tipos de documentos tecnicos reconocidos
TIPOS_DOCUMENTO = {
    "informe_climatologico": {
        "nombre": "Informe Climatologico",
        "capitulo": 3,
        "secciones": ["clima"],
        "campos_extraer": [
            "temperatura_media", "precipitacion_anual", "tipo_clima",
            "periodo_registro", "fuentes_datos_clima"
        ]
    },
    "informe_calidad_aire": {
        "nombre": "Informe de Calidad del Aire",
        "capitulo": 3,
        "secciones": ["calidad_aire"],
        "campos_extraer": [
            "campanas_realizadas", "estaciones_monitoreo",
            "resultados_mp10", "resultados_mp25"
        ]
    },
    "informe_hidrogeologico": {
        "nombre": "Informe Hidrogeologico",
        "capitulo": 3,
        "secciones": ["hidrogeologia"],
        "campos_extraer": [
            "sondajes_realizados", "unidades_acuiferas",
            "niveles_freaticos", "calidad_agua_subterranea"
        ]
    },
    "informe_flora": {
        "nombre": "Informe de Flora y Vegetacion",
        "capitulo": 3,
        "secciones": ["flora"],
        "campos_extraer": [
            "metodologia_flora", "formaciones_vegetacionales",
            "especies_totales", "especies_conservacion"
        ]
    },
    "informe_fauna": {
        "nombre": "Informe de Fauna",
        "capitulo": 3,
        "secciones": ["fauna"],
        "campos_extraer": [
            "metodologia_fauna", "mamiferos_identificados",
            "aves_identificadas", "reptiles_identificados", "fauna_conservacion"
        ]
    },
    "informe_arqueologico": {
        "nombre": "Informe Arqueologico",
        "capitulo": 3,
        "secciones": ["arqueologia"],
        "campos_extraer": [
            "prospeccion_realizada", "sitios_identificados", "autorizacion_cmn"
        ]
    },
    "informe_medio_humano": {
        "nombre": "Informe de Medio Humano",
        "capitulo": 3,
        "secciones": ["medio_humano"],
        "campos_extraer": [
            "comunidades_identificadas", "poblacion_total",
            "actividades_economicas", "servicios_basicos"
        ]
    },
    "ficha_proyecto": {
        "nombre": "Ficha de Proyecto",
        "capitulo": 1,
        "secciones": ["antecedentes", "titular", "localizacion"],
        "campos_extraer": [
            "nombre_proyecto", "objetivo_proyecto", "razon_social",
            "rut_titular", "region", "comuna", "superficie_total"
        ]
    }
}


class ExtraccionDocumentosService:
    """
    Servicio para extraer datos de documentos tecnicos con IA.

    Responsabilidades:
    - Procesar documentos PDF/imagenes con Claude Vision
    - Identificar tipo de documento automaticamente
    - Extraer datos estructurados relevantes
    - Sugerir mapeo a secciones del EIA
    - Persistir historial de extracciones
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._anthropic_client = None

    @property
    def anthropic_client(self):
        """Cliente Anthropic lazy-loaded."""
        if self._anthropic_client is None:
            import anthropic
            self._anthropic_client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )
        return self._anthropic_client

    async def extraer_datos_documento(
        self,
        proyecto_id: int,
        documento_id: int,
        tipo_documento: Optional[str] = None,
        forzar_reprocesar: bool = False
    ) -> ExtraccionDocumentoResponse:
        """
        Extrae datos de un documento usando Claude Vision.

        Args:
            proyecto_id: ID del proyecto
            documento_id: ID del documento a procesar
            tipo_documento: Tipo de documento (opcional, se detecta automaticamente)
            forzar_reprocesar: Si True, reprocesa aunque ya exista extraccion

        Returns:
            ExtraccionDocumentoResponse con datos extraidos
        """
        # Verificar si ya existe extraccion
        if not forzar_reprocesar:
            extraccion_existente = await self._get_extraccion_existente(
                proyecto_id, documento_id
            )
            if extraccion_existente and extraccion_existente.estado == "completado":
                return ExtraccionDocumentoResponse.model_validate(
                    extraccion_existente.to_dict()
                )

        # Obtener proyecto y tipo
        proyecto = await self._get_proyecto(proyecto_id)
        if not proyecto:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")

        # Obtener documento (asumimos que existe modelo Documento)
        documento_path = await self._get_documento_path(documento_id)
        if not documento_path:
            raise ValueError(f"Documento {documento_id} no encontrado")

        # Crear o actualizar registro de extraccion
        extraccion = await self._get_or_create_extraccion(
            proyecto_id, documento_id, tipo_documento
        )
        extraccion.estado = "procesando"
        await self.db.commit()

        try:
            # Leer contenido del documento
            contenido_base64 = await self._leer_documento(documento_path)

            # Detectar tipo de documento si no se especifica
            if not tipo_documento:
                tipo_documento = await self._detectar_tipo_documento(
                    contenido_base64, documento_path
                )
                extraccion.tipo_documento = tipo_documento

            # Extraer datos segun tipo
            datos_extraidos = await self._extraer_con_claude(
                contenido_base64,
                documento_path,
                tipo_documento,
                proyecto.tipo_proyecto_id
            )

            # Generar mapeo a secciones
            mapeo_secciones = self._generar_mapeo_secciones(
                datos_extraidos, tipo_documento
            )

            # Actualizar extraccion
            extraccion.datos_extraidos = datos_extraidos
            extraccion.mapeo_secciones = [m.model_dump() for m in mapeo_secciones]
            extraccion.confianza_extraccion = self._calcular_confianza(datos_extraidos)
            extraccion.marcar_completado(extraccion.confianza_extraccion)

            await self.db.commit()
            await self.db.refresh(extraccion)

            return ExtraccionDocumentoResponse.model_validate(extraccion.to_dict())

        except Exception as e:
            logger.error(f"Error extrayendo datos de documento {documento_id}: {e}")
            extraccion.marcar_error(str(e))
            await self.db.commit()
            raise

    async def aplicar_extraccion(
        self,
        proyecto_id: int,
        extraccion_id: int,
        mapeos_confirmados: List[MapeoSeccionSugerido]
    ) -> Dict[str, Any]:
        """
        Aplica los datos extraidos a las secciones del EIA.

        Args:
            proyecto_id: ID del proyecto
            extraccion_id: ID de la extraccion
            mapeos_confirmados: Lista de mapeos confirmados por el usuario

        Returns:
            Dict con secciones actualizadas
        """
        secciones_actualizadas = []

        for mapeo in mapeos_confirmados:
            # Obtener o crear contenido de la seccion
            contenido = await self._get_or_create_contenido(
                proyecto_id,
                mapeo.capitulo_numero,
                mapeo.seccion_codigo
            )

            # Actualizar contenido
            if contenido.contenido is None:
                contenido.contenido = {}
            contenido.contenido[mapeo.campo] = mapeo.valor

            secciones_actualizadas.append({
                "capitulo": mapeo.capitulo_numero,
                "seccion": mapeo.seccion_codigo,
                "campo": mapeo.campo
            })

        await self.db.commit()

        return {
            "secciones_actualizadas": secciones_actualizadas,
            "total": len(secciones_actualizadas)
        }

    async def _extraer_con_claude(
        self,
        contenido_base64: str,
        documento_path: str,
        tipo_documento: str,
        tipo_proyecto_id: int
    ) -> Dict[str, Any]:
        """Extrae datos del documento usando Claude Vision."""

        # Obtener campos a extraer segun tipo de documento
        config_tipo = TIPOS_DOCUMENTO.get(tipo_documento, {})
        campos_extraer = config_tipo.get("campos_extraer", [])

        # Obtener preguntas relacionadas para contexto
        preguntas_contexto = await self._get_preguntas_para_campos(
            tipo_proyecto_id, campos_extraer
        )

        # Construir prompt de extraccion
        prompt = self._construir_prompt_extraccion(
            tipo_documento, campos_extraer, preguntas_contexto
        )

        # Determinar media type
        extension = Path(documento_path).suffix.lower()
        media_type = self._get_media_type(extension)

        # Llamar a Claude Vision
        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image" if media_type.startswith("image") else "document",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": contenido_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        # Parsear respuesta
        return self._parsear_respuesta_claude(response.content[0].text)

    def _construir_prompt_extraccion(
        self,
        tipo_documento: str,
        campos_extraer: List[str],
        preguntas_contexto: List[PreguntaRecopilacion]
    ) -> str:
        """Construye el prompt para extraccion de datos."""

        campos_descripcion = "\n".join([
            f"- {p.codigo_pregunta}: {p.pregunta}"
            for p in preguntas_contexto
        ])

        if not campos_descripcion:
            campos_descripcion = "\n".join([f"- {c}" for c in campos_extraer])

        return f"""Analiza este documento tecnico de tipo "{tipo_documento}" y extrae la siguiente informacion estructurada.

CAMPOS A EXTRAER:
{campos_descripcion}

INSTRUCCIONES:
1. Extrae SOLO la informacion que aparece explicitamente en el documento
2. Si un campo no tiene informacion disponible, indica "NO_DISPONIBLE"
3. Para valores numericos, incluye las unidades
4. Para listas (como especies), separa los elementos con punto y coma
5. Responde en formato JSON valido

FORMATO DE RESPUESTA:
{{
    "campo1": "valor1",
    "campo2": "valor2",
    ...
}}

Extrae la informacion del documento:"""

    def _parsear_respuesta_claude(self, respuesta: str) -> Dict[str, Any]:
        """Parsea la respuesta de Claude a un diccionario."""
        import json
        import re

        # Buscar JSON en la respuesta
        json_match = re.search(r'\{[^{}]*\}', respuesta, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Si no encuentra JSON, intentar parsear toda la respuesta
        try:
            return json.loads(respuesta)
        except json.JSONDecodeError:
            logger.warning("No se pudo parsear respuesta como JSON")
            return {"raw_response": respuesta}

    def _generar_mapeo_secciones(
        self,
        datos_extraidos: Dict[str, Any],
        tipo_documento: str
    ) -> List[MapeoSeccionSugerido]:
        """Genera mapeo sugerido de datos a secciones del EIA."""
        config_tipo = TIPOS_DOCUMENTO.get(tipo_documento, {})
        capitulo = config_tipo.get("capitulo", 3)
        secciones = config_tipo.get("secciones", [])

        mapeos = []
        seccion_default = secciones[0] if secciones else "general"

        for campo, valor in datos_extraidos.items():
            if valor and valor != "NO_DISPONIBLE":
                # Determinar seccion apropiada
                seccion = self._determinar_seccion_campo(campo, secciones)

                mapeos.append(MapeoSeccionSugerido(
                    capitulo_numero=capitulo,
                    seccion_codigo=seccion or seccion_default,
                    campo=campo,
                    valor=valor,
                    confianza=0.8
                ))

        return mapeos

    def _determinar_seccion_campo(
        self,
        campo: str,
        secciones_disponibles: List[str]
    ) -> Optional[str]:
        """Determina la seccion apropiada para un campo."""
        # Mapeo simple basado en prefijo del campo
        for seccion in secciones_disponibles:
            if seccion in campo or campo.startswith(seccion):
                return seccion

        return secciones_disponibles[0] if secciones_disponibles else None

    def _calcular_confianza(self, datos_extraidos: Dict[str, Any]) -> float:
        """Calcula confianza de la extraccion."""
        if not datos_extraidos:
            return 0.0

        total = len(datos_extraidos)
        validos = sum(
            1 for v in datos_extraidos.values()
            if v and v != "NO_DISPONIBLE"
        )

        return round(validos / total, 2) if total > 0 else 0.0

    async def _detectar_tipo_documento(
        self,
        contenido_base64: str,
        documento_path: str
    ) -> str:
        """Detecta automaticamente el tipo de documento."""
        extension = Path(documento_path).suffix.lower()
        media_type = self._get_media_type(extension)

        prompt = """Analiza este documento y determina su tipo.

TIPOS POSIBLES:
- informe_climatologico: Informes de clima y meteorologia
- informe_calidad_aire: Monitoreo de calidad del aire
- informe_hidrogeologico: Estudios hidrogeologicos
- informe_flora: Estudios de flora y vegetacion
- informe_fauna: Estudios de fauna
- informe_arqueologico: Estudios arqueologicos
- informe_medio_humano: Estudios sociales/antropologicos
- ficha_proyecto: Descripcion general del proyecto
- otro: Otro tipo de documento

Responde SOLO con el codigo del tipo (ej: "informe_flora")"""

        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image" if media_type.startswith("image") else "document",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": contenido_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        tipo = response.content[0].text.strip().lower()
        return tipo if tipo in TIPOS_DOCUMENTO else "otro"

    def _get_media_type(self, extension: str) -> str:
        """Obtiene el media type segun extension."""
        media_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        return media_types.get(extension, "application/pdf")

    async def _leer_documento(self, documento_path: str) -> str:
        """Lee un documento y lo convierte a base64."""
        path = Path(documento_path)
        if not path.exists():
            raise FileNotFoundError(f"Documento no encontrado: {documento_path}")

        with open(path, "rb") as f:
            contenido = f.read()

        return base64.standard_b64encode(contenido).decode("utf-8")

    async def _get_proyecto(self, proyecto_id: int) -> Optional[Proyecto]:
        """Obtiene un proyecto por ID."""
        result = await self.db.execute(
            select(Proyecto).where(Proyecto.id == proyecto_id)
        )
        return result.scalar_one_or_none()

    async def _get_documento_path(self, documento_id: int) -> Optional[str]:
        """Obtiene la ruta de un documento."""
        # TODO: Implementar segun modelo de documentos
        # Por ahora retorna un path placeholder
        return f"/var/www/mineria/data/documentos/{documento_id}.pdf"

    async def _get_extraccion_existente(
        self,
        proyecto_id: int,
        documento_id: int
    ) -> Optional[ExtraccionDocumento]:
        """Obtiene extraccion existente."""
        result = await self.db.execute(
            select(ExtraccionDocumento).where(
                and_(
                    ExtraccionDocumento.proyecto_id == proyecto_id,
                    ExtraccionDocumento.documento_id == documento_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_or_create_extraccion(
        self,
        proyecto_id: int,
        documento_id: int,
        tipo_documento: Optional[str]
    ) -> ExtraccionDocumento:
        """Obtiene o crea registro de extraccion."""
        extraccion = await self._get_extraccion_existente(proyecto_id, documento_id)

        if not extraccion:
            extraccion = ExtraccionDocumento(
                proyecto_id=proyecto_id,
                documento_id=documento_id,
                tipo_documento=tipo_documento,
                estado="pendiente"
            )
            self.db.add(extraccion)
            await self.db.flush()

        return extraccion

    async def _get_preguntas_para_campos(
        self,
        tipo_proyecto_id: int,
        campos: List[str]
    ) -> List[PreguntaRecopilacion]:
        """Obtiene preguntas relacionadas con los campos."""
        if not campos:
            return []

        result = await self.db.execute(
            select(PreguntaRecopilacion).where(
                and_(
                    PreguntaRecopilacion.tipo_proyecto_id == tipo_proyecto_id,
                    PreguntaRecopilacion.codigo_pregunta.in_(campos),
                    PreguntaRecopilacion.activo == True
                )
            )
        )
        return result.scalars().all()

    async def _get_or_create_contenido(
        self,
        proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str
    ) -> ContenidoEIA:
        """Obtiene o crea contenido de seccion."""
        result = await self.db.execute(
            select(ContenidoEIA).where(
                and_(
                    ContenidoEIA.proyecto_id == proyecto_id,
                    ContenidoEIA.capitulo_numero == capitulo_numero,
                    ContenidoEIA.seccion_codigo == seccion_codigo
                )
            )
        )
        contenido = result.scalar_one_or_none()

        if not contenido:
            contenido = ContenidoEIA(
                proyecto_id=proyecto_id,
                capitulo_numero=capitulo_numero,
                seccion_codigo=seccion_codigo,
                contenido={},
                estado="pendiente"
            )
            self.db.add(contenido)
            await self.db.flush()

        return contenido
