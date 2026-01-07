"""
Servicio de gestión y validación de documentación requerida según SEA.
"""
import logging
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.documento import (
    DocumentoProyecto,
    RequerimientoDocumento,
    DocumentoValidacion,
    CategoriaDocumentoSEA
)
from app.db.models.proyecto import Proyecto
from app.schemas.documento import (
    DocumentoRequeridoEstado,
    DocumentosRequeridosResponse,
    ValidacionCompletitudResponse,
    EstadoValidacion,
    CategoriaDocumentoSEA as CategoriaDocumentoSEASchema
)

logger = logging.getLogger(__name__)


class DocumentacionService:
    """Servicio para gestión de documentación requerida SEA."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_documentos_requeridos(
        self,
        proyecto_id: int
    ) -> DocumentosRequeridosResponse:
        """
        Obtiene la lista de documentos requeridos para un proyecto
        con su estado de cumplimiento.
        """
        # Obtener información del proyecto
        proyecto = await self.db.get(Proyecto, proyecto_id)
        if not proyecto:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")

        # Obtener vía de evaluación sugerida
        via_evaluacion = await self._obtener_via_evaluacion(proyecto_id)

        # Obtener requerimientos aplicables
        requerimientos = await self._obtener_requerimientos_aplicables(
            proyecto.tipo_proyecto_id,
            proyecto.subtipo_proyecto_id
        )

        # Obtener documentos subidos del proyecto
        documentos_subidos = await self._obtener_documentos_por_categoria(proyecto_id)

        # Construir lista de estados
        items: List[DocumentoRequeridoEstado] = []
        total_obligatorios = 0
        total_subidos = 0

        for req in requerimientos:
            # Determinar si es obligatorio según la vía
            obligatorio_segun_via = (
                req.es_obligatorio or
                (via_evaluacion == "DIA" and req.obligatorio_para_dia) or
                (via_evaluacion == "EIA" and req.obligatorio_para_eia)
            )

            if obligatorio_segun_via:
                total_obligatorios += 1

            # Buscar documento subido para esta categoría
            doc_subido = documentos_subidos.get(req.categoria_sea)
            estado = EstadoValidacion.PENDIENTE
            doc_id = None
            doc_nombre = None

            if doc_subido:
                doc_id = doc_subido.id
                doc_nombre = doc_subido.nombre
                estado = EstadoValidacion.SUBIDO
                total_subidos += 1

            items.append(DocumentoRequeridoEstado(
                requerimiento_id=req.id,
                categoria_sea=CategoriaDocumentoSEASchema(req.categoria_sea),
                nombre_display=req.nombre_display,
                descripcion=req.descripcion,
                notas_sea=req.notas_sea,
                es_obligatorio=req.es_obligatorio,
                obligatorio_segun_via=obligatorio_segun_via,
                seccion_eia=req.seccion_eia,
                orden=req.orden,
                documento_id=doc_id,
                documento_nombre=doc_nombre,
                estado_cumplimiento=estado,
                formatos_permitidos=req.formatos_permitidos or [],
                requiere_crs_wgs84=req.requiere_crs_wgs84
            ))

        # Ordenar por orden
        items.sort(key=lambda x: x.orden)

        return DocumentosRequeridosResponse(
            proyecto_id=proyecto_id,
            via_evaluacion=via_evaluacion,
            items=items,
            total_requeridos=len(items),
            total_obligatorios=total_obligatorios,
            total_subidos=total_subidos
        )

    async def validar_completitud(
        self,
        proyecto_id: int
    ) -> ValidacionCompletitudResponse:
        """
        Valida la completitud de la documentación de un proyecto.
        Retorna detalle de qué documentos faltan.
        """
        # Obtener documentos requeridos con estado
        docs_requeridos = await self.obtener_documentos_requeridos(proyecto_id)

        # Calcular estadísticas
        obligatorios_faltantes: List[str] = []
        opcionales_faltantes: List[str] = []
        alertas: List[str] = []

        for item in docs_requeridos.items:
            if item.estado_cumplimiento == EstadoValidacion.PENDIENTE:
                if item.obligatorio_segun_via:
                    obligatorios_faltantes.append(item.nombre_display)
                else:
                    opcionales_faltantes.append(item.nombre_display)

        # Calcular porcentaje
        porcentaje = 0.0
        if docs_requeridos.total_requeridos > 0:
            porcentaje = round(
                (docs_requeridos.total_subidos / docs_requeridos.total_requeridos) * 100,
                1
            )

        # Generar alertas
        es_completo = len(obligatorios_faltantes) == 0

        if not es_completo:
            alertas.append(
                f"Faltan {len(obligatorios_faltantes)} documento(s) obligatorio(s)"
            )

        if len(opcionales_faltantes) > 5:
            alertas.append(
                f"Se recomienda completar los {len(opcionales_faltantes)} documentos opcionales"
            )

        # Verificar documentos de cartografía
        cartografia_faltante = any(
            item.categoria_sea == CategoriaDocumentoSEASchema.CARTOGRAFIA_PLANOS
            and item.estado_cumplimiento == EstadoValidacion.PENDIENTE
            for item in docs_requeridos.items
        )
        if cartografia_faltante:
            alertas.append("La cartografía del proyecto es obligatoria para el análisis GIS")

        return ValidacionCompletitudResponse(
            proyecto_id=proyecto_id,
            es_completo=es_completo,
            total_requeridos=docs_requeridos.total_requeridos,
            total_obligatorios=docs_requeridos.total_obligatorios,
            total_subidos=docs_requeridos.total_subidos,
            porcentaje_completitud=porcentaje,
            obligatorios_faltantes=obligatorios_faltantes,
            opcionales_faltantes=opcionales_faltantes,
            alertas=alertas,
            puede_continuar=es_completo
        )

    async def vincular_documento_a_categoria(
        self,
        documento_id: UUID,
        categoria_sea: str
    ) -> DocumentoProyecto:
        """
        Vincula un documento existente a una categoría SEA específica.
        """
        documento = await self.db.get(DocumentoProyecto, documento_id)
        if not documento:
            raise ValueError(f"Documento {documento_id} no encontrado")

        documento.categoria_sea = categoria_sea

        # Actualizar estado de validación si existe
        await self._actualizar_estado_validacion(
            documento.proyecto_id,
            categoria_sea,
            documento_id,
            EstadoValidacion.SUBIDO
        )

        await self.db.commit()
        await self.db.refresh(documento)

        return documento

    async def marcar_no_aplica(
        self,
        proyecto_id: int,
        categoria_sea: str,
        observaciones: Optional[str] = None
    ) -> DocumentoValidacion:
        """
        Marca una categoría de documento como 'no aplica' para el proyecto.
        """
        # Buscar o crear registro de validación
        stmt = select(DocumentoValidacion).where(
            DocumentoValidacion.proyecto_id == proyecto_id,
            DocumentoValidacion.categoria_sea == categoria_sea
        )
        result = await self.db.execute(stmt)
        validacion = result.scalar_one_or_none()

        if not validacion:
            validacion = DocumentoValidacion(
                proyecto_id=proyecto_id,
                categoria_sea=categoria_sea,
                estado=EstadoValidacion.NO_APLICA.value,
                observaciones=observaciones
            )
            self.db.add(validacion)
        else:
            validacion.estado = EstadoValidacion.NO_APLICA.value
            validacion.observaciones = observaciones

        await self.db.commit()
        await self.db.refresh(validacion)

        return validacion

    async def obtener_resumen_por_seccion(
        self,
        proyecto_id: int
    ) -> dict:
        """
        Agrupa los documentos requeridos por sección del EIA.
        """
        docs_requeridos = await self.obtener_documentos_requeridos(proyecto_id)

        secciones = {}
        for item in docs_requeridos.items:
            seccion = item.seccion_eia or "otros"
            if seccion not in secciones:
                secciones[seccion] = {
                    "nombre": self._nombre_seccion(seccion),
                    "documentos": [],
                    "total": 0,
                    "completados": 0
                }

            secciones[seccion]["documentos"].append(item)
            secciones[seccion]["total"] += 1
            if item.estado_cumplimiento != EstadoValidacion.PENDIENTE:
                secciones[seccion]["completados"] += 1

        return secciones

    # =========================================================================
    # Métodos privados
    # =========================================================================

    async def _obtener_via_evaluacion(self, proyecto_id: int) -> str:
        """Obtiene la vía de evaluación sugerida para el proyecto."""
        # Buscar en diagnósticos
        query = text("""
            SELECT via_sugerida
            FROM proyectos.proyecto_diagnosticos
            WHERE proyecto_id = :proyecto_id
            ORDER BY version DESC
            LIMIT 1
        """)
        result = await self.db.execute(query, {"proyecto_id": proyecto_id})
        row = result.fetchone()

        if row and row[0]:
            return row[0]

        # Default a EIA (más conservador)
        return "EIA"

    async def _obtener_requerimientos_aplicables(
        self,
        tipo_proyecto_id: Optional[int],
        subtipo_proyecto_id: Optional[int]
    ) -> List[RequerimientoDocumento]:
        """
        Obtiene los requerimientos de documentos aplicables al tipo de proyecto.
        Prioriza: subtipo > tipo > genéricos
        """
        stmt = select(RequerimientoDocumento).where(
            RequerimientoDocumento.activo == True
        )

        # Filtrar por tipo/subtipo o genéricos
        if tipo_proyecto_id:
            stmt = stmt.where(
                (RequerimientoDocumento.tipo_proyecto_id == tipo_proyecto_id) |
                (RequerimientoDocumento.tipo_proyecto_id.is_(None))
            )

            if subtipo_proyecto_id:
                stmt = stmt.where(
                    (RequerimientoDocumento.subtipo_proyecto_id == subtipo_proyecto_id) |
                    (RequerimientoDocumento.subtipo_proyecto_id.is_(None))
                )
        else:
            # Solo genéricos
            stmt = stmt.where(RequerimientoDocumento.tipo_proyecto_id.is_(None))

        stmt = stmt.order_by(RequerimientoDocumento.orden)

        result = await self.db.execute(stmt)
        requerimientos = result.scalars().all()

        # Deduplicar por categoría (priorizar específicos sobre genéricos)
        categorias_vistas = {}
        resultado_final = []

        for req in requerimientos:
            cat = req.categoria_sea
            if cat not in categorias_vistas:
                categorias_vistas[cat] = req
                resultado_final.append(req)
            elif req.tipo_proyecto_id and not categorias_vistas[cat].tipo_proyecto_id:
                # Reemplazar genérico por específico
                resultado_final.remove(categorias_vistas[cat])
                categorias_vistas[cat] = req
                resultado_final.append(req)

        return resultado_final

    async def _obtener_documentos_por_categoria(
        self,
        proyecto_id: int
    ) -> dict:
        """
        Obtiene los documentos del proyecto indexados por categoría SEA.
        """
        stmt = select(DocumentoProyecto).where(
            DocumentoProyecto.proyecto_id == proyecto_id,
            DocumentoProyecto.categoria_sea.isnot(None)
        )
        result = await self.db.execute(stmt)
        documentos = result.scalars().all()

        return {doc.categoria_sea: doc for doc in documentos}

    async def _actualizar_estado_validacion(
        self,
        proyecto_id: int,
        categoria_sea: str,
        documento_id: UUID,
        estado: EstadoValidacion
    ):
        """Actualiza o crea registro de validación."""
        stmt = select(DocumentoValidacion).where(
            DocumentoValidacion.proyecto_id == proyecto_id,
            DocumentoValidacion.categoria_sea == categoria_sea
        )
        result = await self.db.execute(stmt)
        validacion = result.scalar_one_or_none()

        if validacion:
            validacion.documento_id = documento_id
            validacion.estado = estado.value
        else:
            validacion = DocumentoValidacion(
                proyecto_id=proyecto_id,
                categoria_sea=categoria_sea,
                documento_id=documento_id,
                estado=estado.value
            )
            self.db.add(validacion)

    def _nombre_seccion(self, codigo: str) -> str:
        """Retorna nombre legible de sección EIA."""
        nombres = {
            "descripcion_proyecto": "Descripción del Proyecto",
            "linea_base": "Línea de Base",
            "prediccion_impactos": "Predicción y Evaluación de Impactos",
            "medidas_mitigacion": "Plan de Medidas de Mitigación",
            "plan_seguimiento": "Plan de Seguimiento",
            "plan_cierre": "Plan de Cierre",
            "participacion": "Participación Ciudadana",
            "pas": "Permisos Ambientales Sectoriales",
            "anexos": "Anexos",
            "otros": "Otros"
        }
        return nombres.get(codigo, codigo.replace("_", " ").title())
