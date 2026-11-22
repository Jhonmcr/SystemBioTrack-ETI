# SUMMARY: Recibe eventos ISAPI Hikvision, guarda el marcaje crudo y procesa la asistencia diaria.
"""Rutas HTTP del webhook biométrico Hikvision."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.models import Marcaje_Crudo
from app.db.session import get_db
from app.schemas.hikvision import HikvisionEventPayload
from app.services.attendance_service import Procesar_Marcaje_En_Tiempo_Real


Router_Hikvision = APIRouter()


@Router_Hikvision.post(
    "/hikvision/events",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=None,
    summary="Procesar un evento biométrico de Hikvision",
    description=(
        "Persiste el marcaje crudo recibido y calcula la entrada, salida "
        "o rebote de asistencia diaria asociado."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Evento de sistema ignorado porque no contiene empleado."
        }
    },
)
def Recibir_Evento_Hikvision(
    Datos_Evento: HikvisionEventPayload,
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    """Summary: Procesa marcajes JSON y descarta eventos sin identificador de empleado."""
    if Datos_Evento.employeeNoString is None:
        # Los heartbeats no deben generar reintentos ni filas de marcaje.
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ignored", "reason": "evento_sin_empleado"},
        )
    if Datos_Evento.eventTime is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="eventTime is required when employeeNoString is valid.",
        )

    Tipo_Marcaje = {
        "finger": "huella",
        "pw": "codigo",
        "card": "tarjeta",
    }.get((Datos_Evento.currentVerifyMode or "").strip().lower(), "biometrico")

    # Se almacena primero el evento crudo, que también alimenta el filtro antirrebote.
    Nuevo_Marcaje = Marcaje_Crudo(
        id_empleado_biometrico=Datos_Evento.employeeNoString,
        fecha_hora_marcaje=Datos_Evento.eventTime,
        tipo_marcaje=Tipo_Marcaje,
    )
    Db_Sesion.add(Nuevo_Marcaje)
    Db_Sesion.commit()
    Db_Sesion.refresh(Nuevo_Marcaje)

    # El servicio opera sobre los mismos identificador, timestamp y sesión persistidos.
    Resultado_Procesamiento = Procesar_Marcaje_En_Tiempo_Real(
        Id_Biometrico_Int=Datos_Evento.employeeNoString,
        Fecha_Hora_Evento=Datos_Evento.eventTime,
        Db_Sesion=Db_Sesion,
        Tipo_Marcaje=Tipo_Marcaje,
    )
    return {
        "status": "accepted",
        "marcaje_crudo_id": Nuevo_Marcaje.id,
        "id_empleado_biometrico": Datos_Evento.employeeNoString,
        "eventTime": Datos_Evento.eventTime.isoformat(),
        "calculo_asistencia": Resultado_Procesamiento,
    }
