# SUMMARY: Reexporta los esquemas Pydantic para que los endpoints y servicios importen validaciones de forma centralizada.
from app.schemas.attendance import AttendanceReportFilters, AttendanceSummary  # Importa los esquemas relacionados con reportes de asistencia.
from app.schemas.hikvision import HikvisionEventPayload  # Importa el esquema del webhook de eventos Hikvision.
from app.schemas.user import UserCreate, UserRead  # Importa los esquemas para creación y lectura de usuarios.

__all__ = ["AttendanceReportFilters", "AttendanceSummary", "HikvisionEventPayload", "UserCreate", "UserRead"]  # Expone los contratos de validación de la API para uso global.
