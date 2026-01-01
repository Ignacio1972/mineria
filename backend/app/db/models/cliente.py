"""
Modelo SQLAlchemy para Cliente.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Cliente(Base):
    """Empresa o persona titular de proyectos mineros."""

    __tablename__ = "clientes"
    __table_args__ = {"schema": "proyectos"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rut = Column(String(12), unique=True, nullable=True, index=True)
    razon_social = Column(String(200), nullable=False, index=True)
    nombre_fantasia = Column(String(200), nullable=True)
    email = Column(String(100), nullable=True)
    telefono = Column(String(20), nullable=True)
    direccion = Column(Text, nullable=True)
    notas = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relaciones
    proyectos = relationship(
        "Proyecto",
        back_populates="cliente",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<Cliente {self.razon_social}>"

    @property
    def cantidad_proyectos(self) -> int:
        """Retorna cantidad de proyectos del cliente."""
        return self.proyectos.count()
