"""
Modelos SQLAlchemy para Gestor de Proceso de Evaluación SEIA (ICSARA/Adendas).
Esquema: proyectos
"""
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    ForeignKey, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


# =============================================================================
# ENUMS
# =============================================================================

class EstadoEvaluacion(str, Enum):
    """Estados del proceso de evaluación SEIA."""
    NO_INGRESADO = "no_ingresado"
    INGRESADO = "ingresado"
    EN_ADMISIBILIDAD = "en_admisibilidad"
    ADMITIDO = "admitido"
    INADMITIDO = "inadmitido"
    EN_EVALUACION = "en_evaluacion"
    ICSARA_EMITIDO = "icsara_emitido"
    ADENDA_EN_REVISION = "adenda_en_revision"
    ICE_EMITIDO = "ice_emitido"
    EN_COMISION = "en_comision"
    RCA_APROBADA = "rca_aprobada"
    RCA_RECHAZADA = "rca_rechazada"
    DESISTIDO = "desistido"
    CADUCADO = "caducado"


class ResultadoRCA(str, Enum):
    """Resultado de la Resolución de Calificación Ambiental."""
    FAVORABLE = "favorable"
    FAVORABLE_CON_CONDICIONES = "favorable_con_condiciones"
    DESFAVORABLE = "desfavorable"
    DESISTIMIENTO = "desistimiento"
    CADUCIDAD = "caducidad"


class EstadoICSARA(str, Enum):
    """Estados de un ICSARA."""
    EMITIDO = "emitido"
    RESPONDIDO = "respondido"
    PARCIALMENTE_RESPONDIDO = "parcialmente_respondido"
    VENCIDO = "vencido"


class EstadoAdenda(str, Enum):
    """Estados de una Adenda."""
    EN_ELABORACION = "en_elaboracion"
    PRESENTADA = "presentada"
    EN_REVISION = "en_revision"
    ACEPTADA = "aceptada"
    CON_OBSERVACIONES = "con_observaciones"
    RECHAZADA = "rechazada"


class ResultadoRevision(str, Enum):
    """Resultado de la revisión de una Adenda."""
    SUFICIENTE = "suficiente"
    INSUFICIENTE = "insuficiente"
    PARCIALMENTE_SUFICIENTE = "parcialmente_suficiente"


class TipoObservacion(str, Enum):
    """Tipos de observación en ICSARA."""
    AMPLIACION = "ampliacion"
    ACLARACION = "aclaracion"
    RECTIFICACION = "rectificacion"


class PrioridadObservacion(str, Enum):
    """Prioridad de observación en ICSARA."""
    CRITICA = "critica"
    IMPORTANTE = "importante"
    MENOR = "menor"


class EstadoObservacionICSARA(str, Enum):
    """Estado de una observación individual."""
    PENDIENTE = "pendiente"
    RESPONDIDA = "respondida"
    PARCIAL = "parcial"


# =============================================================================
# MODELOS
# =============================================================================

class ProcesoEvaluacion(Base):
    """
    Gestiona el ciclo de vida de evaluación SEIA de un proyecto.

    Relación 1:1 con Proyecto.
    Contiene múltiples ICSARA (máximo 2, excepcionalmente 3).
    """

    __tablename__ = "proceso_evaluacion"
    __table_args__ = (
        UniqueConstraint('proyecto_id', name='uk_proceso_proyecto'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Estado administrativo
    estado_evaluacion = Column(
        String(50),
        nullable=False,
        default=EstadoEvaluacion.NO_INGRESADO.value,
        index=True
    )
    fecha_ingreso = Column(Date, nullable=True)
    fecha_admisibilidad = Column(Date, nullable=True)
    fecha_rca = Column(Date, nullable=True)
    resultado_rca = Column(String(50), nullable=True)

    # Plazos
    plazo_legal_dias = Column(Integer, default=120)  # EIA=120, DIA=60
    dias_transcurridos = Column(Integer, default=0)
    dias_suspension = Column(Integer, default=0)  # Por Adendas

    # Resolución
    numero_rca = Column(String(50), nullable=True)
    url_rca = Column(Text, nullable=True)
    condiciones_rca = Column(JSONB, nullable=True)  # Array de condiciones

    # Metadatos
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", backref="proceso_evaluacion")
    icsaras = relationship(
        "ICSARA",
        back_populates="proceso_evaluacion",
        cascade="all, delete-orphan",
        order_by="ICSARA.numero_icsara"
    )

    def __repr__(self):
        return f"<ProcesoEvaluacion proyecto_id={self.proyecto_id} estado={self.estado_evaluacion}>"

    @property
    def total_icsara(self) -> int:
        """Número total de ICSARA emitidos."""
        return len(self.icsaras) if self.icsaras else 0

    @property
    def icsara_actual(self) -> Optional["ICSARA"]:
        """Obtiene el ICSARA actual (último emitido)."""
        if self.icsaras:
            return max(self.icsaras, key=lambda x: x.numero_icsara)
        return None

    @property
    def total_observaciones(self) -> int:
        """Total de observaciones en todos los ICSARA."""
        return sum(i.total_observaciones or 0 for i in (self.icsaras or []))

    @property
    def observaciones_pendientes(self) -> int:
        """Observaciones pendientes de resolver."""
        total = 0
        for icsara in (self.icsaras or []):
            for obs in (icsara.observaciones or []):
                if obs.get("estado") == EstadoObservacionICSARA.PENDIENTE.value:
                    total += 1
        return total

    @property
    def dias_restantes(self) -> int:
        """Días restantes de evaluación considerando suspensiones."""
        dias_efectivos = self.dias_transcurridos - self.dias_suspension
        return max(0, self.plazo_legal_dias - dias_efectivos)

    @property
    def porcentaje_plazo(self) -> float:
        """Porcentaje de plazo transcurrido."""
        if not self.plazo_legal_dias:
            return 0.0
        dias_efectivos = self.dias_transcurridos - self.dias_suspension
        return min(100.0, (dias_efectivos / self.plazo_legal_dias) * 100)

    def get_observaciones_por_oaeca(self) -> Dict[str, int]:
        """Agrupa observaciones por organismo (OAECA)."""
        conteo: Dict[str, int] = {}
        for icsara in (self.icsaras or []):
            for obs in (icsara.observaciones or []):
                oaeca = obs.get("oaeca", "Sin organismo")
                conteo[oaeca] = conteo.get(oaeca, 0) + 1
        return conteo

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario completo."""
        return {
            "id": self.id,
            "proyecto_id": self.proyecto_id,
            "estado_evaluacion": self.estado_evaluacion,
            "fecha_ingreso": self.fecha_ingreso.isoformat() if self.fecha_ingreso else None,
            "fecha_admisibilidad": self.fecha_admisibilidad.isoformat() if self.fecha_admisibilidad else None,
            "fecha_rca": self.fecha_rca.isoformat() if self.fecha_rca else None,
            "resultado_rca": self.resultado_rca,
            "plazo_legal_dias": self.plazo_legal_dias,
            "dias_transcurridos": self.dias_transcurridos,
            "dias_suspension": self.dias_suspension,
            "dias_restantes": self.dias_restantes,
            "porcentaje_plazo": self.porcentaje_plazo,
            "numero_rca": self.numero_rca,
            "url_rca": self.url_rca,
            "condiciones_rca": self.condiciones_rca,
            "total_icsara": self.total_icsara,
            "total_observaciones": self.total_observaciones,
            "observaciones_pendientes": self.observaciones_pendientes,
            "icsaras": [i.to_dict() for i in (self.icsaras or [])],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_resumen(self) -> Dict[str, Any]:
        """Resumen para vista rápida."""
        return {
            "id": self.id,
            "proyecto_id": self.proyecto_id,
            "estado_evaluacion": self.estado_evaluacion,
            "dias_restantes": self.dias_restantes,
            "porcentaje_plazo": self.porcentaje_plazo,
            "total_icsara": self.total_icsara,
            "observaciones_pendientes": self.observaciones_pendientes,
            "fecha_rca": self.fecha_rca.isoformat() if self.fecha_rca else None,
            "resultado_rca": self.resultado_rca
        }


class ICSARA(Base):
    """
    Informe Consolidado de Solicitud de Aclaraciones, Rectificaciones y Ampliaciones.

    Contiene las observaciones de los OAECA (Organismos con Competencia Ambiental).
    Puede tener múltiples Adendas como respuesta.
    """

    __tablename__ = "icsara"
    __table_args__ = (
        UniqueConstraint('proceso_evaluacion_id', 'numero_icsara', name='uk_icsara_proceso_numero'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    proceso_evaluacion_id = Column(
        Integer,
        ForeignKey("proyectos.proceso_evaluacion.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Identificación
    numero_icsara = Column(Integer, nullable=False)  # 1, 2, (3 excepcional)
    fecha_emision = Column(Date, nullable=False)
    fecha_limite_respuesta = Column(Date, nullable=False)

    # Contenido
    observaciones = Column(JSONB, nullable=False, default=list)
    total_observaciones = Column(Integer, default=0)
    observaciones_por_oaeca = Column(JSONB, default=dict)

    # Estado
    estado = Column(
        String(50),
        nullable=False,
        default=EstadoICSARA.EMITIDO.value,
        index=True
    )

    # Archivo PDF original
    archivo_id = Column(Integer, nullable=True)

    # Metadatos
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    proceso_evaluacion = relationship("ProcesoEvaluacion", back_populates="icsaras")
    adendas = relationship(
        "Adenda",
        back_populates="icsara",
        cascade="all, delete-orphan",
        order_by="Adenda.numero_adenda"
    )

    def __repr__(self):
        return f"<ICSARA #{self.numero_icsara} proceso_id={self.proceso_evaluacion_id}>"

    @property
    def dias_para_responder(self) -> int:
        """Días restantes para responder."""
        if not self.fecha_limite_respuesta:
            return 0
        delta = self.fecha_limite_respuesta - date.today()
        return max(0, delta.days)

    @property
    def esta_vencido(self) -> bool:
        """Verifica si el plazo de respuesta venció."""
        if not self.fecha_limite_respuesta:
            return False
        return date.today() > self.fecha_limite_respuesta

    @property
    def adenda_actual(self) -> Optional["Adenda"]:
        """Obtiene la última Adenda presentada."""
        if self.adendas:
            return max(self.adendas, key=lambda x: x.numero_adenda)
        return None

    @property
    def observaciones_resueltas(self) -> int:
        """Cuenta observaciones resueltas."""
        return sum(
            1 for obs in (self.observaciones or [])
            if obs.get("estado") == EstadoObservacionICSARA.RESPONDIDA.value
        )

    @property
    def observaciones_pendientes_count(self) -> int:
        """Cuenta observaciones pendientes."""
        return sum(
            1 for obs in (self.observaciones or [])
            if obs.get("estado") == EstadoObservacionICSARA.PENDIENTE.value
        )

    def agregar_observacion(self, observacion: Dict[str, Any]) -> None:
        """Agrega una observación al ICSARA."""
        if self.observaciones is None:
            self.observaciones = []

        # Asignar ID si no tiene
        if "id" not in observacion:
            observacion["id"] = f"OBS-{len(self.observaciones) + 1:03d}"

        # Estado por defecto
        if "estado" not in observacion:
            observacion["estado"] = EstadoObservacionICSARA.PENDIENTE.value

        self.observaciones.append(observacion)
        self.total_observaciones = len(self.observaciones)

        # Actualizar conteo por OAECA
        self._actualizar_conteo_oaeca()

    def _actualizar_conteo_oaeca(self) -> None:
        """Actualiza el conteo de observaciones por OAECA."""
        conteo: Dict[str, int] = {}
        for obs in (self.observaciones or []):
            oaeca = obs.get("oaeca", "Sin organismo")
            conteo[oaeca] = conteo.get(oaeca, 0) + 1
        self.observaciones_por_oaeca = conteo

    def actualizar_estado_observacion(
        self,
        observacion_id: str,
        nuevo_estado: str
    ) -> bool:
        """Actualiza el estado de una observación específica."""
        for obs in (self.observaciones or []):
            if obs.get("id") == observacion_id:
                obs["estado"] = nuevo_estado
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario completo."""
        return {
            "id": self.id,
            "proceso_evaluacion_id": self.proceso_evaluacion_id,
            "numero_icsara": self.numero_icsara,
            "fecha_emision": self.fecha_emision.isoformat() if self.fecha_emision else None,
            "fecha_limite_respuesta": self.fecha_limite_respuesta.isoformat() if self.fecha_limite_respuesta else None,
            "dias_para_responder": self.dias_para_responder,
            "esta_vencido": self.esta_vencido,
            "observaciones": self.observaciones or [],
            "total_observaciones": self.total_observaciones,
            "observaciones_resueltas": self.observaciones_resueltas,
            "observaciones_pendientes": self.observaciones_pendientes_count,
            "observaciones_por_oaeca": self.observaciones_por_oaeca or {},
            "estado": self.estado,
            "archivo_id": self.archivo_id,
            "adendas": [a.to_dict() for a in (self.adendas or [])],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Adenda(Base):
    """
    Documento de respuesta del titular a las observaciones del ICSARA.

    Contiene las respuestas a cada observación y su calificación por el SEA.
    """

    __tablename__ = "adenda"
    __table_args__ = (
        UniqueConstraint('icsara_id', 'numero_adenda', name='uk_adenda_icsara_numero'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    icsara_id = Column(
        Integer,
        ForeignKey("proyectos.icsara.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Identificación
    numero_adenda = Column(Integer, nullable=False)
    fecha_presentacion = Column(Date, nullable=False)

    # Contenido
    respuestas = Column(JSONB, nullable=False, default=list)
    total_respuestas = Column(Integer, default=0)
    observaciones_resueltas = Column(Integer, default=0)
    observaciones_pendientes = Column(Integer, default=0)

    # Evaluación de la Adenda
    estado = Column(
        String(50),
        nullable=False,
        default=EstadoAdenda.PRESENTADA.value,
        index=True
    )
    fecha_revision = Column(Date, nullable=True)
    resultado_revision = Column(String(50), nullable=True)

    # Archivo PDF
    archivo_id = Column(Integer, nullable=True)

    # Metadatos
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    icsara = relationship("ICSARA", back_populates="adendas")

    def __repr__(self):
        return f"<Adenda #{self.numero_adenda} icsara_id={self.icsara_id}>"

    @property
    def porcentaje_resueltas(self) -> float:
        """Porcentaje de observaciones resueltas."""
        total = self.observaciones_resueltas + self.observaciones_pendientes
        if total == 0:
            return 0.0
        return (self.observaciones_resueltas / total) * 100

    def agregar_respuesta(self, respuesta: Dict[str, Any]) -> None:
        """Agrega una respuesta a la Adenda."""
        if self.respuestas is None:
            self.respuestas = []

        self.respuestas.append(respuesta)
        self.total_respuestas = len(self.respuestas)

        # Actualizar conteos
        self._actualizar_conteos()

    def _actualizar_conteos(self) -> None:
        """Actualiza conteos de observaciones resueltas/pendientes."""
        resueltas = 0
        pendientes = 0
        for resp in (self.respuestas or []):
            estado = resp.get("estado", "")
            if estado == "respondida":
                resueltas += 1
            elif estado in ["pendiente", "parcial", "no_respondida"]:
                pendientes += 1
        self.observaciones_resueltas = resueltas
        self.observaciones_pendientes = pendientes

    def actualizar_respuesta(
        self,
        observacion_id: str,
        estado: str,
        calificacion: Optional[str] = None
    ) -> bool:
        """Actualiza una respuesta específica."""
        for resp in (self.respuestas or []):
            if resp.get("observacion_id") == observacion_id:
                resp["estado"] = estado
                if calificacion:
                    resp["calificacion_sea"] = calificacion
                self._actualizar_conteos()
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario completo."""
        return {
            "id": self.id,
            "icsara_id": self.icsara_id,
            "numero_adenda": self.numero_adenda,
            "fecha_presentacion": self.fecha_presentacion.isoformat() if self.fecha_presentacion else None,
            "respuestas": self.respuestas or [],
            "total_respuestas": self.total_respuestas,
            "observaciones_resueltas": self.observaciones_resueltas,
            "observaciones_pendientes": self.observaciones_pendientes,
            "porcentaje_resueltas": self.porcentaje_resueltas,
            "estado": self.estado,
            "fecha_revision": self.fecha_revision.isoformat() if self.fecha_revision else None,
            "resultado_revision": self.resultado_revision,
            "archivo_id": self.archivo_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# Constantes útiles
OAECAS_MINERIA = [
    "SERNAGEOMIN",
    "DGA",
    "SAG",
    "CONAF",
    "SEREMI Salud",
    "SEREMI MMA",
    "CMN",
    "CONADI",
    "Municipalidad",
    "SERNATUR",
]

ESTADOS_TIMELINE = [
    (EstadoEvaluacion.NO_INGRESADO, "No ingresado", "Proyecto en preparación"),
    (EstadoEvaluacion.INGRESADO, "Ingresado", "Enviado a e-SEIA"),
    (EstadoEvaluacion.EN_ADMISIBILIDAD, "En admisibilidad", "Revisión formal (5 días)"),
    (EstadoEvaluacion.ADMITIDO, "Admitido", "Pasa a evaluación"),
    (EstadoEvaluacion.EN_EVALUACION, "En evaluación", "Análisis por OAECA"),
    (EstadoEvaluacion.ICSARA_EMITIDO, "ICSARA emitido", "Esperando respuesta"),
    (EstadoEvaluacion.ADENDA_EN_REVISION, "Adenda en revisión", "Adenda presentada"),
    (EstadoEvaluacion.ICE_EMITIDO, "ICE emitido", "Informe Consolidado"),
    (EstadoEvaluacion.EN_COMISION, "En comisión", "Votación regional"),
    (EstadoEvaluacion.RCA_APROBADA, "RCA aprobada", "Favorable"),
    (EstadoEvaluacion.RCA_RECHAZADA, "RCA rechazada", "Desfavorable"),
]
