# SUMMARY: Mapea las ocho entidades oficiales del SQL institucional sobre la Base modular de SQLAlchemy.
"""SQLAlchemy models matching ``base_de_datos.example.sql``."""

from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Rol(Base):
    """Summary: Mapea el catálogo institucional de roles de usuario."""

    __tablename__ = "rol"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_rol: Mapped[str] = mapped_column(String, nullable=False)


class Cargo(Base):
    """Summary: Mapea los cargos asignables al personal institucional."""

    __tablename__ = "cargo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_cargo: Mapped[str] = mapped_column(String, nullable=False)


class Horario(Base):
    """Summary: Mapea horarios y horas teóricas de los turnos de trabajo."""

    __tablename__ = "horario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_horario: Mapped[str] = mapped_column(String, nullable=False)
    hora_entrada_teorica: Mapped[time] = mapped_column(Time, nullable=False)
    hora_salida_teorica: Mapped[time] = mapped_column(Time, nullable=False)


class Empleado(Base):
    """Summary: Mapea los datos personales, cargo, turno e identificación del empleado."""

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
    ausencias: Mapped[list["Ausencia"]] = relationship(back_populates="empleado")


class Usuario(Base):
    """Summary: Mapea cuentas de acceso relacionadas con empleados y roles."""

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
    ausencias_aprobadas: Mapped[list["Ausencia"]] = relationship(
        back_populates="aprobado_por"
    )


class TipoAusencia(Base):
    """Summary: Mapea el catálogo institucional de tipos de permisos y justificativos."""

    __tablename__ = "tipo_ausencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_tipo: Mapped[str] = mapped_column(String, nullable=False)

    ausencias: Mapped[list["Ausencia"]] = relationship(
        back_populates="tipo_ausencia"
    )


class Ausencia(Base):
    """Summary: Mapea solicitudes de permisos con sus fechas, estado y respaldo PDF."""

    __tablename__ = "ausencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    empleado_id: Mapped[int] = mapped_column(
        ForeignKey("empleado.id"), nullable=False
    )
    tipo_ausencia_id: Mapped[int] = mapped_column(
        ForeignKey("tipo_ausencia.id"), nullable=False
    )
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    archivo_pdf_ruta: Mapped[str | None] = mapped_column(String, nullable=True)
    estado_aprobacion: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default="Pendiente",
        server_default=text("'Pendiente'"),
    )
    aprobado_por_usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id"), nullable=True
    )
    fecha_solicitud: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    empleado: Mapped[Empleado] = relationship(back_populates="ausencias")
    tipo_ausencia: Mapped[TipoAusencia] = relationship(back_populates="ausencias")
    aprobado_por: Mapped[Usuario | None] = relationship(
        back_populates="ausencias_aprobadas"
    )

    @property
    def tiene_archivo_pdf(self) -> bool:
        """Summary: Indica si la solicitud tiene una referencia a un PDF adjunto."""
        # La API expone disponibilidad, no la ruta interna del sistema de archivos.
        return bool(self.archivo_pdf_ruta)


class Estatus_Asistencia(Base):
    """Summary: Mapea el catálogo oficial de estados diarios de asistencia."""

    __tablename__ = "estatus_asistencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_estatus: Mapped[str] = mapped_column(String, nullable=False)


class Marcaje_Crudo(Base):
    """Summary: Mapea marcajes biométricos o por código antes del cálculo diario."""

    # Un evento puede identificar al personal por reloj, llave interna o ambos.
    __tablename__ = "marcaje_crudo"
    __table_args__ = (
        CheckConstraint(
            "id_empleado_biometrico IS NOT NULL OR empleado_id IS NOT NULL",
            name="ck_marcaje_crudo_identificador_empleado",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_empleado_biometrico: Mapped[int | None] = mapped_column(
        ForeignKey("empleado.id_empleado_biometrico"), nullable=True
    )
    empleado_id: Mapped[int | None] = mapped_column(
        ForeignKey("empleado.id"), nullable=True
    )
    fecha_hora_marcaje: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tipo_marcaje: Mapped[str | None] = mapped_column(String, nullable=True)


class Asistencia_Diaria(Base):
    """Summary: Mapea el registro consolidado de asistencia de un empleado por fecha."""

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