# SUMMARY: Consulta y agrega asistencia, tardanzas y permisos aprobados para el dashboard.
"""Summary: Implementa las estadísticas del Módulo 5 sobre los modelos oficiales."""

from datetime import date

from sqlalchemy import case, func
from sqlalchemy.orm import Query, Session

from app.db.models import (
    Asistencia_Diaria,
    Ausencia,
    Cargo,
    Empleado,
    Estatus_Asistencia,
    TipoAusencia,
)
from app.schemas.dashboard import (
    DashboardAbsenceCause,
    DashboardCargoBreakdown,
    DashboardFilters,
    DashboardMetrics,
    DashboardSeriesPoint,
    DashboardSummaryResponse,
)


def _Aplicar_Filtros_Asistencia(
    Consulta: Query,
    Fecha_Inicio: date,
    Fecha_Fin: date,
    Horario_Id: int | None,
    Cargo_Id: int | None,
) -> Query:
    """Summary: Aplica condiciones compartidas de fecha, horario y cargo."""
    # El JOIN explícito permite agrupar y filtrar asistencia por las entidades oficiales.
    Consulta_Filtrada = Consulta.filter(
        Asistencia_Diaria.fecha >= Fecha_Inicio,
        Asistencia_Diaria.fecha <= Fecha_Fin,
    )
    if Horario_Id is not None:
        Consulta_Filtrada = Consulta_Filtrada.filter(
            Empleado.horario_id == Horario_Id
        )
    if Cargo_Id is not None:
        Consulta_Filtrada = Consulta_Filtrada.filter(Empleado.cargo_id == Cargo_Id)
    return Consulta_Filtrada


def Obtener_Resumen_Dashboard(
    Db_Sesion: Session,
    Fecha_Inicio: date,
    Fecha_Fin: date,
    Horario_Id: int | None = None,
    Cargo_Id: int | None = None,
) -> DashboardSummaryResponse:
    """Summary: Calcula KPI, evolución diaria, distribución por cargo y causas."""
    # Los estados se comparan por nombre para no acoplar los cálculos a IDs semilla.
    Estatus_Normalizado = func.lower(func.trim(Estatus_Asistencia.nombre_estatus))
    Condicion_Inasistencia = Estatus_Normalizado == "inasistente"
    Condicion_Puntual = Estatus_Normalizado == "a tiempo"
    Condicion_Retardo = func.coalesce(Asistencia_Diaria.minutos_tarde, 0) > 0

    # El total de filas es el denominador solicitado para la tasa de ausentismo.
    Consulta_KPI = Db_Sesion.query(
        func.count(Asistencia_Diaria.id),
        func.coalesce(
            func.sum(case((Condicion_Puntual, 1), else_=0)),
            0,
        ),
        func.coalesce(
            func.sum(case((Condicion_Inasistencia, 1), else_=0)),
            0,
        ),
        func.coalesce(
            func.sum(case((Condicion_Retardo, 1), else_=0)),
            0,
        ),
    ).join(
        Empleado,
        Empleado.id == Asistencia_Diaria.empleado_id,
    ).join(
        Cargo,
        Cargo.id == Empleado.cargo_id,
    ).join(
        Estatus_Asistencia,
        Estatus_Asistencia.id == Asistencia_Diaria.estatus_id,
    )
    Consulta_KPI = _Aplicar_Filtros_Asistencia(
        Consulta_KPI,
        Fecha_Inicio,
        Fecha_Fin,
        Horario_Id,
        Cargo_Id,
    )
    Total_Registros, Total_Puntuales, Total_Inasistencias, Total_Retardos = (
        Consulta_KPI.one()
    )
    Tasa_Ausentismo = (
        round((Total_Inasistencias / Total_Registros) * 100, 2)
        if Total_Registros
        else 0.0
    )

    # La serie utiliza una fila por fecha para alimentar gráficos de tendencia.
    Consulta_Serie = Db_Sesion.query(
        Asistencia_Diaria.fecha,
        func.coalesce(func.sum(case((Condicion_Puntual, 1), else_=0)), 0),
        func.coalesce(func.sum(case((Condicion_Retardo, 1), else_=0)), 0),
        func.coalesce(func.sum(case((Condicion_Inasistencia, 1), else_=0)), 0),
    ).join(
        Empleado,
        Empleado.id == Asistencia_Diaria.empleado_id,
    ).join(
        Cargo,
        Cargo.id == Empleado.cargo_id,
    ).join(
        Estatus_Asistencia,
        Estatus_Asistencia.id == Asistencia_Diaria.estatus_id,
    )
    Consulta_Serie = _Aplicar_Filtros_Asistencia(
        Consulta_Serie,
        Fecha_Inicio,
        Fecha_Fin,
        Horario_Id,
        Cargo_Id,
    )
    Filas_Serie = (
        Consulta_Serie.group_by(Asistencia_Diaria.fecha)
        .order_by(Asistencia_Diaria.fecha)
        .all()
    )
    Serie = [
        DashboardSeriesPoint(
            fecha=Fecha,
            asistencias_puntuales=Puntuales or 0,
            retardos=Retardos or 0,
            inasistencias=Inasistencias or 0,
        )
        for Fecha, Puntuales, Retardos, Inasistencias in Filas_Serie
    ]

    # Cargo se une directamente a asistencia mediante empleado para mantener el filtro coherente.
    Consulta_Cargos = Db_Sesion.query(
        Cargo.id,
        Cargo.nombre_cargo,
        func.count(Asistencia_Diaria.id),
        func.coalesce(func.sum(case((Condicion_Inasistencia, 1), else_=0)), 0),
        func.coalesce(func.sum(case((Condicion_Retardo, 1), else_=0)), 0),
    ).join(
        Empleado,
        Empleado.cargo_id == Cargo.id,
    ).join(
        Asistencia_Diaria,
        Asistencia_Diaria.empleado_id == Empleado.id,
    ).join(
        Estatus_Asistencia,
        Estatus_Asistencia.id == Asistencia_Diaria.estatus_id,
    )
    Consulta_Cargos = _Aplicar_Filtros_Asistencia(
        Consulta_Cargos,
        Fecha_Inicio,
        Fecha_Fin,
        Horario_Id,
        Cargo_Id,
    )
    Filas_Cargos = (
        Consulta_Cargos.group_by(Cargo.id, Cargo.nombre_cargo)
        .order_by(Cargo.nombre_cargo)
        .all()
    )
    Por_Cargo = [
        DashboardCargoBreakdown(
            cargo_id=Cargo_Id_Fila,
            cargo=Nombre_Cargo,
            total_registros=Total_Cargo,
            inasistencias=Inasistencias_Cargo or 0,
            tasa_ausentismo=(
                round((Inasistencias_Cargo / Total_Cargo) * 100, 2)
                if Total_Cargo
                else 0.0
            ),
            retardos=Retardos_Cargo or 0,
        )
        for (
            Cargo_Id_Fila,
            Nombre_Cargo,
            Total_Cargo,
            Inasistencias_Cargo,
            Retardos_Cargo,
        ) in Filas_Cargos
    ]

    # Las solicitudes se incluyen si su periodo aprobado se solapa con el rango consultado.
    Consulta_Ausencias = Db_Sesion.query(
        TipoAusencia.id,
        TipoAusencia.nombre_tipo,
        func.count(Ausencia.id),
    ).join(
        Ausencia,
        Ausencia.tipo_ausencia_id == TipoAusencia.id,
    ).join(
        Empleado,
        Empleado.id == Ausencia.empleado_id,
    ).filter(
        func.lower(func.trim(Ausencia.estado_aprobacion)) == "aprobado",
        Ausencia.fecha_inicio <= Fecha_Fin,
        Ausencia.fecha_fin >= Fecha_Inicio,
    )
    if Horario_Id is not None:
        Consulta_Ausencias = Consulta_Ausencias.filter(
            Empleado.horario_id == Horario_Id
        )
    if Cargo_Id is not None:
        Consulta_Ausencias = Consulta_Ausencias.filter(Empleado.cargo_id == Cargo_Id)
    Filas_Ausencias = (
        Consulta_Ausencias.group_by(TipoAusencia.id, TipoAusencia.nombre_tipo)
        .order_by(TipoAusencia.nombre_tipo)
        .all()
    )
    Causas_Ausencia = [
        DashboardAbsenceCause(
            tipo_ausencia_id=Tipo_Id,
            tipo_ausencia=Nombre_Tipo,
            total=Total,
        )
        for Tipo_Id, Nombre_Tipo, Total in Filas_Ausencias
    ]
    Total_Ausencias_Justificadas = sum(Causa.total for Causa in Causas_Ausencia)

    return DashboardSummaryResponse(
        filters=DashboardFilters(
            start_date=Fecha_Inicio,
            end_date=Fecha_Fin,
            horario_id=Horario_Id,
            cargo_id=Cargo_Id,
        ),
        metrics=DashboardMetrics(
            total_registros=Total_Registros,
            asistencias_puntuales=Total_Puntuales or 0,
            inasistencias=Total_Inasistencias or 0,
            tasa_ausentismo=Tasa_Ausentismo,
            total_retardos=Total_Retardos or 0,
            ausencias_justificadas=Total_Ausencias_Justificadas,
        ),
        series=Serie,
        por_cargo=Por_Cargo,
        causas_ausencia=Causas_Ausencia,
    )
