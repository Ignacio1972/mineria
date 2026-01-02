"""
OCR usando Claude Vision.

Convierte páginas PDF a imágenes y usa Claude Vision para extraer
texto, tablas y descripciones de gráficos.
"""

import base64
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import anthropic
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ResultadoOCR:
    """Resultado del procesamiento OCR."""
    texto: str
    paginas_procesadas: int
    tokens_usados: int
    tiempo_ms: int
    metodo: str = "claude_vision"
    tablas_detectadas: int = 0
    imagenes_descritas: int = 0


class ClaudeVisionOCR:
    """
    Servicio de OCR usando Claude Vision.

    Convierte PDFs a imágenes y extrae texto usando las capacidades
    de visión de Claude, incluyendo:
    - Texto impreso y manuscrito
    - Tablas (preservando estructura)
    - Descripciones de gráficos e imágenes
    """

    PROMPT_OCR = """Analiza esta imagen de un documento y extrae TODO el contenido textual.

INSTRUCCIONES:
1. Extrae todo el texto visible, preservando la estructura y formato
2. Para TABLAS: reconstruye la estructura usando formato markdown con | para columnas
3. Para GRÁFICOS/FIGURAS: describe brevemente qué muestran entre corchetes [Gráfico: ...]
4. Para FÓRMULAS: transcribe usando notación textual clara
5. Mantén los títulos, subtítulos y numeración original
6. Si hay texto en columnas, procesa de izquierda a derecha

FORMATO DE SALIDA:
- Texto plano estructurado
- Tablas en formato markdown
- Descripciones de imágenes entre corchetes

Extrae el contenido:"""

    def __init__(self):
        self._cliente: Optional[anthropic.Anthropic] = None
        self.modelo = settings.OCR_VISION_MODEL
        self.dpi = settings.OCR_IMAGE_DPI
        self.max_paginas = settings.OCR_MAX_PAGES

    @property
    def cliente(self) -> anthropic.Anthropic:
        """Cliente de Anthropic (síncrono para procesamiento batch)."""
        if self._cliente is None:
            api_key = settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY no configurada")
            self._cliente = anthropic.Anthropic(api_key=api_key)
        return self._cliente

    def pdf_a_imagenes(self, ruta_pdf: str) -> list[Image.Image]:
        """
        Convierte un PDF a lista de imágenes PIL.

        Args:
            ruta_pdf: Ruta al archivo PDF

        Returns:
            Lista de imágenes PIL, una por página
        """
        from pdf2image import convert_from_path

        logger.info(f"Convirtiendo PDF a imágenes: {ruta_pdf}")

        imagenes = convert_from_path(
            ruta_pdf,
            dpi=self.dpi,
            first_page=1,
            last_page=self.max_paginas,
        )

        logger.info(f"Convertidas {len(imagenes)} páginas")
        return imagenes

    def imagen_a_base64(self, imagen: Image.Image, formato: str = "PNG") -> str:
        """Convierte una imagen PIL a base64."""
        buffer = io.BytesIO()

        # Convertir a RGB si es necesario (para JPEG)
        if formato.upper() == "JPEG" and imagen.mode in ("RGBA", "P"):
            imagen = imagen.convert("RGB")

        imagen.save(buffer, format=formato)
        return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

    def optimizar_imagen(self, imagen: Image.Image, max_dimension: int = 1568) -> Image.Image:
        """
        Optimiza una imagen para enviar a Claude Vision.

        Claude Vision tiene un límite de ~1568px en la dimensión mayor
        para mejor rendimiento.
        """
        ancho, alto = imagen.size

        if max(ancho, alto) <= max_dimension:
            return imagen

        if ancho > alto:
            nuevo_ancho = max_dimension
            nuevo_alto = int(alto * (max_dimension / ancho))
        else:
            nuevo_alto = max_dimension
            nuevo_ancho = int(ancho * (max_dimension / alto))

        return imagen.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

    def extraer_texto_imagen(self, imagen: Image.Image, num_pagina: int = 1) -> tuple[str, int]:
        """
        Extrae texto de una imagen usando Claude Vision.

        Args:
            imagen: Imagen PIL
            num_pagina: Número de página (para logging)

        Returns:
            Tupla (texto_extraido, tokens_usados)
        """
        # Optimizar imagen
        imagen_opt = self.optimizar_imagen(imagen)

        # Convertir a base64
        imagen_b64 = self.imagen_a_base64(imagen_opt, formato="PNG")

        logger.debug(f"Procesando página {num_pagina} con Claude Vision")

        try:
            respuesta = self.cliente.messages.create(
                model=self.modelo,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": imagen_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": self.PROMPT_OCR,
                            },
                        ],
                    }
                ],
            )

            texto = respuesta.content[0].text if respuesta.content else ""
            tokens = respuesta.usage.input_tokens + respuesta.usage.output_tokens

            return texto, tokens

        except Exception as e:
            logger.error(f"Error en OCR página {num_pagina}: {e}")
            return f"[Error procesando página {num_pagina}]", 0

    def procesar_pdf(self, ruta_pdf: str) -> ResultadoOCR:
        """
        Procesa un PDF completo y extrae todo el texto.

        Args:
            ruta_pdf: Ruta al archivo PDF

        Returns:
            ResultadoOCR con el texto y metadatos
        """
        import time
        inicio = time.time()

        if not Path(ruta_pdf).exists():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta_pdf}")

        # Convertir PDF a imágenes
        imagenes = self.pdf_a_imagenes(ruta_pdf)

        if not imagenes:
            return ResultadoOCR(
                texto="",
                paginas_procesadas=0,
                tokens_usados=0,
                tiempo_ms=0,
            )

        # Procesar cada página
        textos = []
        tokens_total = 0
        tablas = 0
        graficos = 0

        for i, imagen in enumerate(imagenes, 1):
            logger.info(f"OCR página {i}/{len(imagenes)}")

            texto_pagina, tokens = self.extraer_texto_imagen(imagen, i)

            # Agregar separador de página
            textos.append(f"\n--- Página {i} ---\n{texto_pagina}")
            tokens_total += tokens

            # Contar tablas y gráficos detectados
            if "|" in texto_pagina and "---" in texto_pagina:
                tablas += texto_pagina.count("\n|")
            if "[Gráfico:" in texto_pagina or "[Figura:" in texto_pagina:
                graficos += texto_pagina.count("[Gráfico:") + texto_pagina.count("[Figura:")

        tiempo_ms = int((time.time() - inicio) * 1000)
        texto_completo = "\n".join(textos)

        logger.info(
            f"OCR completado: {len(imagenes)} páginas, "
            f"{len(texto_completo)} chars, {tokens_total} tokens, {tiempo_ms}ms"
        )

        return ResultadoOCR(
            texto=texto_completo,
            paginas_procesadas=len(imagenes),
            tokens_usados=tokens_total,
            tiempo_ms=tiempo_ms,
            tablas_detectadas=tablas,
            imagenes_descritas=graficos,
        )


# Instancia singleton
_ocr_service: Optional[ClaudeVisionOCR] = None


def get_ocr_service() -> ClaudeVisionOCR:
    """Obtiene la instancia singleton del servicio OCR."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = ClaudeVisionOCR()
    return _ocr_service


def extraer_texto_con_vision(ruta_pdf: str) -> str:
    """
    Función de conveniencia para extraer texto de un PDF usando Claude Vision.

    Args:
        ruta_pdf: Ruta al archivo PDF

    Returns:
        Texto extraído del PDF
    """
    ocr = get_ocr_service()
    resultado = ocr.procesar_pdf(ruta_pdf)
    return resultado.texto
