"""
Servicio de configuración por industria.

Gestiona tipos, subtipos, umbrales SEIA, PAS, normativa, OAECA,
impactos, anexos y árboles de preguntas configurables por sector.
"""
import logging
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.config_industria import (
    TipoProyecto,
    SubtipoProyecto,
    UmbralSEIA,
    PASPorTipo,
    NormativaPorTipo,
    OAECAPorTipo,
    ImpactoPorTipo,
    AnexoPorTipo,
    ArbolPregunta,
)
from app.schemas.config_industria import (
    ConfigIndustriaCompleta,
    TipoProyectoResponse,
    SubtipoProyectoResponse,
    UmbralSEIAResponse,
    PASPorTipoResponse,
    NormativaPorTipoResponse,
    OAECAPorTipoResponse,
    ImpactoPorTipoResponse,
    AnexoPorTipoResponse,
    ArbolPreguntaResponse,
    EvaluarUmbralResponse,
    PASAplicableResponse,
    ResultadoUmbralEnum,
)

logger = logging.getLogger(__name__)


class ConfigIndustriaService:
    """
    Servicio para gestionar la configuración por industria.

    Proporciona acceso a tipos de proyecto, subtipos, umbrales SEIA,
    PAS, normativa, OAECA, impactos, anexos y árboles de preguntas.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            db: Sesión de base de datos async
        """
        self.db = db

    # =========================================================================
    # Tipos de Proyecto
    # =========================================================================

    async def get_tipos_proyecto(self, solo_activos: bool = True) -> List[TipoProyecto]:
        """
        Obtiene todos los tipos de proyecto.

        Args:
            solo_activos: Si True, solo retorna tipos activos

        Returns:
            Lista de tipos de proyecto
        """
        query = select(TipoProyecto).options(selectinload(TipoProyecto.subtipos))
        if solo_activos:
            query = query.where(TipoProyecto.activo == True)
        query = query.order_by(TipoProyecto.nombre)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_tipo_por_codigo(self, codigo: str) -> Optional[TipoProyecto]:
        """
        Obtiene un tipo de proyecto por su código.

        Args:
            codigo: Código del tipo (ej: 'mineria', 'energia')

        Returns:
            TipoProyecto o None
        """
        result = await self.db.execute(
            select(TipoProyecto)
            .options(selectinload(TipoProyecto.subtipos))
            .where(TipoProyecto.codigo == codigo)
        )
        return result.scalar()

    async def get_tipo_por_id(self, tipo_id: int) -> Optional[TipoProyecto]:
        """
        Obtiene un tipo de proyecto por ID.

        Args:
            tipo_id: ID del tipo

        Returns:
            TipoProyecto o None
        """
        result = await self.db.execute(
            select(TipoProyecto)
            .options(selectinload(TipoProyecto.subtipos))
            .where(TipoProyecto.id == tipo_id)
        )
        return result.scalar()

    # =========================================================================
    # Subtipos de Proyecto
    # =========================================================================

    async def get_subtipos(
        self,
        tipo_codigo: str,
        solo_activos: bool = True
    ) -> List[SubtipoProyecto]:
        """
        Obtiene los subtipos de un tipo de proyecto.

        Args:
            tipo_codigo: Código del tipo padre
            solo_activos: Si True, solo retorna subtipos activos

        Returns:
            Lista de subtipos
        """
        tipo = await self.get_tipo_por_codigo(tipo_codigo)
        if not tipo:
            return []

        query = select(SubtipoProyecto).where(
            SubtipoProyecto.tipo_proyecto_id == tipo.id
        )
        if solo_activos:
            query = query.where(SubtipoProyecto.activo == True)
        query = query.order_by(SubtipoProyecto.nombre)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_subtipo_por_codigo(
        self,
        tipo_codigo: str,
        subtipo_codigo: str
    ) -> Optional[SubtipoProyecto]:
        """
        Obtiene un subtipo por código.

        Args:
            tipo_codigo: Código del tipo padre
            subtipo_codigo: Código del subtipo

        Returns:
            SubtipoProyecto o None
        """
        tipo = await self.get_tipo_por_codigo(tipo_codigo)
        if not tipo:
            return None

        result = await self.db.execute(
            select(SubtipoProyecto).where(
                and_(
                    SubtipoProyecto.tipo_proyecto_id == tipo.id,
                    SubtipoProyecto.codigo == subtipo_codigo
                )
            )
        )
        return result.scalar()

    # =========================================================================
    # Configuración Completa
    # =========================================================================

    async def get_config_completa(
        self,
        tipo_codigo: str,
        subtipo_codigo: Optional[str] = None
    ) -> Optional[ConfigIndustriaCompleta]:
        """
        Obtiene la configuración completa para un tipo/subtipo de proyecto.

        Args:
            tipo_codigo: Código del tipo de proyecto
            subtipo_codigo: Código del subtipo (opcional)

        Returns:
            ConfigIndustriaCompleta con toda la configuración
        """
        tipo = await self.get_tipo_por_codigo(tipo_codigo)
        if not tipo:
            logger.warning(f"Tipo de proyecto no encontrado: {tipo_codigo}")
            return None

        subtipo = None
        subtipo_id = None
        if subtipo_codigo:
            subtipo = await self.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
            if subtipo:
                subtipo_id = subtipo.id

        # Obtener todos los datos en paralelo
        subtipos = await self.get_subtipos(tipo_codigo)
        umbrales = await self.get_umbrales(tipo.id, subtipo_id)
        pas = await self.get_pas(tipo.id, subtipo_id)
        normativa = await self.get_normativa(tipo.id)
        oaeca = await self.get_oaeca(tipo.id)
        impactos = await self.get_impactos(tipo.id, subtipo_id)
        anexos = await self.get_anexos(tipo.id, subtipo_id)
        preguntas = await self.get_preguntas(tipo.id, subtipo_id)

        return ConfigIndustriaCompleta(
            tipo=TipoProyectoResponse.model_validate(tipo),
            subtipo=SubtipoProyectoResponse.model_validate(subtipo) if subtipo else None,
            subtipos_disponibles=[SubtipoProyectoResponse.model_validate(s) for s in subtipos],
            umbrales=[UmbralSEIAResponse.model_validate(u) for u in umbrales],
            pas=[PASPorTipoResponse.model_validate(p) for p in pas],
            normativa=[NormativaPorTipoResponse.model_validate(n) for n in normativa],
            oaeca=[OAECAPorTipoResponse.model_validate(o) for o in oaeca],
            impactos=[ImpactoPorTipoResponse.model_validate(i) for i in impactos],
            anexos=[AnexoPorTipoResponse.model_validate(a) for a in anexos],
            preguntas=[ArbolPreguntaResponse.model_validate(p) for p in preguntas],
        )

    # =========================================================================
    # Umbrales SEIA
    # =========================================================================

    async def get_umbrales(
        self,
        tipo_id: int,
        subtipo_id: Optional[int] = None
    ) -> List[UmbralSEIA]:
        """
        Obtiene los umbrales SEIA para un tipo/subtipo.

        Args:
            tipo_id: ID del tipo de proyecto
            subtipo_id: ID del subtipo (opcional)

        Returns:
            Lista de umbrales aplicables
        """
        # Obtener umbrales del tipo y del subtipo si aplica
        query = select(UmbralSEIA).where(
            and_(
                UmbralSEIA.tipo_proyecto_id == tipo_id,
                UmbralSEIA.activo == True,
                or_(
                    UmbralSEIA.subtipo_id == None,
                    UmbralSEIA.subtipo_id == subtipo_id
                ) if subtipo_id else UmbralSEIA.subtipo_id == None
            )
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def evaluar_umbral(
        self,
        tipo_codigo: str,
        parametros: Dict[str, float],
        subtipo_codigo: Optional[str] = None
    ) -> Optional[EvaluarUmbralResponse]:
        """
        Evalúa si un proyecto cumple umbrales de ingreso SEIA.

        Args:
            tipo_codigo: Código del tipo de proyecto
            parametros: Dict con parámetros a evaluar (ej: {'tonelaje_mensual': 4500})
            subtipo_codigo: Código del subtipo (opcional)

        Returns:
            EvaluarUmbralResponse con el resultado de la evaluación
        """
        tipo = await self.get_tipo_por_codigo(tipo_codigo)
        if not tipo:
            return None

        subtipo_id = None
        if subtipo_codigo:
            subtipo = await self.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
            if subtipo:
                subtipo_id = subtipo.id

        umbrales = await self.get_umbrales(tipo.id, subtipo_id)

        for parametro, valor_proyecto in parametros.items():
            for umbral in umbrales:
                if umbral.parametro == parametro:
                    cumple = umbral.evaluar(valor_proyecto)
                    umbral_valor = float(umbral.valor)

                    if cumple:
                        mensaje = (
                            f"Con {valor_proyecto} {umbral.unidad or ''} "
                            f"CUMPLE el umbral de {umbral_valor} {umbral.unidad or ''} "
                            f"({umbral.norma_referencia or 'DS 40'}). "
                            f"Resultado: {umbral.resultado}"
                        )
                    else:
                        mensaje = (
                            f"Con {valor_proyecto} {umbral.unidad or ''} "
                            f"NO cumple el umbral de {umbral_valor} {umbral.unidad or ''} "
                            f"({umbral.norma_referencia or 'DS 40'}). "
                            f"Podría ingresar por otra causal."
                        )

                    return EvaluarUmbralResponse(
                        cumple_umbral=cumple,
                        resultado=ResultadoUmbralEnum(umbral.resultado) if cumple else ResultadoUmbralEnum.NO_INGRESA,
                        umbral_evaluado=UmbralSEIAResponse.model_validate(umbral),
                        valor_proyecto=valor_proyecto,
                        diferencia=valor_proyecto - umbral_valor,
                        mensaje=mensaje
                    )

        return EvaluarUmbralResponse(
            cumple_umbral=False,
            resultado=ResultadoUmbralEnum.NO_INGRESA,
            umbral_evaluado=None,
            valor_proyecto=0,
            diferencia=0,
            mensaje="No se encontró umbral aplicable para los parámetros proporcionados"
        )

    # =========================================================================
    # PAS (Permisos Ambientales Sectoriales)
    # =========================================================================

    async def get_pas(
        self,
        tipo_id: int,
        subtipo_id: Optional[int] = None
    ) -> List[PASPorTipo]:
        """
        Obtiene los PAS para un tipo/subtipo.

        Args:
            tipo_id: ID del tipo de proyecto
            subtipo_id: ID del subtipo (opcional)

        Returns:
            Lista de PAS aplicables
        """
        query = select(PASPorTipo).where(
            and_(
                PASPorTipo.tipo_proyecto_id == tipo_id,
                PASPorTipo.activo == True,
                or_(
                    PASPorTipo.subtipo_id == None,
                    PASPorTipo.subtipo_id == subtipo_id
                ) if subtipo_id else PASPorTipo.subtipo_id == None
            )
        ).order_by(PASPorTipo.articulo)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_pas_aplicables(
        self,
        tipo_codigo: str,
        caracteristicas: Dict[str, Any],
        subtipo_codigo: Optional[str] = None
    ) -> List[PASAplicableResponse]:
        """
        Identifica los PAS que aplican según características del proyecto.

        Args:
            tipo_codigo: Código del tipo de proyecto
            caracteristicas: Dict con características del proyecto
            subtipo_codigo: Código del subtipo (opcional)

        Returns:
            Lista de PAS con indicación de si aplican
        """
        tipo = await self.get_tipo_por_codigo(tipo_codigo)
        if not tipo:
            return []

        subtipo_id = None
        if subtipo_codigo:
            subtipo = await self.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
            if subtipo:
                subtipo_id = subtipo.id

        pas_list = await self.get_pas(tipo.id, subtipo_id)
        resultado = []

        for pas in pas_list:
            aplica = pas.aplica(caracteristicas)

            if aplica:
                razon = f"PAS obligatorio para {tipo_codigo}"
                if pas.condicion_activacion:
                    razon = f"Aplica por: {list(pas.condicion_activacion.keys())}"
            else:
                if pas.obligatoriedad == "obligatorio" and not pas.condicion_activacion:
                    aplica = True
                    razon = "PAS obligatorio para este tipo de proyecto"
                else:
                    razon = "No cumple condiciones de activación"

            resultado.append(PASAplicableResponse(
                pas=PASPorTipoResponse.model_validate(pas),
                aplica=aplica,
                razon=razon
            ))

        return resultado

    # =========================================================================
    # Normativa
    # =========================================================================

    async def get_normativa(self, tipo_id: int) -> List[NormativaPorTipo]:
        """
        Obtiene la normativa aplicable a un tipo de proyecto.

        Args:
            tipo_id: ID del tipo de proyecto

        Returns:
            Lista de normativas
        """
        query = select(NormativaPorTipo).where(
            and_(
                NormativaPorTipo.tipo_proyecto_id == tipo_id,
                NormativaPorTipo.activo == True
            )
        ).order_by(NormativaPorTipo.tipo_norma, NormativaPorTipo.norma)

        result = await self.db.execute(query)
        return result.scalars().all()

    # =========================================================================
    # OAECA
    # =========================================================================

    async def get_oaeca(self, tipo_id: int) -> List[OAECAPorTipo]:
        """
        Obtiene los OAECA relevantes para un tipo de proyecto.

        Args:
            tipo_id: ID del tipo de proyecto

        Returns:
            Lista de OAECA ordenados por relevancia
        """
        query = select(OAECAPorTipo).where(
            and_(
                OAECAPorTipo.tipo_proyecto_id == tipo_id,
                OAECAPorTipo.activo == True
            )
        ).order_by(OAECAPorTipo.relevancia, OAECAPorTipo.organismo)

        result = await self.db.execute(query)
        return result.scalars().all()

    # =========================================================================
    # Impactos
    # =========================================================================

    async def get_impactos(
        self,
        tipo_id: int,
        subtipo_id: Optional[int] = None
    ) -> List[ImpactoPorTipo]:
        """
        Obtiene los impactos típicos de un tipo/subtipo.

        Args:
            tipo_id: ID del tipo de proyecto
            subtipo_id: ID del subtipo (opcional)

        Returns:
            Lista de impactos típicos
        """
        query = select(ImpactoPorTipo).where(
            and_(
                ImpactoPorTipo.tipo_proyecto_id == tipo_id,
                ImpactoPorTipo.activo == True,
                or_(
                    ImpactoPorTipo.subtipo_id == None,
                    ImpactoPorTipo.subtipo_id == subtipo_id
                ) if subtipo_id else ImpactoPorTipo.subtipo_id == None
            )
        ).order_by(ImpactoPorTipo.componente, ImpactoPorTipo.frecuencia)

        result = await self.db.execute(query)
        return result.scalars().all()

    # =========================================================================
    # Anexos
    # =========================================================================

    async def get_anexos(
        self,
        tipo_id: int,
        subtipo_id: Optional[int] = None
    ) -> List[AnexoPorTipo]:
        """
        Obtiene los anexos requeridos para un tipo/subtipo.

        Args:
            tipo_id: ID del tipo de proyecto
            subtipo_id: ID del subtipo (opcional)

        Returns:
            Lista de anexos
        """
        query = select(AnexoPorTipo).where(
            and_(
                AnexoPorTipo.tipo_proyecto_id == tipo_id,
                AnexoPorTipo.activo == True,
                or_(
                    AnexoPorTipo.subtipo_id == None,
                    AnexoPorTipo.subtipo_id == subtipo_id
                ) if subtipo_id else AnexoPorTipo.subtipo_id == None
            )
        ).order_by(AnexoPorTipo.codigo)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_anexos_aplicables(
        self,
        tipo_codigo: str,
        caracteristicas: Dict[str, Any],
        subtipo_codigo: Optional[str] = None
    ) -> List[AnexoPorTipo]:
        """
        Obtiene los anexos que aplican según características del proyecto.

        Args:
            tipo_codigo: Código del tipo de proyecto
            caracteristicas: Dict con características del proyecto
            subtipo_codigo: Código del subtipo (opcional)

        Returns:
            Lista de anexos aplicables
        """
        tipo = await self.get_tipo_por_codigo(tipo_codigo)
        if not tipo:
            return []

        subtipo_id = None
        if subtipo_codigo:
            subtipo = await self.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
            if subtipo:
                subtipo_id = subtipo.id

        anexos = await self.get_anexos(tipo.id, subtipo_id)
        return [a for a in anexos if a.aplica(caracteristicas)]

    # =========================================================================
    # Árbol de Preguntas
    # =========================================================================

    async def get_preguntas(
        self,
        tipo_id: int,
        subtipo_id: Optional[int] = None
    ) -> List[ArbolPregunta]:
        """
        Obtiene las preguntas del árbol para un tipo/subtipo.

        Args:
            tipo_id: ID del tipo de proyecto
            subtipo_id: ID del subtipo (opcional)

        Returns:
            Lista de preguntas ordenadas
        """
        query = select(ArbolPregunta).where(
            and_(
                ArbolPregunta.tipo_proyecto_id == tipo_id,
                ArbolPregunta.activo == True,
                or_(
                    ArbolPregunta.subtipo_id == None,
                    ArbolPregunta.subtipo_id == subtipo_id
                ) if subtipo_id else ArbolPregunta.subtipo_id == None
            )
        ).order_by(ArbolPregunta.orden)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_siguiente_pregunta(
        self,
        tipo_codigo: str,
        respuestas_previas: Dict[str, Any],
        subtipo_codigo: Optional[str] = None
    ) -> Optional[ArbolPregunta]:
        """
        Obtiene la siguiente pregunta del árbol según respuestas previas.

        Args:
            tipo_codigo: Código del tipo de proyecto
            respuestas_previas: Dict con respuestas ya recopiladas
            subtipo_codigo: Código del subtipo (opcional)

        Returns:
            Siguiente pregunta a mostrar o None si completado
        """
        tipo = await self.get_tipo_por_codigo(tipo_codigo)
        if not tipo:
            return None

        subtipo_id = None
        if subtipo_codigo:
            subtipo = await self.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
            if subtipo:
                subtipo_id = subtipo.id

        preguntas = await self.get_preguntas(tipo.id, subtipo_id)
        codigos_respondidos = set(respuestas_previas.keys())

        for pregunta in preguntas:
            # Saltar preguntas ya respondidas
            if pregunta.codigo in codigos_respondidos:
                continue

            # Verificar si la pregunta debe mostrarse
            if pregunta.debe_mostrarse(respuestas_previas):
                return pregunta

        return None

    async def calcular_progreso(
        self,
        tipo_codigo: str,
        respuestas_previas: Dict[str, Any],
        subtipo_codigo: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Calcula el progreso de recopilación.

        Args:
            tipo_codigo: Código del tipo de proyecto
            respuestas_previas: Dict con respuestas ya recopiladas
            subtipo_codigo: Código del subtipo (opcional)

        Returns:
            Tupla (preguntas_respondidas, total_preguntas_aplicables)
        """
        tipo = await self.get_tipo_por_codigo(tipo_codigo)
        if not tipo:
            return (0, 0)

        subtipo_id = None
        if subtipo_codigo:
            subtipo = await self.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
            if subtipo:
                subtipo_id = subtipo.id

        preguntas = await self.get_preguntas(tipo.id, subtipo_id)

        # Contar preguntas aplicables y respondidas
        aplicables = 0
        respondidas = 0

        for pregunta in preguntas:
            if pregunta.debe_mostrarse(respuestas_previas):
                aplicables += 1
                if pregunta.codigo in respuestas_previas:
                    respondidas += 1

        return (respondidas, aplicables)


# =============================================================================
# Factory Function
# =============================================================================

def get_config_industria_service(db: AsyncSession) -> ConfigIndustriaService:
    """
    Factory function para obtener el servicio.

    Args:
        db: Sesión de base de datos async

    Returns:
        ConfigIndustriaService configurado
    """
    return ConfigIndustriaService(db)
