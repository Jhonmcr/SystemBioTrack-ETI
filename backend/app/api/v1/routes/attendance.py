# SUMMARY: Expone consultas, marcajes por código y gestión de asistencia del personal.
"""Rutas HTTP del módulo de asistencia de empleados."""

from datetime import date, datetime, time, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Query as SQLQuery
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    Asistencia_Diaria,
    Empleado,
    Estatus_Asistencia,
    Horario,
    Marcaje_Crudo,
)
from app.db.session import get_db
from app.schemas.attendance import (
    AttendancePunchCodeRequest,
    AttendanceRecordResponse,
    AttendanceReportResponse,
    AttendanceScheduleResponse,
    AttendanceTardinessResponse,
    AttendanceUpdateRequest,
)
from app.services.attendance_service import (
    Procesar_Inasistencias_Diarias,
    Procesar_Marcaje_En_Tiempo_Real,
)


Router_Asistencia = APIRouter()


def Aplicar_Filtro_Horario(
    Consulta: SQLQuery[Any],
    Horario_Id: int | None,
    Turno: str | None,
) -> SQLQuery[Any]:
    """Summary: Filtra consultas de asistencia por horario asignado o nombre de turno."""
    # Los nombres institucionales comunes se equiparan con las etiquetas mañana y tarde.
    if Horario_Id is not None or Turno:
        Consulta = Consulta.join(Asistencia_Diaria.empleado)
    if Horario_Id is not None:
        Consulta = Consulta.filter(Empleado.horario_id == Horario_Id)
    if Turno:
        Consulta = Consulta.join(Empleado.horario)
        Turno_Normalizado = Turno.strip().casefold()
        if Turno_Normalizado in {"matutino", "mañana", "manana"}:
            Nombres_Turno = ("matutino", "mañana", "manana")
        elif Turno_Normalizado in {"vespertino", "tarde"}:
            Nombres_Turno = ("vespertino", "tarde")
        else:
            Nombres_Turno = (Turno_Normalizado,)
        Condiciones_Turno = [
            func.lower(Horario.nombre_horario).contains(Nombre_Turno)
            for Nombre_Turno in Nombres_Turno
        ]
        Consulta = Consulta.filter(or_(*Condiciones_Turno))
    return Consulta


def Serializar_Registro_Asistencia(
    Registro_Asistencia: Asistencia_Diaria,
    Db_Sesion: Session,
) -> dict[str, Any]:
    """Summary: Convierte un registro ORM y agrega horario, método y duración trabajada."""
    # La hora inicial del día identifica el método que originó el registro consolidado.
    Respuesta = AttendanceRecordResponse.model_validate(
        Registro_Asistencia
    ).model_dump(mode="json")
    Empleado_Asistencia = Registro_Asistencia.empleado
    Respuesta["horario"] = AttendanceScheduleResponse.model_validate(
        Empleado_Asistencia.horario
    ).model_dump(mode="json")
    Inicio_Dia = datetime.combine(Registro_Asistencia.fecha, time.min)
    Fin_Dia = Inicio_Dia + timedelta(days=1)
    Condiciones_Marcaje = [Marcaje_Crudo.empleado_id == Empleado_Asistencia.id]
    if Empleado_Asistencia.id_empleado_biometrico is not None:
        Condiciones_Marcaje.append(
            Marcaje_Crudo.id_empleado_biometrico
            == Empleado_Asistencia.id_empleado_biometrico
        )
    Marcaje_Inicial = (
        Db_Sesion.query(Marcaje_Crudo)
        .filter(
            or_(*Condiciones_Marcaje),
            Marcaje_Crudo.fecha_hora_marcaje >= Inicio_Dia,
            Marcaje_Crudo.fecha_hora_marcaje < Fin_Dia,
        )
        .order_by(Marcaje_Crudo.fecha_hora_marcaje, Marcaje_Crudo.id)
        .first()
    )
    Respuesta["tipo_marcaje"] = (
        Marcaje_Inicial.tipo_marcaje if Marcaje_Inicial else None
    )

    if Registro_Asistencia.hora_entrada and Registro_Asistencia.hora_salida:
        Inicio_Jornada = datetime.combine(
            Registro_Asistencia.fecha,
            Registro_Asistencia.hora_entrada,
        )
        Fin_Jornada = datetime.combine(
            Registro_Asistencia.fecha,
            Registro_Asistencia.hora_salida,
        )
        if Fin_Jornada < Inicio_Jornada:
            Fin_Jornada += timedelta(days=1)
        Respuesta["duracion_trabajada"] = str(Fin_Jornada - Inicio_Jornada)
    return Respuesta


@Router_Asistencia.post(
    "/attendance/close-day",
    summary="Cerrar el día de asistencia",
    description=(
        "Operación de gestión para los roles Superadmin, Administrador o Dirección. "
        "Crea inasistencias para empleados "
        "sin asistencia en la fecha y, si se indica horario_id, solo para ese turno."
    ),
)
def Cerrar_Dia_Asistencia(
    Fecha_Objetivo: date = Query(
        default_factory=date.today,
        alias="fecha",
        description="Fecha objetivo del cierre diario, en formato YYYY-MM-DD.",
    ),
    Horario_Id: int | None = Query(
        default=None,
        alias="horario_id",
        gt=0,
        description="Limita el cierre a los empleados asignados a este horario.",
    ),
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, int | str]:
    """Summary: Cierra el día creando inasistencias para empleados del horario elegido."""
    # Un horario inválido se comunica en lugar de producir un cierre aparentemente exitoso.
    if Horario_Id is not None and not Db_Sesion.query(Horario.id).filter(
        Horario.id == Horario_Id
    ).first():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="horario_id does not identify an existing schedule.",
        )
    return Procesar_Inasistencias_Diarias(
        Fecha_Objetivo,
        Db_Sesion,
        Horario_Id=Horario_Id,
    )


@Router_Asistencia.post(
    "/attendance/punch-code",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Registrar asistencia mediante código",
    description=(
        "Registra un marcaje manual con código o cédula y aplica el mismo "
        "antirrebote, tolerancia y cálculo de entrada/salida que el webhook biométrico."
    ),
)
def Registrar_Marcaje_Por_Codigo(
    Datos_Marcaje: AttendancePunchCodeRequest,
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, Any]:
    """Summary: Persiste un marcaje tipo codigo y ejecuta el motor común de asistencia."""
    # El código acepta cédula o ID biométrico, mientras que los campos explícitos no son ambiguos.
    if Datos_Marcaje.cedula:
        Empleado_Encontrado = (
            Db_Sesion.query(Empleado)
            .filter(Empleado.cedula == Datos_Marcaje.cedula)
            .first()
        )
    elif Datos_Marcaje.id_empleado_biometrico is not None:
        Empleado_Encontrado = (
            Db_Sesion.query(Empleado)
            .filter(
                Empleado.id_empleado_biometrico
                == Datos_Marcaje.id_empleado_biometrico
            )
            .first()
        )
    else:
        Codigo_Empleado = Datos_Marcaje.codigo_empleado
        Condiciones_Identificador = [Empleado.cedula == Codigo_Empleado]
        if Codigo_Empleado and Codigo_Empleado.isdecimal():
            Condiciones_Identificador.append(
                Empleado.id_empleado_biometrico == int(Codigo_Empleado)
            )
        Empleado_Encontrado = (
            Db_Sesion.query(Empleado)
            .filter(or_(*Condiciones_Identificador))
            .first()
        )
    if not Empleado_Encontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found for the supplied identifier.",
        )
    Fecha_Hora_Evento = Datos_Marcaje.fecha_hora or datetime.now()
    Nuevo_Marcaje = Marcaje_Crudo(
        id_empleado_biometrico=Empleado_Encontrado.id_empleado_biometrico,
        empleado_id=Empleado_Encontrado.id,
        fecha_hora_marcaje=Fecha_Hora_Evento,
        tipo_marcaje="codigo",
    )
    Db_Sesion.add(Nuevo_Marcaje)
    Db_Sesion.commit()
    Db_Sesion.refresh(Nuevo_Marcaje)
    Resultado_Procesamiento = Procesar_Marcaje_En_Tiempo_Real(
        Id_Biometrico_Int=Empleado_Encontrado.id_empleado_biometrico,
        Fecha_Hora_Evento=Fecha_Hora_Evento,
        Db_Sesion=Db_Sesion,
        Empleado_Id=Empleado_Encontrado.id,
    )
    return {
        "status": "accepted",
        "marcaje_crudo_id": Nuevo_Marcaje.id,
        "empleado_id": Empleado_Encontrado.id,
        "fecha_hora": Fecha_Hora_Evento.isoformat(),
        "tipo_marcaje": Nuevo_Marcaje.tipo_marcaje,
        "calculo_asistencia": Resultado_Procesamiento,
    }


@Router_Asistencia.get(
    "/attendance/today",
    summary="Consultar asistencias de hoy",
    description=(
        "Devuelve los registros diarios de hoy, con el nombre del horario "
        "asignado y filtros opcionales horario_id o turno."
    ),
)
def Obtener_Asistencia_Hoy(
    Horario_Id: int | None = Query(
        default=None,
        alias="horario_id",
        gt=0,
        description="ID del horario.",
    ),
    Turno: str | None = Query(
        default=None,
        alias="turno",
        min_length=1,
        description="Nombre de turno, por ejemplo matutino o vespertino.",
    ),
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, Any]:
    """Summary: Consulta los registros de hoy aplicando filtros opcionales de turno."""
    # Empleado y horario se cargan juntos para que toda fila incluya el nombre del turno.
    Fecha_Hoy = date.today()
    Consulta_Asistencia = Db_Sesion.query(Asistencia_Diaria).options(
        joinedload(Asistencia_Diaria.empleado).joinedload(Empleado.horario),
        joinedload(Asistencia_Diaria.estatus),
    )
    Consulta_Asistencia = Aplicar_Filtro_Horario(
        Consulta_Asistencia,
        Horario_Id,
        Turno,
    )
    Registros_Asistencia = (
        Consulta_Asistencia.filter(Asistencia_Diaria.fecha == Fecha_Hoy)
        .order_by(Asistencia_Diaria.id)
        .all()
    )
    return {
        "date": Fecha_Hoy.isoformat(),
        "items": [
            Serializar_Registro_Asistencia(Registro_Asistencia, Db_Sesion)
            for Registro_Asistencia in Registros_Asistencia
        ],
    }


def Obtener_Registros_Reporte(
    Db_Sesion: Session,
    Fecha_Inicio: date | None,
    Fecha_Fin: date | None,
    Empleado_Id: int | None,
    Estatus: str | None,
    Horario_Id: int | None,
    Turno: str | None,
    Solo_Retardos: bool,
) -> list[Asistencia_Diaria]:
    """Summary: Ejecuta las condiciones comunes de fecha, empleado, estado y horario."""
    # Esta consulta compartida mantiene coherentes el reporte general y el de retardos.
    Consulta_Asistencia = Db_Sesion.query(Asistencia_Diaria).options(
        joinedload(Asistencia_Diaria.empleado).joinedload(Empleado.horario),
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
    if Empleado_Id is not None:
        Consulta_Asistencia = Consulta_Asistencia.filter(
            Asistencia_Diaria.empleado_id == Empleado_Id
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
    Consulta_Asistencia = Aplicar_Filtro_Horario(
        Consulta_Asistencia,
        Horario_Id,
        Turno,
    )
    if Solo_Retardos:
        Consulta_Asistencia = Consulta_Asistencia.filter(
            Asistencia_Diaria.minutos_tarde > 0
        )
    return Consulta_Asistencia.order_by(
        Asistencia_Diaria.fecha,
        Asistencia_Diaria.id,
    ).all()


@Router_Asistencia.get(
    "/attendance/reports",
    response_model=AttendanceReportResponse,
    summary="Consultar reportes de asistencia",
    description=(
        "Filtra registros por rango de fechas, empleado, estado y horario; "
        "student_id se conserva como alias secundario de empleado_id."
    ),
)
def Obtener_Reportes_Asistencia(
    Fecha_Inicio: date | None = Query(default=None, alias="start_date"),
    Fecha_Fin: date | None = Query(default=None, alias="end_date"),
    Empleado_Id: int | None = Query(default=None, alias="empleado_id", gt=0),
    Student_Id: int | None = Query(
        default=None,
        alias="student_id",
        gt=0,
        description="Alias de compatibilidad; usar empleado_id.",
    ),
    Estatus: str | None = Query(default=None, alias="status"),
    Horario_Id: int | None = Query(default=None, alias="horario_id", gt=0),
    Turno: str | None = Query(default=None, alias="turno", min_length=1),
    Solo_Retardos: bool = Query(
        default=False,
        alias="solo_retardos",
    ),
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, Any]:
    """Summary: Genera reportes detallados y aplica filtros de personal y turnos."""
    # Dos nombres de empleado simultáneos solo son válidos si contienen el mismo ID.
    if (
        Empleado_Id is not None
        and Student_Id is not None
        and Empleado_Id != Student_Id
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="empleado_id and student_id must identify the same employee.",
        )
    Empleado_Filtro = Empleado_Id if Empleado_Id is not None else Student_Id
    if Fecha_Inicio and Fecha_Fin and Fecha_Inicio > Fecha_Fin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be earlier than or equal to end_date.",
        )
    Registros_Asistencia = Obtener_Registros_Reporte(
        Db_Sesion,
        Fecha_Inicio,
        Fecha_Fin,
        Empleado_Filtro,
        Estatus,
        Horario_Id,
        Turno,
        Solo_Retardos,
    )
    return {
        "message": "Attendance reports generated",
        "filters": {
            "start_date": Fecha_Inicio.isoformat() if Fecha_Inicio else None,
            "end_date": Fecha_Fin.isoformat() if Fecha_Fin else None,
            "empleado_id": Empleado_Filtro,
            "student_id": Empleado_Filtro,
            "status": Estatus,
            "horario_id": Horario_Id,
            "turno": Turno,
            "solo_retardos": Solo_Retardos,
        },
        "items": [
            Serializar_Registro_Asistencia(Registro_Asistencia, Db_Sesion)
            for Registro_Asistencia in Registros_Asistencia
        ],
    }


@Router_Asistencia.get(
    "/attendance/reports/tardiness",
    response_model=AttendanceTardinessResponse,
    summary="Consultar retardos de empleados",
    description=(
        "Devuelve el detalle de retardos y el acumulado por empleado en el "
        "rango indicado, con filtro opcional por horario_id."
    ),
)
def Obtener_Reporte_Retardos(
    Fecha_Inicio: date | None = Query(default=None, alias="start_date"),
    Fecha_Fin: date | None = Query(default=None, alias="end_date"),
    Horario_Id: int | None = Query(default=None, alias="horario_id", gt=0),
    Turno: str | None = Query(default=None, alias="turno", min_length=1),
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, Any]:
    """Summary: Resume número y minutos de retardos por empleado para un rango."""
    # El endpoint usa el mismo orden y definición de tardanza que el reporte general.
    if Fecha_Inicio and Fecha_Fin and Fecha_Inicio > Fecha_Fin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be earlier than or equal to end_date.",
        )
    Registros_Retrasados = Obtener_Registros_Reporte(
        Db_Sesion,
        Fecha_Inicio,
        Fecha_Fin,
        None,
        None,
        Horario_Id,
        Turno,
        True,
    )
    Resumen_Por_Empleado: dict[int, dict[str, Any]] = {}
    for Registro_Asistencia in Registros_Retrasados:
        Resumen_Empleado = Resumen_Por_Empleado.setdefault(
            Registro_Asistencia.empleado_id,
            {
                "empleado": {
                    "id": Registro_Asistencia.empleado.id,
                    "nombre": Registro_Asistencia.empleado.nombre,
                    "apellido": Registro_Asistencia.empleado.apellido,
                    "cedula": Registro_Asistencia.empleado.cedula,
                },
                "horario": {
                    "id": Registro_Asistencia.empleado.horario.id,
                    "nombre_horario": (
                        Registro_Asistencia.empleado.horario.nombre_horario
                    ),
                },
                "total_retardos": 0,
                "minutos_tarde_acumulados": 0,
            },
        )
        Resumen_Empleado["total_retardos"] += 1
        Resumen_Empleado["minutos_tarde_acumulados"] += (
            Registro_Asistencia.minutos_tarde or 0
        )
    return {
        "filters": {
            "start_date": Fecha_Inicio.isoformat() if Fecha_Inicio else None,
            "end_date": Fecha_Fin.isoformat() if Fecha_Fin else None,
            "horario_id": Horario_Id,
            "turno": Turno,
        },
        "total_retardos": len(Registros_Retrasados),
        "minutos_tarde_acumulados": sum(
            Registro_Asistencia.minutos_tarde or 0
            for Registro_Asistencia in Registros_Retrasados
        ),
        "empleados": list(Resumen_Por_Empleado.values()),
        "items": [
            Serializar_Registro_Asistencia(Registro_Asistencia, Db_Sesion)
            for Registro_Asistencia in Registros_Retrasados
        ],
    }


@Router_Asistencia.patch(
    "/attendance/{asistencia_id}",
    summary="Corregir manualmente una asistencia",
    description=(
        "Operación de gestión para los roles Superadmin, Administrador o Dirección. "
        "Actualiza horas o estatus y "
        "marca el registro como modificado manualmente."
    ),
)
def Actualizar_Asistencia(
    asistencia_id: int,
    Datos_Actualizacion: AttendanceUpdateRequest,
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, Any]:
    """Summary: Corrige campos permitidos y marca la edición como manual."""
    # La búsqueda usa la llave primaria oficial y carga horario para la respuesta.
    Registro_Asistencia = (
        Db_Sesion.query(Asistencia_Diaria)
        .options(
            joinedload(Asistencia_Diaria.empleado).joinedload(Empleado.horario),
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
    if Id_Estatus is not None and not Db_Sesion.query(Estatus_Asistencia).filter(
        Estatus_Asistencia.id == Id_Estatus
    ).first():
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
    return Serializar_Registro_Asistencia(Registro_Asistencia, Db_Sesion)
