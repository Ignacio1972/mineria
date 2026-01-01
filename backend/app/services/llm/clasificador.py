"""
Clasificador de documentos legales mediante LLM.

Utiliza Claude para clasificar automáticamente fragmentos de texto legal
según temas, triggers Art. 11, componentes ambientales y categorías.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.services.llm.cliente import get_cliente_llm, ClienteLLM, ModeloLLM

logger = logging.getLogger(__name__)


@dataclass
class ClasificacionFragmento:
    """Resultado de clasificación de un fragmento."""
    temas: List[Dict[str, Any]]  # [{codigo, confianza}, ...]
    triggers_art11: List[str]  # ['a', 'b', 'd', ...]
    componentes_ambientales: List[str]  # ['agua', 'aire', ...]
    confianza_general: float
    razonamiento: str = ""


@dataclass
class ClasificacionDocumento:
    """Resultado de clasificación de un documento completo."""
    categoria_sugerida: Optional[str]
    tipo_documento: str
    temas_principales: List[str]
    triggers_art11: List[str]
    componentes_ambientales: List[str]
    sectores: List[str]
    etapa_proceso: Optional[str]
    confianza: float
    resumen: str = ""


# Prompts especializados para clasificación
PROMPT_SISTEMA_CLASIFICACION = """Eres un experto en normativa ambiental chilena especializado en el Sistema de Evaluación de Impacto Ambiental (SEIA).

Tu tarea es clasificar fragmentos de documentos legales chilenos (leyes, reglamentos, guías del SEA, instructivos, criterios de evaluación) según categorías específicas.

IMPORTANTE:
1. Basa tu clasificación ÚNICAMENTE en el contenido del texto proporcionado
2. Asigna confianza entre 0.0 y 1.0 según qué tan claro sea el tema en el texto
3. Un fragmento puede tener múltiples temas, triggers y componentes
4. Si no estás seguro, usa confianza baja pero no omitas categorías relevantes
5. Responde SIEMPRE en formato JSON válido"""

PROMPT_CLASIFICAR_FRAGMENTO = """Clasifica el siguiente fragmento de documento legal chileno.

FRAGMENTO:
```
{texto}
```

CATÁLOGO DE TEMAS DISPONIBLES (usa SOLO estos códigos):
{catalogo_temas}

TRIGGERS ART. 11 LEY 19.300:
- a: Riesgo para la salud de la población
- b: Efectos adversos sobre recursos naturales renovables (agua, suelo, aire, flora, fauna, glaciares)
- c: Reasentamiento de comunidades humanas o alteración significativa de sistemas de vida
- d: Localización en o próxima a áreas protegidas, sitios prioritarios o glaciares
- e: Alteración significativa del patrimonio cultural (arqueológico, paleontológico, histórico)
- f: Alteración significativa de paisaje o sitios con valor turístico

COMPONENTES AMBIENTALES:
- agua (recursos hídricos superficiales y subterráneos)
- aire (calidad del aire, emisiones atmosféricas)
- suelo (erosión, contaminación, cambio de uso)
- flora (vegetación, especies vegetales)
- fauna (animales, hábitats)
- glaciares (criosfera, ambiente periglaciar)
- ruido (acústico, vibraciones)
- patrimonio (arqueológico, paleontológico, histórico)
- paisaje (visual, turístico)
- social (comunidades humanas, indígenas)

Responde con JSON:
{{
  "temas": [
    {{"codigo": "codigo_tema", "confianza": 0.0-1.0}},
    ...
  ],
  "triggers_art11": ["a", "b", ...],
  "componentes_ambientales": ["agua", "aire", ...],
  "confianza_general": 0.0-1.0,
  "razonamiento": "Breve explicación de la clasificación"
}}"""

PROMPT_CLASIFICAR_DOCUMENTO = """Clasifica el siguiente documento legal chileno para determinar su categoría y metadatos.

TÍTULO: {titulo}
TIPO DECLARADO: {tipo}

CONTENIDO (primeros fragmentos):
```
{contenido_muestra}
```

CATEGORÍAS DISPONIBLES:
{categorias}

SECTORES PRODUCTIVOS:
- mineria (proyectos mineros, relaves, procesamiento de minerales)
- energia (generación eléctrica, transmisión, hidrocarburos)
- inmobiliario (desarrollo urbano, loteos)
- infraestructura (vialidad, puertos, aeropuertos)
- acuicultura (salmonicultura, cultivos marinos)
- forestal (plantaciones, manejo de bosques)
- industrial (plantas industriales, manufactura)
- agricola (riego, agroindustria)
- saneamiento (agua potable, tratamiento de aguas)
- todos (aplica a múltiples sectores)

ETAPAS DEL PROCESO SEIA:
- pertinencia (consultas de pertinencia de ingreso)
- ingreso (admisibilidad, contenidos mínimos)
- evaluacion (análisis técnico, ICSARA, ICE)
- participacion (PAC, observaciones ciudadanas)
- consulta_indigena (proceso de consulta Convenio 169)
- calificacion (RCA, votación)
- seguimiento (fiscalización post-RCA)
- general (aplica a todo el proceso)

Responde con JSON:
{{
  "categoria_codigo": "codigo_categoria_sugerida",
  "tipo_documento": "Ley|Reglamento|Decreto|Guía SEA|Instructivo|Criterio|Jurisprudencia|Otro",
  "temas_principales": ["tema1", "tema2", ...],
  "triggers_art11": ["a", "b", ...],
  "componentes_ambientales": ["agua", "aire", ...],
  "sectores": ["mineria", "energia", ...],
  "etapa_proceso": "pertinencia|ingreso|evaluacion|...|general",
  "confianza": 0.0-1.0,
  "resumen": "Resumen breve del documento en 1-2 oraciones"
}}"""


class ClasificadorLLM:
    """
    Clasificador de documentos legales usando LLM.

    Utiliza Claude para clasificar automáticamente textos legales
    según el catálogo de temas, triggers y categorías del sistema.
    """

    def __init__(self, cliente_llm: Optional[ClienteLLM] = None):
        """
        Inicializa el clasificador.

        Args:
            cliente_llm: Cliente LLM opcional. Si no se proporciona, usa el singleton.
        """
        self.cliente = cliente_llm or get_cliente_llm()
        self._cache_temas: Optional[List[Dict]] = None
        self._cache_categorias: Optional[List[Dict]] = None
        logger.info("ClasificadorLLM inicializado")

    async def _cargar_catalogo_temas(self, db: AsyncSession) -> List[Dict]:
        """Carga el catálogo de temas desde la base de datos."""
        if self._cache_temas:
            return self._cache_temas

        result = await db.execute(
            text("""
                SELECT codigo, nombre, grupo, keywords
                FROM legal.temas
                WHERE activo = true
                ORDER BY grupo, nombre
            """)
        )
        temas = []
        for row in result.fetchall():
            temas.append({
                "codigo": row[0],
                "nombre": row[1],
                "grupo": row[2],
                "keywords": row[3] or []
            })

        self._cache_temas = temas
        logger.debug(f"Catálogo de temas cargado: {len(temas)} temas")
        return temas

    async def _cargar_categorias(self, db: AsyncSession) -> List[Dict]:
        """Carga las categorías desde la base de datos."""
        if self._cache_categorias:
            return self._cache_categorias

        result = await db.execute(
            text("""
                SELECT c.codigo, c.nombre, c.descripcion, c.nivel,
                       p.codigo as parent_codigo
                FROM legal.categorias c
                LEFT JOIN legal.categorias p ON c.parent_id = p.id
                WHERE c.activo = true
                ORDER BY c.nivel, c.orden
            """)
        )
        categorias = []
        for row in result.fetchall():
            categorias.append({
                "codigo": row[0],
                "nombre": row[1],
                "descripcion": row[2],
                "nivel": row[3],
                "parent": row[4]
            })

        self._cache_categorias = categorias
        logger.debug(f"Categorías cargadas: {len(categorias)} categorías")
        return categorias

    def _formatear_catalogo_temas(self, temas: List[Dict]) -> str:
        """Formatea el catálogo de temas para el prompt."""
        lineas = []
        grupo_actual = None

        for tema in temas:
            if tema["grupo"] != grupo_actual:
                grupo_actual = tema["grupo"]
                lineas.append(f"\n[{grupo_actual.upper()}]")

            keywords = ", ".join(tema["keywords"][:5]) if tema["keywords"] else ""
            lineas.append(f"- {tema['codigo']}: {tema['nombre']}" +
                         (f" (keywords: {keywords})" if keywords else ""))

        return "\n".join(lineas)

    def _formatear_categorias(self, categorias: List[Dict]) -> str:
        """Formatea las categorías para el prompt."""
        lineas = []

        for cat in categorias:
            indent = "  " * (cat["nivel"] - 1)
            desc = f" - {cat['descripcion'][:60]}..." if cat["descripcion"] else ""
            lineas.append(f"{indent}- {cat['codigo']}: {cat['nombre']}{desc}")

        return "\n".join(lineas)

    async def clasificar_fragmento(
        self,
        db: AsyncSession,
        texto: str,
        usar_cache: bool = True
    ) -> ClasificacionFragmento:
        """
        Clasifica un fragmento de texto legal.

        Args:
            db: Sesión de base de datos
            texto: Texto del fragmento a clasificar
            usar_cache: Si usar caché de catálogos

        Returns:
            ClasificacionFragmento con los resultados
        """
        if not usar_cache:
            self._cache_temas = None

        # Cargar catálogo de temas
        temas = await self._cargar_catalogo_temas(db)
        catalogo = self._formatear_catalogo_temas(temas)

        # Truncar texto si es muy largo
        texto_truncado = texto[:3000] if len(texto) > 3000 else texto

        # Construir prompt
        prompt = PROMPT_CLASIFICAR_FRAGMENTO.format(
            texto=texto_truncado,
            catalogo_temas=catalogo
        )

        # Llamar al LLM
        try:
            resultado = await self.cliente.generar_estructurado(
                prompt_usuario=prompt,
                prompt_sistema=PROMPT_SISTEMA_CLASIFICACION,
                modelo=ModeloLLM.CLAUDE_HAIKU.value,  # Usar Haiku para clasificación rápida
                temperatura=0.1,  # Baja temperatura para consistencia
            )

            if resultado.get("error") or not resultado.get("data"):
                logger.warning(f"Error en clasificación LLM: {resultado.get('error')}")
                return self._clasificacion_por_defecto_fragmento(texto, temas)

            data = resultado["data"]

            return ClasificacionFragmento(
                temas=data.get("temas", []),
                triggers_art11=data.get("triggers_art11", []),
                componentes_ambientales=data.get("componentes_ambientales", []),
                confianza_general=data.get("confianza_general", 0.5),
                razonamiento=data.get("razonamiento", "")
            )

        except Exception as e:
            logger.error(f"Error clasificando fragmento: {e}")
            return self._clasificacion_por_defecto_fragmento(texto, temas)

    async def clasificar_documento(
        self,
        db: AsyncSession,
        titulo: str,
        tipo: str,
        contenido: str,
        usar_cache: bool = True
    ) -> ClasificacionDocumento:
        """
        Clasifica un documento completo para sugerir categoría y metadatos.

        Args:
            db: Sesión de base de datos
            titulo: Título del documento
            tipo: Tipo declarado del documento
            contenido: Contenido completo del documento
            usar_cache: Si usar caché de catálogos

        Returns:
            ClasificacionDocumento con los resultados
        """
        if not usar_cache:
            self._cache_temas = None
            self._cache_categorias = None

        # Cargar catálogos
        categorias = await self._cargar_categorias(db)
        categorias_fmt = self._formatear_categorias(categorias)

        # Tomar muestra del contenido (inicio, medio, final)
        if len(contenido) > 6000:
            inicio = contenido[:2000]
            medio = contenido[len(contenido)//2 - 1000:len(contenido)//2 + 1000]
            final = contenido[-2000:]
            contenido_muestra = f"{inicio}\n\n[...]\n\n{medio}\n\n[...]\n\n{final}"
        else:
            contenido_muestra = contenido

        # Construir prompt
        prompt = PROMPT_CLASIFICAR_DOCUMENTO.format(
            titulo=titulo,
            tipo=tipo,
            contenido_muestra=contenido_muestra,
            categorias=categorias_fmt
        )

        # Llamar al LLM
        try:
            resultado = await self.cliente.generar_estructurado(
                prompt_usuario=prompt,
                prompt_sistema=PROMPT_SISTEMA_CLASIFICACION,
                modelo=ModeloLLM.CLAUDE_HAIKU.value,
                temperatura=0.1,
            )

            if resultado.get("error") or not resultado.get("data"):
                logger.warning(f"Error en clasificación documento: {resultado.get('error')}")
                return self._clasificacion_por_defecto_documento(titulo, tipo)

            data = resultado["data"]

            return ClasificacionDocumento(
                categoria_sugerida=data.get("categoria_codigo"),
                tipo_documento=data.get("tipo_documento", tipo),
                temas_principales=data.get("temas_principales", []),
                triggers_art11=data.get("triggers_art11", []),
                componentes_ambientales=data.get("componentes_ambientales", []),
                sectores=data.get("sectores", []),
                etapa_proceso=data.get("etapa_proceso"),
                confianza=data.get("confianza", 0.5),
                resumen=data.get("resumen", "")
            )

        except Exception as e:
            logger.error(f"Error clasificando documento: {e}")
            return self._clasificacion_por_defecto_documento(titulo, tipo)

    def _clasificacion_por_defecto_fragmento(
        self,
        texto: str,
        temas: List[Dict]
    ) -> ClasificacionFragmento:
        """
        Clasificación por defecto usando keywords cuando el LLM falla.
        Fallback al método tradicional basado en keywords.
        """
        texto_lower = texto.lower()
        temas_detectados = []

        for tema in temas:
            for keyword in (tema.get("keywords") or []):
                if keyword.lower() in texto_lower:
                    temas_detectados.append({
                        "codigo": tema["codigo"],
                        "confianza": 0.6
                    })
                    break

        # Detectar triggers por keywords
        triggers = []
        triggers_keywords = {
            "a": ["salud", "poblacion", "contaminacion", "riesgo sanitario"],
            "b": ["recurso natural", "agua", "suelo", "flora", "fauna", "glaciar"],
            "c": ["reasentamiento", "comunidad", "sistema de vida", "relocalizacion"],
            "d": ["area protegida", "snaspe", "parque nacional", "reserva", "santuario"],
            "e": ["patrimonio", "arqueologico", "paleontologico", "monumento"],
            "f": ["paisaje", "turismo", "turistico", "valor visual"]
        }
        for letra, keywords in triggers_keywords.items():
            for kw in keywords:
                if kw in texto_lower:
                    triggers.append(letra)
                    break

        return ClasificacionFragmento(
            temas=temas_detectados if temas_detectados else [{"codigo": "general", "confianza": 0.3}],
            triggers_art11=list(set(triggers)),
            componentes_ambientales=[],
            confianza_general=0.4,
            razonamiento="Clasificación por keywords (fallback)"
        )

    def _clasificacion_por_defecto_documento(
        self,
        titulo: str,
        tipo: str
    ) -> ClasificacionDocumento:
        """Clasificación por defecto cuando el LLM falla."""
        # Inferir categoría del tipo
        categoria_map = {
            "Ley": "leyes",
            "Reglamento": "reglamentos",
            "Decreto": "decretos_resoluciones",
            "Guía SEA": "guias_descripcion",
            "Instructivo": "instructivos_procedimientos",
            "Criterio": "criterios_componentes",
        }

        return ClasificacionDocumento(
            categoria_sugerida=categoria_map.get(tipo, "normativa_legal"),
            tipo_documento=tipo,
            temas_principales=[],
            triggers_art11=[],
            componentes_ambientales=[],
            sectores=["todos"],
            etapa_proceso="general",
            confianza=0.3,
            resumen=""
        )

    def invalidar_cache(self):
        """Invalida el caché de catálogos."""
        self._cache_temas = None
        self._cache_categorias = None
        logger.debug("Caché de clasificador invalidado")


# Instancia singleton
_clasificador: Optional[ClasificadorLLM] = None


def get_clasificador_llm() -> ClasificadorLLM:
    """Obtiene la instancia singleton del clasificador."""
    global _clasificador
    if _clasificador is None:
        _clasificador = ClasificadorLLM()
    return _clasificador
