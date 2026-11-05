"""
=============================================================================
SUMMARY DEL MÓDULO
-----------------------------------------------------------------------------
Proyecto: Sistema de Control de Asistencia Biométrico (SystemBioTrack-ETI)
Módulo: Módulo 3 - Motor Biométrico y Asistencia (Core)
Responsables: Pablo y Jhon
Archivo: models.py
Descripción: Modelos ORM homologados al 100% con el diagrama de base de datos
             institucional (base_de_datos.example.sql). id_empleado_biometrico
             definido estrictamente como Integer.
=============================================================================
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base_Entidad


class Horario(Base_Entidad):
    """Mapeo de la tabla horario del esquema oficial."""
    __tablename__ = "horario"

    id = Column(Integer, primary_key=True, index=True)
    nombre_horario = Column(String, nullable=False)
    hora_entrada_teorica = Column(Time, nullable=False)
    hora_salida_teorica = Column(Time, nullable=False)


class Empleado(Base_Entidad):
    """Mapeo de la tabla empleado del esquema oficial."""
    __tablename__ = "empleado"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    cedula = Column(String, nullable=False)
    id_empleado_biometrico = Column(Integer, nullable=False, unique=True, index=True)
    cargo_id = Column(Integer, ForeignKey("cargo.id"), nullable=False)
    horario_id = Column(Integer, ForeignKey("horario.id"), nullable=False)

    Relacion_Horario = relationship("Horario")


class Estatus_Asistencia(Base_Entidad):
    """Mapeo del catálogo estatus_asistencia del esquema oficial."""
    __tablename__ = "estatus_asistencia"

    id = Column(Integer, primary_key=True)
    nombre_estatus = Column(String, nullable=False)


class Marcaje_Crudo(Base_Entidad):
    """Mapeo estricto de la tabla marcaje_crudo del esquema oficial."""
    __tablename__ = "marcaje_crudo"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_empleado_biometrico = Column(Integer, ForeignKey("empleado.id_empleado_biometrico"), nullable=False)
    fecha_hora_marcaje = Column(DateTime, nullable=False)
    tipo_marcaje = Column(String, nullable=True)


class Asistencia_Diaria(Base_Entidad):
    """Mapeo estricto de la tabla asistencia_diaria del esquema oficial."""
    __tablename__ = "asistencia_diaria"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_entrada = Column(Time, nullable=True)
    hora_salida = Column(Time, nullable=True)
    minutos_tarde = Column(Integer, nullable=True, default=0)
    estatus_id = Column(Integer, ForeignKey("estatus_asistencia.id"), nullable=False)
    modificado_manualmente = Column(Boolean, default=False)

    Relacion_Empleado = relationship("Empleado")
    Relacion_Estatus = relationship("Estatus_Asistencia")