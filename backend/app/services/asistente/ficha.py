"""
Servicio de Ficha Acumulativa del Proyecto.

Gestiona las características del proyecto (ficha acumulativa),
ubicaciones, PAS, análisis Art. 11 y diagnósticos.

Este servicio es usado por el AsistenteService para persistir
las respuestas del usuario durante la conversación.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.proyecto import Proyecto
from app.db.models.proyecto_extendido import (
    ProyectoCaracteristica,
    ProyectoUbicacion,
    ProyectoPAS,
    ProyectoAnalisisArt11,
    ProyectoDiagnostico,
    ProyectoConversacion,
)
from app.db.models.config_industria import TipoProyecto, SubtipoProyecto
from app.schemas.ficha import (
    CaracteristicaCreate,
    CaracteristicaUpdate,
    CaracteristicaResponse,
    CaracteristicasByCategoriaResponse,
    PASProyectoCreate,
    PASProyectoUpdate,
    PASProyectoResponse,
    AnalisisArt11Create,
    AnalisisArt11Update,
    AnalisisArt11Response,
    FichaProyectoResponse,
    FichaResumenResponse,
    ProgresoFichaResponse,
    GuardarRespuestaAsistente,
    GuardarRespuestasAsistenteResponse,
    UbicacionResponse,
    DiagnosticoResponse,
    CategoriaCaracteristica,
    FuenteDatoEnum,
)

logger = logging.getLogger(__name__)


class FichaService:
    """
    Servicio para gestionar la ficha acumulativa del proyecto.

    Proporciona operaciones CRUD para características, PAS, análisis Art. 11,
    y métodos para calcular progreso y obtener la ficha consolidada.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            db: Sesión de base de datos async
        """
        self.db = db

    # =========================================================================
    # Características (Ficha Acumulativa)
    # =========================================================================

    async def get_caracteristica(
        self,
        proyecto_id: int,
        categoria: str,
        clave: str
    ) -> Optional[ProyectoCaracteristica]:
        """
        Obtiene una característica específica.

        Args:
            proyecto_id: ID del proyecto
            categoria: Categoría de la característica
            clave: Clave de la característica

        Returns:
            ProyectoCaracteristica o None
        """
        result = await self.db.execute(
            select(ProyectoCaracteristica).where(
                and_(
                    ProyectoCaracteristica.proyecto_id == proyecto_id,
                    ProyectoCaracteristica.categoria == categoria,
                    ProyectoCaracteristica.clave == clave
                )
            )
        )
        return result.scalar()

    async def get_caracteristicas(
        self,
        proyecto_id: int,
        categoria: Optional[str] = None
    ) -> List[ProyectoCaracteristica]:
        """
        Obtiene las características de un proyecto.

        Args:
            proyecto_id: ID del proyecto
            categoria: Filtrar por categoría (opcional)

        Returns:
            Lista de características
        """
        query = select(ProyectoCaracteristica).where(
            ProyectoCaracteristica.proyecto_id == proyecto_id
        )

        if categoria:
            query = query.where(ProyectoCaracteristica.categoria == categoria)

        query = query.order_by(
            ProyectoCaracteristica.categoria,
            ProyectoCaracteristica.clave
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_caracteristicas_by_categoria(
        self,
        proyecto_id: int
    ) -> CaracteristicasByCategoriaResponse:
        """
        Obtiene las características agrupadas por categoría.

        Args:
            proyecto_id: ID del proyecto

        Returns:
            Características organizadas por categoría
        """
        caracteristicas = await self.get_caracteristicas(proyecto_id)

        resultado = CaracteristicasByCategoriaResponse()

        for c in caracteristicas:
            # Obtener el diccionario de la categoría
            categoria_dict = getattr(resultado, c.categoria, {})
            if categoria_dict is None:
                categoria_dict = {}

            # Usar valor numérico si existe, sino texto
            valor = c.valor_numerico if c.valor_numerico is not None else c.valor
            if c.valor_numerico is not None:
                valor = float(c.valor_numerico)

            categoria_dict[c.clave] = valor
            setattr(resultado, c.categoria, categoria_dict)

        return resultado

    async def guardar_caracteristica(
        self,
        proyecto_id: int,
        data: CaracteristicaCreate
    ) -> ProyectoCaracteristica:
        """
        Guarda o actualiza una característica (upsert).

        Args:
            proyecto_id: ID del proyecto
            data: Datos de la característica

        Returns:
            Característica guardada
        """
        # Buscar existente
        existente = await self.get_caracteristica(
            proyecto_id,
            data.categoria.value,
            data.clave
        )

        if existente:
            # Actualizar
            existente.valor = data.valor
            existente.valor_numerico = data.valor_numerico
            existente.unidad = data.unidad
            existente.fuente = data.fuente.value
            existente.pregunta_codigo = data.pregunta_codigo
            existente.notas = data.notas
            existente.updated_at = datetime.utcnow()
            await self.db.flush()
            return existente
        else:
            # Crear nueva
            caracteristica = ProyectoCaracteristica(
                proyecto_id=proyecto_id,
                categoria=data.categoria.value,
                clave=data.clave,
                valor=data.valor,
                valor_numerico=data.valor_numerico,
                unidad=data.unidad,
                fuente=data.fuente.value,
                pregunta_codigo=data.pregunta_codigo,
                notas=data.notas,
            )
            self.db.add(caracteristica)
            await self.db.flush()
            return caracteristica

    async def guardar_caracteristicas_bulk(
        self,
        proyecto_id: int,
        caracteristicas: List[CaracteristicaCreate]
    ) -> List[ProyectoCaracteristica]:
        """
        Guarda múltiples características.

        Args:
            proyecto_id: ID del proyecto
            caracteristicas: Lista de características a guardar

        Returns:
            Lista de características guardadas
        """
        resultado = []
        for data in caracteristicas:
            caracteristica = await self.guardar_caracteristica(proyecto_id, data)
            resultado.append(caracteristica)
        return resultado

    async def guardar_respuestas_asistente(
        self,
        proyecto_id: int,
        respuestas: List[GuardarRespuestaAsistente]
    ) -> GuardarRespuestasAsistenteResponse:
        """
        Guarda respuestas del asistente en la ficha.

        Este método es llamado por el AsistenteService cuando el usuario
        responde preguntas durante la conversación.

        Args:
            proyecto_id: ID del proyecto
            respuestas: Lista de respuestas a guardar

        Returns:
            Resultado con estadísticas y características guardadas
        """
        guardadas = 0
        actualizadas = 0
        errores = []
        caracteristicas_guardadas = []

        for resp in respuestas:
            try:
                # Verificar que hay al menos un valor
                if resp.valor is None and resp.valor_numerico is None:
                    errores.append({
                        "clave": resp.clave,
                        "error": "Debe proporcionar valor o valor_numerico"
                    })
                    continue

                # Buscar existente
                existente = await self.get_caracteristica(
                    proyecto_id,
                    resp.categoria.value,
                    resp.clave
                )

                if existente:
                    existente.valor = resp.valor
                    existente.valor_numerico = resp.valor_numerico
                    existente.unidad = resp.unidad
                    existente.fuente = FuenteDatoEnum.ASISTENTE.value
                    existente.pregunta_codigo = resp.pregunta_codigo
                    existente.updated_at = datetime.utcnow()
                    await self.db.flush()
                    caracteristicas_guardadas.append(existente)
                    actualizadas += 1
                else:
                    caracteristica = ProyectoCaracteristica(
                        proyecto_id=proyecto_id,
                        categoria=resp.categoria.value,
                        clave=resp.clave,
                        valor=resp.valor,
                        valor_numerico=resp.valor_numerico,
                        unidad=resp.unidad,
                        fuente=FuenteDatoEnum.ASISTENTE.value,
                        pregunta_codigo=resp.pregunta_codigo,
                    )
                    self.db.add(caracteristica)
                    await self.db.flush()
                    caracteristicas_guardadas.append(caracteristica)
                    guardadas += 1

            except Exception as e:
                logger.error(f"Error guardando respuesta {resp.clave}: {e}")
                errores.append({
                    "clave": resp.clave,
                    "error": str(e)
                })

        return GuardarRespuestasAsistenteResponse(
            guardadas=guardadas,
            actualizadas=actualizadas,
            errores=errores,
            caracteristicas=[
                CaracteristicaResponse.model_validate(c)
                for c in caracteristicas_guardadas
            ]
        )

    async def validar_caracteristica(
        self,
        proyecto_id: int,
        categoria: str,
        clave: str,
        validado_por: str
    ) -> Optional[ProyectoCaracteristica]:
        """
        Marca una característica como validada.

        Args:
            proyecto_id: ID del proyecto
            categoria: Categoría de la característica
            clave: Clave de la característica
            validado_por: Usuario que valida

        Returns:
            Característica actualizada o None
        """
        caracteristica = await self.get_caracteristica(proyecto_id, categoria, clave)
        if caracteristica:
            caracteristica.validado = True
            caracteristica.validado_por = validado_por
            caracteristica.validado_fecha = datetime.utcnow()
            await self.db.flush()
        return caracteristica

    async def eliminar_caracteristica(
        self,
        proyecto_id: int,
        categoria: str,
        clave: str
    ) -> bool:
        """
        Elimina una característica.

        Args:
            proyecto_id: ID del proyecto
            categoria: Categoría
            clave: Clave

        Returns:
            True si se eliminó
        """
        result = await self.db.execute(
            delete(ProyectoCaracteristica).where(
                and_(
                    ProyectoCaracteristica.proyecto_id == proyecto_id,
                    ProyectoCaracteristica.categoria == categoria,
                    ProyectoCaracteristica.clave == clave
                )
            )
        )
        return result.rowcount > 0

    # =========================================================================
    # PAS del Proyecto
    # =========================================================================

    async def get_pas(self, proyecto_id: int) -> List[ProyectoPAS]:
        """
        Obtiene los PAS de un proyecto.

        Args:
            proyecto_id: ID del proyecto

        Returns:
            Lista de PAS
        """
        result = await self.db.execute(
            select(ProyectoPAS)
            .where(ProyectoPAS.proyecto_id == proyecto_id)
            .order_by(ProyectoPAS.articulo)
        )
        return result.scalars().all()

    async def get_pas_by_articulo(
        self,
        proyecto_id: int,
        articulo: int
    ) -> Optional[ProyectoPAS]:
        """
        Obtiene un PAS específico por artículo.

        Args:
            proyecto_id: ID del proyecto
            articulo: Número de artículo

        Returns:
            ProyectoPAS o None
        """
        result = await self.db.execute(
            select(ProyectoPAS).where(
                and_(
                    ProyectoPAS.proyecto_id == proyecto_id,
                    ProyectoPAS.articulo == articulo
                )
            )
        )
        return result.scalar()

    async def guardar_pas(
        self,
        proyecto_id: int,
        data: PASProyectoCreate
    ) -> ProyectoPAS:
        """
        Guarda o actualiza un PAS (upsert).

        Args:
            proyecto_id: ID del proyecto
            data: Datos del PAS

        Returns:
            PAS guardado
        """
        existente = await self.get_pas_by_articulo(proyecto_id, data.articulo)

        if existente:
            existente.nombre = data.nombre
            existente.organismo = data.organismo
            existente.estado = data.estado.value
            existente.obligatorio = data.obligatorio
            existente.justificacion = data.justificacion
            existente.condicion_activada = data.condicion_activada
            existente.updated_at = datetime.utcnow()
            await self.db.flush()
            return existente
        else:
            pas = ProyectoPAS(
                proyecto_id=proyecto_id,
                articulo=data.articulo,
                nombre=data.nombre,
                organismo=data.organismo,
                estado=data.estado.value,
                obligatorio=data.obligatorio,
                justificacion=data.justificacion,
                condicion_activada=data.condicion_activada,
            )
            self.db.add(pas)
            await self.db.flush()
            return pas

    async def actualizar_estado_pas(
        self,
        proyecto_id: int,
        articulo: int,
        estado: str,
        justificacion: Optional[str] = None
    ) -> Optional[ProyectoPAS]:
        """
        Actualiza el estado de un PAS.

        Args:
            proyecto_id: ID del proyecto
            articulo: Número de artículo
            estado: Nuevo estado
            justificacion: Justificación opcional

        Returns:
            PAS actualizado o None
        """
        pas = await self.get_pas_by_articulo(proyecto_id, articulo)
        if pas:
            pas.estado = estado
            if justificacion:
                pas.justificacion = justificacion
            pas.updated_at = datetime.utcnow()
            await self.db.flush()
        return pas

    # =========================================================================
    # Análisis Art. 11
    # =========================================================================

    async def get_analisis_art11(
        self,
        proyecto_id: int
    ) -> List[ProyectoAnalisisArt11]:
        """
        Obtiene el análisis Art. 11 de un proyecto.

        Args:
            proyecto_id: ID del proyecto

        Returns:
            Lista de análisis por literal
        """
        result = await self.db.execute(
            select(ProyectoAnalisisArt11)
            .where(ProyectoAnalisisArt11.proyecto_id == proyecto_id)
            .order_by(ProyectoAnalisisArt11.literal)
        )
        return result.scalars().all()

    async def get_analisis_literal(
        self,
        proyecto_id: int,
        literal: str
    ) -> Optional[ProyectoAnalisisArt11]:
        """
        Obtiene el análisis de un literal específico.

        Args:
            proyecto_id: ID del proyecto
            literal: Literal (a-f)

        Returns:
            ProyectoAnalisisArt11 o None
        """
        result = await self.db.execute(
            select(ProyectoAnalisisArt11).where(
                and_(
                    ProyectoAnalisisArt11.proyecto_id == proyecto_id,
                    ProyectoAnalisisArt11.literal == literal
                )
            )
        )
        return result.scalar()

    async def guardar_analisis_art11(
        self,
        proyecto_id: int,
        data: AnalisisArt11Create
    ) -> ProyectoAnalisisArt11:
        """
        Guarda o actualiza análisis de literal Art. 11.

        Args:
            proyecto_id: ID del proyecto
            data: Datos del análisis

        Returns:
            Análisis guardado
        """
        existente = await self.get_analisis_literal(proyecto_id, data.literal)

        if existente:
            existente.estado = data.estado.value
            existente.justificacion = data.justificacion
            existente.confianza = data.confianza
            existente.evidencias = data.evidencias or []
            existente.fuente_gis = data.fuente_gis
            existente.fuente_usuario = data.fuente_usuario
            existente.fuente_asistente = data.fuente_asistente
            existente.updated_at = datetime.utcnow()
            await self.db.flush()
            return existente
        else:
            analisis = ProyectoAnalisisArt11(
                proyecto_id=proyecto_id,
                literal=data.literal,
                estado=data.estado.value,
                justificacion=data.justificacion,
                confianza=data.confianza,
                evidencias=data.evidencias or [],
                fuente_gis=data.fuente_gis,
                fuente_usuario=data.fuente_usuario,
                fuente_asistente=data.fuente_asistente,
            )
            self.db.add(analisis)
            await self.db.flush()
            return analisis

    # =========================================================================
    # Diagnóstico
    # =========================================================================

    async def get_diagnostico_actual(
        self,
        proyecto_id: int
    ) -> Optional[ProyectoDiagnostico]:
        """
        Obtiene el diagnóstico más reciente del proyecto.

        Args:
            proyecto_id: ID del proyecto

        Returns:
            ProyectoDiagnostico o None
        """
        result = await self.db.execute(
            select(ProyectoDiagnostico)
            .where(ProyectoDiagnostico.proyecto_id == proyecto_id)
            .order_by(ProyectoDiagnostico.version.desc())
            .limit(1)
        )
        return result.scalar()

    async def crear_diagnostico(
        self,
        proyecto_id: int,
        via_sugerida: str,
        confianza: int,
        literales_gatillados: List[str],
        cumple_umbral_seia: Optional[bool] = None,
        umbral_evaluado: Optional[Dict[str, Any]] = None,
        alertas: Optional[List[Dict[str, Any]]] = None,
        recomendaciones: Optional[List[Dict[str, Any]]] = None,
        resumen: Optional[str] = None,
        generado_por: str = "sistema"
    ) -> ProyectoDiagnostico:
        """
        Crea un nuevo diagnóstico (nueva versión).

        Args:
            proyecto_id: ID del proyecto
            via_sugerida: Vía sugerida (DIA/EIA/NO_SEIA)
            confianza: Nivel de confianza (0-100)
            literales_gatillados: Literales del Art. 11 gatillados
            cumple_umbral_seia: Si cumple umbral de ingreso SEIA
            umbral_evaluado: Detalle del umbral evaluado
            alertas: Lista de alertas
            recomendaciones: Lista de recomendaciones
            resumen: Resumen del diagnóstico
            generado_por: Origen del diagnóstico

        Returns:
            Nuevo diagnóstico creado
        """
        # Obtener versión actual
        actual = await self.get_diagnostico_actual(proyecto_id)
        nueva_version = (actual.version + 1) if actual else 1

        # Obtener PAS identificados
        pas_list = await self.get_pas(proyecto_id)
        permisos = [
            {
                "articulo": p.articulo,
                "nombre": p.nombre,
                "organismo": p.organismo,
                "obligatorio": p.obligatorio,
                "estado": p.estado
            }
            for p in pas_list
        ]

        diagnostico = ProyectoDiagnostico(
            proyecto_id=proyecto_id,
            version=nueva_version,
            via_sugerida=via_sugerida,
            confianza=confianza,
            literales_gatillados=literales_gatillados,
            cumple_umbral_seia=cumple_umbral_seia,
            umbral_evaluado=umbral_evaluado,
            permisos_identificados=permisos,
            alertas=alertas or [],
            recomendaciones=recomendaciones or [],
            resumen=resumen,
            generado_por=generado_por,
        )
        self.db.add(diagnostico)
        await self.db.flush()
        return diagnostico

    # =========================================================================
    # Ubicación
    # =========================================================================

    async def get_ubicacion_vigente(
        self,
        proyecto_id: int
    ) -> Optional[ProyectoUbicacion]:
        """
        Obtiene la ubicación vigente del proyecto.

        Args:
            proyecto_id: ID del proyecto

        Returns:
            ProyectoUbicacion o None
        """
        result = await self.db.execute(
            select(ProyectoUbicacion)
            .where(
                and_(
                    ProyectoUbicacion.proyecto_id == proyecto_id,
                    ProyectoUbicacion.es_vigente == True
                )
            )
            .order_by(ProyectoUbicacion.version.desc())
            .limit(1)
        )
        return result.scalar()

    # =========================================================================
    # Ficha Consolidada
    # =========================================================================

    async def get_ficha_completa(
        self,
        proyecto_id: int
    ) -> Optional[FichaProyectoResponse]:
        """
        Obtiene la ficha completa consolidada del proyecto.

        Incluye todas las características, análisis Art. 11, PAS,
        diagnóstico actual y estadísticas.

        Args:
            proyecto_id: ID del proyecto

        Returns:
            FichaProyectoResponse o None si no existe el proyecto
        """
        # Obtener proyecto con tipo
        result = await self.db.execute(
            select(Proyecto)
            .where(Proyecto.id == proyecto_id)
        )
        proyecto = result.scalar()

        if not proyecto:
            return None

        # Obtener tipo y subtipo
        tipo_codigo = None
        tipo_nombre = None
        subtipo_codigo = None
        subtipo_nombre = None

        if hasattr(proyecto, 'tipo_proyecto_id') and proyecto.tipo_proyecto_id:
            result = await self.db.execute(
                select(TipoProyecto).where(TipoProyecto.id == proyecto.tipo_proyecto_id)
            )
            tipo = result.scalar()
            if tipo:
                tipo_codigo = tipo.codigo
                tipo_nombre = tipo.nombre

        if hasattr(proyecto, 'subtipo_proyecto_id') and proyecto.subtipo_proyecto_id:
            result = await self.db.execute(
                select(SubtipoProyecto).where(SubtipoProyecto.id == proyecto.subtipo_proyecto_id)
            )
            subtipo = result.scalar()
            if subtipo:
                subtipo_codigo = subtipo.codigo
                subtipo_nombre = subtipo.nombre

        # Obtener ubicación vigente
        ubicacion = await self.get_ubicacion_vigente(proyecto_id)
        ubicacion_response = None
        if ubicacion:
            ubicacion_response = UbicacionResponse.model_validate(ubicacion)

        # Obtener características por categoría
        caracteristicas = await self.get_caracteristicas_by_categoria(proyecto_id)

        # Obtener análisis Art. 11
        analisis_list = await self.get_analisis_art11(proyecto_id)
        analisis_dict = {
            a.literal: AnalisisArt11Response.model_validate(a)
            for a in analisis_list
        }

        # Obtener diagnóstico actual
        diagnostico = await self.get_diagnostico_actual(proyecto_id)
        diagnostico_response = None
        if diagnostico:
            diagnostico_response = DiagnosticoResponse.model_validate(diagnostico)

        # Obtener PAS
        pas_list = await self.get_pas(proyecto_id)
        pas_responses = [PASProyectoResponse.model_validate(p) for p in pas_list]

        # Calcular estadísticas
        todas_caracteristicas = await self.get_caracteristicas(proyecto_id)
        total = len(todas_caracteristicas)
        validadas = sum(1 for c in todas_caracteristicas if c.validado)

        # Calcular progreso (basado en categorías completadas)
        progreso = await self.calcular_progreso(proyecto_id)

        return FichaProyectoResponse(
            proyecto_id=proyecto_id,
            nombre=proyecto.nombre,
            estado=proyecto.estado,
            tipo_codigo=tipo_codigo,
            tipo_nombre=tipo_nombre,
            subtipo_codigo=subtipo_codigo,
            subtipo_nombre=subtipo_nombre,
            ubicacion=ubicacion_response,
            caracteristicas=caracteristicas,
            analisis_art11=analisis_dict,
            diagnostico_actual=diagnostico_response,
            pas=pas_responses,
            total_caracteristicas=total,
            caracteristicas_validadas=validadas,
            progreso_porcentaje=int(progreso.porcentaje_completitud) if progreso else 0,
            created_at=proyecto.created_at,
            updated_at=proyecto.updated_at,
        )

    async def get_ficha_resumen(
        self,
        proyecto_id: int
    ) -> Optional[FichaResumenResponse]:
        """
        Obtiene un resumen de la ficha para listados.

        Args:
            proyecto_id: ID del proyecto

        Returns:
            FichaResumenResponse o None
        """
        result = await self.db.execute(
            select(Proyecto).where(Proyecto.id == proyecto_id)
        )
        proyecto = result.scalar()

        if not proyecto:
            return None

        # Tipo
        tipo_nombre = None
        if hasattr(proyecto, 'tipo_proyecto_id') and proyecto.tipo_proyecto_id:
            result = await self.db.execute(
                select(TipoProyecto.nombre).where(TipoProyecto.id == proyecto.tipo_proyecto_id)
            )
            tipo_nombre = result.scalar()

        # Diagnóstico
        diagnostico = await self.get_diagnostico_actual(proyecto_id)
        via_sugerida = diagnostico.via_sugerida if diagnostico else None

        # PAS
        pas_count = await self.db.execute(
            select(func.count(ProyectoPAS.id)).where(ProyectoPAS.proyecto_id == proyecto_id)
        )
        total_pas = pas_count.scalar() or 0

        # Ubicación
        ubicacion = await self.get_ubicacion_vigente(proyecto_id)

        # Progreso
        progreso = await self.calcular_progreso(proyecto_id)

        return FichaResumenResponse(
            proyecto_id=proyecto_id,
            nombre=proyecto.nombre,
            estado=proyecto.estado,
            tipo_nombre=tipo_nombre,
            via_sugerida=via_sugerida,
            progreso_porcentaje=int(progreso.porcentaje_completitud) if progreso else 0,
            total_pas=total_pas,
            has_ubicacion=ubicacion is not None,
        )

    # =========================================================================
    # Progreso
    # =========================================================================

    async def calcular_progreso(
        self,
        proyecto_id: int,
        campos_obligatorios: Optional[Dict[str, List[str]]] = None
    ) -> ProgresoFichaResponse:
        """
        Calcula el progreso de completitud de la ficha.

        Args:
            proyecto_id: ID del proyecto
            campos_obligatorios: Dict de categoría -> lista de claves obligatorias

        Returns:
            ProgresoFichaResponse con estadísticas
        """
        # Campos obligatorios por defecto
        if campos_obligatorios is None:
            campos_obligatorios = {
                "identificacion": ["nombre", "titular"],
                "tecnico": ["tipo_extraccion", "tonelaje_mensual", "mineral_principal"],
                "obras": [],
                "insumos": ["uso_agua_lps", "fuente_agua"],
            }

        # Obtener características
        caracteristicas = await self.get_caracteristicas(proyecto_id)

        # Contar por categoría
        por_categoria = {}
        for cat in CategoriaCaracteristica:
            cat_value = cat.value
            cat_caracteristicas = [c for c in caracteristicas if c.categoria == cat_value]
            por_categoria[cat_value] = {
                "total": len(cat_caracteristicas),
                "validadas": sum(1 for c in cat_caracteristicas if c.validado),
            }

        # Calcular campos faltantes obligatorios
        campos_faltantes = []
        for categoria, claves in campos_obligatorios.items():
            for clave in claves:
                existe = any(
                    c.categoria == categoria and c.clave == clave
                    for c in caracteristicas
                )
                if not existe:
                    campos_faltantes.append(f"{categoria}.{clave}")

        # Calcular totales
        total_campos = sum(len(claves) for claves in campos_obligatorios.values())
        campos_completados = total_campos - len(campos_faltantes)
        campos_validados = sum(1 for c in caracteristicas if c.validado)

        porcentaje_completitud = (
            (campos_completados / total_campos * 100) if total_campos > 0 else 0
        )
        porcentaje_validacion = (
            (campos_validados / len(caracteristicas) * 100) if caracteristicas else 0
        )

        return ProgresoFichaResponse(
            proyecto_id=proyecto_id,
            total_campos=total_campos,
            campos_completados=campos_completados,
            campos_validados=campos_validados,
            porcentaje_completitud=round(porcentaje_completitud, 1),
            porcentaje_validacion=round(porcentaje_validacion, 1),
            por_categoria=por_categoria,
            campos_faltantes_obligatorios=campos_faltantes,
        )


# =============================================================================
# Factory Function
# =============================================================================

def get_ficha_service(db: AsyncSession) -> FichaService:
    """
    Factory function para obtener el servicio.

    Args:
        db: Sesión de base de datos async

    Returns:
        FichaService configurado
    """
    return FichaService(db)
