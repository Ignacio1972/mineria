"""
Endpoints del Asistente IA.

Proporciona APIs REST y WebSocket para el chat conversacional
con soporte para tool use y confirmacion de acciones.
"""
import logging
from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.db.session import get_db
from app.db.models.asistente import (
    Conversacion,
    Mensaje,
    AccionPendiente,
    Feedback,
    NotificacionEnviada,
)
from app.db.models.proyecto import Proyecto
from app.schemas.asistente import (
    ChatRequest,
    ChatResponse,
    ConfirmacionAccion,
    ResultadoAccion,
    ConversacionResponse,
    ConversacionConMensajes,
    MensajeResponse,
    AccionPendienteResponse,
    FeedbackCreate,
    FeedbackResponse,
    HerramientasDisponibles,
    HerramientaInfo,
    NotificacionProactiva,
    WebSocketMessage,
    RolMensaje,
    EstadoAccion,
    TipoAccion,
)
from app.services.asistente import (
    get_asistente_service,
    AsistenteService,
    registro_herramientas,
    get_tools_count,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Chat Endpoints
# =============================================================================

@router.post("/chat", response_model=ChatResponse)
async def enviar_mensaje(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Envia un mensaje al asistente y obtiene una respuesta.

    El asistente puede usar herramientas para buscar normativa,
    consultar proyectos y ejecutar acciones. Las acciones que
    modifican datos requieren confirmacion del usuario.

    Args:
        request: Solicitud de chat con mensaje y contexto

    Returns:
        ChatResponse con la respuesta del asistente
    """
    try:
        servicio = get_asistente_service(db)
        respuesta = await servicio.chat(request)
        return respuesta
    except ValueError as e:
        logger.warning(f"Error de validacion en chat: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al procesar el mensaje. Intente nuevamente."
        )


@router.post("/confirm", response_model=ResultadoAccion)
async def confirmar_accion(
    confirmacion: ConfirmacionAccion,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirma o cancela una accion pendiente.

    Las acciones que modifican datos (crear proyecto, ejecutar analisis)
    requieren confirmacion explicita del usuario antes de ejecutarse.

    Args:
        confirmacion: Datos de confirmacion con accion_id y estado

    Returns:
        ResultadoAccion con el resultado de la operacion
    """
    try:
        servicio = get_asistente_service(db)
        resultado = await servicio.confirmar_accion(
            confirmacion.accion_id,
            confirmacion
        )
        return resultado
    except Exception as e:
        logger.error(f"Error confirmando accion: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al procesar la confirmacion"
        )


# =============================================================================
# Conversaciones
# =============================================================================

@router.get("/conversaciones", response_model=List[ConversacionResponse])
async def listar_conversaciones(
    session_id: UUID = Query(..., description="ID de sesion del usuario"),
    limite: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista las conversaciones de una sesion.

    Args:
        session_id: ID de sesion
        limite: Numero maximo de conversaciones

    Returns:
        Lista de conversaciones ordenadas por fecha
    """
    # Query con LEFT JOIN a proyectos para obtener el nombre
    result = await db.execute(
        select(Conversacion, Proyecto.nombre)
        .outerjoin(Proyecto, Conversacion.proyecto_activo_id == Proyecto.id)
        .where(Conversacion.session_id == session_id)
        .order_by(desc(Conversacion.updated_at))
        .limit(limite)
    )
    rows = result.all()

    respuestas = []
    for conv, proyecto_nombre in rows:
        # Contar mensajes
        count_result = await db.execute(
            select(func.count()).where(Mensaje.conversacion_id == conv.id)
        )
        total_mensajes = count_result.scalar() or 0

        respuestas.append(ConversacionResponse(
            id=conv.id,
            session_id=conv.session_id,
            user_id=conv.user_id,
            titulo=conv.titulo,
            proyecto_activo_id=conv.proyecto_activo_id,
            proyecto_nombre=proyecto_nombre,
            vista_actual=conv.vista_actual,
            activa=conv.activa,
            total_mensajes=total_mensajes,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        ))

    return respuestas


@router.get("/conversaciones/{conversacion_id}", response_model=ConversacionConMensajes)
async def obtener_conversacion(
    conversacion_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene una conversacion con su historial de mensajes.

    Args:
        conversacion_id: ID de la conversacion

    Returns:
        Conversacion con mensajes
    """
    # Query con LEFT JOIN a proyectos para obtener el nombre
    result = await db.execute(
        select(Conversacion, Proyecto.nombre)
        .outerjoin(Proyecto, Conversacion.proyecto_activo_id == Proyecto.id)
        .where(Conversacion.id == conversacion_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    conversacion, proyecto_nombre = row

    # Obtener mensajes
    result_msgs = await db.execute(
        select(Mensaje)
        .where(Mensaje.conversacion_id == conversacion_id)
        .order_by(Mensaje.created_at)
    )
    mensajes = result_msgs.scalars().all()

    mensajes_response = [
        MensajeResponse(
            id=msg.id,
            conversacion_id=msg.conversacion_id,
            rol=RolMensaje(msg.rol),
            contenido=msg.contenido,
            tool_calls=msg.tool_calls,
            fuentes=msg.fuentes,
            tokens_input=msg.tokens_input,
            tokens_output=msg.tokens_output,
            latencia_ms=msg.latencia_ms,
            created_at=msg.created_at,
        )
        for msg in mensajes
        if msg.rol in ["user", "assistant"]  # Filtrar tool results
    ]

    return ConversacionConMensajes(
        id=conversacion.id,
        session_id=conversacion.session_id,
        user_id=conversacion.user_id,
        titulo=conversacion.titulo,
        proyecto_activo_id=conversacion.proyecto_activo_id,
        proyecto_nombre=proyecto_nombre,
        vista_actual=conversacion.vista_actual,
        activa=conversacion.activa,
        total_mensajes=len(mensajes_response),
        created_at=conversacion.created_at,
        updated_at=conversacion.updated_at,
        mensajes=mensajes_response,
    )


@router.delete("/conversaciones/{conversacion_id}")
async def eliminar_conversacion(
    conversacion_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Elimina (desactiva) una conversacion.

    Args:
        conversacion_id: ID de la conversacion

    Returns:
        Confirmacion de eliminacion
    """
    result = await db.execute(
        select(Conversacion).where(Conversacion.id == conversacion_id)
    )
    conversacion = result.scalar()

    if not conversacion:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    conversacion.activa = False
    await db.commit()

    return {"message": "Conversacion eliminada", "id": str(conversacion_id)}


# =============================================================================
# Acciones Pendientes
# =============================================================================

@router.get("/acciones-pendientes", response_model=List[AccionPendienteResponse])
async def listar_acciones_pendientes(
    session_id: UUID = Query(..., description="ID de sesion"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista las acciones pendientes de confirmacion.

    Args:
        session_id: ID de sesion

    Returns:
        Lista de acciones pendientes
    """
    # Obtener conversaciones de la sesion
    conv_result = await db.execute(
        select(Conversacion.id).where(Conversacion.session_id == session_id)
    )
    conv_ids = [row[0] for row in conv_result.fetchall()]

    if not conv_ids:
        return []

    # Obtener acciones pendientes
    result = await db.execute(
        select(AccionPendiente)
        .where(
            AccionPendiente.conversacion_id.in_(conv_ids),
            AccionPendiente.estado == "pendiente",
        )
        .order_by(desc(AccionPendiente.created_at))
    )
    acciones = result.scalars().all()

    return [
        AccionPendienteResponse(
            id=accion.id,
            conversacion_id=accion.conversacion_id,
            tipo=TipoAccion(accion.tipo) if accion.tipo in TipoAccion.__members__.values() else TipoAccion.CREAR_PROYECTO,
            parametros=accion.parametros,
            descripcion=accion.descripcion,
            estado=EstadoAccion(accion.estado),
            resultado=accion.resultado,
            error_mensaje=accion.error_mensaje,
            created_at=accion.created_at,
            expires_at=accion.expires_at,
            puede_confirmarse=accion.puede_confirmarse,
        )
        for accion in acciones
    ]


# =============================================================================
# Herramientas
# =============================================================================

@router.get("/herramientas", response_model=HerramientasDisponibles)
async def listar_herramientas():
    """
    Lista las herramientas disponibles del asistente.

    Returns:
        Lista de herramientas con descripcion y permisos
    """
    definiciones = registro_herramientas.listar()

    herramientas = [
        HerramientaInfo(
            name=d.name,
            description=d.description,
            categoria=d.categoria.value,
            requiere_confirmacion=d.requiere_confirmacion,
            permisos_requeridos=[p.value for p in d.permisos],
        )
        for d in definiciones
    ]

    return HerramientasDisponibles(
        herramientas=herramientas,
        total=len(herramientas),
    )


@router.get("/herramientas/stats")
async def estadisticas_herramientas():
    """
    Obtiene estadisticas de las herramientas.

    Returns:
        Conteo de herramientas por categoria
    """
    return get_tools_count()


# =============================================================================
# Feedback
# =============================================================================

@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def crear_feedback(
    data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra feedback sobre un mensaje del asistente.

    Args:
        data: Datos del feedback

    Returns:
        Feedback creado
    """
    # Verificar que el mensaje existe
    result = await db.execute(
        select(Mensaje).where(Mensaje.id == data.mensaje_id)
    )
    mensaje = result.scalar()

    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    feedback = Feedback(
        mensaje_id=data.mensaje_id,
        valoracion=data.valoracion,
        es_util=data.es_util,
        comentario=data.comentario,
        categorias_problema=data.categorias_problema,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        mensaje_id=feedback.mensaje_id,
        valoracion=feedback.valoracion,
        es_util=feedback.es_util,
        comentario=feedback.comentario,
        created_at=feedback.created_at,
    )


# =============================================================================
# Notificaciones Proactivas
# =============================================================================

@router.get("/notificaciones", response_model=List[NotificacionProactiva])
async def listar_notificaciones(
    session_id: UUID = Query(..., description="ID de sesion"),
    solo_no_leidas: bool = Query(True, description="Solo notificaciones no leidas"),
    limite: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista las notificaciones proactivas del asistente.

    Args:
        session_id: ID de sesion
        solo_no_leidas: Filtrar solo no leidas
        limite: Numero maximo de notificaciones

    Returns:
        Lista de notificaciones
    """
    query = select(NotificacionEnviada).where(
        NotificacionEnviada.session_id == session_id
    )

    if solo_no_leidas:
        query = query.where(NotificacionEnviada.leida == False)

    query = query.order_by(desc(NotificacionEnviada.created_at)).limit(limite)

    result = await db.execute(query)
    notificaciones = result.scalars().all()

    return [
        NotificacionProactiva(
            id=n.id,
            trigger_codigo=n.trigger_codigo,
            mensaje=n.mensaje,
            proyecto_id=n.proyecto_id,
            created_at=n.created_at,
        )
        for n in notificaciones
    ]


@router.post("/notificaciones/{notificacion_id}/leer")
async def marcar_notificacion_leida(
    notificacion_id: UUID,
    accion_tomada: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Marca una notificacion como leida.

    Args:
        notificacion_id: ID de la notificacion
        accion_tomada: Accion que tomo el usuario (opcional)

    Returns:
        Confirmacion
    """
    result = await db.execute(
        select(NotificacionEnviada).where(NotificacionEnviada.id == notificacion_id)
    )
    notificacion = result.scalar()

    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")

    from datetime import datetime
    notificacion.leida = True
    notificacion.leida_at = datetime.utcnow()
    if accion_tomada:
        notificacion.accion_tomada = accion_tomada

    await db.commit()

    return {"message": "Notificacion marcada como leida"}


# =============================================================================
# WebSocket para Chat en Tiempo Real
# =============================================================================

class ConnectionManager:
    """Gestor de conexiones WebSocket."""

    def __init__(self):
        self.active_connections: dict[UUID, WebSocket] = {}

    async def connect(self, session_id: UUID, websocket: WebSocket):
        """Conecta un cliente."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket conectado: session_id={session_id}")

    def disconnect(self, session_id: UUID):
        """Desconecta un cliente."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket desconectado: session_id={session_id}")

    async def send_message(self, session_id: UUID, message: dict):
        """Envia un mensaje a un cliente especifico."""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def broadcast(self, message: dict):
        """Envia un mensaje a todos los clientes."""
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: UUID,
):
    """
    WebSocket para chat en tiempo real.

    Soporta:
    - Mensajes de chat
    - Indicadores de typing
    - Notificaciones proactivas
    - Ping/pong para keep-alive
    """
    await manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("tipo", "chat")

            if msg_type == "ping":
                await websocket.send_json({"tipo": "pong"})

            elif msg_type == "chat":
                # Procesar mensaje de chat
                # Nota: En produccion, esto deberia usar un pool de conexiones DB
                # y manejar mejor los errores
                await websocket.send_json({
                    "tipo": "typing",
                    "payload": {"is_typing": True}
                })

                # Aqui se procesaria el mensaje con el AsistenteService
                # Por ahora enviamos un placeholder
                await websocket.send_json({
                    "tipo": "chat",
                    "payload": {
                        "mensaje": "Respuesta recibida via WebSocket",
                        "nota": "Implementar integracion completa con AsistenteService"
                    }
                })

                await websocket.send_json({
                    "tipo": "typing",
                    "payload": {"is_typing": False}
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
        manager.disconnect(session_id)


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def health_check():
    """
    Verifica el estado del servicio de asistente.

    Returns:
        Estado del servicio
    """
    tools_count = get_tools_count()
    return {
        "status": "healthy",
        "service": "asistente",
        "herramientas_registradas": sum(tools_count.values()),
        "herramientas_por_categoria": tools_count,
    }
