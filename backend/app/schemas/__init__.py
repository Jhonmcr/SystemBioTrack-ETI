# SUMMARY: Reexporta los esquemas públicos de asistencia, Hikvision y usuarios.
"""API pública de esquemas Pydantic del backend."""

# Las rutas y consumidores externos importan los contratos desde este paquete.
from app.schemas.attendance import (
    AttendanceEmployeeResponse,
    AttendancePunchCodeRequest,
    AttendanceRecordResponse,
    AttendanceReportResponse,
    AttendanceReportFilters,
    AttendanceScheduleResponse,
    AttendanceStatusResponse,
    AttendanceSummary,
    AttendanceTardinessEmployeeSummary,
    AttendanceTardinessResponse,
    AttendanceUpdateRequest,
)
from app.schemas.hikvision import HikvisionEventPayload
from app.schemas.user import UserCreate, UserRead

# La lista explícita mantiene estable la superficie pública de esquemas.
__all__ = [
    "AttendanceReportFilters",
    "AttendanceSummary",
    "AttendanceEmployeeResponse",
    "AttendanceScheduleResponse",
    "AttendanceStatusResponse",
    "AttendanceRecordResponse",
    "AttendanceReportResponse",
    "AttendancePunchCodeRequest",
    "AttendanceTardinessEmployeeSummary",
    "AttendanceTardinessResponse",
    "AttendanceUpdateRequest",
    "HikvisionEventPayload",
    "UserCreate",
    "UserRead",
]
