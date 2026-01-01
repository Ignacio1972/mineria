from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, DateTime, func
from geoalchemy2 import Geometry

from app.db.session import Base


class AreaProtegida(Base):
    __tablename__ = "areas_protegidas"
    __table_args__ = {"schema": "gis"}

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(100), nullable=False)
    categoria = Column(String(100))
    region = Column(String(100))
    comuna = Column(String(100))
    superficie_ha = Column(Numeric(12, 2))
    fecha_creacion = Column(Date)
    decreto = Column(String(100))
    fuente = Column(String(255))
    fecha_actualizacion = Column(DateTime, default=func.now())
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)


class Glaciar(Base):
    __tablename__ = "glaciares"
    __table_args__ = {"schema": "gis"}

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255))
    tipo = Column(String(100))
    cuenca = Column(String(255))
    subcuenca = Column(String(255))
    region = Column(String(100))
    superficie_km2 = Column(Numeric(10, 4))
    altitud_min_m = Column(Integer)
    altitud_max_m = Column(Integer)
    fuente = Column(String(255))
    fecha_actualizacion = Column(DateTime, default=func.now())
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)


class CuerpoAgua(Base):
    __tablename__ = "cuerpos_agua"
    __table_args__ = {"schema": "gis"}

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255))
    tipo = Column(String(100), nullable=False)
    cuenca = Column(String(255))
    subcuenca = Column(String(255))
    region = Column(String(100))
    es_sitio_ramsar = Column(Boolean, default=False)
    fuente = Column(String(255))
    fecha_actualizacion = Column(DateTime, default=func.now())
    geom = Column(Geometry("GEOMETRY", srid=4326), nullable=False)


class ComunidadIndigena(Base):
    __tablename__ = "comunidades_indigenas"
    __table_args__ = {"schema": "gis"}

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    pueblo = Column(String(100))
    tipo = Column(String(100))
    region = Column(String(100))
    comuna = Column(String(100))
    es_adi = Column(Boolean, default=False)
    nombre_adi = Column(String(255))
    fuente = Column(String(255))
    fecha_actualizacion = Column(DateTime, default=func.now())
    geom = Column(Geometry("GEOMETRY", srid=4326), nullable=False)


class CentroPoblado(Base):
    __tablename__ = "centros_poblados"
    __table_args__ = {"schema": "gis"}

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(100))
    region = Column(String(100))
    comuna = Column(String(100))
    poblacion = Column(Integer)
    fuente = Column(String(255))
    fecha_actualizacion = Column(DateTime, default=func.now())
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
