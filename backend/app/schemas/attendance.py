# SUMMARY: Define los filtros, respuestas, marcajes por código y correcciones manuales de asistencia.
"""Esquemas Pydantic del módulo de asistencia de personal."""

from datetime import date, datetime, time

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class AttendanceReportFilters(BaseModel):
    """Summary: Representa los filtros públicos disponibles para reportes."""

    # empleado_id es el nombre institucional; student_id se acepta solo por compatibilidad.
    start_date: date | None = Field(
        default=None,
        description="Fecha inicial inclusiva del rango de reportes.",
    )
    end_date: date | None = Field(
        default=None,
        description="Fecha final inclusiva del rango de reportes.",
    )
    empleado_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("empleado_id", "student_id"),
        description="Identificador interno del empleado.",
    )
    status: str | None = Field(
        default=None,
        description="Identificador o nombre del estado de asistencia.",
    )
    horario_id: int | None = Field(
        default=None,
        gt=0,
        description="Identificador del horario asignado al empleado.",
    )
    turno: str | None = Field(
        default=None,
        description="Nombre de turno, por ejemplo matutino o vespertino.",
    )
    solo_retardos: bool = Field(
        default=False,
        description="Limita el reporte a registros con minutos de retraso.",
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


class AttendanceEmployeeResponse(BaseModel):
    """Summary: Expone los datos identificativos del empleado en un registro."""

    # Los datos se validan desde la relación ORM cargada por la consulta.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    apellido: str
    cedula: str


class AttendanceScheduleResponse(BaseModel):
    """Summary: Expone el horario o turno asignado al empleado."""

    # La relación ORM aporta tanto el identificador como el nombre institucional.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_horario: str


class AttendanceStatusResponse(BaseModel):
    """Summary: Expone el estado oficial asociado al registro diario."""

    # La relación refleja el catálogo oficial estatus_asistencia.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_estatus: str


class AttendanceRecordResponse(BaseModel):
    """Summary: Representa asistencia con datos personales, turno y métricas de jornada."""

    # Relaciones ORM ya cargadas evitan consultas al serializar cada registro.
    model_config = ConfigDict(from_attributes=True)

    id: int
    empleado_id: int
    fecha: date
    hora_entrada: time | None
    hora_salida: time | None
    minutos_tarde: int | None
    estatus_id: int
    modificado_manualmente: bool | None
    tipo_marcaje: str | None = None
    duracion_trabajada: str | None = None
    empleado: AttendanceEmployeeResponse
    horario: AttendanceScheduleResponse | None = None
    estatus: AttendanceStatusResponse


class AttendanceReportResponse(BaseModel):
    """Summary: Define la respuesta paginada como conjunto de filtros y registros."""

    # Cada elemento expone el esquema detallado compartido por los endpoints de reportes.
    message: str
    filters: dict[str, str | int | bool | None]
    items: list[AttendanceRecordResponse]


class AttendanceTardinessEmployeeSummary(BaseModel):
    """Summary: Resume los retardos y minutos acumulados de un empleado."""

    # Se conservan las mismas representaciones personales y de horario del detalle.
    empleado: AttendanceEmployeeResponse
    horario: AttendanceScheduleResponse
    total_retardos: int
    minutos_tarde_acumulados: int


class AttendanceTardinessResponse(BaseModel):
    """Summary: Define el resumen general y el detalle de retardos en un rango."""

    # El total acumulado general se puede cotejar con los resúmenes individuales.
    filters: dict[str, str | int | None]
    total_retardos: int
    minutos_tarde_acumulados: int
    empleados: list[AttendanceTardinessEmployeeSummary]
    items: list[AttendanceRecordResponse]


class AttendancePunchCodeRequest(BaseModel):
    """Summary: Valida la identidad del empleado y el timestamp de un marcaje manual."""

    # Se permite un solo identificador para resolver inequívocamente al empleado.
    codigo_empleado: str | None = Field(
        default=None,
        min_length=1,
        description="Código del empleado o su cédula.",
    )
    cedula: str | None = Field(
        default=None,
        min_length=1,
        description="Cédula registrada del empleado.",
    )
    id_empleado_biometrico: int | None = Field(
        default=None,
        gt=0,
        description="Identificador de empleado registrado en el sistema biométrico.",
    )
    fecha_hora: datetime | None = Field(
        default=None,
        description="Fecha y hora del marcaje; por omisión se usa la hora actual.",
    )

    @model_validator(mode="after")
    def Validar_Identificador_Unico(self) -> "AttendancePunchCodeRequest":
        """Summary: Rechaza solicitudes sin identificador o con más de uno."""
        # La entrada por teclado debe resolverse mediante exactamente un dato de identidad.
        Identificadores = (
            self.codigo_empleado,
            self.cedula,
            self.id_empleado_biometrico,
        )
        if sum(Identificador is not None for Identificador in Identificadores) != 1:
            raise ValueError("Provide exactly one employee identifier.")
        return self


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
