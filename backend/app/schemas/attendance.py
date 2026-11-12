# SUMMARY: Define los filtros, respuestas y correcciones manuales de asistencia diaria.
"""Esquemas de entrada y salida compatibles con las entidades oficiales de asistencia."""

from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class AttendanceReportFilters(BaseModel):
    """Summary: Representa los filtros públicos disponibles para reportes."""

    # Se mantienen los nombres existentes para preservar los alias HTTP.
    start_date: date | None = Field(
        default=None,
        description="Fecha inicial inclusiva del rango de reportes.",
    )
    end_date: date | None = Field(
        default=None,
        description="Fecha final inclusiva del rango de reportes.",
    )
    student_id: int | None = Field(
        default=None,
        description="Identificador interno del empleado.",
    )
    status: str | None = Field(
        default=None,
        description="Identificador o nombre del estado de asistencia.",
    )


class AttendanceSummary(BaseModel):
    """Summary: Conserva el contrato agregado anterior para resúmenes de asistencia."""

    # Estos campos permanecen disponibles para consumidores existentes del paquete.
    date: str
    total_present: int = Field(
        default=0,
        description="Cantidad total de registros con asistencia a tiempo.",
    )
    total_late: int = Field(
        default=0,
        description="Cantidad total de registros de llegada retrasada.",
    )
    total_absent: int = Field(
        default=0,
        description="Cantidad total de ausencias registradas.",
    )
    section: str | None = Field(
        default=None,
        description="Sección o grado asociado al resumen.",
    )


class AttendanceEmployeeResponse(BaseModel):
    """Summary: Expone los datos identificativos del empleado en un registro."""

    # Los datos se validan desde la relación ORM cargada por la consulta.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    apellido: str


class AttendanceStatusResponse(BaseModel):
    """Summary: Expone el estado oficial asociado al registro diario."""

    # La relación refleja el catálogo oficial estatus_asistencia.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_estatus: str


class AttendanceRecordResponse(BaseModel):
    """Summary: Representa un registro diario con empleado y estado relacionados."""

    # Los nombres directos corresponden a columnas de asistencia_diaria.
    model_config = ConfigDict(from_attributes=True)

    id: int
    empleado_id: int
    fecha: date
    hora_entrada: time | None
    hora_salida: time | None
    minutos_tarde: int | None
    estatus_id: int
    modificado_manualmente: bool | None
    empleado: AttendanceEmployeeResponse
    estatus: AttendanceStatusResponse


class AttendanceUpdateRequest(BaseModel):
    """Summary: Valida los campos editables de una corrección manual de asistencia."""

    # Los campos opcionales permiten enviar únicamente las columnas que se corrigen.
    hora_entrada: time | None = Field(
        default=None,
        description="Nueva hora de entrada, o null para eliminarla.",
    )
    hora_salida: time | None = Field(
        default=None,
        description="Nueva hora de salida, o null para eliminarla.",
    )
    estatus_id: int | None = Field(
        default=None,
        gt=0,
        description="Identificador positivo de un estado oficial.",
    )
