# SUMMARY: Define el payload Pydantic esperado por el receptor ISAPI de Hikvision para validar eventos biométricos antes del procesamiento.
from __future__ import annotations  # Activa soporte para tipos con Pydantic y definiciones modernas de modelos.
from pydantic import BaseModel, Field  # Importa BaseModel y Field para declarar estructuralmente los eventos entrantes.


class HikvisionEventPayload(BaseModel):  # Define la estructura del evento biométrico entrante del lector Hikvision.
    employeeNoString: str = Field(..., min_length=1, description="Número o identificador del empleado reportado por el lector.")  # Guarda el valor de employeeNoString enviado por el dispositivo.
    eventTime: str = Field(..., min_length=1, description="Marca de tiempo del evento en formato del lector o ISO 8601.")  # Guarda la fecha y hora del evento para evaluar el horario del usuario.
    deviceId: str | None = Field(default=None, description="Identificador del lector si el dispositivo lo envía en el payload.")  # Guarda el identificador del dispositivo cuando el evento lo incluye.
