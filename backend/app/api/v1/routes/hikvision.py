# SUMMARY: Recibe eventos ISAPI Hikvision, guarda el marcaje crudo y procesa la asistencia diaria.
"""Rutas HTTP del webhook biométrico Hikvision."""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.models import Marcaje_Crudo
from app.db.session import get_db
from app.schemas.hikvision import HikvisionEventPayload
from app.services.attendance_service import Procesar_Marcaje_En_Tiempo_Real


Router_Hikvision = APIRouter()


@Router_Hikvision.post(
    "/hikvision/events",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Procesar un evento biométrico de Hikvision",
    description=(
        "Persiste el marcaje crudo recibido y calcula la entrada, salida "
        "o rebote de asistencia diaria asociado."
    ),
)
def receive_hikvision_event(
    Datos_Evento: HikvisionEventPayload,
    Db_Sesion: Session = Depends(get_db),
) -> dict[str, Any]:
    """Summary: Persiste el evento validado y devuelve el resultado del motor."""
    # Se almacena primero el evento crudo, que también alimenta el filtro antirrebote.
    Nuevo_Marcaje = Marcaje_Crudo(
        id_empleado_biometrico=Datos_Evento.employeeNoString,
        fecha_hora_marcaje=Datos_Evento.eventTime,
        tipo_marcaje=None,
    )
    Db_Sesion.add(Nuevo_Marcaje)
    Db_Sesion.commit()
    Db_Sesion.refresh(Nuevo_Marcaje)

    # El servicio opera sobre los mismos identificador, timestamp y sesión persistidos.
    Resultado_Procesamiento = Procesar_Marcaje_En_Tiempo_Real(
        Id_Biometrico_Int=Datos_Evento.employeeNoString,
        Fecha_Hora_Evento=Datos_Evento.eventTime,
        Db_Sesion=Db_Sesion,
    )
    return {
        "status": "accepted",
        "marcaje_crudo_id": Nuevo_Marcaje.id,
        "id_empleado_biometrico": Datos_Evento.employeeNoString,
        "eventTime": Datos_Evento.eventTime.isoformat(),
        "calculo_asistencia": Resultado_Procesamiento,
    }
