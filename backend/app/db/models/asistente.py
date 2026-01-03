"""
Modelos SQLAlchemy para el Asistente IA.
"""
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Optional
from enum import Enum

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer, Float,
    ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.db.session import Base


class RolMensaje(str, Enum):
    """Roles posibles de un mensaje."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class EstadoAccion(str, Enum):
    """Estados posibles de una accion pendiente."""
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    EXPIRADA = "expirada"
    EJECUTADA = "ejecutada"
    ERROR = "error"


class TipoMemoria(str, Enum):
    """Tipos de memoria del usuario."""
    PREFERENCIA = "preferencia"
    CONSULTA_FRECUENTE = "consulta_frecuente"
    FEEDBACK = "feedback"
    HECHO_IMPORTANTE = "hecho_importante"


class TipoDocumentacion(str, Enum):
    """Tipos de documentacion del sistema."""
    ARCHIVO_MD = "archivo_md"
    DOCSTRING = "docstring"
    ENDPOINT = "endpoint"
    COMPONENTE = "componente"
    GUIA_USO = "guia_uso"


class Conversacion(Base):
    """Sesiones de chat del asistente IA."""

    __tablename__ = "conversaciones"
    __table_args__ = {"schema": "asistente"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    titulo = Column(String(255), nullable=True)
    proyecto_activo_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    vista_actual = Column(String(50), default="dashboard")
    activa = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    datos_extra = Column(JSONB, default=dict)

    # Relaciones
    mensajes = relationship(
        "Mensaje",
        back_populates="conversacion",
        cascade="all, delete-orphan",
        order_by="Mensaje.created_at"
    )
    acciones = relationship(
        "AccionPendiente",
        back_populates="conversacion",
        cascade="all, delete-orphan"
    )
    cliente = relationship("Cliente", foreign_keys=[user_id])
    proyecto_activo = relationship("Proyecto", foreign_keys=[proyecto_activo_id])

    def __repr__(self):
        return f"<Conversacion {self.id} - session:{self.session_id}>"

    @property
    def total_mensajes(self) -> int:
        """Retorna el total de mensajes en la conversacion."""
        return len(self.mensajes) if self.mensajes else 0


class Mensaje(Base):
    """Mensajes de las conversaciones del asistente."""

    __tablename__ = "mensajes"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('user', 'assistant', 'system', 'tool')",
            name="check_rol_valido"
        ),
        {"schema": "asistente"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversacion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("asistente.conversaciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    rol = Column(String(20), nullable=False)
    contenido = Column(Text, nullable=False)

    # Tool use
    tool_calls = Column(JSONB, nullable=True)
    tool_call_id = Column(String(100), nullable=True, index=True)
    tool_name = Column(String(100), nullable=True)

    # Fuentes citadas
    fuentes = Column(JSONB, nullable=True)

    # Metricas
    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    latencia_ms = Column(Integer, nullable=True)
    modelo_usado = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    datos_extra = Column(JSONB, default=dict)

    # Relaciones
    conversacion = relationship("Conversacion", back_populates="mensajes")
    feedback = relationship(
        "Feedback",
        back_populates="mensaje",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        preview = self.contenido[:50] + "..." if len(self.contenido) > 50 else self.contenido
        return f"<Mensaje {self.rol}: {preview}>"

    def to_anthropic_format(self) -> dict:
        """Convierte el mensaje al formato de la API de Anthropic."""
        msg = {"role": self.rol, "content": self.contenido}
        if self.tool_calls:
            msg["tool_use"] = self.tool_calls
        if self.tool_call_id:
            msg["tool_use_id"] = self.tool_call_id
        return msg


class AccionPendiente(Base):
    """Acciones del asistente que requieren confirmacion del usuario."""

    __tablename__ = "acciones_pendientes"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'confirmada', 'cancelada', 'expirada', 'ejecutada', 'error')",
            name="check_estado_valido"
        ),
        {"schema": "asistente"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversacion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("asistente.conversaciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    mensaje_id = Column(
        UUID(as_uuid=True),
        ForeignKey("asistente.mensajes.id", ondelete="SET NULL"),
        nullable=True
    )
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    tipo = Column(String(50), nullable=False, index=True)
    parametros = Column(JSONB, nullable=False)
    descripcion = Column(Text, nullable=False)
    estado = Column(String(20), default="pendiente", index=True)
    resultado = Column(JSONB, nullable=True)
    error_mensaje = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.utcnow() + timedelta(minutes=5)
    )
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    conversacion = relationship("Conversacion", back_populates="acciones")
    mensaje = relationship("Mensaje")
    proyecto = relationship("Proyecto", foreign_keys=[proyecto_id])

    def __repr__(self):
        return f"<AccionPendiente {self.tipo} - {self.estado}>"

    @property
    def esta_expirada(self) -> bool:
        """Verifica si la accion ha expirado."""
        return self.estado == "pendiente" and datetime.utcnow() > self.expires_at

    @property
    def puede_confirmarse(self) -> bool:
        """Verifica si la accion puede ser confirmada."""
        return self.estado == "pendiente" and not self.esta_expirada


class MemoriaUsuario(Base):
    """Memoria persistente del asistente por usuario."""

    __tablename__ = "memoria_usuario"
    __table_args__ = {"schema": "asistente"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.clientes.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    tipo = Column(String(50), nullable=False, index=True)
    clave = Column(String(100), nullable=True, index=True)
    valor = Column(JSONB, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    importancia = Column(Float, default=1.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    cliente = relationship("Cliente", foreign_keys=[user_id])

    def __repr__(self):
        return f"<MemoriaUsuario {self.tipo}: {self.clave}>"


class DocumentacionSistema(Base):
    """Documentacion del sistema para RAG del asistente."""

    __tablename__ = "documentacion_sistema"
    __table_args__ = {"schema": "asistente"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tipo = Column(String(50), nullable=False, index=True)
    ruta = Column(String(500), nullable=True, index=True)
    titulo = Column(String(255), nullable=True)
    contenido = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    version = Column(String(50), nullable=True)
    tags = Column(ARRAY(String(100)), default=list)
    activo = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    datos_extra = Column(JSONB, default=dict)

    def __repr__(self):
        return f"<DocumentacionSistema {self.titulo or self.ruta}>"


class TriggerProactivo(Base):
    """Configuracion de triggers para notificaciones proactivas."""

    __tablename__ = "triggers_proactivos"
    __table_args__ = {"schema": "asistente"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, index=True)
    prioridad = Column(Integer, default=5)
    condicion_sql = Column(Text, nullable=False)
    mensaje_template = Column(Text, nullable=False)
    accion_sugerida = Column(String(100), nullable=True)
    accion_parametros = Column(JSONB, nullable=True)
    max_por_hora = Column(Integer, default=3)
    cooldown_minutos = Column(Integer, default=30)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    notificaciones = relationship(
        "NotificacionEnviada",
        back_populates="trigger",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TriggerProactivo {self.codigo}>"


class NotificacionEnviada(Base):
    """Historial de notificaciones proactivas enviadas."""

    __tablename__ = "notificaciones_enviadas"
    __table_args__ = {"schema": "asistente"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    trigger_id = Column(
        UUID(as_uuid=True),
        ForeignKey("asistente.triggers_proactivos.id", ondelete="SET NULL"),
        nullable=True
    )
    trigger_codigo = Column(String(50), nullable=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.clientes.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="SET NULL"),
        nullable=True
    )
    mensaje = Column(Text, nullable=False)
    leida = Column(Boolean, default=False)
    accion_tomada = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    leida_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    trigger = relationship("TriggerProactivo", back_populates="notificaciones")
    cliente = relationship("Cliente", foreign_keys=[user_id])
    proyecto = relationship("Proyecto", foreign_keys=[proyecto_id])

    def __repr__(self):
        return f"<NotificacionEnviada {self.trigger_codigo} - leida:{self.leida}>"


class Feedback(Base):
    """Feedback de usuarios sobre respuestas del asistente."""

    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint("valoracion BETWEEN 1 AND 5", name="check_valoracion_rango"),
        {"schema": "asistente"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mensaje_id = Column(
        UUID(as_uuid=True),
        ForeignKey("asistente.mensajes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    valoracion = Column(Integer, nullable=True)
    es_util = Column(Boolean, nullable=True)
    comentario = Column(Text, nullable=True)
    categorias_problema = Column(ARRAY(String(50)), default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    mensaje = relationship("Mensaje", back_populates="feedback")
    cliente = relationship("Cliente", foreign_keys=[user_id])

    def __repr__(self):
        return f"<Feedback valoracion:{self.valoracion} util:{self.es_util}>"
