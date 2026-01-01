"""
Servicio para actualizar guías del SEA desde su sitio web.

Scrapea el buscador de guías y criterios del SEA, detecta documentos nuevos
y los ingesta automáticamente al corpus RAG.
"""

import asyncio
import logging
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin, unquote

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.services.rag.embeddings import get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configuración
SEA_BASE_URL = "https://www.sea.gob.cl"
SEA_GUIAS_URL = f"{SEA_BASE_URL}/documentacion/guias-y-criterios"
DOWNLOAD_DIR = Path("/app/data/legal/guias_sea")
MAX_PAGES = 10  # Máximo de páginas a scrapear


@dataclass
class GuiaSEA:
    """Representa una guía o criterio del SEA."""
    titulo: str
    url_pdf: str
    categoria: str
    anio: Optional[int] = None
    resolucion: Optional[str] = None
    tipo: str = "Guía SEA"  # o "Criterio SEA"


@dataclass
class ResultadoActualizacion:
    """Resultado del proceso de actualización."""
    guias_encontradas: int = 0
    guias_nuevas: int = 0
    guias_actualizadas: int = 0
    guias_existentes: int = 0
    errores: List[str] = field(default_factory=list)
    documentos_ingresados: List[Dict] = field(default_factory=list)
    tiempo_total_ms: int = 0


class ActualizadorGuiasSEA:
    """
    Actualiza el corpus RAG con guías del SEA.

    Flujo:
    1. Scrapea el sitio web del SEA
    2. Compara con documentos existentes en BD
    3. Descarga PDFs nuevos
    4. Ingesta documentos nuevos
    """

    def __init__(self):
        self.embedding_service = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=60.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; MineriaSEA/1.0)"
                }
            )
        return self._http_client

    async def close(self):
        """Cierra el cliente HTTP."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def scrapear_guias(self) -> List[GuiaSEA]:
        """
        Scrapea todas las guías del sitio del SEA.

        Returns:
            Lista de guías encontradas
        """
        guias = []
        client = await self._get_client()
        page = 0

        while page < MAX_PAGES:
            url = f"{SEA_GUIAS_URL}?page={page}"
            logger.info(f"Scrapeando página {page + 1}: {url}")

            try:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Buscar items de guías - ajustar selectores según estructura real
                items = self._extraer_items_pagina(soup)

                if not items:
                    logger.info(f"No hay más items en página {page + 1}")
                    break

                guias.extend(items)
                logger.info(f"Página {page + 1}: {len(items)} guías encontradas")

                # Verificar si hay siguiente página
                if not self._hay_siguiente_pagina(soup, page):
                    break

                page += 1
                await asyncio.sleep(0.5)  # Rate limiting

            except Exception as e:
                logger.error(f"Error scrapeando página {page}: {e}")
                break

        logger.info(f"Total guías scrapeadas: {len(guias)}")
        return guias

    def _extraer_items_pagina(self, soup: BeautifulSoup) -> List[GuiaSEA]:
        """Extrae guías de una página HTML."""
        guias = []

        # Buscar todos los enlaces a PDFs del SEA
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')

            # Filtrar solo PDFs de guías/criterios
            if '/sites/default/files/' in href and href.endswith('.pdf'):
                titulo = link.get_text(strip=True)
                if not titulo or len(titulo) < 10:
                    # Buscar título en elemento padre
                    parent = link.find_parent(['div', 'td', 'li'])
                    if parent:
                        titulo = parent.get_text(strip=True)[:200]

                if not titulo or len(titulo) < 10:
                    continue

                # Normalizar URL
                url_pdf = href if href.startswith('http') else urljoin(SEA_BASE_URL, href)

                # Detectar tipo y categoría
                tipo = "Criterio SEA" if "criterio" in titulo.lower() else "Guía SEA"
                categoria = self._detectar_categoria(titulo)
                anio = self._extraer_anio(titulo, url_pdf)

                guias.append(GuiaSEA(
                    titulo=self._limpiar_titulo(titulo),
                    url_pdf=url_pdf,
                    categoria=categoria,
                    anio=anio,
                    tipo=tipo,
                ))

        # También buscar en estructuras de tabla o lista
        for row in soup.find_all(['tr', 'div'], class_=re.compile(r'guia|criterio|item|row', re.I)):
            titulo_elem = row.find(['h3', 'h4', 'a', 'strong'])
            if not titulo_elem:
                continue

            titulo = titulo_elem.get_text(strip=True)

            # Buscar enlace PDF en la fila
            pdf_link = row.find('a', href=re.compile(r'\.pdf$', re.I))
            if not pdf_link:
                continue

            url_pdf = pdf_link.get('href', '')
            if not url_pdf.startswith('http'):
                url_pdf = urljoin(SEA_BASE_URL, url_pdf)

            # Evitar duplicados
            if any(g.url_pdf == url_pdf for g in guias):
                continue

            tipo = "Criterio SEA" if "criterio" in titulo.lower() else "Guía SEA"

            guias.append(GuiaSEA(
                titulo=self._limpiar_titulo(titulo),
                url_pdf=url_pdf,
                categoria=self._detectar_categoria(titulo),
                anio=self._extraer_anio(titulo, url_pdf),
                tipo=tipo,
            ))

        return guias

    def _hay_siguiente_pagina(self, soup: BeautifulSoup, current_page: int) -> bool:
        """Verifica si hay siguiente página de resultados."""
        # Buscar links de paginación
        pager = soup.find(['nav', 'ul', 'div'], class_=re.compile(r'pager|pagination', re.I))
        if pager:
            next_link = pager.find('a', href=re.compile(f'page={current_page + 1}'))
            return next_link is not None
        return False

    def _limpiar_titulo(self, titulo: str) -> str:
        """Limpia y normaliza un título."""
        # Eliminar caracteres de control
        titulo = re.sub(r'[\x00-\x1f\x7f]', '', titulo)
        # Normalizar espacios
        titulo = re.sub(r'\s+', ' ', titulo)
        # Limitar longitud
        return titulo.strip()[:500]

    def _detectar_categoria(self, titulo: str) -> str:
        """Detecta la categoría de una guía por su título."""
        titulo_lower = titulo.lower()

        if 'criterio' in titulo_lower:
            return 'Criterios de evaluación'
        elif 'pas' in titulo_lower or 'permiso' in titulo_lower:
            return 'Permisos Ambientales Sectoriales'
        elif 'descripción' in titulo_lower or 'proyecto' in titulo_lower:
            return 'Descripción de proyectos'
        elif 'área de influencia' in titulo_lower:
            return 'Área de influencia'
        elif 'metodolog' in titulo_lower:
            return 'Metodologías y modelos'
        elif 'participación' in titulo_lower:
            return 'Participación ciudadana'
        elif 'artículo 11' in titulo_lower or 'art. 11' in titulo_lower:
            return 'Artículo 11 Ley 19.300'
        else:
            return 'Evaluación ambiental'

    def _extraer_anio(self, titulo: str, url: str) -> Optional[int]:
        """Extrae el año de publicación del título o URL."""
        # Buscar en título (ej: "2024", "segunda edición 2023")
        match = re.search(r'\b(20[0-2][0-9])\b', titulo)
        if match:
            return int(match.group(1))

        # Buscar en URL (ej: /archivos/2024/06/...)
        match = re.search(r'/archivos/(20[0-2][0-9])/', url)
        if match:
            return int(match.group(1))

        return None

    async def obtener_documentos_existentes(self, db: AsyncSession) -> Dict[str, int]:
        """
        Obtiene los documentos ya existentes en la BD.

        Returns:
            Dict con URL normalizada -> documento_id
        """
        result = await db.execute(
            text("""
                SELECT id, url_fuente, titulo
                FROM legal.documentos
                WHERE tipo IN ('Guía SEA', 'Criterio SEA')
            """)
        )

        existentes = {}
        for row in result.fetchall():
            if row.url_fuente:
                # Normalizar URL para comparación
                url_norm = self._normalizar_url(row.url_fuente)
                existentes[url_norm] = row.id
            # También por título
            titulo_norm = row.titulo.lower().strip()[:100]
            existentes[titulo_norm] = row.id

        return existentes

    def _normalizar_url(self, url: str) -> str:
        """Normaliza una URL para comparación."""
        url = unquote(url)
        url = url.replace('https://', '').replace('http://', '')
        url = url.replace('www.', '')
        return url.lower().strip()

    async def descargar_pdf(self, url: str, destino: Path) -> bool:
        """Descarga un PDF."""
        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()

            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(response.content)

            logger.debug(f"Descargado: {destino.name}")
            return True

        except Exception as e:
            logger.warning(f"Error descargando {url}: {e}")
            return False

    def extraer_texto_pdf(self, ruta_pdf: Path) -> str:
        """Extrae texto de un PDF."""
        try:
            import fitz  # PyMuPDF

            texto = ""
            with fitz.open(str(ruta_pdf)) as doc:
                for pagina in doc:
                    texto += pagina.get_text()

            return texto.strip()
        except Exception as e:
            logger.error(f"Error extrayendo texto de {ruta_pdf}: {e}")
            return ""

    def _detectar_categoria_id(self, titulo: str, tipo: str) -> int:
        """
        Detecta la categoria_id apropiada basándose en el título y tipo.

        Returns:
            ID de categoría (2=guias_sea, 4=criterios_evaluacion, o subcategorías)
        """
        titulo_lower = titulo.lower()

        # Criterios de evaluación
        if tipo == "Criterio SEA" or 'criterio' in titulo_lower:
            # Subcategorías de criterios (id 4)
            if any(x in titulo_lower for x in ['patrimonio', 'arqueolog', 'paleontolog']):
                return 26  # criterios_patrimonio
            elif any(x in titulo_lower for x in ['agua', 'hídrico', 'hidrico']):
                return 25  # criterios_componentes
            elif any(x in titulo_lower for x in ['ruido', 'fauna', 'flora', 'biodiversidad']):
                return 25  # criterios_componentes
            elif any(x in titulo_lower for x in ['impacto', 'efecto']):
                return 27  # criterios_impactos
            return 4  # criterios_evaluacion (padre)

        # Guías SEA - subcategorías más específicas
        if any(x in titulo_lower for x in ['artículo 11', 'art. 11', 'art 11']):
            # Guías Art. 11 específicas
            if 'letra a' in titulo_lower or 'salud' in titulo_lower:
                return 36  # guias_art11_letra_a
            elif 'letra b' in titulo_lower or 'recurso natural' in titulo_lower:
                return 37  # guias_art11_letra_b
            elif 'letra c' in titulo_lower or 'reasentamiento' in titulo_lower:
                return 38  # guias_art11_letra_c
            elif 'letra d' in titulo_lower or any(x in titulo_lower for x in ['área protegida', 'glaciar']):
                return 39  # guias_art11_letra_d
            elif 'letra e' in titulo_lower or 'patrimonio' in titulo_lower:
                return 40  # guias_art11_letra_e
            elif 'letra f' in titulo_lower or 'paisaje' in titulo_lower:
                return 41  # guias_art11_letra_f
            return 12  # guias_art11 (padre)

        if any(x in titulo_lower for x in ['descripción', 'descripcion']):
            # Guías de descripción por sector
            if 'minería' in titulo_lower or 'mineria' in titulo_lower:
                return 42  # guias_desc_mineria
            elif 'energía' in titulo_lower or 'energia' in titulo_lower:
                return 43  # guias_desc_energia
            elif 'infraestructura' in titulo_lower:
                return 44  # guias_desc_infraestructura
            elif 'acuicultura' in titulo_lower:
                return 45  # guias_desc_acuicultura
            return 11  # guias_descripcion (padre)

        if 'área de influencia' in titulo_lower or 'area de influencia' in titulo_lower:
            return 13  # guias_area_influencia

        if 'participación' in titulo_lower or 'participacion' in titulo_lower or 'pac' in titulo_lower:
            return 14  # guias_pac

        if any(x in titulo_lower for x in ['metodolog', 'modelo', 'estimación', 'estimacion']):
            return 15  # guias_metodologias

        if 'pas' in titulo_lower or 'permiso' in titulo_lower:
            return 16  # guias_pas

        if 'norma' in titulo_lower:
            return 17  # guias_normas

        # Por defecto: guias_sea (padre)
        return 2

    async def ingestar_guia(
        self,
        db: AsyncSession,
        guia: GuiaSEA,
        contenido: str,
    ) -> Optional[int]:
        """Ingesta una guía al corpus RAG."""

        if self.embedding_service is None:
            self.embedding_service = get_embedding_service()

        # Detectar triggers, componentes y categoría
        triggers = self._detectar_triggers(contenido)
        componentes = self._detectar_componentes(contenido)
        categoria_id = self._detectar_categoria_id(guia.titulo, guia.tipo)

        # Fecha de publicación
        fecha_pub = None
        if guia.anio:
            fecha_pub = datetime(guia.anio, 1, 1).date()

        # Insertar documento con categoria_id
        result = await db.execute(
            text("""
                INSERT INTO legal.documentos
                (titulo, tipo, fecha_publicacion, organismo, url_fuente,
                 contenido_completo, triggers_art11, componentes_ambientales,
                 categoria_id, estado)
                VALUES (:titulo, :tipo, :fecha, :organismo, :url,
                        :contenido, :triggers, :componentes, :categoria_id, 'vigente')
                RETURNING id
            """),
            {
                "titulo": guia.titulo,
                "tipo": guia.tipo,
                "fecha": fecha_pub,
                "organismo": "Servicio de Evaluación Ambiental",
                "url": guia.url_pdf,
                "contenido": contenido,
                "triggers": triggers,
                "componentes": componentes,
                "categoria_id": categoria_id,
            }
        )
        documento_id = result.scalar()

        # Segmentar y crear fragmentos
        fragmentos = self._segmentar_texto(contenido)

        if fragmentos:
            textos = [f['contenido'] for f in fragmentos]
            embeddings = self.embedding_service.embed_texts(textos)

            for frag, embedding in zip(fragmentos, embeddings):
                embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

                await db.execute(
                    text(f"""
                        INSERT INTO legal.fragmentos
                        (documento_id, seccion, numero_seccion, contenido, temas, embedding)
                        VALUES (:doc_id, :seccion, :num, :contenido, :temas, '{embedding_str}'::vector)
                    """),
                    {
                        "doc_id": documento_id,
                        "seccion": frag['seccion'],
                        "num": frag['numero'],
                        "contenido": frag['contenido'],
                        "temas": ['guia_sea'],
                    }
                )

        await db.commit()
        logger.info(f"Ingresado: {guia.titulo[:50]}... ({len(fragmentos)} fragmentos)")

        return documento_id

    def _detectar_triggers(self, texto: str) -> List[str]:
        """Detecta triggers del Art. 11 en el texto."""
        triggers_keywords = {
            'a': ['salud', 'población', 'riesgo sanitario'],
            'b': ['recurso natural', 'renovable', 'agua', 'flora', 'fauna'],
            'c': ['reasentamiento', 'comunidad humana'],
            'd': ['área protegida', 'glaciar', 'parque nacional'],
            'e': ['patrimonio', 'arqueológico', 'monumento'],
            'f': ['paisaje', 'turismo'],
        }

        texto_lower = texto.lower()
        triggers = []

        for letra, keywords in triggers_keywords.items():
            for keyword in keywords:
                if keyword in texto_lower:
                    triggers.append(letra)
                    break

        return triggers

    def _detectar_componentes(self, texto: str) -> List[str]:
        """Detecta componentes ambientales."""
        componentes_keywords = {
            'agua': ['agua', 'hídrico', 'acuífero'],
            'aire': ['aire', 'emisión', 'atmosférico'],
            'suelo': ['suelo', 'erosión'],
            'flora': ['flora', 'vegetación'],
            'fauna': ['fauna', 'biodiversidad'],
            'ruido': ['ruido', 'acústico'],
            'paisaje': ['paisaje', 'visual'],
        }

        texto_lower = texto.lower()
        componentes = []

        for comp, keywords in componentes_keywords.items():
            for keyword in keywords:
                if keyword in texto_lower:
                    componentes.append(comp)
                    break

        return componentes

    def _segmentar_texto(self, contenido: str, max_chars: int = 1500) -> List[Dict]:
        """Segmenta texto en fragmentos."""
        fragmentos = []

        # Dividir por chunks
        chunks = self._dividir_en_chunks(contenido, max_chars)
        for i, chunk in enumerate(chunks):
            if len(chunk) >= 100:
                fragmentos.append({
                    'seccion': f'Sección {i+1}',
                    'numero': str(i+1),
                    'contenido': chunk,
                })

        return fragmentos

    def _dividir_en_chunks(self, texto: str, max_chars: int = 1500) -> List[str]:
        """Divide texto en chunks respetando oraciones."""
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

    async def actualizar(self, db: AsyncSession) -> ResultadoActualizacion:
        """
        Ejecuta el proceso completo de actualización.

        Returns:
            ResultadoActualizacion con estadísticas
        """
        import time
        inicio = time.time()

        resultado = ResultadoActualizacion()

        try:
            # 1. Scrapear guías del sitio
            logger.info("Iniciando scraping del sitio SEA...")
            guias = await self.scrapear_guias()
            resultado.guias_encontradas = len(guias)

            if not guias:
                resultado.errores.append("No se encontraron guías en el sitio del SEA")
                return resultado

            # 2. Obtener documentos existentes
            existentes = await self.obtener_documentos_existentes(db)
            logger.info(f"Documentos existentes en BD: {len(existentes)}")

            # 3. Filtrar guías nuevas
            guias_nuevas = []
            for guia in guias:
                url_norm = self._normalizar_url(guia.url_pdf)
                titulo_norm = guia.titulo.lower().strip()[:100]

                if url_norm not in existentes and titulo_norm not in existentes:
                    guias_nuevas.append(guia)
                else:
                    resultado.guias_existentes += 1

            logger.info(f"Guías nuevas a procesar: {len(guias_nuevas)}")

            # 4. Procesar guías nuevas
            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

            for guia in guias_nuevas:
                try:
                    # Generar nombre de archivo
                    nombre_archivo = hashlib.md5(guia.url_pdf.encode()).hexdigest()[:12] + ".pdf"
                    ruta_pdf = DOWNLOAD_DIR / nombre_archivo

                    # Descargar PDF
                    if not ruta_pdf.exists():
                        ok = await self.descargar_pdf(guia.url_pdf, ruta_pdf)
                        if not ok:
                            resultado.errores.append(f"Error descargando: {guia.titulo[:50]}")
                            continue

                    # Extraer texto
                    contenido = self.extraer_texto_pdf(ruta_pdf)
                    if len(contenido) < 200:
                        resultado.errores.append(f"Contenido muy corto: {guia.titulo[:50]}")
                        continue

                    # Ingestar
                    doc_id = await self.ingestar_guia(db, guia, contenido)
                    if doc_id:
                        resultado.guias_nuevas += 1
                        resultado.documentos_ingresados.append({
                            "id": doc_id,
                            "titulo": guia.titulo,
                            "tipo": guia.tipo,
                        })

                except Exception as e:
                    logger.error(f"Error procesando {guia.titulo[:50]}: {e}")
                    resultado.errores.append(f"{guia.titulo[:50]}: {str(e)}")

        except Exception as e:
            logger.error(f"Error en actualización: {e}")
            resultado.errores.append(str(e))

        finally:
            await self.close()

        resultado.tiempo_total_ms = int((time.time() - inicio) * 1000)

        logger.info(
            f"Actualización completada: {resultado.guias_nuevas} nuevas, "
            f"{resultado.guias_existentes} existentes, {len(resultado.errores)} errores"
        )

        return resultado


# Singleton
_actualizador: Optional[ActualizadorGuiasSEA] = None


def get_actualizador() -> ActualizadorGuiasSEA:
    """Obtiene la instancia del actualizador."""
    global _actualizador
    if _actualizador is None:
        _actualizador = ActualizadorGuiasSEA()
    return _actualizador
