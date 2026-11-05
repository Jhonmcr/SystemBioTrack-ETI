# SUMMARY: Define los esquemas Pydantic para consultar reportes y resúmenes de asistencia según filtros de fecha, estudiante y estado.
from __future__ import annotations  # Permite anotaciones modernas para modelos de respuesta y filtros complejos.
from pydantic import BaseModel, Field  # Importa BaseModel y Field para validación de filtros y payloads de respuesta.


class AttendanceReportFilters(BaseModel):  # Define los filtros posibles para consultar reportes de asistencia.
    start_date: str | None = Field(default=None, description="Fecha inicial del rango de reportes.")  # Guarda la fecha inicial para filtrar por período.
    end_date: str | None = Field(default=None, description="Fecha final del rango de reportes.")  # Guarda la fecha final para filtrar por período.
    student_id: int | None = Field(default=None, description="Identificador del estudiante para filtrar por persona.")  # Guarda la referencia al estudiante si se desea filtrar por usuario.
    status: str | None = Field(default=None, description="Estado de asistencia a filtrar, por ejemplo PRESENTE o LLEGADA_TARDIA.")  # Guarda el estado de asistencia seleccionado.


class AttendanceSummary(BaseModel):  # Define el esquema de salida para un resumen de asistencia del día.
    date: str  # Guarda la fecha del resumen.
    total_present: int = Field(default=0, description="Cantidad total de usuarios presentes.")  # Guarda el número de asistencias en tiempo.
    total_late: int = Field(default=0, description="Cantidad total de llegadas tardías.")  # Guarda el número de llegadas tardías.
    total_absent: int = Field(default=0, description="Cantidad total de ausencias registradas.")  # Guarda el número de ausencias según la lógica de negocio.
    section: str | None = Field(default=None, description="Sección o grado agrupado en el resumen.")  # Guarda la agregación visual por sección o curso.
