"""
Modelos SQLAlchemy para Recopilacion Guiada (Fase 3).
Esquemas: asistente_config, proyectos
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Numeric,
    ForeignKey, UniqueConstraint, CheckConstraint, ARRAY
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.session import Base


# =============================================================================
# ENUMS
# =============================================================================

class EstadoSeccion(str, Enum):
    """Estados posibles de una seccion del EIA."""
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    VALIDADO = "validado"


class TipoRespuesta(str, Enum):
    """Tipos de respuesta para preguntas de recopilacion."""
    TEXTO = "texto"
    NUMERO = "numero"
    FECHA = "fecha"
    SELECCION = "seleccion"
    SELECCION_MULTIPLE = "seleccion_multiple"
    ARCHIVO = "archivo"
    COORDENADAS = "coordenadas"
    TABLA = "tabla"
    BOOLEANO = "booleano"


class TipoReglaConsistencia(str, Enum):
    """Tipos de reglas de consistencia."""
    IGUALDAD = "igualdad"
    CONTENIDO = "contenido"
    RANGO = "rango"
    REFERENCIA = "referencia"
    COHERENCIA = "coherencia"


class SeveridadInconsistencia(str, Enum):
    """Niveles de severidad de inconsistencias."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EstadoExtraccion(str, Enum):
    """Estados de extraccion de documentos."""
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    COMPLETADO = "completado"
    ERROR = "error"


# =============================================================================
# MODELOS DE CONFIGURACIÓN (asistente_config)
# =============================================================================

class PreguntaRecopilacion(Base):
    """Preguntas guiadas para recopilar informacion por seccion del EIA."""

    __tablename__ = "preguntas_recopilacion"
    __table_args__ = (
        UniqueConstraint(
            'tipo_proyecto_id', 'capitulo_numero', 'seccion_codigo', 'codigo_pregunta',
            name='preguntas_recopilacion_unique'
        ),
        {"schema": "asistente_config"}
    )

    id = Column(Integer, primary_key=True)
    tipo_proyecto_id = Column(
        Integer,
        ForeignKey("asistente_config.tipos_proyecto.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    subtipo_id = Column(
        Integer,
        ForeignKey("asistente_config.subtipos_proyecto.id", ondelete="SET NULL"),
        nullable=True
    )
    capitulo_numero = Column(Integer, nullable=False, index=True)
    seccion_codigo = Column(String(50), nullable=False, index=True)
    seccion_nombre = Column(String(200), nullable=True)
    codigo_pregunta = Column(String(50), nullable=False)
    pregunta = Column(Text, nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo_respuesta = Column(String(30), nullable=False, default="texto")
    opciones = Column(JSONB, nullable=True)  # Para tipo seleccion
    valor_por_defecto = Column(JSONB, nullable=True)
    validaciones = Column(JSONB, nullable=True)  # {min, max, patron, requerido}
    es_obligatoria = Column(Boolean, default=True)
    condicion_activacion = Column(JSONB, nullable=True)  # {campo: valor}
    orden = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto")
    subtipo = relationship("SubtipoProyecto")

    def __repr__(self):
        return f"<PreguntaRecopilacion {self.codigo_pregunta}: {self.pregunta[:50]}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la pregunta a diccionario."""
        return {
            "id": self.id,
            "capitulo_numero": self.capitulo_numero,
            "seccion_codigo": self.seccion_codigo,
            "seccion_nombre": self.seccion_nombre,
            "codigo_pregunta": self.codigo_pregunta,
            "pregunta": self.pregunta,
            "descripcion": self.descripcion,
            "tipo_respuesta": self.tipo_respuesta,
            "opciones": self.opciones,
            "valor_por_defecto": self.valor_por_defecto,
            "validaciones": self.validaciones,
            "es_obligatoria": self.es_obligatoria,
            "condicion_activacion": self.condicion_activacion,
            "orden": self.orden
        }

    def aplica(self, respuestas_previas: dict) -> bool:
        """Evalua si la pregunta debe mostrarse segun condiciones."""
        if not self.condicion_activacion:
            return True

        for campo, valor_esperado in self.condicion_activacion.items():
            valor_actual = respuestas_previas.get(campo)
            if isinstance(valor_esperado, list):
                if valor_actual not in valor_esperado:
                    return False
            elif valor_actual != valor_esperado:
                return False
        return True

    def validar_respuesta(self, valor: Any) -> tuple[bool, Optional[str]]:
        """Valida una respuesta segun las reglas definidas."""
        if not self.validaciones:
            return True, None

        validaciones = self.validaciones

        # Validar requerido
        if validaciones.get("requerido", self.es_obligatoria):
            if valor is None or valor == "" or (isinstance(valor, list) and len(valor) == 0):
                return False, "Este campo es obligatorio"

        if valor is None or valor == "":
            return True, None  # Campo vacio pero no requerido

        # Validar minimo
        if "min" in validaciones:
            if self.tipo_respuesta == "numero":
                if float(valor) < validaciones["min"]:
                    return False, f"El valor debe ser mayor o igual a {validaciones['min']}"
            elif self.tipo_respuesta == "texto":
                if len(str(valor)) < validaciones["min"]:
                    return False, f"El texto debe tener al menos {validaciones['min']} caracteres"

        # Validar maximo
        if "max" in validaciones:
            if self.tipo_respuesta == "numero":
                if float(valor) > validaciones["max"]:
                    return False, f"El valor debe ser menor o igual a {validaciones['max']}"
            elif self.tipo_respuesta == "texto":
                if len(str(valor)) > validaciones["max"]:
                    return False, f"El texto debe tener maximo {validaciones['max']} caracteres"

        # Validar patron regex
        if "patron" in validaciones:
            import re
            if not re.match(validaciones["patron"], str(valor)):
                return False, validaciones.get("mensaje_patron", "El formato no es valido")

        return True, None


class ReglaConsistencia(Base):
    """Reglas para detectar inconsistencias entre capitulos del EIA."""

    __tablename__ = "reglas_consistencia"
    __table_args__ = {"schema": "asistente_config"}

    id = Column(Integer, primary_key=True)
    tipo_proyecto_id = Column(
        Integer,
        ForeignKey("asistente_config.tipos_proyecto.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    codigo = Column(String(50), nullable=False, unique=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    capitulo_origen = Column(Integer, nullable=False)
    seccion_origen = Column(String(50), nullable=False)
    campo_origen = Column(String(100), nullable=False)
    capitulo_destino = Column(Integer, nullable=False)
    seccion_destino = Column(String(50), nullable=False)
    campo_destino = Column(String(100), nullable=False)
    tipo_regla = Column(String(30), nullable=False, default="igualdad")
    parametros = Column(JSONB, nullable=True)
    mensaje_error = Column(Text, nullable=False)
    severidad = Column(String(20), default="warning")
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto")

    def __repr__(self):
        return f"<ReglaConsistencia {self.codigo}: {self.nombre}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la regla a diccionario."""
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "capitulo_origen": self.capitulo_origen,
            "seccion_origen": self.seccion_origen,
            "campo_origen": self.campo_origen,
            "capitulo_destino": self.capitulo_destino,
            "seccion_destino": self.seccion_destino,
            "campo_destino": self.campo_destino,
            "tipo_regla": self.tipo_regla,
            "mensaje_error": self.mensaje_error,
            "severidad": self.severidad
        }

    def evaluar(self, valor_origen: Any, valor_destino: Any) -> tuple[bool, Optional[str]]:
        """Evalua si se cumple la regla de consistencia."""
        if valor_origen is None or valor_destino is None:
            return True, None  # No evaluar si faltan valores

        if self.tipo_regla == "igualdad":
            if valor_origen != valor_destino:
                return False, self.mensaje_error
        elif self.tipo_regla == "contenido":
            # El valor destino debe contener el valor origen
            if isinstance(valor_destino, list):
                if valor_origen not in valor_destino:
                    return False, self.mensaje_error
            elif str(valor_origen) not in str(valor_destino):
                return False, self.mensaje_error
        elif self.tipo_regla == "rango":
            # El valor origen debe estar dentro del rango del destino
            try:
                origen = float(valor_origen)
                destino = float(valor_destino)
                if origen > destino:
                    return False, self.mensaje_error
            except (ValueError, TypeError):
                pass
        elif self.tipo_regla == "referencia":
            # El valor destino debe hacer referencia al origen
            if str(valor_origen) not in str(valor_destino):
                return False, self.mensaje_error

        return True, None


# =============================================================================
# MODELOS DE INSTANCIA POR PROYECTO (proyectos)
# =============================================================================

class ContenidoEIA(Base):
    """Contenido recopilado por seccion del EIA para cada proyecto."""

    __tablename__ = "contenido_eia"
    __table_args__ = (
        UniqueConstraint(
            'proyecto_id', 'capitulo_numero', 'seccion_codigo',
            name='contenido_eia_proyecto_capitulo_seccion_key'
        ),
        CheckConstraint('progreso >= 0 AND progreso <= 100', name='contenido_eia_progreso_check'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    capitulo_numero = Column(Integer, nullable=False, index=True)
    seccion_codigo = Column(String(50), nullable=False)
    seccion_nombre = Column(String(200), nullable=True)
    contenido = Column(JSONB, default=dict)
    estado = Column(String(20), default="pendiente")
    progreso = Column(Integer, default=0)
    documentos_vinculados = Column(ARRAY(Integer), default=list)
    validaciones = Column(JSONB, default=list)
    inconsistencias = Column(JSONB, default=list)
    sugerencias = Column(JSONB, default=list)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True), nullable=True)

    # Relaciones
    proyecto = relationship("Proyecto", backref="contenidos_eia")

    def __repr__(self):
        return f"<ContenidoEIA proyecto={self.proyecto_id} cap={self.capitulo_numero} sec={self.seccion_codigo}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el contenido a diccionario."""
        return {
            "id": self.id,
            "proyecto_id": self.proyecto_id,
            "capitulo_numero": self.capitulo_numero,
            "seccion_codigo": self.seccion_codigo,
            "seccion_nombre": self.seccion_nombre,
            "contenido": self.contenido or {},
            "estado": self.estado,
            "progreso": self.progreso,
            "documentos_vinculados": self.documentos_vinculados or [],
            "validaciones": self.validaciones or [],
            "inconsistencias": self.inconsistencias or [],
            "sugerencias": self.sugerencias or [],
            "notas": self.notas,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def actualizar_respuesta(self, codigo_pregunta: str, valor: Any) -> None:
        """Actualiza una respuesta en el contenido."""
        if self.contenido is None:
            self.contenido = {}
        self.contenido[codigo_pregunta] = valor

    def obtener_respuesta(self, codigo_pregunta: str) -> Any:
        """Obtiene una respuesta del contenido."""
        if self.contenido is None:
            return None
        return self.contenido.get(codigo_pregunta)

    def calcular_progreso(self, preguntas_obligatorias: int) -> int:
        """Calcula el progreso basado en preguntas respondidas."""
        if preguntas_obligatorias == 0:
            return 100
        if not self.contenido:
            return 0
        respondidas = sum(1 for v in self.contenido.values() if v is not None and v != "")
        return min(100, round((respondidas / preguntas_obligatorias) * 100))

    def agregar_inconsistencia(self, regla_codigo: str, mensaje: str, severidad: str = "warning") -> None:
        """Agrega una inconsistencia detectada."""
        if self.inconsistencias is None:
            self.inconsistencias = []
        self.inconsistencias.append({
            "regla_codigo": regla_codigo,
            "mensaje": mensaje,
            "severidad": severidad,
            "fecha": datetime.utcnow().isoformat()
        })

    def limpiar_inconsistencias(self) -> None:
        """Limpia las inconsistencias previas."""
        self.inconsistencias = []

    def vincular_documento(self, documento_id: int) -> None:
        """Vincula un documento a esta seccion."""
        if self.documentos_vinculados is None:
            self.documentos_vinculados = []
        if documento_id not in self.documentos_vinculados:
            self.documentos_vinculados = self.documentos_vinculados + [documento_id]


class ExtraccionDocumento(Base):
    """Historial de extracciones de datos de documentos con IA."""

    __tablename__ = "extracciones_documento"
    __table_args__ = {"schema": "proyectos"}

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    documento_id = Column(Integer, nullable=False, index=True)
    tipo_documento = Column(String(50), nullable=True)
    datos_extraidos = Column(JSONB, nullable=False, default=dict)
    mapeo_secciones = Column(JSONB, default=list)
    confianza_extraccion = Column(Numeric(3, 2), default=0.00)
    estado = Column(String(20), default="pendiente")
    errores = Column(JSONB, default=list)
    procesado_por = Column(String(50), default="claude_vision")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", backref="extracciones_documentos")

    def __repr__(self):
        return f"<ExtraccionDocumento proyecto={self.proyecto_id} doc={self.documento_id}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la extraccion a diccionario."""
        return {
            "id": self.id,
            "proyecto_id": self.proyecto_id,
            "documento_id": self.documento_id,
            "tipo_documento": self.tipo_documento,
            "datos_extraidos": self.datos_extraidos or {},
            "mapeo_secciones": self.mapeo_secciones or [],
            "confianza_extraccion": float(self.confianza_extraccion) if self.confianza_extraccion else 0.0,
            "estado": self.estado,
            "errores": self.errores or [],
            "procesado_por": self.procesado_por,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def agregar_mapeo(self, capitulo: int, seccion: str, campo: str, valor: Any, confianza: float = 0.8) -> None:
        """Agrega un mapeo sugerido de dato extraido a seccion."""
        if self.mapeo_secciones is None:
            self.mapeo_secciones = []
        self.mapeo_secciones.append({
            "capitulo_numero": capitulo,
            "seccion_codigo": seccion,
            "campo": campo,
            "valor": valor,
            "confianza": confianza
        })

    def marcar_completado(self, confianza: float) -> None:
        """Marca la extraccion como completada."""
        self.estado = "completado"
        self.confianza_extraccion = confianza

    def marcar_error(self, mensaje: str) -> None:
        """Marca la extraccion como error."""
        self.estado = "error"
        if self.errores is None:
            self.errores = []
        self.errores.append({
            "mensaje": mensaje,
            "fecha": datetime.utcnow().isoformat()
        })
