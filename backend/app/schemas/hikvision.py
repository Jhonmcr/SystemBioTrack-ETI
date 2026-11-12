# SUMMARY: Valida eventos Hikvision directos y anidados del controlador de acceso.
"""Esquema de entrada para eventos biométricos ISAPI de Hikvision."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HikvisionEventPayload(BaseModel):
    """Summary: Normaliza el identificador y la fecha de un evento Hikvision."""

    # El dispositivo puede envolver los campos de identificación y tiempo.
    model_config = ConfigDict(extra="ignore")

    employeeNoString: int = Field(
        ...,
        gt=0,
        description="Identificador biométrico del empleado convertible a entero.",
    )
    eventTime: datetime = Field(
        ...,
        description="Fecha y hora del evento reportada por el dispositivo.",
    )
    deviceId: str | None = Field(
        default=None,
        description="Identificador opcional del dispositivo biométrico.",
    )

    @model_validator(mode="before")
    @classmethod
    def Normalizar_Evento_Anidado(cls, Payload: Any) -> Any:
        """Summary: Aplana AccessControllerEvent y normaliza aliases de fecha."""
        # Se conservan campos desconocidos fuera del modelo para admitir payloads ISAPI amplios.
        if not isinstance(Payload, dict):
            return Payload

        Datos_Normalizados = dict(Payload)
        Datos_Controlador = Payload.get("AccessControllerEvent")
        for Nombre_Fecha in ("eventTime", "dateTime"):
            if Nombre_Fecha in Payload:
                Datos_Normalizados["eventTime"] = Payload[Nombre_Fecha]
                break

        if isinstance(Datos_Controlador, dict):
            if "employeeNoString" not in Datos_Normalizados:
                Datos_Normalizados["employeeNoString"] = Datos_Controlador.get(
                    "employeeNoString"
                )
            if "eventTime" not in Datos_Normalizados:
                for Nombre_Fecha in ("eventTime", "dateTime"):
                    if Nombre_Fecha in Datos_Controlador:
                        Datos_Normalizados["eventTime"] = Datos_Controlador[
                            Nombre_Fecha
                        ]
                        break
        return Datos_Normalizados
