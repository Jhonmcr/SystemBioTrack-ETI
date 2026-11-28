# SUMMARY: Define los filtros y contratos de respuesta para estadísticas y exportaciones del dashboard.
"""Summary: Define los esquemas públicos de agregados estadísticos del Módulo 5."""

from datetime import date

from pydantic import BaseModel, Field, model_validator


class DashboardFilters(BaseModel):
    """Summary: Expone el rango de fechas y filtros aplicados al dashboard."""

    start_date: date
    end_date: date
    horario_id: int | None = Field(default=None, gt=0)
    cargo_id: int | None = Field(default=None, gt=0)


class DashboardMetrics(BaseModel):
    """Summary: Representa los indicadores principales de asistencia."""

    total_registros: int = Field(ge=0)
    asistencias_puntuales: int = Field(ge=0)
    inasistencias: int = Field(ge=0)
    tasa_ausentismo: float = Field(ge=0)
    total_retardos: int = Field(ge=0)
    ausencias_justificadas: int = Field(ge=0)


class DashboardSeriesPoint(BaseModel):
    """Summary: Agrupa los registros estadísticos diarios para los gráficos."""

    fecha: date
    asistencias_puntuales: int = Field(ge=0)
    retardos: int = Field(ge=0)
    inasistencias: int = Field(ge=0)


class DashboardCargoBreakdown(BaseModel):
    """Summary: Resume asistencia, inasistencias y tardanzas por cargo."""

    cargo_id: int
    cargo: str
    total_registros: int = Field(ge=0)
    inasistencias: int = Field(ge=0)
    tasa_ausentismo: float = Field(ge=0)
    retardos: int = Field(ge=0)


class DashboardAbsenceCause(BaseModel):
    """Summary: Expone el total aprobado agrupado por tipo de ausencia."""

    tipo_ausencia_id: int
    tipo_ausencia: str
    total: int = Field(ge=0)


class DashboardSummaryResponse(BaseModel):
    """Summary: Define el contrato agregado consumido por el dashboard."""

    filters: DashboardFilters
    metrics: DashboardMetrics
    series: list[DashboardSeriesPoint]
    por_cargo: list[DashboardCargoBreakdown]
    causas_ausencia: list[DashboardAbsenceCause]

    @model_validator(mode="after")
    def Validar_Rango_Filtros(self) -> "DashboardSummaryResponse":
        """Summary: Garantiza que el rango devuelto no esté invertido."""
        # La respuesta repite el contrato de entrada para auditar filtros exportados.
        if self.filters.start_date > self.filters.end_date:
            raise ValueError("start_date debe ser menor o igual que end_date.")
        return self
