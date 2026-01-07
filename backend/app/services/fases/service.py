"""
Servicio de Fases del Workflow EIA.

Calcula la fase actual del proyecto y el progreso global
basándose en el estado de completitud de diferentes etapas.
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.proyecto import Proyecto, Analisis, ComponenteEIAChecklist
from app.schemas.proyecto import FaseProyecto

logger = logging.getLogger(__name__)


class ServicioFases:
    """Servicio para calcular fase actual y progreso del proyecto."""

    @staticmethod
    async def calcular_fase_actual(
        db: AsyncSession,
        proyecto_id: int,
    ) -> str:
        """
        Calcula la fase actual del proyecto en el workflow EIA.

        Reglas:
        1. identificacion: Sin geometría O sin análisis
        2. prefactibilidad: Tiene análisis, NO tiene checklist
        3. recopilacion: Tiene checklist, <50% componentes avanzados
        4. generacion: >50% componentes avanzados, NO tiene EIA generado
        5. refinamiento: Tiene EIA generado

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto

        Returns:
            Fase actual (identificacion | prefactibilidad | recopilacion | generacion | refinamiento)
        """
        # Obtener proyecto
        result = await db.execute(
            select(Proyecto).where(Proyecto.id == proyecto_id)
        )
        proyecto = result.scalar_one_or_none()

        if not proyecto:
            logger.warning(f"Proyecto {proyecto_id} no encontrado")
            return FaseProyecto.IDENTIFICACION.value

        # 1. Identificación: Sin geometría o sin análisis
        if not proyecto.geom:
            return FaseProyecto.IDENTIFICACION.value

        # Verificar si tiene análisis
        result = await db.execute(
            select(func.count(Analisis.id))
            .where(Analisis.proyecto_id == proyecto_id)
        )
        tiene_analisis = result.scalar() > 0

        if not tiene_analisis:
            return FaseProyecto.IDENTIFICACION.value

        # 2. Prefactibilidad: Tiene análisis pero NO tiene checklist
        result = await db.execute(
            select(func.count(ComponenteEIAChecklist.id))
            .where(ComponenteEIAChecklist.proyecto_id == proyecto_id)
        )
        tiene_checklist = result.scalar() > 0

        if not tiene_checklist:
            return FaseProyecto.PREFACTIBILIDAD.value

        # 3-4. Recopilación vs Generación: Depende de progreso de componentes
        result = await db.execute(
            select(
                func.count(ComponenteEIAChecklist.id).label("total"),
                func.count(
                    func.nullif(
                        ComponenteEIAChecklist.estado != 'pendiente',
                        False
                    )
                ).label("avanzados")
            )
            .where(ComponenteEIAChecklist.proyecto_id == proyecto_id)
        )
        stats = result.one()

        if stats.total == 0:
            return FaseProyecto.PREFACTIBILIDAD.value

        porcentaje_avanzado = (stats.avanzados / stats.total) * 100

        # Si menos del 50% están avanzados → Recopilación
        if porcentaje_avanzado < 50:
            return FaseProyecto.RECOPILACION.value

        # 5. Refinamiento: Verificar si tiene EIA generado
        # TODO: Implementar verificación de documento EIA generado
        # Por ahora, si >50% avanzado → Generación
        return FaseProyecto.GENERACION.value

    @staticmethod
    async def calcular_progreso_global(
        db: AsyncSession,
        proyecto_id: int,
    ) -> int:
        """
        Calcula el progreso global del proyecto (0-100%).

        Ponderación:
        - Identificación: 0-20%
          - Sin geometría: 0%
          - Con geometría: 20%
        - Prefactibilidad: 20-30%
          - Sin análisis: 20%
          - Con análisis: 30%
        - Recopilación: 30-70% (40 puntos)
          - Basado en % de componentes avanzados
        - Generación: 70-90% (20 puntos)
          - Basado en % de capítulos generados
        - Refinamiento: 90-100% (10 puntos)
          - Basado en validaciones completadas

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto

        Returns:
            Progreso global (0-100)
        """
        # Obtener proyecto
        result = await db.execute(
            select(Proyecto).where(Proyecto.id == proyecto_id)
        )
        proyecto = result.scalar_one_or_none()

        if not proyecto:
            return 0

        progreso = 0

        # FASE 1: Identificación (0-20%)
        if proyecto.geom:
            progreso = 20
        else:
            return 0  # Sin geometría, progreso mínimo

        # FASE 2: Prefactibilidad (20-30%)
        result = await db.execute(
            select(func.count(Analisis.id))
            .where(Analisis.proyecto_id == proyecto_id)
        )
        tiene_analisis = result.scalar() > 0

        if tiene_analisis:
            progreso = 30
        else:
            return 20  # Solo geometría

        # FASE 3: Recopilación (30-70%) - 40 puntos
        result = await db.execute(
            select(
                func.count(ComponenteEIAChecklist.id).label("total"),
                func.avg(ComponenteEIAChecklist.progreso_porcentaje).label("promedio_progreso"),
                func.count(
                    func.nullif(
                        ComponenteEIAChecklist.estado == 'completado',
                        False
                    )
                ).label("completados")
            )
            .where(ComponenteEIAChecklist.proyecto_id == proyecto_id)
        )
        stats = result.one()

        if stats.total > 0:
            # Calcular progreso de recopilación basado en componentes
            promedio_componentes = stats.promedio_progreso or 0
            progreso_recopilacion = (promedio_componentes / 100) * 40  # 40 puntos máximo
            progreso = 30 + int(progreso_recopilacion)
        else:
            return 30  # Solo análisis, sin checklist

        # FASE 4: Generación (70-90%) - 20 puntos
        # TODO: Implementar cuando exista sistema de generación de capítulos
        # Por ahora, si todos los componentes están >80%, dar 10 puntos extra
        if stats.total > 0 and (stats.promedio_progreso or 0) >= 80:
            progreso = min(progreso + 10, 90)

        # FASE 5: Refinamiento (90-100%) - 10 puntos
        # TODO: Implementar cuando exista sistema de validación/refinamiento
        # Por ahora, si todos los componentes están completos, dar 5 puntos extra
        if stats.total > 0 and stats.completados == stats.total:
            progreso = min(progreso + 5, 100)

        return min(progreso, 100)  # Asegurar que no exceda 100

    @staticmethod
    async def actualizar_fase_y_progreso(
        db: AsyncSession,
        proyecto_id: int,
    ) -> Dict[str, Any]:
        """
        Actualiza fase_actual y progreso_global del proyecto.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto

        Returns:
            Diccionario con fase_actual y progreso_global actualizados
        """
        # Calcular valores
        fase_actual = await ServicioFases.calcular_fase_actual(db, proyecto_id)
        progreso_global = await ServicioFases.calcular_progreso_global(db, proyecto_id)

        # Actualizar proyecto
        result = await db.execute(
            select(Proyecto).where(Proyecto.id == proyecto_id)
        )
        proyecto = result.scalar_one_or_none()

        if proyecto:
            proyecto.fase_actual = fase_actual
            proyecto.progreso_global = progreso_global
            await db.commit()
            await db.refresh(proyecto)

            logger.info(
                f"Proyecto {proyecto_id}: fase={fase_actual}, progreso={progreso_global}%"
            )

            return {
                "fase_actual": fase_actual,
                "progreso_global": progreso_global,
            }

        return {
            "fase_actual": FaseProyecto.IDENTIFICACION.value,
            "progreso_global": 0,
        }

    @staticmethod
    async def obtener_estadisticas_componentes(
        db: AsyncSession,
        proyecto_id: int,
    ) -> Dict[str, int]:
        """
        Obtiene estadísticas de los componentes del checklist.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto

        Returns:
            Diccionario con estadísticas
        """
        result = await db.execute(
            select(
                func.count(ComponenteEIAChecklist.id).label("total"),
                func.count(
                    func.nullif(
                        ComponenteEIAChecklist.estado == 'completado',
                        False
                    )
                ).label("completados"),
                func.count(
                    func.nullif(
                        ComponenteEIAChecklist.estado == 'en_progreso',
                        False
                    )
                ).label("en_progreso"),
                func.count(
                    func.nullif(
                        ComponenteEIAChecklist.estado == 'pendiente',
                        False
                    )
                ).label("pendientes"),
            )
            .where(ComponenteEIAChecklist.proyecto_id == proyecto_id)
        )
        stats = result.one()

        return {
            "total": stats.total,
            "completados": stats.completados,
            "en_progreso": stats.en_progreso,
            "pendientes": stats.pendientes,
        }
