"""
Servicio de Estructura EIA (Fase 2).

Genera y gestiona la estructura del EIA para proyectos que requieren
Estudio de Impacto Ambiental según Art. 11 de la Ley 19.300.
"""
import logging
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.db.models.estructura_eia import (
    CapituloEIA,
    ComponenteLineaBase,
    EstructuraEIAProyecto,
    EstructuraPorInstrumento,
)
from app.db.models.config_industria import (
    TipoProyecto,
    PASPorTipo,
    AnexoPorTipo,
)
from app.db.models.proyecto import Proyecto
from app.db.models.proyecto_extendido import (
    ProyectoCaracteristica,
    ProyectoPAS,
    ProyectoAnalisisArt11,
    ProyectoDiagnostico,
)
from app.schemas.estructura_eia import (
    CapituloConEstado,
    PASConEstado,
    AnexoRequerido,
    ComponenteLineaBaseEnPlan,
    EstimacionComplejidad,
    FactorComplejidad,
    RecursoSugerido,
    EstructuraEIAResponse,
    ResumenEstructuraParaAsistente,
    EstadoCapituloEnum,
    EstadoPASEnum,
    EstadoAnexoEnum,
    NivelComplejidadEnum,
    ObligatoriedadPASEnum,
)

logger = logging.getLogger(__name__)


class EstructuraEIAService:
    """
    Servicio para generar y gestionar estructura del EIA.

    Genera los 11 capítulos según Art. 18 DS 40, identifica PAS aplicables,
    anexos técnicos, plan de línea base y estimación de complejidad.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Generación de Estructura
    # =========================================================================

    async def generar_estructura(
        self,
        proyecto_id: int,
        instrumento: Literal["EIA", "DIA"] = "EIA",
        forzar_regenerar: bool = False
    ) -> Optional[EstructuraEIAResponse]:
        """
        Genera la estructura completa del EIA o DIA para un proyecto.

        Args:
            proyecto_id: ID del proyecto
            instrumento: Tipo de instrumento ("EIA" o "DIA")
            forzar_regenerar: Si True, regenera aunque exista

        Returns:
            EstructuraEIAResponse con la estructura generada
        """
        # Verificar si ya existe estructura
        estructura_existente = await self.get_estructura_proyecto(proyecto_id)
        if estructura_existente and not forzar_regenerar:
            logger.info(f"Estructura {instrumento} ya existe para proyecto {proyecto_id}")
            return await self._convertir_a_response(estructura_existente)

        # Obtener proyecto con tipo
        proyecto = await self._get_proyecto_con_tipo(proyecto_id)
        if not proyecto:
            logger.error(f"Proyecto {proyecto_id} no encontrado")
            return None

        tipo_proyecto_id = proyecto.tipo_proyecto_id
        subtipo_id = proyecto.subtipo_proyecto_id

        if not tipo_proyecto_id:
            logger.error(f"Proyecto {proyecto_id} no tiene tipo asignado")
            return None

        # Obtener configuración por instrumento
        config_instrumento = await self._get_config_instrumento(instrumento, tipo_proyecto_id)

        # Generar componentes según instrumento
        capitulos = await self._generar_capitulos(tipo_proyecto_id, instrumento)
        pas_requeridos = await self._generar_pas(proyecto_id, tipo_proyecto_id, subtipo_id)
        anexos = await self._generar_anexos(proyecto_id, tipo_proyecto_id, subtipo_id)

        # DIA no requiere línea base completa
        plan_linea_base = []
        if config_instrumento and config_instrumento.requiere_linea_base:
            plan_linea_base = await self._generar_plan_linea_base(tipo_proyecto_id, subtipo_id)
        elif instrumento == "EIA":
            # Fallback para EIA sin config
            plan_linea_base = await self._generar_plan_linea_base(tipo_proyecto_id, subtipo_id)

        # Estimar complejidad (solo para EIA, DIA es más simple)
        estimacion = None
        if instrumento == "EIA":
            estimacion = await self._estimar_complejidad(proyecto_id, tipo_proyecto_id)

        # Determinar versión
        version = 1
        if estructura_existente:
            version = estructura_existente.version + 1

        # Crear estructura
        estructura = EstructuraEIAProyecto(
            proyecto_id=proyecto_id,
            version=version,
            instrumento=instrumento,
            capitulos=[c.model_dump() for c in capitulos],
            pas_requeridos=[p.model_dump() for p in pas_requeridos],
            anexos_requeridos=[a.model_dump() for a in anexos],
            plan_linea_base=[p.model_dump() for p in plan_linea_base],
            estimacion_complejidad=estimacion.model_dump() if estimacion else None,
        )

        self.db.add(estructura)
        await self.db.commit()
        await self.db.refresh(estructura)

        logger.info(f"Estructura {instrumento} generada para proyecto {proyecto_id} v{version}")
        return await self._convertir_a_response(estructura)

    async def _get_config_instrumento(
        self,
        instrumento: str,
        tipo_proyecto_id: int
    ) -> Optional[EstructuraPorInstrumento]:
        """Obtiene la configuración para un instrumento específico."""
        result = await self.db.execute(
            select(EstructuraPorInstrumento)
            .where(
                and_(
                    EstructuraPorInstrumento.instrumento == instrumento,
                    EstructuraPorInstrumento.tipo_proyecto_id == tipo_proyecto_id,
                    EstructuraPorInstrumento.activo == True
                )
            )
        )
        return result.scalar()

    async def _generar_capitulos(
        self,
        tipo_proyecto_id: int,
        instrumento: str = "EIA"
    ) -> List[CapituloConEstado]:
        """Genera los capítulos según tipo de proyecto e instrumento."""
        result = await self.db.execute(
            select(CapituloEIA)
            .where(
                and_(
                    CapituloEIA.tipo_proyecto_id == tipo_proyecto_id,
                    CapituloEIA.activo == True
                )
            )
            .order_by(CapituloEIA.orden)
        )
        capitulos_config = result.scalars().all()

        capitulos = []
        for cap in capitulos_config:
            # Filtrar por instrumento
            aplica_instrumentos = cap.aplica_instrumento or ['EIA']
            if instrumento not in aplica_instrumentos:
                continue

            contenido = cap.contenido_requerido or []

            # Para DIA, capítulo 2 es "Justificación inexistencia Art. 11"
            if instrumento == "DIA" and cap.numero == 2:
                contenido = [
                    "Análisis literal a) - Riesgo para salud de población",
                    "Análisis literal b) - Recursos naturales renovables",
                    "Análisis literal c) - Reasentamiento o alteración sistemas de vida",
                    "Análisis literal d) - Áreas protegidas o sitios prioritarios",
                    "Análisis literal e) - Valor paisajístico o turístico",
                    "Análisis literal f) - Patrimonio cultural",
                    "Conclusión general de inexistencia de efectos"
                ]

            capitulos.append(CapituloConEstado(
                numero=cap.numero,
                titulo=cap.titulo if instrumento == "EIA" else self._get_titulo_dia(cap.numero, cap.titulo),
                descripcion=cap.descripcion,
                contenido_requerido=contenido,
                es_obligatorio=cap.es_obligatorio,
                estado=EstadoCapituloEnum.PENDIENTE,
                progreso_porcentaje=0,
                secciones_completadas=0,
                secciones_totales=len(contenido),
            ))

        return capitulos

    def _get_titulo_dia(self, numero: int, titulo_eia: str) -> str:
        """Obtiene título adaptado para DIA."""
        titulos_dia = {
            1: "Descripción del Proyecto",
            2: "Justificación de Inexistencia de Efectos Art. 11",
            8: "Normativa Ambiental Aplicable",
            9: "Permisos Ambientales Sectoriales",
            11: "Compromisos Ambientales Voluntarios"
        }
        return titulos_dia.get(numero, titulo_eia)

    async def _generar_pas(
        self,
        proyecto_id: int,
        tipo_proyecto_id: int,
        subtipo_id: Optional[int]
    ) -> List[PASConEstado]:
        """Genera lista de PAS requeridos según características del proyecto."""
        # Obtener características del proyecto
        caracteristicas = await self._get_caracteristicas_proyecto(proyecto_id)

        # Obtener PAS configurados
        query = select(PASPorTipo).where(
            and_(
                PASPorTipo.tipo_proyecto_id == tipo_proyecto_id,
                PASPorTipo.activo == True
            )
        ).order_by(PASPorTipo.articulo)

        result = await self.db.execute(query)
        pas_config = result.scalars().all()

        pas_list = []
        for pas in pas_config:
            aplica, razon = self._evaluar_pas(pas, caracteristicas)
            if aplica:
                pas_list.append(PASConEstado(
                    articulo=pas.articulo,
                    nombre=pas.nombre,
                    organismo=pas.organismo,
                    obligatoriedad=ObligatoriedadPASEnum(pas.obligatoriedad),
                    estado=EstadoPASEnum.IDENTIFICADO,
                    condiciones=pas.condicion_activacion,
                    razon_aplicacion=razon,
                ))

        return pas_list

    def _evaluar_pas(self, pas: PASPorTipo, caracteristicas: Dict) -> tuple[bool, str]:
        """Evalúa si un PAS aplica y retorna razón."""
        # PAS obligatorios siempre aplican
        if pas.obligatoriedad == "obligatorio" and not pas.condicion_activacion:
            return True, "PAS obligatorio para este tipo de proyecto"

        # Evaluar condiciones
        if pas.condicion_activacion:
            for campo, valor_esperado in pas.condicion_activacion.items():
                valor_proyecto = caracteristicas.get(campo)
                if valor_proyecto == valor_esperado:
                    return True, f"Aplica por {campo}={valor_esperado}"

        # PAS frecuentes se incluyen
        if pas.obligatoriedad == "frecuente":
            return True, "PAS frecuente para este tipo de proyecto"

        return False, ""

    async def _generar_anexos(
        self,
        proyecto_id: int,
        tipo_proyecto_id: int,
        subtipo_id: Optional[int]
    ) -> List[AnexoRequerido]:
        """Genera lista de anexos técnicos requeridos."""
        caracteristicas = await self._get_caracteristicas_proyecto(proyecto_id)

        query = select(AnexoPorTipo).where(
            and_(
                AnexoPorTipo.tipo_proyecto_id == tipo_proyecto_id,
                AnexoPorTipo.activo == True
            )
        ).order_by(AnexoPorTipo.codigo)

        result = await self.db.execute(query)
        anexos_config = result.scalars().all()

        anexos = []
        for anexo in anexos_config:
            aplica, razon = self._evaluar_anexo(anexo, caracteristicas)
            if aplica:
                anexos.append(AnexoRequerido(
                    codigo=anexo.codigo,
                    nombre=anexo.nombre,
                    descripcion=anexo.descripcion,
                    profesional_responsable=anexo.profesional_responsable,
                    obligatorio=anexo.obligatorio,
                    estado=EstadoAnexoEnum.PENDIENTE,
                    condicion_activacion=anexo.condicion_activacion,
                    razon_aplicacion=razon,
                ))

        return anexos

    def _evaluar_anexo(self, anexo: AnexoPorTipo, caracteristicas: Dict) -> tuple[bool, str]:
        """Evalúa si un anexo aplica y retorna razón."""
        if anexo.obligatorio and not anexo.condicion_activacion:
            return True, "Anexo obligatorio"

        if anexo.condicion_activacion:
            for campo, valor_esperado in anexo.condicion_activacion.items():
                if caracteristicas.get(campo) == valor_esperado:
                    return True, f"Aplica por {campo}={valor_esperado}"

        if anexo.obligatorio:
            return True, "Anexo obligatorio"

        return False, ""

    async def _generar_plan_linea_base(
        self,
        tipo_proyecto_id: int,
        subtipo_id: Optional[int]
    ) -> List[ComponenteLineaBaseEnPlan]:
        """Genera el plan de línea base."""
        query = select(ComponenteLineaBase).where(
            and_(
                ComponenteLineaBase.tipo_proyecto_id == tipo_proyecto_id,
                ComponenteLineaBase.activo == True
            )
        ).order_by(ComponenteLineaBase.orden)

        result = await self.db.execute(query)
        componentes = result.scalars().all()

        plan = []
        for comp in componentes:
            plan.append(ComponenteLineaBaseEnPlan(
                codigo=comp.codigo,
                nombre=comp.nombre,
                descripcion=comp.descripcion,
                metodologia=comp.metodologia,
                variables_monitorear=comp.variables_monitorear or [],
                estudios_requeridos=comp.estudios_requeridos or [],
                duracion_estimada_dias=comp.duracion_estimada_dias,
                es_obligatorio=comp.es_obligatorio,
                aplica=True,
                razon_aplicacion="Componente estándar para este tipo de proyecto",
                prioridad=1 if comp.es_obligatorio else 2,
            ))

        return plan

    async def _estimar_complejidad(
        self,
        proyecto_id: int,
        tipo_proyecto_id: int
    ) -> EstimacionComplejidad:
        """Estima la complejidad del EIA."""
        factores = []
        puntaje_total = 0

        # Factor 1: Triggers Art. 11 activados
        triggers = await self._contar_triggers_art11(proyecto_id)
        peso_triggers = 0.25
        valor_triggers = min(triggers * 2, 10)
        factores.append(FactorComplejidad(
            nombre="Triggers Art. 11",
            descripcion=f"{triggers} triggers activados",
            peso=peso_triggers,
            valor=valor_triggers,
            contribucion=peso_triggers * valor_triggers
        ))
        puntaje_total += peso_triggers * valor_triggers

        # Factor 2: Número de PAS
        num_pas = await self._contar_pas_proyecto(proyecto_id, tipo_proyecto_id)
        peso_pas = 0.2
        valor_pas = min(num_pas, 10)
        factores.append(FactorComplejidad(
            nombre="PAS requeridos",
            descripcion=f"{num_pas} permisos sectoriales",
            peso=peso_pas,
            valor=valor_pas,
            contribucion=peso_pas * valor_pas
        ))
        puntaje_total += peso_pas * valor_pas

        # Factor 3: Componentes de línea base
        num_componentes = await self._contar_componentes_lb(tipo_proyecto_id)
        peso_componentes = 0.2
        valor_componentes = min(num_componentes / 2, 10)
        factores.append(FactorComplejidad(
            nombre="Componentes línea base",
            descripcion=f"{num_componentes} componentes a caracterizar",
            peso=peso_componentes,
            valor=valor_componentes,
            contribucion=peso_componentes * valor_componentes
        ))
        puntaje_total += peso_componentes * valor_componentes

        # Factor 4: Sensibilidad territorial (áreas protegidas, comunidades)
        sensibilidad = await self._evaluar_sensibilidad(proyecto_id)
        peso_sensibilidad = 0.2
        factores.append(FactorComplejidad(
            nombre="Sensibilidad territorial",
            descripcion=f"Nivel {sensibilidad}/10",
            peso=peso_sensibilidad,
            valor=sensibilidad,
            contribucion=peso_sensibilidad * sensibilidad
        ))
        puntaje_total += peso_sensibilidad * sensibilidad

        # Factor 5: Escala del proyecto
        escala = await self._evaluar_escala(proyecto_id)
        peso_escala = 0.15
        factores.append(FactorComplejidad(
            nombre="Escala del proyecto",
            descripcion=f"Nivel {escala}/10",
            peso=peso_escala,
            valor=escala,
            contribucion=peso_escala * escala
        ))
        puntaje_total += peso_escala * escala

        # Normalizar puntaje a 0-100
        puntaje_normalizado = int(puntaje_total * 10)

        # Determinar nivel
        if puntaje_normalizado <= 25:
            nivel = NivelComplejidadEnum.BAJA
            tiempo_meses = 6
        elif puntaje_normalizado <= 50:
            nivel = NivelComplejidadEnum.MEDIA
            tiempo_meses = 12
        elif puntaje_normalizado <= 75:
            nivel = NivelComplejidadEnum.ALTA
            tiempo_meses = 18
        else:
            nivel = NivelComplejidadEnum.MUY_ALTA
            tiempo_meses = 24

        # Recursos sugeridos
        recursos = self._sugerir_recursos(nivel, num_componentes, num_pas)

        # Riesgos principales
        riesgos = self._identificar_riesgos(factores, triggers, sensibilidad)

        # Recomendaciones
        recomendaciones = self._generar_recomendaciones(nivel, factores)

        return EstimacionComplejidad(
            nivel=nivel,
            puntaje=puntaje_normalizado,
            factores=factores,
            tiempo_estimado_meses=tiempo_meses,
            recursos_sugeridos=recursos,
            riesgos_principales=riesgos,
            recomendaciones=recomendaciones,
        )

    async def _contar_triggers_art11(self, proyecto_id: int) -> int:
        """Cuenta triggers Art. 11 activados (estado='confirmado')."""
        result = await self.db.execute(
            select(ProyectoAnalisisArt11)
            .where(
                and_(
                    ProyectoAnalisisArt11.proyecto_id == proyecto_id,
                    ProyectoAnalisisArt11.estado == "confirmado"
                )
            )
        )
        return len(result.scalars().all())

    async def _contar_pas_proyecto(self, proyecto_id: int, tipo_proyecto_id: int) -> int:
        """Cuenta PAS aplicables."""
        result = await self.db.execute(
            select(PASPorTipo)
            .where(
                and_(
                    PASPorTipo.tipo_proyecto_id == tipo_proyecto_id,
                    PASPorTipo.activo == True
                )
            )
        )
        return len(result.scalars().all())

    async def _contar_componentes_lb(self, tipo_proyecto_id: int) -> int:
        """Cuenta componentes de línea base."""
        result = await self.db.execute(
            select(ComponenteLineaBase)
            .where(
                and_(
                    ComponenteLineaBase.tipo_proyecto_id == tipo_proyecto_id,
                    ComponenteLineaBase.activo == True
                )
            )
        )
        return len(result.scalars().all())

    async def _evaluar_sensibilidad(self, proyecto_id: int) -> float:
        """Evalúa sensibilidad territorial (0-10)."""
        caracteristicas = await self._get_caracteristicas_proyecto(proyecto_id)

        sensibilidad = 5.0  # Base

        # Ajustar según características
        if caracteristicas.get("cerca_area_protegida"):
            sensibilidad += 2.0
        if caracteristicas.get("cerca_comunidad_indigena"):
            sensibilidad += 2.0
        if caracteristicas.get("zona_sensible"):
            sensibilidad += 1.5

        return min(sensibilidad, 10.0)

    async def _evaluar_escala(self, proyecto_id: int) -> float:
        """Evalúa escala del proyecto (0-10)."""
        caracteristicas = await self._get_caracteristicas_proyecto(proyecto_id)

        # Evaluar según superficie o producción
        superficie = caracteristicas.get("superficie_total_ha", 0)
        if superficie > 1000:
            return 9.0
        elif superficie > 500:
            return 7.0
        elif superficie > 100:
            return 5.0
        elif superficie > 50:
            return 3.0

        return 4.0  # Default medio

    def _sugerir_recursos(
        self,
        nivel: NivelComplejidadEnum,
        num_componentes: int,
        num_pas: int
    ) -> List[RecursoSugerido]:
        """Sugiere recursos según complejidad."""
        recursos = []

        # Director de proyecto
        recursos.append(RecursoSugerido(
            tipo="profesional",
            nombre="Director de Proyecto EIA",
            descripcion="Coordinación general del estudio",
            cantidad=1,
            prioridad="alta"
        ))

        # Especialistas según componentes
        if num_componentes > 10:
            recursos.append(RecursoSugerido(
                tipo="profesional",
                nombre="Especialistas ambientales",
                descripcion="Medio físico, biótico y humano",
                cantidad=min(num_componentes // 4, 6),
                prioridad="alta"
            ))

        # Gestor de permisos
        if num_pas > 5:
            recursos.append(RecursoSugerido(
                tipo="profesional",
                nombre="Gestor de permisos",
                descripcion="Tramitación de PAS",
                cantidad=1,
                prioridad="media"
            ))

        return recursos

    def _identificar_riesgos(
        self,
        factores: List[FactorComplejidad],
        triggers: int,
        sensibilidad: float
    ) -> List[str]:
        """Identifica riesgos principales."""
        riesgos = []

        if triggers >= 3:
            riesgos.append("Múltiples efectos Art. 11 pueden generar observaciones complejas")

        if sensibilidad >= 7:
            riesgos.append("Alta sensibilidad territorial puede requerir consulta indígena (Art. 85)")

        for factor in factores:
            if factor.valor >= 8:
                riesgos.append(f"Alto valor en {factor.nombre}: revisar estrategia")

        if not riesgos:
            riesgos.append("Sin riesgos críticos identificados")

        return riesgos

    def _generar_recomendaciones(
        self,
        nivel: NivelComplejidadEnum,
        factores: List[FactorComplejidad]
    ) -> List[str]:
        """Genera recomendaciones según nivel."""
        recomendaciones = []

        if nivel in [NivelComplejidadEnum.ALTA, NivelComplejidadEnum.MUY_ALTA]:
            recomendaciones.append("Considerar reunión de inicio con SEA regional")
            recomendaciones.append("Planificar participación ciudadana anticipada")

        recomendaciones.append("Comenzar línea de base lo antes posible (componentes con estacionalidad)")
        recomendaciones.append("Identificar tempranamente requisitos de PAS críticos")

        return recomendaciones

    # =========================================================================
    # Consultas y Actualizaciones
    # =========================================================================

    async def get_estructura_proyecto(
        self,
        proyecto_id: int,
        version: Optional[int] = None
    ) -> Optional[EstructuraEIAProyecto]:
        """Obtiene la estructura EIA de un proyecto."""
        query = select(EstructuraEIAProyecto).where(
            EstructuraEIAProyecto.proyecto_id == proyecto_id
        )

        if version:
            query = query.where(EstructuraEIAProyecto.version == version)
        else:
            query = query.order_by(desc(EstructuraEIAProyecto.version))

        result = await self.db.execute(query)
        return result.scalar()

    async def get_capitulos_tipo(self, tipo_codigo: str) -> List[CapituloEIA]:
        """Obtiene capítulos configurados para un tipo."""
        result = await self.db.execute(
            select(CapituloEIA)
            .join(TipoProyecto)
            .where(
                and_(
                    TipoProyecto.codigo == tipo_codigo,
                    CapituloEIA.activo == True
                )
            )
            .order_by(CapituloEIA.orden)
        )
        return result.scalars().all()

    async def get_componentes_linea_base(
        self,
        tipo_codigo: str
    ) -> List[ComponenteLineaBase]:
        """Obtiene componentes de línea base para un tipo."""
        result = await self.db.execute(
            select(ComponenteLineaBase)
            .join(TipoProyecto)
            .where(
                and_(
                    TipoProyecto.codigo == tipo_codigo,
                    ComponenteLineaBase.activo == True
                )
            )
            .order_by(ComponenteLineaBase.orden)
        )
        return result.scalars().all()

    async def actualizar_estado_capitulo(
        self,
        proyecto_id: int,
        capitulo_numero: int,
        estado: str,
        progreso: Optional[int] = None
    ) -> Optional[EstructuraEIAProyecto]:
        """Actualiza el estado de un capítulo."""
        estructura = await self.get_estructura_proyecto(proyecto_id)
        if not estructura:
            return None

        if estructura.actualizar_capitulo(capitulo_numero, estado, progreso):
            flag_modified(estructura, "capitulos")
            await self.db.commit()
            await self.db.refresh(estructura)

        return estructura

    async def actualizar_estado_pas(
        self,
        proyecto_id: int,
        articulo: int,
        estado: str
    ) -> Optional[EstructuraEIAProyecto]:
        """Actualiza el estado de un PAS."""
        estructura = await self.get_estructura_proyecto(proyecto_id)
        if not estructura:
            return None

        if estructura.actualizar_pas(articulo, estado):
            flag_modified(estructura, "pas_requeridos")
            await self.db.commit()
            await self.db.refresh(estructura)

        return estructura

    async def actualizar_estado_anexo(
        self,
        proyecto_id: int,
        codigo: str,
        estado: str
    ) -> Optional[EstructuraEIAProyecto]:
        """Actualiza el estado de un anexo."""
        estructura = await self.get_estructura_proyecto(proyecto_id)
        if not estructura:
            return None

        if estructura.actualizar_anexo(codigo, estado):
            flag_modified(estructura, "anexos_requeridos")
            await self.db.commit()
            await self.db.refresh(estructura)

        return estructura

    # =========================================================================
    # Métodos para el Asistente
    # =========================================================================

    async def get_resumen_para_asistente(
        self,
        proyecto_id: int
    ) -> ResumenEstructuraParaAsistente:
        """Obtiene resumen de estructura formateado para el asistente."""
        estructura = await self.get_estructura_proyecto(proyecto_id)

        if not estructura:
            return ResumenEstructuraParaAsistente(
                existe_estructura=False,
                proyecto_id=proyecto_id,
                proximos_pasos=["Generar estructura EIA con 'generar_estructura_eia'"]
            )

        # Contar estados de capítulos
        capitulos = estructura.capitulos or []
        cap_completados = sum(1 for c in capitulos if c.get("estado") == "completado")
        cap_en_progreso = sum(1 for c in capitulos if c.get("estado") == "en_progreso")
        cap_pendientes = len(capitulos) - cap_completados - cap_en_progreso

        # Contar estados de PAS
        pas = estructura.pas_requeridos or []
        pas_aprobados = sum(1 for p in pas if p.get("estado") == "aprobado")
        pas_en_tramite = sum(1 for p in pas if p.get("estado") == "en_tramite")
        pas_pendientes = len(pas) - pas_aprobados - pas_en_tramite

        # Contar anexos
        anexos = estructura.anexos_requeridos or []
        anexos_completados = sum(1 for a in anexos if a.get("estado") == "completado")

        # Complejidad
        estimacion = estructura.estimacion_complejidad or {}
        nivel = estimacion.get("nivel")
        tiempo = estimacion.get("tiempo_estimado_meses")

        # Próximos pasos
        proximos_pasos = []
        if cap_pendientes > 0:
            proximos_pasos.append(f"Avanzar en {cap_pendientes} capítulos pendientes")
        if pas_pendientes > 0:
            proximos_pasos.append(f"Iniciar tramitación de {pas_pendientes} PAS")
        if not proximos_pasos:
            proximos_pasos.append("Revisar contenido de capítulos completados")

        return ResumenEstructuraParaAsistente(
            existe_estructura=True,
            proyecto_id=proyecto_id,
            version=estructura.version,
            progreso_general=estructura.progreso_general,
            capitulos_total=len(capitulos),
            capitulos_completados=cap_completados,
            capitulos_en_progreso=cap_en_progreso,
            capitulos_pendientes=cap_pendientes,
            pas_total=len(pas),
            pas_aprobados=pas_aprobados,
            pas_en_tramite=pas_en_tramite,
            pas_pendientes=pas_pendientes,
            anexos_total=len(anexos),
            anexos_completados=anexos_completados,
            nivel_complejidad=nivel,
            tiempo_estimado_meses=tiempo,
            proximos_pasos=proximos_pasos,
        )

    # =========================================================================
    # Helpers Privados
    # =========================================================================

    async def _get_proyecto_con_tipo(self, proyecto_id: int) -> Optional[Proyecto]:
        """Obtiene proyecto con su tipo."""
        result = await self.db.execute(
            select(Proyecto).where(Proyecto.id == proyecto_id)
        )
        return result.scalar()

    async def _get_caracteristicas_proyecto(self, proyecto_id: int) -> Dict[str, Any]:
        """Obtiene características del proyecto como dict."""
        result = await self.db.execute(
            select(ProyectoCaracteristica)
            .where(ProyectoCaracteristica.proyecto_id == proyecto_id)
        )
        caracteristicas_db = result.scalars().all()

        caracteristicas = {}
        for car in caracteristicas_db:
            if car.valor_numerico is not None:
                caracteristicas[car.clave] = float(car.valor_numerico)
            elif car.valor is not None:
                caracteristicas[car.clave] = car.valor

        return caracteristicas

    async def _convertir_a_response(
        self,
        estructura: EstructuraEIAProyecto
    ) -> EstructuraEIAResponse:
        """Convierte modelo a response."""
        capitulos = [CapituloConEstado(**c) for c in (estructura.capitulos or [])]
        pas = [PASConEstado(**p) for p in (estructura.pas_requeridos or [])]
        anexos = [AnexoRequerido(**a) for a in (estructura.anexos_requeridos or [])]
        plan_lb = [ComponenteLineaBaseEnPlan(**c) for c in (estructura.plan_linea_base or [])]

        estimacion = None
        if estructura.estimacion_complejidad:
            estimacion = EstimacionComplejidad(**estructura.estimacion_complejidad)

        return EstructuraEIAResponse(
            id=estructura.id,
            proyecto_id=estructura.proyecto_id,
            version=estructura.version,
            instrumento=estructura.instrumento or "EIA",
            capitulos=capitulos,
            pas_requeridos=pas,
            anexos_requeridos=anexos,
            plan_linea_base=plan_lb,
            estimacion_complejidad=estimacion,
            progreso_general=estructura.progreso_general,
            capitulos_completados=estructura.capitulos_completados,
            total_capitulos=len(capitulos),
            pas_aprobados=estructura.pas_aprobados,
            total_pas=len(pas),
            notas=estructura.notas,
            created_at=estructura.created_at,
            updated_at=estructura.updated_at,
        )


# =============================================================================
# Factory Function
# =============================================================================

def get_estructura_eia_service(db: AsyncSession) -> EstructuraEIAService:
    """Factory function para obtener el servicio."""
    return EstructuraEIAService(db)
