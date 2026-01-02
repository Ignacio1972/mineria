"""
Ingestor de documentos legales para el sistema RAG.

Procesa PDFs y textos, los segmenta, clasifica con LLM y genera embeddings.
Integrado con el sistema de gestión documental (categorías, temas, colecciones).
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload

from app.services.rag.embeddings import get_embedding_service
from app.services.llm.clasificador import get_clasificador_llm, ClasificadorLLM
from app.db.models.legal import Documento, Fragmento
from app.db.models.corpus import Categoria, Tema, ArchivoOriginal, FragmentoTema
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FragmentoIngestado:
    """Fragmento de documento para indexar."""
    seccion: str
    numero_seccion: str
    contenido: str
    temas_codigos: List[str] = field(default_factory=list)
    temas_confianza: Dict[str, float] = field(default_factory=dict)
    triggers_art11: List[str] = field(default_factory=list)
    componentes: List[str] = field(default_factory=list)


@dataclass
class DocumentoAIngestar:
    """Documento legal a ingestar."""
    titulo: str
    tipo: str  # 'Ley', 'Reglamento', 'Decreto', 'Guía SEA', etc.
    numero: Optional[str] = None
    fecha_publicacion: Optional[date] = None
    organismo: Optional[str] = None
    contenido: str = ""
    url_fuente: Optional[str] = None
    # Nuevos campos para integración con corpus
    categoria_id: Optional[int] = None
    archivo_id: Optional[int] = None
    sectores: List[str] = field(default_factory=list)
    triggers_art11: List[str] = field(default_factory=list)
    componentes_ambientales: List[str] = field(default_factory=list)
    etapa_proceso: Optional[str] = None


@dataclass
class ResultadoIngestion:
    """Resultado de la ingestión de un documento."""
    documento_id: int
    titulo: str
    fragmentos_creados: int
    temas_detectados: List[str]
    triggers_detectados: List[str]
    componentes_detectados: List[str]
    categoria_asignada: Optional[str]
    clasificacion_llm_usada: bool
    tiempo_procesamiento_ms: int
    errores: List[str] = field(default_factory=list)


class IngestorLegal:
    """
    Procesa e ingesta documentos legales al sistema RAG.

    Características:
    - Segmentación inteligente por artículos/secciones
    - Clasificación automática con LLM (temas, triggers, componentes)
    - Fallback a clasificación por keywords si LLM falla
    - Integración con tabla de temas (many-to-many)
    - Soporte para archivos originales (PDF/DOCX)
    - Generación de embeddings en batch
    """

    # Patrones para detectar secciones en leyes chilenas
    PATRONES_SECCION = [
        (r'(?:TÍTULO|Título)\s+([IVXLCDM]+)[.\s-]*(.+?)(?=\n)', 'titulo'),
        (r'(?:PÁRRAFO|Párrafo)\s+(\d+)[°º]?[.\s-]*(.+?)(?=\n)', 'parrafo'),
        (r'(?:Artículo|ARTÍCULO|Art\.?)\s+(\d+)[°º]?[.\s-]*', 'articulo'),
    ]

    def __init__(
        self,
        usar_llm: bool = True,
        clasificador: Optional[ClasificadorLLM] = None
    ):
        """
        Inicializa el ingestor.

        Args:
            usar_llm: Si usar LLM para clasificación (default: True)
            clasificador: Clasificador LLM opcional. Si no se proporciona, usa singleton.
        """
        self.embedding_service = get_embedding_service()
        self.usar_llm = usar_llm
        self.clasificador = clasificador if usar_llm else None
        self._cache_temas: Optional[Dict[str, Dict]] = None
        logger.info(f"IngestorLegal inicializado (usar_llm={usar_llm})")

    async def _cargar_temas(self, db: AsyncSession) -> Dict[str, Dict]:
        """Carga el catálogo de temas con sus keywords."""
        if self._cache_temas:
            return self._cache_temas

        result = await db.execute(
            text("""
                SELECT id, codigo, nombre, keywords
                FROM legal.temas
                WHERE activo = true
            """)
        )

        self._cache_temas = {}
        for row in result.fetchall():
            self._cache_temas[row[1]] = {
                "id": row[0],
                "codigo": row[1],
                "nombre": row[2],
                "keywords": row[3] or []
            }

        logger.debug(f"Temas cargados: {len(self._cache_temas)}")
        return self._cache_temas

    def _detectar_temas_por_keywords(
        self,
        texto: str,
        temas: Dict[str, Dict]
    ) -> List[Dict[str, Any]]:
        """
        Detecta temas usando keywords (fallback cuando LLM no está disponible).

        Args:
            texto: Texto a analizar
            temas: Diccionario de temas con keywords

        Returns:
            Lista de temas detectados con confianza
        """
        texto_lower = texto.lower()
        temas_detectados = []

        for codigo, info in temas.items():
            for keyword in info.get("keywords", []):
                if keyword.lower() in texto_lower:
                    temas_detectados.append({
                        "codigo": codigo,
                        "confianza": 0.6,
                        "metodo": "keywords"
                    })
                    break

        return temas_detectados if temas_detectados else [
            {"codigo": "general", "confianza": 0.3, "metodo": "default"}
        ]

    def segmentar_documento(self, contenido: str) -> List[Dict[str, Any]]:
        """
        Segmenta un documento legal en fragmentos indexables.

        Estrategia:
        - Detectar artículos como unidad principal
        - Si un artículo es muy largo, subdividir por oraciones
        - Mantener contexto (título/párrafo actual)

        Args:
            contenido: Contenido completo del documento

        Returns:
            Lista de fragmentos con seccion, numero y contenido
        """
        fragmentos = []

        # Buscar artículos
        patron_articulo = r'(?:Artículo|ARTÍCULO|Art\.?)\s+(\d+)[°º]?[.\s-]*(.*?)(?=(?:Artículo|ARTÍCULO|Art\.?)\s+\d+|$)'
        articulos = re.findall(patron_articulo, contenido, re.DOTALL | re.IGNORECASE)

        for num_art, texto_art in articulos:
            texto_limpio = self._limpiar_texto(texto_art)

            if len(texto_limpio) < 50:  # Artículo muy corto, saltar
                continue

            # Si el artículo es muy largo, dividir en chunks
            if len(texto_limpio) > 2000:
                chunks = self._dividir_en_chunks(texto_limpio, max_chars=1500)
                for i, chunk in enumerate(chunks):
                    fragmentos.append({
                        "seccion": f"Artículo {num_art}" + (f" (parte {i+1})" if len(chunks) > 1 else ""),
                        "numero_seccion": num_art,
                        "contenido": chunk,
                    })
            else:
                fragmentos.append({
                    "seccion": f"Artículo {num_art}",
                    "numero_seccion": num_art,
                    "contenido": texto_limpio,
                })

        # Si no se encontraron artículos, dividir por párrafos/chunks
        if not fragmentos:
            chunks = self._dividir_en_chunks(contenido, max_chars=1500)
            for i, chunk in enumerate(chunks):
                fragmentos.append({
                    "seccion": f"Sección {i+1}",
                    "numero_seccion": str(i+1),
                    "contenido": chunk,
                })

        logger.debug(f"Documento segmentado en {len(fragmentos)} fragmentos")
        return fragmentos

    def _limpiar_texto(self, texto: str) -> str:
        """Limpia y normaliza texto."""
        # Eliminar saltos de línea múltiples
        texto = re.sub(r'\n{3,}', '\n\n', texto)
        # Eliminar espacios múltiples
        texto = re.sub(r' {2,}', ' ', texto)
        # Eliminar caracteres de control
        texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', texto)
        return texto.strip()

    def _dividir_en_chunks(self, texto: str, max_chars: int = 1500) -> List[str]:
        """Divide texto largo en chunks respetando oraciones."""
        if len(texto) <= max_chars:
            return [texto]

        chunks = []
        oraciones = re.split(r'(?<=[.!?])\s+', texto)
        chunk_actual = ""

        for oracion in oraciones:
            if len(chunk_actual) + len(oracion) + 1 <= max_chars:
                chunk_actual += (" " if chunk_actual else "") + oracion
            else:
                if chunk_actual:
                    chunks.append(chunk_actual)
                chunk_actual = oracion

        if chunk_actual:
            chunks.append(chunk_actual)

        return chunks

    async def _clasificar_fragmentos_con_llm(
        self,
        db: AsyncSession,
        fragmentos: List[Dict[str, Any]]
    ) -> List[FragmentoIngestado]:
        """
        Clasifica fragmentos usando LLM.

        Args:
            db: Sesión de base de datos
            fragmentos: Lista de fragmentos a clasificar

        Returns:
            Lista de FragmentoIngestado con clasificación
        """
        if not self.clasificador:
            self.clasificador = get_clasificador_llm()

        resultados = []

        for frag in fragmentos:
            try:
                clasificacion = await self.clasificador.clasificar_fragmento(
                    db=db,
                    texto=frag["contenido"]
                )

                resultados.append(FragmentoIngestado(
                    seccion=frag["seccion"],
                    numero_seccion=frag["numero_seccion"],
                    contenido=frag["contenido"],
                    temas_codigos=[t["codigo"] for t in clasificacion.temas],
                    temas_confianza={t["codigo"]: t["confianza"] for t in clasificacion.temas},
                    triggers_art11=clasificacion.triggers_art11,
                    componentes=clasificacion.componentes_ambientales,
                ))

            except Exception as e:
                logger.warning(f"Error clasificando fragmento con LLM: {e}, usando fallback")
                # Fallback a keywords
                temas = await self._cargar_temas(db)
                temas_detectados = self._detectar_temas_por_keywords(frag["contenido"], temas)

                resultados.append(FragmentoIngestado(
                    seccion=frag["seccion"],
                    numero_seccion=frag["numero_seccion"],
                    contenido=frag["contenido"],
                    temas_codigos=[t["codigo"] for t in temas_detectados],
                    temas_confianza={t["codigo"]: t["confianza"] for t in temas_detectados},
                    triggers_art11=[],
                    componentes=[],
                ))

        return resultados

    async def _clasificar_fragmentos_por_keywords(
        self,
        db: AsyncSession,
        fragmentos: List[Dict[str, Any]]
    ) -> List[FragmentoIngestado]:
        """Clasifica fragmentos usando keywords (sin LLM)."""
        temas = await self._cargar_temas(db)
        resultados = []

        for frag in fragmentos:
            temas_detectados = self._detectar_temas_por_keywords(frag["contenido"], temas)

            resultados.append(FragmentoIngestado(
                seccion=frag["seccion"],
                numero_seccion=frag["numero_seccion"],
                contenido=frag["contenido"],
                temas_codigos=[t["codigo"] for t in temas_detectados],
                temas_confianza={t["codigo"]: t["confianza"] for t in temas_detectados},
                triggers_art11=[],
                componentes=[],
            ))

        return resultados

    async def ingestar_documento(
        self,
        db: AsyncSession,
        documento: DocumentoAIngestar,
        clasificar_con_llm: Optional[bool] = None,
    ) -> ResultadoIngestion:
        """
        Ingesta un documento completo al sistema RAG.

        Args:
            db: Sesión de base de datos
            documento: Documento a ingestar
            clasificar_con_llm: Override para usar/no usar LLM (None = usar config del ingestor)

        Returns:
            ResultadoIngestion con estadísticas y metadatos
        """
        import time
        inicio = time.time()
        errores = []

        usar_llm = clasificar_con_llm if clasificar_con_llm is not None else self.usar_llm
        logger.info(f"Iniciando ingestión: {documento.titulo} (LLM={usar_llm})")

        # 1. Clasificar documento completo con LLM si está habilitado
        categoria_asignada = None
        if usar_llm and documento.categoria_id is None:
            try:
                if not self.clasificador:
                    self.clasificador = get_clasificador_llm()

                clasif_doc = await self.clasificador.clasificar_documento(
                    db=db,
                    titulo=documento.titulo,
                    tipo=documento.tipo,
                    contenido=documento.contenido
                )

                # Buscar ID de categoría sugerida
                if clasif_doc.categoria_sugerida:
                    result = await db.execute(
                        text("SELECT id FROM legal.categorias WHERE codigo = :codigo"),
                        {"codigo": clasif_doc.categoria_sugerida}
                    )
                    cat_row = result.fetchone()
                    if cat_row:
                        documento.categoria_id = cat_row[0]
                        categoria_asignada = clasif_doc.categoria_sugerida

                # Actualizar metadatos del documento si no están definidos
                if not documento.sectores and clasif_doc.sectores:
                    documento.sectores = clasif_doc.sectores
                if not documento.triggers_art11 and clasif_doc.triggers_art11:
                    documento.triggers_art11 = clasif_doc.triggers_art11
                if not documento.componentes_ambientales and clasif_doc.componentes_ambientales:
                    documento.componentes_ambientales = clasif_doc.componentes_ambientales
                if not documento.etapa_proceso and clasif_doc.etapa_proceso:
                    documento.etapa_proceso = clasif_doc.etapa_proceso

                logger.debug(f"Clasificación documento: categoria={categoria_asignada}, "
                           f"sectores={documento.sectores}, triggers={documento.triggers_art11}")

            except Exception as e:
                logger.warning(f"Error en clasificación LLM de documento: {e}")
                errores.append(f"Clasificación documento: {str(e)}")

        # 2. Insertar documento en BD
        result = await db.execute(
            text("""
                INSERT INTO legal.documentos
                (titulo, tipo, numero, fecha_publicacion, organismo, url_fuente,
                 contenido_completo, categoria_id, archivo_id, sectores,
                 triggers_art11, componentes_ambientales, etapa_proceso)
                VALUES (:titulo, :tipo, :numero, :fecha, :organismo, :url,
                        :contenido, :categoria_id, :archivo_id, :sectores,
                        :triggers, :componentes, :etapa)
                RETURNING id
            """),
            {
                "titulo": documento.titulo,
                "tipo": documento.tipo,
                "numero": documento.numero,
                "fecha": documento.fecha_publicacion,
                "organismo": documento.organismo,
                "url": documento.url_fuente,
                "contenido": documento.contenido,
                "categoria_id": documento.categoria_id,
                "archivo_id": documento.archivo_id,
                "sectores": documento.sectores or [],
                "triggers": documento.triggers_art11 or [],
                "componentes": documento.componentes_ambientales or [],
                "etapa": documento.etapa_proceso,
            }
        )
        documento_id = result.scalar()
        logger.debug(f"Documento insertado con ID: {documento_id}")

        # 3. Segmentar documento
        fragmentos_raw = self.segmentar_documento(documento.contenido)
        logger.info(f"Documento segmentado en {len(fragmentos_raw)} fragmentos")

        # 4. Clasificar fragmentos
        if usar_llm:
            fragmentos = await self._clasificar_fragmentos_con_llm(db, fragmentos_raw)
        else:
            fragmentos = await self._clasificar_fragmentos_por_keywords(db, fragmentos_raw)

        # 5. Generar embeddings en batch
        textos = [f.contenido for f in fragmentos]
        logger.debug(f"Generando embeddings para {len(textos)} fragmentos...")
        embeddings = self.embedding_service.embed_texts(textos)

        # 6. Cargar mapeo de temas para insertar relaciones
        temas_map = await self._cargar_temas(db)

        # 7. Insertar fragmentos y crear relaciones con temas
        todos_temas = set()
        todos_triggers = set()
        todos_componentes = set()

        for fragmento, embedding in zip(fragmentos, embeddings):
            # Convertir embedding a formato string para pgvector
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

            # Insertar fragmento
            result = await db.execute(
                text(f"""
                    INSERT INTO legal.fragmentos
                    (documento_id, seccion, numero_seccion, contenido, temas, embedding)
                    VALUES (:doc_id, :seccion, :num, :contenido, :temas, '{embedding_str}'::vector)
                    RETURNING id
                """),
                {
                    "doc_id": documento_id,
                    "seccion": fragmento.seccion,
                    "num": fragmento.numero_seccion,
                    "contenido": fragmento.contenido,
                    "temas": fragmento.temas_codigos,  # Array legacy para compatibilidad
                }
            )
            fragmento_id = result.scalar()

            # Insertar relaciones fragmento-tema en tabla junction
            for tema_codigo in fragmento.temas_codigos:
                if tema_codigo in temas_map:
                    tema_id = temas_map[tema_codigo]["id"]
                    confianza = fragmento.temas_confianza.get(tema_codigo, 0.5)
                    metodo = "llm" if usar_llm else "keywords"

                    await db.execute(
                        text("""
                            INSERT INTO legal.fragmentos_temas
                            (fragmento_id, tema_id, confianza, detectado_por)
                            VALUES (:frag_id, :tema_id, :confianza, :metodo)
                            ON CONFLICT (fragmento_id, tema_id) DO UPDATE
                            SET confianza = :confianza, detectado_por = :metodo
                        """),
                        {
                            "frag_id": fragmento_id,
                            "tema_id": tema_id,
                            "confianza": confianza,
                            "metodo": metodo,
                        }
                    )
                    todos_temas.add(tema_codigo)

            # Acumular triggers y componentes
            todos_triggers.update(fragmento.triggers_art11)
            todos_componentes.update(fragmento.componentes)

        # 8. Actualizar triggers y componentes del documento si se detectaron nuevos
        if todos_triggers or todos_componentes:
            triggers_actualizados = list(set(documento.triggers_art11 or []) | todos_triggers)
            componentes_actualizados = list(set(documento.componentes_ambientales or []) | todos_componentes)

            await db.execute(
                text("""
                    UPDATE legal.documentos
                    SET triggers_art11 = :triggers,
                        componentes_ambientales = :componentes
                    WHERE id = :doc_id
                """),
                {
                    "doc_id": documento_id,
                    "triggers": triggers_actualizados,
                    "componentes": componentes_actualizados,
                }
            )

        await db.commit()

        tiempo_ms = int((time.time() - inicio) * 1000)
        logger.info(f"Ingestión completada: {len(fragmentos)} fragmentos, "
                   f"{len(todos_temas)} temas, {tiempo_ms}ms")

        return ResultadoIngestion(
            documento_id=documento_id,
            titulo=documento.titulo,
            fragmentos_creados=len(fragmentos),
            temas_detectados=list(todos_temas),
            triggers_detectados=list(todos_triggers),
            componentes_detectados=list(todos_componentes),
            categoria_asignada=categoria_asignada,
            clasificacion_llm_usada=usar_llm,
            tiempo_procesamiento_ms=tiempo_ms,
            errores=errores,
        )

    async def procesar_documento_existente(
        self,
        db: AsyncSession,
        documento_id: int,
        clasificar_con_llm: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Procesa un documento ya existente en la BD, creando fragmentos y embeddings.

        Usado cuando se crea un documento via API y se quiere procesar automáticamente.

        Args:
            db: Sesión de base de datos
            documento_id: ID del documento existente
            clasificar_con_llm: Override para usar/no usar LLM

        Returns:
            Diccionario con estadísticas del procesamiento
        """
        import time
        inicio = time.time()

        usar_llm = clasificar_con_llm if clasificar_con_llm is not None else self.usar_llm
        logger.info(f"Procesando documento existente ID={documento_id} (LLM={usar_llm})")

        # 1. Obtener documento de la BD
        result = await db.execute(
            text("""
                SELECT id, titulo, contenido_completo, categoria_id,
                       triggers_art11, componentes_ambientales
                FROM legal.documentos
                WHERE id = :doc_id
            """),
            {"doc_id": documento_id}
        )
        doc_row = result.fetchone()

        if not doc_row:
            return {"error": "Documento no encontrado", "documento_id": documento_id}

        doc_id, titulo, contenido, categoria_id, triggers_doc, componentes_doc = doc_row

        if not contenido:
            return {"error": "Documento sin contenido", "documento_id": documento_id}

        # 2. Segmentar documento
        fragmentos_raw = self.segmentar_documento(contenido)
        logger.info(f"Documento segmentado en {len(fragmentos_raw)} fragmentos")

        if not fragmentos_raw:
            return {
                "documento_id": documento_id,
                "fragmentos_creados": 0,
                "temas_detectados": [],
                "mensaje": "No se pudieron crear fragmentos del documento"
            }

        # 3. Clasificar fragmentos
        if usar_llm:
            fragmentos = await self._clasificar_fragmentos_con_llm(db, fragmentos_raw)
        else:
            fragmentos = await self._clasificar_fragmentos_por_keywords(db, fragmentos_raw)

        # 4. Generar embeddings en batch
        textos = [f.contenido for f in fragmentos]
        logger.debug(f"Generando embeddings para {len(textos)} fragmentos...")
        embeddings = self.embedding_service.embed_texts(textos)

        # 5. Cargar mapeo de temas
        temas_map = await self._cargar_temas(db)

        # 6. Insertar fragmentos y crear relaciones con temas
        todos_temas = set()
        todos_triggers = set()
        todos_componentes = set()

        for fragmento, embedding in zip(fragmentos, embeddings):
            # Convertir embedding a formato string para pgvector
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

            # Insertar fragmento
            result = await db.execute(
                text(f"""
                    INSERT INTO legal.fragmentos
                    (documento_id, seccion, numero_seccion, contenido, temas, embedding)
                    VALUES (:doc_id, :seccion, :num, :contenido, :temas, '{embedding_str}'::vector)
                    RETURNING id
                """),
                {
                    "doc_id": documento_id,
                    "seccion": fragmento.seccion,
                    "num": fragmento.numero_seccion,
                    "contenido": fragmento.contenido,
                    "temas": fragmento.temas_codigos,
                }
            )
            fragmento_id = result.scalar()

            # Insertar relaciones fragmento-tema
            for tema_codigo in fragmento.temas_codigos:
                if tema_codigo in temas_map:
                    tema_id = temas_map[tema_codigo]["id"]
                    confianza = fragmento.temas_confianza.get(tema_codigo, 0.5)
                    metodo = "llm" if usar_llm else "keywords"

                    await db.execute(
                        text("""
                            INSERT INTO legal.fragmentos_temas
                            (fragmento_id, tema_id, confianza, detectado_por)
                            VALUES (:frag_id, :tema_id, :confianza, :metodo)
                            ON CONFLICT (fragmento_id, tema_id) DO UPDATE
                            SET confianza = :confianza, detectado_por = :metodo
                        """),
                        {
                            "frag_id": fragmento_id,
                            "tema_id": tema_id,
                            "confianza": confianza,
                            "metodo": metodo,
                        }
                    )
                    todos_temas.add(tema_codigo)

            # Acumular triggers y componentes
            todos_triggers.update(fragmento.triggers_art11)
            todos_componentes.update(fragmento.componentes)

        # 7. Actualizar triggers y componentes del documento si se detectaron nuevos
        if todos_triggers or todos_componentes:
            triggers_actualizados = list(set(triggers_doc or []) | todos_triggers)
            componentes_actualizados = list(set(componentes_doc or []) | todos_componentes)

            await db.execute(
                text("""
                    UPDATE legal.documentos
                    SET triggers_art11 = :triggers,
                        componentes_ambientales = :componentes
                    WHERE id = :doc_id
                """),
                {
                    "doc_id": documento_id,
                    "triggers": triggers_actualizados,
                    "componentes": componentes_actualizados,
                }
            )

        await db.commit()

        tiempo_ms = int((time.time() - inicio) * 1000)
        logger.info(f"Procesamiento completado: {len(fragmentos)} fragmentos, "
                   f"{len(todos_temas)} temas, {tiempo_ms}ms")

        return {
            "documento_id": documento_id,
            "titulo": titulo,
            "fragmentos_creados": len(fragmentos),
            "temas_detectados": list(todos_temas),
            "triggers_detectados": list(todos_triggers),
            "componentes_detectados": list(todos_componentes),
            "clasificacion_llm_usada": usar_llm,
            "tiempo_procesamiento_ms": tiempo_ms,
        }

    async def reprocesar_fragmentos(
        self,
        db: AsyncSession,
        documento_id: int,
        regenerar_embeddings: bool = True,
        reclasificar: bool = True,
    ) -> Dict[str, Any]:
        """
        Reprocesa los fragmentos de un documento existente.

        Útil para:
        - Regenerar embeddings con nuevo modelo
        - Reclasificar con LLM
        - Actualizar relaciones de temas

        Args:
            db: Sesión de base de datos
            documento_id: ID del documento a reprocesar
            regenerar_embeddings: Si regenerar los embeddings
            reclasificar: Si reclasificar temas con LLM

        Returns:
            Estadísticas del reprocesamiento
        """
        import time
        inicio = time.time()

        # Obtener fragmentos existentes
        result = await db.execute(
            text("""
                SELECT id, contenido
                FROM legal.fragmentos
                WHERE documento_id = :doc_id
            """),
            {"doc_id": documento_id}
        )
        fragmentos = result.fetchall()

        if not fragmentos:
            return {"error": "No se encontraron fragmentos", "documento_id": documento_id}

        fragmentos_actualizados = 0
        temas_actualizados = 0

        for frag_id, contenido in fragmentos:
            # Reclasificar
            if reclasificar and self.usar_llm:
                if not self.clasificador:
                    self.clasificador = get_clasificador_llm()

                clasificacion = await self.clasificador.clasificar_fragmento(
                    db=db,
                    texto=contenido
                )

                # Actualizar array legacy de temas
                await db.execute(
                    text("""
                        UPDATE legal.fragmentos
                        SET temas = :temas
                        WHERE id = :frag_id
                    """),
                    {
                        "frag_id": frag_id,
                        "temas": [t["codigo"] for t in clasificacion.temas],
                    }
                )

                # Eliminar relaciones anteriores
                await db.execute(
                    text("DELETE FROM legal.fragmentos_temas WHERE fragmento_id = :frag_id"),
                    {"frag_id": frag_id}
                )

                # Crear nuevas relaciones
                temas_map = await self._cargar_temas(db)
                for tema in clasificacion.temas:
                    if tema["codigo"] in temas_map:
                        await db.execute(
                            text("""
                                INSERT INTO legal.fragmentos_temas
                                (fragmento_id, tema_id, confianza, detectado_por)
                                VALUES (:frag_id, :tema_id, :confianza, 'llm')
                            """),
                            {
                                "frag_id": frag_id,
                                "tema_id": temas_map[tema["codigo"]]["id"],
                                "confianza": tema["confianza"],
                            }
                        )
                        temas_actualizados += 1

            # Regenerar embedding
            if regenerar_embeddings:
                embedding = self.embedding_service.embed_text(contenido)
                embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

                await db.execute(
                    text(f"""
                        UPDATE legal.fragmentos
                        SET embedding = '{embedding_str}'::vector
                        WHERE id = :frag_id
                    """),
                    {"frag_id": frag_id}
                )

            fragmentos_actualizados += 1

        await db.commit()

        return {
            "documento_id": documento_id,
            "fragmentos_actualizados": fragmentos_actualizados,
            "temas_actualizados": temas_actualizados,
            "tiempo_ms": int((time.time() - inicio) * 1000),
        }

    def invalidar_cache(self):
        """Invalida el caché de temas."""
        self._cache_temas = None
        if self.clasificador:
            self.clasificador.invalidar_cache()


def extraer_texto_pdf(ruta_pdf: str, usar_ocr_vision: bool = True) -> str:
    """
    Extrae texto de un archivo PDF.

    Intenta primero extracción nativa con PyMuPDF. Si el texto extraído
    es insuficiente (< OCR_MIN_TEXT_THRESHOLD caracteres) y OCR está
    habilitado, usa Claude Vision para OCR.

    Args:
        ruta_pdf: Ruta al archivo PDF
        usar_ocr_vision: Si usar Claude Vision como fallback (default: True)

    Returns:
        Texto extraído
    """
    import fitz  # PyMuPDF
    import logging
    from app.core.config import settings

    logger = logging.getLogger(__name__)

    # Intento 1: Extracción nativa con PyMuPDF
    texto = ""
    num_paginas = 0
    with fitz.open(ruta_pdf) as doc:
        num_paginas = len(doc)
        for pagina in doc:
            texto += pagina.get_text()

    texto_limpio = texto.strip()
    chars_extraidos = len(texto_limpio)

    logger.info(f"PyMuPDF extrajo {chars_extraidos} caracteres de {num_paginas} páginas")

    # Verificar si necesitamos OCR
    umbral = settings.OCR_MIN_TEXT_THRESHOLD
    ocr_habilitado = settings.OCR_VISION_ENABLED and usar_ocr_vision

    if chars_extraidos >= umbral:
        # Texto suficiente, no necesitamos OCR
        return texto

    if not ocr_habilitado:
        logger.warning(
            f"Texto insuficiente ({chars_extraidos} < {umbral}) pero OCR deshabilitado"
        )
        return texto

    # Intento 2: OCR con Claude Vision
    logger.info(
        f"Texto insuficiente ({chars_extraidos} < {umbral}), "
        f"usando Claude Vision OCR..."
    )

    try:
        from app.services.ocr import extraer_texto_con_vision

        texto_ocr = extraer_texto_con_vision(ruta_pdf)

        if len(texto_ocr.strip()) > chars_extraidos:
            logger.info(
                f"Claude Vision extrajo {len(texto_ocr)} caracteres "
                f"(mejora: +{len(texto_ocr) - chars_extraidos})"
            )
            return texto_ocr
        else:
            logger.warning("Claude Vision no mejoró la extracción, usando texto original")
            return texto

    except Exception as e:
        logger.error(f"Error en OCR con Claude Vision: {e}")
        return texto


def extraer_texto_docx(ruta_docx: str) -> str:
    """
    Extrae texto de un archivo DOCX.

    Args:
        ruta_docx: Ruta al archivo DOCX

    Returns:
        Texto extraído
    """
    from docx import Document

    doc = Document(ruta_docx)
    texto = []

    for para in doc.paragraphs:
        texto.append(para.text)

    return "\n".join(texto)


# Instancia singleton
_ingestor: Optional[IngestorLegal] = None


def get_ingestor_legal(usar_llm: bool = True) -> IngestorLegal:
    """
    Obtiene la instancia del ingestor.

    Args:
        usar_llm: Si usar LLM para clasificación

    Returns:
        IngestorLegal configurado
    """
    global _ingestor
    if _ingestor is None or _ingestor.usar_llm != usar_llm:
        _ingestor = IngestorLegal(usar_llm=usar_llm)
    return _ingestor
