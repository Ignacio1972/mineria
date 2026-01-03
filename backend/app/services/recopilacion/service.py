"""
Servicio de Recopilacion Guiada - Orquestador principal.
Gestiona la recopilacion de contenido del EIA capitulo por capitulo.
"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.recopilacion import (
    PreguntaRecopilacion, ReglaConsistencia, ContenidoEIA, EstadoSeccion
)
from app.db.models.estructura_eia import CapituloEIA, EstructuraEIAProyecto
from app.db.models.proyecto import Proyecto
from app.schemas.recopilacion import (
    PreguntaConRespuesta, SeccionConPreguntas, SeccionResumen,
    CapituloProgreso, ProgresoGeneralEIA, InconsistenciaDetectada,
    ValidacionConsistenciaResponse, ContenidoEIAResponse,
    IniciarCapituloResponse, SeveridadInconsistencia
)

logger = logging.getLogger(__name__)


class RecopilacionService:
    """
    Servicio para gestionar la recopilacion guiada del EIA.

    Responsabilidades:
    - Obtener preguntas por capitulo/seccion
    - Guardar respuestas del usuario
    - Validar completitud de secciones
    - Detectar inconsistencias entre capitulos
    - Calcular progreso general
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # INICIALIZACION Y NAVEGACION
    # =========================================================================

    async def iniciar_capitulo(
        self,
        proyecto_id: int,
        capitulo_numero: int
    ) -> IniciarCapituloResponse:
        """
        Inicia o retoma la recopilacion de un capitulo.

        Returns:
            IniciarCapituloResponse con secciones y preguntas
        """
        # Obtener proyecto y su tipo
        proyecto = await self._get_proyecto(proyecto_id)
        if not proyecto:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")

        # Obtener info del capitulo
        capitulo = await self._get_capitulo(proyecto.tipo_proyecto_id, capitulo_numero)
        if not capitulo:
            raise ValueError(f"Capitulo {capitulo_numero} no configurado para este tipo de proyecto")

        # Obtener preguntas del capitulo
        preguntas = await self._get_preguntas_capitulo(
            proyecto.tipo_proyecto_id,
            capitulo_numero
        )

        # Obtener contenido existente
        contenidos_existentes = await self._get_contenidos_capitulo(
            proyecto_id,
            capitulo_numero
        )
        contenido_por_seccion = {c.seccion_codigo: c for c in contenidos_existentes}

        # Agrupar preguntas por seccion
        secciones_dict: Dict[str, SeccionConPreguntas] = {}

        for pregunta in preguntas:
            seccion_codigo = pregunta.seccion_codigo

            if seccion_codigo not in secciones_dict:
                contenido = contenido_por_seccion.get(seccion_codigo)
                secciones_dict[seccion_codigo] = SeccionConPreguntas(
                    capitulo_numero=capitulo_numero,
                    seccion_codigo=seccion_codigo,
                    seccion_nombre=pregunta.seccion_nombre,
                    preguntas=[],
                    estado=EstadoSeccion(contenido.estado) if contenido else EstadoSeccion.PENDIENTE,
                    progreso=contenido.progreso if contenido else 0
                )

            # Obtener respuesta existente
            contenido = contenido_por_seccion.get(seccion_codigo)
            respuesta_actual = None
            if contenido and contenido.contenido:
                respuesta_actual = contenido.contenido.get(pregunta.codigo_pregunta)

            # Validar respuesta
            es_valida, mensaje = pregunta.validar_respuesta(respuesta_actual)

            # Crear pregunta con respuesta
            pregunta_response = PreguntaConRespuesta(
                id=pregunta.id,
                capitulo_numero=pregunta.capitulo_numero,
                seccion_codigo=pregunta.seccion_codigo,
                seccion_nombre=pregunta.seccion_nombre,
                codigo_pregunta=pregunta.codigo_pregunta,
                pregunta=pregunta.pregunta,
                descripcion=pregunta.descripcion,
                tipo_respuesta=pregunta.tipo_respuesta,
                opciones=pregunta.opciones,
                valor_por_defecto=pregunta.valor_por_defecto,
                validaciones=pregunta.validaciones,
                es_obligatoria=pregunta.es_obligatoria,
                condicion_activacion=pregunta.condicion_activacion,
                orden=pregunta.orden,
                respuesta_actual=respuesta_actual,
                es_valida=es_valida,
                mensaje_validacion=mensaje
            )
            secciones_dict[seccion_codigo].preguntas.append(pregunta_response)

        # Calcular estadisticas por seccion
        secciones = list(secciones_dict.values())
        for seccion in secciones:
            seccion.total_preguntas = len(seccion.preguntas)
            seccion.preguntas_obligatorias = sum(1 for p in seccion.preguntas if p.es_obligatoria)
            seccion.preguntas_respondidas = sum(
                1 for p in seccion.preguntas
                if p.respuesta_actual is not None and p.respuesta_actual != ""
            )
            if seccion.preguntas_obligatorias > 0:
                seccion.progreso = round(
                    (seccion.preguntas_respondidas / seccion.preguntas_obligatorias) * 100
                )

        # Ordenar secciones
        secciones.sort(key=lambda s: s.preguntas[0].orden if s.preguntas else 0)

        total_preguntas = sum(s.total_preguntas for s in secciones)
        preguntas_obligatorias = sum(s.preguntas_obligatorias for s in secciones)

        return IniciarCapituloResponse(
            capitulo_numero=capitulo_numero,
            titulo=capitulo.titulo,
            secciones=secciones,
            total_preguntas=total_preguntas,
            preguntas_obligatorias=preguntas_obligatorias,
            mensaje_bienvenida=self._generar_mensaje_bienvenida(capitulo, secciones)
        )

    async def get_preguntas_seccion(
        self,
        proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str
    ) -> SeccionConPreguntas:
        """Obtiene las preguntas de una seccion especifica."""
        proyecto = await self._get_proyecto(proyecto_id)
        if not proyecto:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")

        preguntas = await self._get_preguntas_seccion(
            proyecto.tipo_proyecto_id,
            capitulo_numero,
            seccion_codigo
        )

        contenido = await self._get_contenido_seccion(
            proyecto_id, capitulo_numero, seccion_codigo
        )

        preguntas_response = []
        for pregunta in preguntas:
            respuesta_actual = None
            if contenido and contenido.contenido:
                respuesta_actual = contenido.contenido.get(pregunta.codigo_pregunta)

            es_valida, mensaje = pregunta.validar_respuesta(respuesta_actual)

            preguntas_response.append(PreguntaConRespuesta(
                **pregunta.to_dict(),
                respuesta_actual=respuesta_actual,
                es_valida=es_valida,
                mensaje_validacion=mensaje
            ))

        seccion_nombre = preguntas[0].seccion_nombre if preguntas else None
        preguntas_obligatorias = sum(1 for p in preguntas_response if p.es_obligatoria)
        preguntas_respondidas = sum(
            1 for p in preguntas_response
            if p.respuesta_actual is not None and p.respuesta_actual != ""
        )

        return SeccionConPreguntas(
            capitulo_numero=capitulo_numero,
            seccion_codigo=seccion_codigo,
            seccion_nombre=seccion_nombre,
            preguntas=preguntas_response,
            total_preguntas=len(preguntas_response),
            preguntas_obligatorias=preguntas_obligatorias,
            preguntas_respondidas=preguntas_respondidas,
            progreso=contenido.progreso if contenido else 0,
            estado=EstadoSeccion(contenido.estado) if contenido else EstadoSeccion.PENDIENTE
        )

    # =========================================================================
    # GUARDAR RESPUESTAS
    # =========================================================================

    async def guardar_respuesta(
        self,
        proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str,
        codigo_pregunta: str,
        valor: Any
    ) -> ContenidoEIAResponse:
        """Guarda una respuesta individual."""
        return await self.guardar_respuestas(
            proyecto_id,
            capitulo_numero,
            seccion_codigo,
            {codigo_pregunta: valor}
        )

    async def guardar_respuestas(
        self,
        proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str,
        respuestas: Dict[str, Any]
    ) -> ContenidoEIAResponse:
        """
        Guarda multiples respuestas en una seccion.

        Args:
            proyecto_id: ID del proyecto
            capitulo_numero: Numero del capitulo
            seccion_codigo: Codigo de la seccion
            respuestas: Dict {codigo_pregunta: valor}

        Returns:
            ContenidoEIAResponse actualizado
        """
        # Obtener o crear contenido
        contenido = await self._get_or_create_contenido(
            proyecto_id, capitulo_numero, seccion_codigo
        )

        # Actualizar respuestas
        if contenido.contenido is None:
            contenido.contenido = {}

        for codigo, valor in respuestas.items():
            contenido.contenido[codigo] = valor

        # Obtener preguntas para calcular progreso
        proyecto = await self._get_proyecto(proyecto_id)
        preguntas = await self._get_preguntas_seccion(
            proyecto.tipo_proyecto_id,
            capitulo_numero,
            seccion_codigo
        )

        # Calcular progreso
        preguntas_obligatorias = [p for p in preguntas if p.es_obligatoria]
        respondidas = sum(
            1 for p in preguntas_obligatorias
            if contenido.contenido.get(p.codigo_pregunta) not in [None, ""]
        )

        if len(preguntas_obligatorias) > 0:
            contenido.progreso = round((respondidas / len(preguntas_obligatorias)) * 100)
        else:
            contenido.progreso = 100

        # Actualizar estado
        if contenido.progreso == 0:
            contenido.estado = "pendiente"
        elif contenido.progreso < 100:
            contenido.estado = "en_progreso"
        else:
            contenido.estado = "completado"

        contenido.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(contenido)

        return ContenidoEIAResponse.model_validate(contenido.to_dict())

    # =========================================================================
    # PROGRESO Y ESTADISTICAS
    # =========================================================================

    async def get_progreso_capitulo(
        self,
        proyecto_id: int,
        capitulo_numero: int
    ) -> CapituloProgreso:
        """Obtiene el progreso de un capitulo."""
        proyecto = await self._get_proyecto(proyecto_id)
        capitulo = await self._get_capitulo(proyecto.tipo_proyecto_id, capitulo_numero)

        if not capitulo:
            raise ValueError(f"Capitulo {capitulo_numero} no encontrado")

        # Obtener todas las secciones del capitulo
        preguntas = await self._get_preguntas_capitulo(
            proyecto.tipo_proyecto_id, capitulo_numero
        )

        # Agrupar por seccion
        secciones_codigos = set(p.seccion_codigo for p in preguntas)

        # Obtener contenidos
        contenidos = await self._get_contenidos_capitulo(proyecto_id, capitulo_numero)
        contenido_por_seccion = {c.seccion_codigo: c for c in contenidos}

        secciones_resumen = []
        secciones_completadas = 0

        for seccion_codigo in secciones_codigos:
            contenido = contenido_por_seccion.get(seccion_codigo)
            seccion_preguntas = [p for p in preguntas if p.seccion_codigo == seccion_codigo]
            seccion_nombre = seccion_preguntas[0].seccion_nombre if seccion_preguntas else None

            estado = EstadoSeccion(contenido.estado) if contenido else EstadoSeccion.PENDIENTE
            progreso = contenido.progreso if contenido else 0
            tiene_inconsistencias = bool(contenido and contenido.inconsistencias)
            docs_vinculados = len(contenido.documentos_vinculados) if contenido else 0

            if estado == EstadoSeccion.COMPLETADO:
                secciones_completadas += 1

            secciones_resumen.append(SeccionResumen(
                capitulo_numero=capitulo_numero,
                seccion_codigo=seccion_codigo,
                seccion_nombre=seccion_nombre,
                estado=estado,
                progreso=progreso,
                tiene_inconsistencias=tiene_inconsistencias,
                documentos_vinculados=docs_vinculados
            ))

        total_secciones = len(secciones_codigos)
        progreso_capitulo = round((secciones_completadas / total_secciones) * 100) if total_secciones > 0 else 0

        estado_capitulo = EstadoSeccion.PENDIENTE
        if secciones_completadas == total_secciones:
            estado_capitulo = EstadoSeccion.COMPLETADO
        elif secciones_completadas > 0:
            estado_capitulo = EstadoSeccion.EN_PROGRESO

        return CapituloProgreso(
            numero=capitulo_numero,
            titulo=capitulo.titulo,
            total_secciones=total_secciones,
            secciones_completadas=secciones_completadas,
            progreso=progreso_capitulo,
            estado=estado_capitulo,
            tiene_inconsistencias=any(s.tiene_inconsistencias for s in secciones_resumen),
            secciones=secciones_resumen
        )

    async def get_progreso_general(self, proyecto_id: int) -> ProgresoGeneralEIA:
        """Obtiene el progreso general del EIA."""
        proyecto = await self._get_proyecto(proyecto_id)

        # Obtener capitulos configurados
        result = await self.db.execute(
            select(CapituloEIA)
            .where(CapituloEIA.tipo_proyecto_id == proyecto.tipo_proyecto_id)
            .where(CapituloEIA.activo == True)
            .order_by(CapituloEIA.orden)
        )
        capitulos = result.scalars().all()

        capitulos_progreso = []
        capitulos_completados = 0
        total_inconsistencias = 0

        for capitulo in capitulos:
            progreso = await self.get_progreso_capitulo(proyecto_id, capitulo.numero)
            capitulos_progreso.append(progreso)

            if progreso.estado == EstadoSeccion.COMPLETADO:
                capitulos_completados += 1

            if progreso.tiene_inconsistencias:
                total_inconsistencias += sum(
                    1 for s in progreso.secciones if s.tiene_inconsistencias
                )

        total_capitulos = len(capitulos)
        progreso_general = round((capitulos_completados / total_capitulos) * 100) if total_capitulos > 0 else 0

        return ProgresoGeneralEIA(
            proyecto_id=proyecto_id,
            total_capitulos=total_capitulos,
            capitulos_completados=capitulos_completados,
            progreso_general=progreso_general,
            total_inconsistencias=total_inconsistencias,
            capitulos=capitulos_progreso
        )

    # =========================================================================
    # VALIDACION DE CONSISTENCIA
    # =========================================================================

    async def validar_consistencia(
        self,
        proyecto_id: int,
        capitulos: Optional[List[int]] = None
    ) -> ValidacionConsistenciaResponse:
        """
        Valida la consistencia entre capitulos del EIA.

        Args:
            proyecto_id: ID del proyecto
            capitulos: Lista de capitulos a validar (None = todos)

        Returns:
            ValidacionConsistenciaResponse con inconsistencias detectadas
        """
        proyecto = await self._get_proyecto(proyecto_id)

        # Obtener reglas de consistencia
        query = select(ReglaConsistencia).where(
            ReglaConsistencia.activo == True
        )
        if proyecto.tipo_proyecto_id:
            query = query.where(
                (ReglaConsistencia.tipo_proyecto_id == proyecto.tipo_proyecto_id) |
                (ReglaConsistencia.tipo_proyecto_id == None)
            )

        result = await self.db.execute(query)
        reglas = result.scalars().all()

        # Filtrar por capitulos si se especifican
        if capitulos:
            reglas = [
                r for r in reglas
                if r.capitulo_origen in capitulos or r.capitulo_destino in capitulos
            ]

        # Obtener todos los contenidos
        result = await self.db.execute(
            select(ContenidoEIA).where(ContenidoEIA.proyecto_id == proyecto_id)
        )
        contenidos = result.scalars().all()

        # Indexar por capitulo/seccion
        contenido_index: Dict[Tuple[int, str], ContenidoEIA] = {}
        for contenido in contenidos:
            key = (contenido.capitulo_numero, contenido.seccion_codigo)
            contenido_index[key] = contenido

        # Evaluar cada regla
        inconsistencias = []
        errores = 0
        warnings = 0

        for regla in reglas:
            key_origen = (regla.capitulo_origen, regla.seccion_origen)
            key_destino = (regla.capitulo_destino, regla.seccion_destino)

            contenido_origen = contenido_index.get(key_origen)
            contenido_destino = contenido_index.get(key_destino)

            if not contenido_origen or not contenido_destino:
                continue

            valor_origen = contenido_origen.contenido.get(regla.campo_origen) if contenido_origen.contenido else None
            valor_destino = contenido_destino.contenido.get(regla.campo_destino) if contenido_destino.contenido else None

            es_consistente, mensaje = regla.evaluar(valor_origen, valor_destino)

            if not es_consistente:
                severidad = SeveridadInconsistencia(regla.severidad)

                if severidad == SeveridadInconsistencia.ERROR:
                    errores += 1
                elif severidad == SeveridadInconsistencia.WARNING:
                    warnings += 1

                inconsistencias.append(InconsistenciaDetectada(
                    regla_codigo=regla.codigo,
                    regla_nombre=regla.nombre,
                    capitulo_origen=regla.capitulo_origen,
                    seccion_origen=regla.seccion_origen,
                    campo_origen=regla.campo_origen,
                    valor_origen=valor_origen,
                    capitulo_destino=regla.capitulo_destino,
                    seccion_destino=regla.seccion_destino,
                    campo_destino=regla.campo_destino,
                    valor_destino=valor_destino,
                    mensaje=mensaje,
                    severidad=severidad,
                    fecha_deteccion=datetime.utcnow()
                ))

                # Guardar inconsistencia en contenido origen
                contenido_origen.agregar_inconsistencia(
                    regla.codigo, mensaje, regla.severidad
                )

        await self.db.commit()

        return ValidacionConsistenciaResponse(
            proyecto_id=proyecto_id,
            total_reglas_evaluadas=len(reglas),
            inconsistencias=inconsistencias,
            errores=errores,
            warnings=warnings,
            es_consistente=(errores == 0)
        )

    # =========================================================================
    # VINCULACION DE DOCUMENTOS
    # =========================================================================

    async def vincular_documento(
        self,
        proyecto_id: int,
        documento_id: int,
        capitulo_numero: int,
        seccion_codigo: str
    ) -> ContenidoEIAResponse:
        """Vincula un documento a una seccion."""
        contenido = await self._get_or_create_contenido(
            proyecto_id, capitulo_numero, seccion_codigo
        )
        contenido.vincular_documento(documento_id)
        await self.db.commit()
        await self.db.refresh(contenido)
        return ContenidoEIAResponse.model_validate(contenido.to_dict())

    async def desvincular_documento(
        self,
        proyecto_id: int,
        documento_id: int,
        capitulo_numero: int,
        seccion_codigo: str
    ) -> ContenidoEIAResponse:
        """Desvincula un documento de una seccion."""
        contenido = await self._get_contenido_seccion(
            proyecto_id, capitulo_numero, seccion_codigo
        )
        if contenido and contenido.documentos_vinculados:
            contenido.documentos_vinculados = [
                d for d in contenido.documentos_vinculados if d != documento_id
            ]
            await self.db.commit()
            await self.db.refresh(contenido)
        return ContenidoEIAResponse.model_validate(contenido.to_dict()) if contenido else None

    # =========================================================================
    # HELPERS PRIVADOS
    # =========================================================================

    async def _get_proyecto(self, proyecto_id: int) -> Optional[Proyecto]:
        """Obtiene un proyecto por ID."""
        result = await self.db.execute(
            select(Proyecto).where(Proyecto.id == proyecto_id)
        )
        return result.scalar_one_or_none()

    async def _get_capitulo(
        self,
        tipo_proyecto_id: int,
        capitulo_numero: int
    ) -> Optional[CapituloEIA]:
        """Obtiene un capitulo por tipo y numero."""
        result = await self.db.execute(
            select(CapituloEIA).where(
                and_(
                    CapituloEIA.tipo_proyecto_id == tipo_proyecto_id,
                    CapituloEIA.numero == capitulo_numero,
                    CapituloEIA.activo == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_preguntas_capitulo(
        self,
        tipo_proyecto_id: int,
        capitulo_numero: int
    ) -> List[PreguntaRecopilacion]:
        """Obtiene todas las preguntas de un capitulo."""
        result = await self.db.execute(
            select(PreguntaRecopilacion).where(
                and_(
                    PreguntaRecopilacion.tipo_proyecto_id == tipo_proyecto_id,
                    PreguntaRecopilacion.capitulo_numero == capitulo_numero,
                    PreguntaRecopilacion.activo == True
                )
            ).order_by(PreguntaRecopilacion.seccion_codigo, PreguntaRecopilacion.orden)
        )
        return result.scalars().all()

    async def _get_preguntas_seccion(
        self,
        tipo_proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str
    ) -> List[PreguntaRecopilacion]:
        """Obtiene las preguntas de una seccion."""
        result = await self.db.execute(
            select(PreguntaRecopilacion).where(
                and_(
                    PreguntaRecopilacion.tipo_proyecto_id == tipo_proyecto_id,
                    PreguntaRecopilacion.capitulo_numero == capitulo_numero,
                    PreguntaRecopilacion.seccion_codigo == seccion_codigo,
                    PreguntaRecopilacion.activo == True
                )
            ).order_by(PreguntaRecopilacion.orden)
        )
        return result.scalars().all()

    async def _get_contenido_seccion(
        self,
        proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str
    ) -> Optional[ContenidoEIA]:
        """Obtiene el contenido de una seccion."""
        result = await self.db.execute(
            select(ContenidoEIA).where(
                and_(
                    ContenidoEIA.proyecto_id == proyecto_id,
                    ContenidoEIA.capitulo_numero == capitulo_numero,
                    ContenidoEIA.seccion_codigo == seccion_codigo
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_contenidos_capitulo(
        self,
        proyecto_id: int,
        capitulo_numero: int
    ) -> List[ContenidoEIA]:
        """Obtiene todos los contenidos de un capitulo."""
        result = await self.db.execute(
            select(ContenidoEIA).where(
                and_(
                    ContenidoEIA.proyecto_id == proyecto_id,
                    ContenidoEIA.capitulo_numero == capitulo_numero
                )
            )
        )
        return result.scalars().all()

    async def _get_or_create_contenido(
        self,
        proyecto_id: int,
        capitulo_numero: int,
        seccion_codigo: str
    ) -> ContenidoEIA:
        """Obtiene o crea el contenido de una seccion."""
        contenido = await self._get_contenido_seccion(
            proyecto_id, capitulo_numero, seccion_codigo
        )

        if not contenido:
            # Obtener nombre de seccion
            proyecto = await self._get_proyecto(proyecto_id)
            preguntas = await self._get_preguntas_seccion(
                proyecto.tipo_proyecto_id, capitulo_numero, seccion_codigo
            )
            seccion_nombre = preguntas[0].seccion_nombre if preguntas else None

            contenido = ContenidoEIA(
                proyecto_id=proyecto_id,
                capitulo_numero=capitulo_numero,
                seccion_codigo=seccion_codigo,
                seccion_nombre=seccion_nombre,
                contenido={},
                estado="pendiente",
                progreso=0
            )
            self.db.add(contenido)
            await self.db.flush()

        return contenido

    def _generar_mensaje_bienvenida(
        self,
        capitulo: CapituloEIA,
        secciones: List[SeccionConPreguntas]
    ) -> str:
        """Genera mensaje de bienvenida para un capitulo."""
        total_preguntas = sum(s.total_preguntas for s in secciones)
        preguntas_respondidas = sum(s.preguntas_respondidas for s in secciones)

        if preguntas_respondidas == 0:
            return (
                f"Iniciamos el **Capitulo {capitulo.numero}: {capitulo.titulo}**. "
                f"Este capitulo tiene {len(secciones)} secciones con {total_preguntas} preguntas en total. "
                f"Te guiare seccion por seccion para completar la informacion requerida."
            )
        elif preguntas_respondidas < total_preguntas:
            progreso = round((preguntas_respondidas / total_preguntas) * 100)
            return (
                f"Retomamos el **Capitulo {capitulo.numero}: {capitulo.titulo}**. "
                f"Ya has completado {preguntas_respondidas} de {total_preguntas} preguntas ({progreso}%). "
                f"Continuemos desde donde quedaste."
            )
        else:
            return (
                f"El **Capitulo {capitulo.numero}: {capitulo.titulo}** esta completo. "
                f"Puedes revisar o modificar las respuestas si lo necesitas."
            )
