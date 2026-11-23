"""Summary: Define contratos Pydantic para tipos, solicitudes y decisiones de ausencia."""

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EstadoAprobacion(str, Enum):
    """Summary: Enumera los estados de aprobación admitidos por el módulo."""

    Pendiente = "Pendiente"
    Aprobado = "Aprobado"
    Rechazado = "Rechazado"


class TipoAusenciaCreate(BaseModel):
    """Summary: Valida la creación de un tipo de ausencia."""

    nombre_tipo: str = Field(..., min_length=1, max_length=255)


class TipoAusenciaRead(BaseModel):
    """Summary: Expone los datos de un tipo de ausencia desde una entidad ORM."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_tipo: str


class AusenciaCreate(BaseModel):
    """Summary: Valida los datos de una nueva solicitud de ausencia."""

    empleado_id: int = Field(..., gt=0)
    tipo_ausencia_id: int = Field(..., gt=0)
    fecha_inicio: date
    fecha_fin: date
    descripcion: str | None = None

    @model_validator(mode="after")
    def Validar_Rango_Fechas(self) -> "AusenciaCreate":
        """Summary: Rechaza una solicitud cuya fecha final preceda a la inicial."""
        # El intervalo se valida antes de consultar o persistir la solicitud.
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin debe ser mayor o igual que fecha_inicio.")
        return self


class AusenciaDecision(BaseModel):
    """Summary: Valida una decisión final de aprobación o rechazo."""

    estado_aprobacion: Literal["Aprobado", "Rechazado"]


class AusenciaRead(BaseModel):
    """Summary: Expone una solicitud sin revelar rutas internas de sus adjuntos."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    empleado_id: int
    tipo_ausencia_id: int
    fecha_inicio: date
    fecha_fin: date
    descripcion: str | None
    estado_aprobacion: EstadoAprobacion
    aprobado_por_usuario_id: int | None
    fecha_solicitud: datetime | None
    tiene_archivo_pdf: bool


class AusenciaPage(BaseModel):
    """Summary: Representa una página de solicitudes y el total del filtro."""

    items: list[AusenciaRead]
    total: int
    limit: int
    offset: int
