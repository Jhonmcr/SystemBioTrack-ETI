# SUMMARY: Define el endpoint webhook del lector Hikvision para recibir eventos ISAPI y preparar la lógica de validación y persistencia.
from __future__ import annotations  # Activa tipado moderno para contratos HTTP y respuestas.
from typing import Any  # Importa Any para payloads de respuesta flexibles y no tipados estricto.
from fastapi import APIRouter, HTTPException, status  # Importa APIRouter y utilidades HTTP para el webhook.
from pydantic import BaseModel, Field  # Importa BaseModel y Field para definir la estructura del payload entrante.

router = APIRouter()  # Crea el router del dominio Hikvision para separar el webhook del resto de APIs.


class HikvisionEventPayload(BaseModel):  # Define el esquema base esperado por el lector biométrico para un evento.
    employeeNoString: str = Field(..., description="Número de empleado o identificador del usuario según el lector biométrico.")  # Guarda el valor de identificación del usuario en el evento.
    eventTime: str = Field(..., description="Marca de tiempo del evento en formato ISO o equivalente del dispositivo.")  # Guarda la hora del evento recibido desde el lector.
    deviceId: str | None = Field(default=None, description="Identificador opcional del dispositivo que emitió el evento.")  # Guarda la identidad del dispositivo si llega en el payload.


@router.post("/hikvision/events", status_code=status.HTTP_202_ACCEPTED)  # Define el endpoint receptor ISAPI del lector biométrico Hikvision.
def receive_hikvision_event(payload: HikvisionEventPayload) -> dict[str, Any]:  # Recibe el payload del biométrico y responde con estado de aceptación.
    if not payload.employeeNoString:  # Valida que venga el identificador del usuario para continuar.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="employeeNoString is required.")  # Retorna error claro si falta el identificador principal.
    return {"message": "Hikvision event received", "employeeNoString": payload.employeeNoString, "eventTime": payload.eventTime, "status": "accepted"}  # Responde confirmando que el evento fue leído y aceptado por el backend.
