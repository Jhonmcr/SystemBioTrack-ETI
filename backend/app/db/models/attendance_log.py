# SUMMARY: Define el modelo SQLAlchemy AttendanceLog para consolidar los eventos de asistencia del día y su estado final.
from __future__ import annotations  # Permite usar tipos avanzados y referencias a entidades relacionadas.
from datetime import datetime  # Importa datetime para registrar marcas horarias con precisión.
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String  # Importa columnas y enums usados por el registro de asistencia.
from sqlalchemy.orm import Mapped, mapped_column, relationship  # Importa API ORM declarativa y relaciones de SQLAlchemy.
from app.db.base import Base  # Importa Base para registrar la entidad en la metadata global.


class AttendanceStatus(str, Enum):  # Define el catálogo de estados permitidos para los registros de asistencia.
    PRESENTE = "PRESENTE"  # Marca acceso puntual según el horario del estudiante.
    LLEGADA_TARDIA = "LLEGADA_TARDIA"  # Marca acceso fuera de horario permitido y dentro del margen de tolerancia.
    AUSENTE = "AUSENTE"  # Marca ausencia cuando no existe ingreso o se descarta un registro.
    JUSTIFICADO = "JUSTIFICADO"  # Marca ausencia o tardanza con justificación autorizada.


class AttendanceLog(Base):  # Define la entidad consolidada para eventos de asistencia.
    __tablename__ = "attendance_logs"  # Establece el nombre de la tabla de registros horarios en PostgreSQL.

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)  # Guarda el identificador único del registro.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)  # Relaciona el registro con el estudiante o colaborador.
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)  # Guarda la marca temporal del evento de asistencia.
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus), nullable=False, index=True)  # Guarda el estado final del registro según la lógica de negocio.
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)  # Almacena el identificador del dispositivo que capturó el evento.

    user: Mapped["User"] = relationship(back_populates="attendances")  # Relaciona el registro hacia el usuario que pertenece al evento.
