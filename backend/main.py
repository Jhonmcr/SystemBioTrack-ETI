"""
=============================================================================
SUMMARY DEL MÓDULO
-----------------------------------------------------------------------------
Proyecto: Sistema de Control de Asistencia Biométrico (SystemBioTrack-ETI)
Módulo: Módulo 3 - Motor Biométrico y Asistencia (Core)
Responsables: Pablo y Jhon
Archivo: main.py
Descripción: Servidor principal FastAPI. Recepción y persistencia de eventos
             siguiendo la estructura estricta de base_de_datos.example.sql.
=============================================================================
"""

import os
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database import Obtener_Sesion_Db
from models import Marcaje_Crudo
from attendance_service import Procesar_Marcaje_En_Tiempo_Real

load_dotenv()

Ip_Biometrico_Autorizada = os.getenv("BIOMETRIC_IP", "127.0.0.1")

App_Principal = FastAPI(
    title="SystemBioTrack API - Core Biométrico",
    description="Receptor de eventos y motor de asistencia",
    version="1.0.0"
)

# ---------------------------------------------------------------------------
# ESQUEMAS PYDANTIC
# ---------------------------------------------------------------------------

class Evento_Detalle_Hikvision(BaseModel):
    deviceName: Optional[str] = Field(default=None)
    majorEventType: int = Field(...)
    subEventType: int = Field(...)
    employeeNoString: str = Field(...)
    attendanceStatus: str = Field(default="checkIn")
    verifyNo: Optional[int] = Field(default=1)


class Payload_Marcaje_Hikvision(BaseModel):
    ipAddress: Optional[str] = None
    dateTime: str = Field(...)
    eventType: str = Field(default="AccessControl")
    AccessControllerEvent: Evento_Detalle_Hikvision


# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@App_Principal.get("/api/v1/health")
def Verificar_Salud_Sistema():
    return {"Estado": "Operativo", "Modulo": "Módulo 3 - Asistencia"}


@App_Principal.post("/api/v1/biometric/event-listener", status_code=status.HTTP_201_CREATED)
async def Recibir_Marcaje_Biometrico(
    Datos_Evento: Payload_Marcaje_Hikvision,
    Peticion_Http: Request,
    Db_Sesion: Session = Depends(Obtener_Sesion_Db)
):
    """
    Webhook receptor: valida la IP, guarda el marcaje en marcaje_crudo
    y calcula la asistencia diaria según las tablas oficiales.
    """
    Ip_Cliente_Origen = Peticion_Http.client.host if Peticion_Http.client else "0.0.0.0"

    if Ip_Cliente_Origen not in [Ip_Biometrico_Autorizada, "127.0.0.1", "testclient"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"IP {Ip_Cliente_Origen} no autorizada."
        )

    Detalle_Acceso = Datos_Evento.AccessControllerEvent
    Identificador_Raw = Detalle_Acceso.employeeNoString
    Tipo_Marcaje = Detalle_Acceso.attendanceStatus

    # Extracción de solo dígitos para garantizar compatibilidad con INTEGER en PostgreSQL
    Solo_Digitos = "".join(filter(str.isdigit, Identificador_Raw))
    Id_Biometrico_Int = int(Solo_Digitos) if Solo_Digitos else 1

    try:
        Fecha_Hora_Parsed = datetime.fromisoformat(Datos_Evento.dateTime)
    except ValueError:
        Fecha_Hora_Parsed = datetime.now()

    # 1. Guardar en marcaje_crudo (estrictamente las 4 columnas oficiales del diagrama)
    Nuevo_Marcaje_Crudo = Marcaje_Crudo(
        id_empleado_biometrico=Id_Biometrico_Int,
        fecha_hora_marcaje=Fecha_Hora_Parsed,
        tipo_marcaje=Tipo_Marcaje
    )
    Db_Sesion.add(Nuevo_Marcaje_Crudo)
    Db_Sesion.commit()
    Db_Sesion.refresh(Nuevo_Marcaje_Crudo)

    # 2. Procesar cálculo de asistencia diaria
    Resultado_Motor = Procesar_Marcaje_En_Tiempo_Real(
        Id_Biometrico_Int=Id_Biometrico_Int,
        Fecha_Hora_Evento=Fecha_Hora_Parsed,
        Db_Sesion=Db_Sesion
    )

    return {
        "status": "success",
        "marcaje_crudo_id": Nuevo_Marcaje_Crudo.id,
        "id_empleado_biometrico": Id_Biometrico_Int,
        "calculo_asistencia": Resultado_Motor
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(App_Principal, host="127.0.0.1", port=8000)