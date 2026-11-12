# SUMMARY: Consulta y corrige registros diarios de asistencia con filtros por fecha, empleado y estado.
"""Rutas HTTP del módulo de asistencia diaria."""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.db.models import Asistencia_Diaria, Estatus_Asistencia
from app.db.session import get_db
from app.schemas.attendance import (
    AttendanceRecordResponse,
    AttendanceUpdateRequest,
)
from app.services.attendance_service import Procesar_Inasistencias_Diarias


Router_Asistencia = APIRouter()


@Router_Asistencia.post(
    "/attendance/close-day",
    summary="Cerrar el día de asistencia",
    description=(
        "Registra como inasistentes a los empleados que no tengan asistencia "
        "en la fecha indicada; si se omite, usa la fecha de hoy."
    ),
)
def close_attendance_day(
    Fecha_Objetivo: date = Query(
        default_factory=date.today,
        alias="fecha",
        description="Fecha objetivo del cierre diario, en formato YYYY-MM-DD.",
    ),
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, int | str]:
    """Summary: Cierra el día creando inasistencias para empleados sin registro."""
    # La fecha se delega al servicio, que evita duplicar registros existentes.
    return Procesar_Inasistencias_Diarias(Fecha_Objetivo, Db_Sesion)


def Serializar_Registro_Asistencia(
    Registro_Asistencia: Asistencia_Diaria,
) -> dict[str, Any]:
    """Summary: Convierte un registro ORM y sus relaciones a un diccionario JSON."""
    # La consulta debe cargar ambas relaciones para evitar accesos ORM fuera de sesión.
    return AttendanceRecordResponse.model_validate(
        Registro_Asistencia
    ).model_dump(mode="json")


@Router_Asistencia.get(
    "/attendance/today",
    summary="Consultar asistencias de hoy",
    description="Devuelve los registros diarios cuya fecha coincide con la fecha actual.",
)
def get_attendance_today(
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, Any]:
    """Summary: Consulta los registros de asistencia correspondientes al día actual."""
    # Se cargan empleado y estado en la consulta para serializar una respuesta completa.
    Fecha_Hoy = date.today()
    Registros_Asistencia = (
        Db_Sesion.query(Asistencia_Diaria)
        .options(
            joinedload(Asistencia_Diaria.empleado),
            joinedload(Asistencia_Diaria.estatus),
        )
        .filter(Asistencia_Diaria.fecha == Fecha_Hoy)
        .order_by(Asistencia_Diaria.id)
        .all()
    )
    return {
        "date": Fecha_Hoy.isoformat(),
        "items": [
            Serializar_Registro_Asistencia(Registro_Asistencia)
            for Registro_Asistencia in Registros_Asistencia
        ],
    }


@Router_Asistencia.get(
    "/attendance/reports",
    summary="Consultar reportes de asistencia",
    description=(
        "Filtra registros por rango inclusivo de fechas, empleado y estado "
        "identificado por ID o nombre."
    ),
)
def get_attendance_reports(
    Fecha_Inicio: date | None = Query(
        default=None,
        alias="start_date",
        description="Fecha inicial inclusiva del rango de reportes.",
    ),
    Fecha_Fin: date | None = Query(
        default=None,
        alias="end_date",
        description="Fecha final inclusiva del rango de reportes.",
    ),
    Id_Estudiante: int | None = Query(
        default=None,
        alias="student_id",
        description="Identificador interno del empleado.",
    ),
    Estatus: str | None = Query(
        default=None,
        alias="status",
        description="Identificador o nombre del estado de asistencia.",
    ),
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, Any]:
    """Summary: Genera registros de asistencia aplicando los filtros solicitados."""
    # Un rango invertido es una consulta inválida y se informa antes de acceder a datos.
    if Fecha_Inicio and Fecha_Fin and Fecha_Inicio > Fecha_Fin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be earlier than or equal to end_date.",
        )

    # Los filtros se aplican directamente a las columnas indexables del registro.
    Consulta_Asistencia = Db_Sesion.query(Asistencia_Diaria).options(
        joinedload(Asistencia_Diaria.empleado),
        joinedload(Asistencia_Diaria.estatus),
    )
    if Fecha_Inicio:
        Consulta_Asistencia = Consulta_Asistencia.filter(
            Asistencia_Diaria.fecha >= Fecha_Inicio
        )
    if Fecha_Fin:
        Consulta_Asistencia = Consulta_Asistencia.filter(
            Asistencia_Diaria.fecha <= Fecha_Fin
        )
    if Id_Estudiante is not None:
        Consulta_Asistencia = Consulta_Asistencia.filter(
            Asistencia_Diaria.empleado_id == Id_Estudiante
        )
    if Estatus:
        if Estatus.isdecimal():
            Consulta_Asistencia = Consulta_Asistencia.filter(
                Asistencia_Diaria.estatus_id == int(Estatus)
            )
        else:
            Consulta_Asistencia = Consulta_Asistencia.join(
                Asistencia_Diaria.estatus
            ).filter(
                func.lower(Estatus_Asistencia.nombre_estatus) == Estatus.lower()
            )

    # El orden estable simplifica el consumo y las pruebas de reportes.
    Registros_Asistencia = Consulta_Asistencia.order_by(
        Asistencia_Diaria.fecha,
        Asistencia_Diaria.id,
    ).all()
    return {
        "message": "Attendance reports generated",
        "filters": {
            "start_date": Fecha_Inicio.isoformat() if Fecha_Inicio else None,
            "end_date": Fecha_Fin.isoformat() if Fecha_Fin else None,
            "student_id": Id_Estudiante,
            "status": Estatus,
        },
        "items": [
            Serializar_Registro_Asistencia(Registro_Asistencia)
            for Registro_Asistencia in Registros_Asistencia
        ],
    }


@Router_Asistencia.patch(
    "/attendance/{asistencia_id}",
    summary="Corregir manualmente una asistencia",
    description=(
        "Actualiza hora_entrada, hora_salida o estatus_id y marca el registro "
        "como modificado manualmente."
    ),
)
def update_attendance(
    asistencia_id: int,
    Datos_Actualizacion: AttendanceUpdateRequest,
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, Any]:
    """Summary: Actualiza los campos permitidos y marca la edición como manual."""
    # La búsqueda usa la llave primaria oficial y responde 404 para IDs inexistentes.
    Registro_Asistencia = (
        Db_Sesion.query(Asistencia_Diaria)
        .options(
            joinedload(Asistencia_Diaria.empleado),
            joinedload(Asistencia_Diaria.estatus),
        )
        .filter(Asistencia_Diaria.id == asistencia_id)
        .first()
    )
    if not Registro_Asistencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found.",
        )

    # PATCH vacío no modifica columnas ni marca indebidamente el registro.
    Campos_Actualizados = Datos_Actualizacion.model_dump(exclude_unset=True)
    if not Campos_Actualizados:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one attendance field must be provided.",
        )

    # El ID de estado debe existir en el catálogo oficial antes de asignarlo.
    Id_Estatus = Campos_Actualizados.get("estatus_id")
    if Id_Estatus is not None:
        Estatus_Encontrado = (
            Db_Sesion.query(Estatus_Asistencia)
            .filter(Estatus_Asistencia.id == Id_Estatus)
            .first()
        )
        if not Estatus_Encontrado:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="estatus_id does not identify an existing attendance status.",
            )

    # Solo se asignan las columnas incluidas en el PATCH y después se confirma la edición.
    for Nombre_Campo, Valor_Campo in Campos_Actualizados.items():
        setattr(Registro_Asistencia, Nombre_Campo, Valor_Campo)
    Registro_Asistencia.modificado_manualmente = True
    Db_Sesion.commit()
    Db_Sesion.refresh(Registro_Asistencia)

    # Las relaciones refrescadas mantienen coherente la respuesta con las llaves foráneas.
    return Serializar_Registro_Asistencia(Registro_Asistencia)
