# SUMMARY: Mapea las ocho entidades oficiales del SQL institucional sobre la Base modular de SQLAlchemy.
"""SQLAlchemy models matching ``base_de_datos.example.sql``."""

from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Rol(Base):
    __tablename__ = "rol"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_rol: Mapped[str] = mapped_column(String, nullable=False)


class Cargo(Base):
    __tablename__ = "cargo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_cargo: Mapped[str] = mapped_column(String, nullable=False)


class Horario(Base):
    __tablename__ = "horario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_horario: Mapped[str] = mapped_column(String, nullable=False)
    hora_entrada_teorica: Mapped[time] = mapped_column(Time, nullable=False)
    hora_salida_teorica: Mapped[time] = mapped_column(Time, nullable=False)


class Empleado(Base):
    __tablename__ = "empleado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    apellido: Mapped[str] = mapped_column(String, nullable=False)
    cedula: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    id_empleado_biometrico: Mapped[int | None] = mapped_column(
        Integer, unique=True, nullable=True
    )
    cargo_id: Mapped[int] = mapped_column(ForeignKey("cargo.id"), nullable=False)
    horario_id: Mapped[int] = mapped_column(ForeignKey("horario.id"), nullable=False)

    cargo: Mapped[Cargo] = relationship()
    horario: Mapped[Horario] = relationship()


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    empleado_id: Mapped[int] = mapped_column(
        ForeignKey("empleado.id"), nullable=False, unique=True
    )
    correo: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    contrasena_hash: Mapped[str] = mapped_column(String, nullable=False)
    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.id"), nullable=False)

    empleado: Mapped[Empleado] = relationship()
    rol: Mapped[Rol] = relationship()


class Estatus_Asistencia(Base):
    __tablename__ = "estatus_asistencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_estatus: Mapped[str] = mapped_column(String, nullable=False)


class Marcaje_Crudo(Base):
    __tablename__ = "marcaje_crudo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_empleado_biometrico: Mapped[int] = mapped_column(
        ForeignKey("empleado.id_empleado_biometrico"), nullable=False
    )
    fecha_hora_marcaje: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tipo_marcaje: Mapped[str | None] = mapped_column(String, nullable=True)


class Asistencia_Diaria(Base):
    __tablename__ = "asistencia_diaria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleado.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora_entrada: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_salida: Mapped[time | None] = mapped_column(Time, nullable=True)
    minutos_tarde: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estatus_id: Mapped[int] = mapped_column(
        ForeignKey("estatus_asistencia.id"), nullable=False
    )
    modificado_manualmente: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, server_default=text("false")
    )

    empleado: Mapped[Empleado] = relationship()
    estatus: Mapped[Estatus_Asistencia] = relationship()