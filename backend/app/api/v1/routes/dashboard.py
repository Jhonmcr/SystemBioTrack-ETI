# SUMMARY: Expone el resumen estadístico y la exportación PDF/XLSX del Módulo 5.
"""Summary: Define los endpoints HTTP del dashboard estadístico."""

from datetime import date
from io import BytesIO
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import Obtener_Resumen_Dashboard
from app.services.report_export_service import (
    Generar_Reporte_PDF,
    Generar_Reporte_XLSX,
)

Router_Dashboard = APIRouter()


def _Resolver_Rango_Fechas(
    Fecha_Inicio: date | None,
    Fecha_Fin: date | None,
) -> tuple[date, date]:
    """Summary: Completa el rango opcional con el mes de la fecha final."""
    # Si el cliente omite ambas fechas, el dashboard muestra el mes actual hasta hoy.
    Fecha_Hoy = date.today()
    Fecha_Final = Fecha_Fin or Fecha_Hoy
    Fecha_Inicial = Fecha_Inicio or Fecha_Final.replace(day=1)
    if Fecha_Inicial > Fecha_Final:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date debe ser menor o igual que end_date.",
        )
    return Fecha_Inicial, Fecha_Final


@Router_Dashboard.get(
    "/dashboard/summary",
    response_model=DashboardSummaryResponse,
    summary="Consultar resumen estadístico del dashboard",
    description=(
        "Devuelve indicadores, evolución diaria, distribución por cargo y causas "
        "de ausencias aprobadas. Por omisión consulta el mes hasta la fecha actual."
    ),
)
def Obtener_Resumen_Estadistico(
    Fecha_Inicio: date | None = Query(default=None, alias="start_date"),
    Fecha_Fin: date | None = Query(default=None, alias="end_date"),
    Horario_Id: int | None = Query(default=None, alias="horario_id", gt=0),
    Cargo_Id: int | None = Query(default=None, alias="cargo_id", gt=0),
    Db_Sesion: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """Summary: Valida los filtros y entrega las estadísticas del rango solicitado."""
    # La normalización del rango se comparte con la exportación del mismo recurso.
    Fecha_Inicial, Fecha_Final = _Resolver_Rango_Fechas(Fecha_Inicio, Fecha_Fin)
    return Obtener_Resumen_Dashboard(
        Db_Sesion,
        Fecha_Inicial,
        Fecha_Final,
        Horario_Id,
        Cargo_Id,
    )


@Router_Dashboard.get(
    "/dashboard/export",
    summary="Exportar el resumen estadístico del dashboard",
    description=(
        "Genera el mismo resumen filtrado en PDF o XLSX. "
        "El parámetro format acepta pdf o xlsx."
    ),
)
def Exportar_Resumen_Dashboard(
    Formato: Literal["pdf", "xlsx"] = Query(..., alias="format"),
    Fecha_Inicio: date | None = Query(default=None, alias="start_date"),
    Fecha_Fin: date | None = Query(default=None, alias="end_date"),
    Horario_Id: int | None = Query(default=None, alias="horario_id", gt=0),
    Cargo_Id: int | None = Query(default=None, alias="cargo_id", gt=0),
    Db_Sesion: Session = Depends(get_db),
) -> StreamingResponse:
    """Summary: Genera y transmite el reporte estadístico en el formato solicitado."""
    # PDF y XLSX comparten consulta, filtros y contrato para no divergir en cifras.
    Fecha_Inicial, Fecha_Final = _Resolver_Rango_Fechas(Fecha_Inicio, Fecha_Fin)
    Resumen = Obtener_Resumen_Dashboard(
        Db_Sesion,
        Fecha_Inicial,
        Fecha_Final,
        Horario_Id,
        Cargo_Id,
    )

    # Cada formato declara su MIME type y nombre de descarga para el navegador.
    if Formato == "pdf":
        Archivo: BytesIO = Generar_Reporte_PDF(Resumen)
        Nombre_Archivo = (
            f"dashboard_{Fecha_Inicial.isoformat()}_{Fecha_Final.isoformat()}.pdf"
        )
        Media_Type = "application/pdf"
    else:
        Archivo = Generar_Reporte_XLSX(Resumen)
        Nombre_Archivo = (
            f"dashboard_{Fecha_Inicial.isoformat()}_{Fecha_Final.isoformat()}.xlsx"
        )
        Media_Type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    return StreamingResponse(
        Archivo,
        media_type=Media_Type,
        headers={"Content-Disposition": f'attachment; filename="{Nombre_Archivo}"'},
    )
