"""
Servicio de Generación de Texto con Claude (LLM).

Genera contenido de capítulos EIA basado en templates,
contenido recopilado y contexto del proyecto.
"""
import logging
from typing import Dict, Any, Optional, List
import anthropic
from jinja2 import Template

from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Proyecto
from app.db.models.generacion_eia import TemplateCapitulo
from app.db.models.recopilacion import ContenidoEIA
from app.db.models.config_industria import TipoProyecto


logger = logging.getLogger(__name__)


class GeneradorTextoService:
    """Servicio para generar texto de capítulos EIA con Claude."""

    def __init__(self):
        """Inicializa el servicio."""
        self._anthropic_client: Optional[anthropic.Anthropic] = None
        self.modelo = settings.LLM_MODEL or "claude-sonnet-4-20250514"
        self.max_tokens = 16000  # Claude Sonnet 4 soporta outputs largos

    @property
    def cliente(self) -> anthropic.Anthropic:
        """Cliente Anthropic lazy-loaded."""
        if self._anthropic_client is None:
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY no configurada")
            self._anthropic_client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )
        return self._anthropic_client

    async def generar_texto_capitulo(
        self,
        db: AsyncSession,
        proyecto_id: int,
        capitulo_numero: int,
        instrucciones_adicionales: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera el texto completo de un capítulo del EIA.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            capitulo_numero: Número del capítulo (1-11)
            instrucciones_adicionales: Instrucciones opcionales del usuario

        Returns:
            Dict con 'contenido', 'titulo', 'subsecciones', 'metadatos'
        """
        logger.info(f"Generando capítulo {capitulo_numero} para proyecto {proyecto_id}")

        # 1. Obtener contexto del proyecto
        contexto = await self._get_contexto_proyecto(db, proyecto_id)

        # 2. Obtener template del capítulo
        template = await self._get_template_capitulo(db, contexto['tipo_proyecto_id'], capitulo_numero)

        # 3. Obtener contenido recopilado
        contenido_recopilado = await self._get_contenido_recopilado(db, proyecto_id, capitulo_numero)

        # 4. Construir prompt
        prompt = self._construir_prompt(
            template=template,
            contexto=contexto,
            contenido_recopilado=contenido_recopilado,
            instrucciones_adicionales=instrucciones_adicionales
        )

        # 5. Generar con Claude
        texto_generado = await self._generar_con_claude(prompt, capitulo_numero)

        # 6. Post-procesar
        resultado = self._post_procesar(texto_generado, capitulo_numero, template)

        logger.info(f"Capítulo {capitulo_numero} generado exitosamente ({len(resultado['contenido'])} caracteres)")

        return resultado

    async def mejorar_redaccion(
        self,
        texto: str,
        estilo: str = "tecnico",
        instrucciones: Optional[str] = None
    ) -> str:
        """
        Mejora la redacción de un texto existente.

        Args:
            texto: Texto a mejorar
            estilo: Estilo de redacción (tecnico, formal, etc.)
            instrucciones: Instrucciones específicas

        Returns:
            Texto mejorado
        """
        prompt = f"""Mejora la redacción del siguiente texto manteniendo un estilo {estilo}.

INSTRUCCIONES:
- Mantener el contenido técnico y datos específicos
- Mejorar claridad y cohesión
- Usar lenguaje profesional y objetivo
- Corregir errores gramaticales
{"- " + instrucciones if instrucciones else ""}

TEXTO ORIGINAL:
{texto}

Por favor, proporciona el texto mejorado sin comentarios adicionales."""

        return await self._generar_con_claude(prompt, contexto_adicional="mejora_redaccion")

    async def expandir_seccion(
        self,
        db: AsyncSession,
        proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str,
        texto_actual: str,
        instrucciones: str
    ) -> str:
        """
        Expande una sección específica con más detalle.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            capitulo_numero: Número del capítulo
            seccion_codigo: Código de la sección
            texto_actual: Texto actual de la sección
            instrucciones: Instrucciones de expansión

        Returns:
            Texto expandido
        """
        # Obtener contexto del proyecto
        contexto = await self._get_contexto_proyecto(db, proyecto_id)

        # Obtener contenido recopilado relevante
        contenido_recopilado = await self._get_contenido_recopilado(db, proyecto_id, capitulo_numero)

        prompt = f"""Expande la siguiente sección del capítulo {capitulo_numero} de un EIA.

CONTEXTO DEL PROYECTO:
- Nombre: {contexto['nombre']}
- Tipo: {contexto['tipo_proyecto']}
- Ubicación: {contexto.get('region', 'N/A')}, {contexto.get('comuna', 'N/A')}

TEXTO ACTUAL:
{texto_actual}

INSTRUCCIONES DE EXPANSIÓN:
{instrucciones}

DATOS DISPONIBLES:
{self._formatear_contenido_recopilado(contenido_recopilado)}

Por favor, proporciona la versión expandida de la sección manteniendo el estilo técnico y objetivo."""

        return await self._generar_con_claude(prompt, contexto_adicional=f"expansion_seccion_{seccion_codigo}")

    # =========================================================================
    # Métodos privados
    # =========================================================================

    async def _get_contexto_proyecto(self, db: AsyncSession, proyecto_id: int) -> Dict[str, Any]:
        """Obtiene el contexto completo del proyecto."""
        from sqlalchemy.orm import join
        from app.db.models.config_industria import SubtipoProyecto

        # Query con joins manuales para obtener tipo y subtipo
        query = select(
            Proyecto,
            TipoProyecto.nombre.label('tipo_nombre'),
            SubtipoProyecto.nombre.label('subtipo_nombre')
        ).outerjoin(
            TipoProyecto,
            Proyecto.tipo_proyecto_id == TipoProyecto.id
        ).outerjoin(
            SubtipoProyecto,
            Proyecto.subtipo_proyecto_id == SubtipoProyecto.id
        ).where(Proyecto.id == proyecto_id)

        result = await db.execute(query)
        row = result.one_or_none()

        if not row:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")

        proyecto = row[0]
        tipo_nombre = row[1] or 'N/A'
        subtipo_nombre = row[2] or 'N/A'

        return {
            'proyecto_id': proyecto.id,
            'nombre': proyecto.nombre,
            'tipo_proyecto_id': proyecto.tipo_proyecto_id,
            'tipo_proyecto': tipo_nombre,
            'subtipo_proyecto': subtipo_nombre,
            'titular': proyecto.titular,
            'region': proyecto.region,
            'comuna': proyecto.comuna,
            'superficie_ha': float(proyecto.superficie_ha) if proyecto.superficie_ha else None,
            'inversion_musd': float(proyecto.inversion_musd) if proyecto.inversion_musd else None,
            'descripcion': proyecto.descripcion,
            'fase': proyecto.fase,
        }

    async def _get_template_capitulo(
        self,
        db: AsyncSession,
        tipo_proyecto_id: int,
        capitulo_numero: int
    ) -> Dict[str, Any]:
        """Obtiene el template del capítulo para el tipo de proyecto."""
        query = select(TemplateCapitulo).where(
            TemplateCapitulo.tipo_proyecto_id == tipo_proyecto_id,
            TemplateCapitulo.capitulo_numero == capitulo_numero
        )

        result = await db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            # Template por defecto si no existe uno específico
            return {
                'titulo': f'Capítulo {capitulo_numero}',
                'template_prompt': f'Genera el capítulo {capitulo_numero} del EIA.',
                'estructura_esperada': {},
                'instrucciones_generacion': None,
                'ejemplos': None
            }

        return {
            'titulo': template.titulo,
            'template_prompt': template.template_prompt,
            'estructura_esperada': template.estructura_esperada or {},
            'instrucciones_generacion': template.instrucciones_generacion,
            'ejemplos': template.ejemplos
        }

    async def _get_contenido_recopilado(
        self,
        db: AsyncSession,
        proyecto_id: int,
        capitulo_numero: int
    ) -> Dict[str, Any]:
        """Obtiene el contenido recopilado para el capítulo."""
        # Buscar contenido recopilado del capítulo
        query = select(ContenidoEIA).where(
            ContenidoEIA.proyecto_id == proyecto_id,
            ContenidoEIA.capitulo_numero == capitulo_numero
        )

        result = await db.execute(query)
        contenidos = result.scalars().all()

        # Agrupar por sección
        contenido_por_seccion = {}
        for contenido in contenidos:
            seccion = contenido.seccion_codigo
            contenido_por_seccion[seccion] = contenido.contenido or {}

        return contenido_por_seccion

    def _construir_prompt(
        self,
        template: Dict[str, Any],
        contexto: Dict[str, Any],
        contenido_recopilado: Dict[str, Any],
        instrucciones_adicionales: Optional[str]
    ) -> str:
        """Construye el prompt completo para Claude."""
        # Renderizar template con datos del proyecto usando Jinja2
        try:
            template_jinja = Template(template['template_prompt'])
            prompt_base = template_jinja.render(**contexto)
        except Exception as e:
            logger.warning(f"Error renderizando template con Jinja2: {e}. Usando template sin procesar.")
            prompt_base = template['template_prompt']

        # Preparar secciones opcionales
        instrucciones_adicionales_str = ""
        if instrucciones_adicionales:
            instrucciones_adicionales_str = f"INSTRUCCIONES ADICIONALES:\n{instrucciones_adicionales}\n\n"

        ejemplos_str = ""
        if template.get('ejemplos'):
            ejemplos_str = f"EJEMPLOS DE REFERENCIA:\n{template.get('ejemplos')}\n\n"

        instrucciones_gen_str = ""
        if template.get('instrucciones_generacion'):
            instrucciones_gen_str = f"INSTRUCCIONES DE GENERACIÓN:\n{template.get('instrucciones_generacion')}\n\n"

        # Construir prompt completo
        prompt = f"""Eres un experto en elaboración de Estudios de Impacto Ambiental (EIA) en Chile.

Tu tarea es generar el siguiente capítulo de un EIA siguiendo las normas del SEA (Servicio de Evaluación Ambiental).

INSTRUCCIONES BASE:
{prompt_base}

CONTEXTO DEL PROYECTO:
- Nombre: {contexto['nombre']}
- Tipo: {contexto['tipo_proyecto']} - {contexto['subtipo_proyecto']}
- Titular: {contexto['titular']}
- Ubicación: {contexto.get('region', 'N/A')}, {contexto.get('comuna', 'N/A')}
- Superficie: {contexto.get('superficie_ha', 'N/A')} ha
- Inversión: {contexto.get('inversion_musd', 'N/A')} MUSD
- Fase: {contexto.get('fase', 'N/A')}

INFORMACIÓN RECOPILADA:
{self._formatear_contenido_recopilado(contenido_recopilado)}

ESTRUCTURA ESPERADA:
{self._formatear_estructura(template.get('estructura_esperada', {}))}

{instrucciones_adicionales_str}{ejemplos_str}{instrucciones_gen_str}IMPORTANTE:
- Usa un estilo técnico y objetivo
- Cita normativa aplicable cuando corresponda
- Incluye detalles específicos del proyecto
- Mantén coherencia con la información recopilada
- NO inventes datos técnicos que no se proporcionen

Por favor, genera el contenido del capítulo en formato Markdown."""

        return prompt

    def _formatear_contenido_recopilado(self, contenido: Dict[str, Any]) -> str:
        """Formatea el contenido recopilado para el prompt."""
        if not contenido:
            return "No se ha recopilado información específica aún para este capítulo."

        lineas = []
        for seccion, datos in contenido.items():
            lineas.append(f"\n### {seccion}")
            if isinstance(datos, dict):
                for clave, valor in datos.items():
                    lineas.append(f"- {clave}: {valor}")
            else:
                lineas.append(f"{datos}")

        return "\n".join(lineas)

    def _formatear_estructura(self, estructura: Dict[str, Any]) -> str:
        """Formatea la estructura esperada para el prompt."""
        if not estructura or not estructura.get('secciones'):
            return "No se especifica estructura particular."

        secciones = estructura.get('secciones', [])
        if isinstance(secciones, list):
            return "El capítulo debe incluir las siguientes secciones:\n" + "\n".join(
                f"- {seccion}" for seccion in secciones
            )

        return str(estructura)

    async def _generar_con_claude(
        self,
        prompt: str,
        contexto_adicional: Any = None
    ) -> str:
        """
        Genera texto usando Claude.

        Args:
            prompt: Prompt completo
            contexto_adicional: Contexto adicional para logging

        Returns:
            Texto generado
        """
        try:
            logger.debug(f"Generando con Claude (contexto: {contexto_adicional})")

            respuesta = self.cliente.messages.create(
                model=self.modelo,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extraer texto de la respuesta
            texto = ""
            for bloque in respuesta.content:
                if bloque.type == "text":
                    texto += bloque.text

            logger.info(f"Texto generado: {len(texto)} caracteres, {respuesta.usage.input_tokens} tokens input, {respuesta.usage.output_tokens} tokens output")

            return texto.strip()

        except anthropic.RateLimitError as e:
            logger.error(f"Rate limit de Claude alcanzado: {e}")
            raise ValueError("Se excedió el límite de solicitudes a Claude. Intenta de nuevo en unos momentos.")

        except anthropic.APIError as e:
            logger.error(f"Error de API de Claude: {e}")
            raise ValueError(f"Error al comunicarse con Claude: {str(e)}")

        except Exception as e:
            logger.error(f"Error inesperado al generar con Claude: {e}")
            raise

    def _post_procesar(
        self,
        texto_generado: str,
        capitulo_numero: int,
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post-procesa el texto generado.

        Args:
            texto_generado: Texto generado por Claude
            capitulo_numero: Número del capítulo
            template: Template usado

        Returns:
            Dict con contenido estructurado
        """
        # Extraer título si está en el texto
        lineas = texto_generado.split('\n')
        titulo = template['titulo']

        # Buscar primer heading como título alternativo
        for linea in lineas[:5]:
            if linea.startswith('# '):
                titulo = linea[2:].strip()
                break

        # Detectar subsecciones (## Título)
        subsecciones = {}
        seccion_actual = None
        contenido_seccion = []

        for linea in lineas:
            if linea.startswith('## '):
                # Guardar sección anterior
                if seccion_actual:
                    subsecciones[seccion_actual] = '\n'.join(contenido_seccion).strip()

                # Nueva sección
                seccion_actual = linea[3:].strip()
                contenido_seccion = []
            elif seccion_actual:
                contenido_seccion.append(linea)

        # Guardar última sección
        if seccion_actual and contenido_seccion:
            subsecciones[seccion_actual] = '\n'.join(contenido_seccion).strip()

        # Contar elementos
        num_figuras = texto_generado.lower().count('figura ')
        num_tablas = texto_generado.lower().count('tabla ')
        num_palabras = len(texto_generado.split())

        return {
            'numero': capitulo_numero,
            'titulo': titulo,
            'contenido': texto_generado,
            'subsecciones': subsecciones,
            'figuras': [],  # TODO: Extraer referencias a figuras
            'tablas': [],   # TODO: Extraer referencias a tablas
            'referencias': [],  # TODO: Extraer referencias bibliográficas
            'estadisticas': {
                'palabras': num_palabras,
                'figuras_detectadas': num_figuras,
                'tablas_detectadas': num_tablas,
                'subsecciones': len(subsecciones)
            }
        }
