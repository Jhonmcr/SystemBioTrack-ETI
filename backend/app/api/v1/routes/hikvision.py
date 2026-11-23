# SUMMARY: Implementa el receptor de eventos del lector Hikvision para evaluar asistencia y registrar los marcajes.
from __future__ import annotations  # Habilita tipado moderno para payloads HTTP y respuestas de la API.
from typing import Any  # Importa Any para devolver diccionarios con contenido din?mico en la respuesta.
from fastapi import APIRouter, Depends, HTTPException, status  # Importa los componentes HTTP de FastAPI para rutas y validaciones.
from sqlalchemy.orm import Session  # Importa Session para manejar la sesi?n de PostgreSQL dentro del endpoint.
from app.db.session import get_db  # Importa la dependencia de sesi?n de base de datos del proyecto.
from app.schemas.hikvision import HikvisionEventPayload  # Importa el esquema Pydantic del evento del lector biom?trico.
from app.services.attendance_service import parse_event_time, save_attendance_event  # Importa las funciones auxiliares para parsear tiempos y guardar asistencia.

router = APIRouter()  # Crea el router del dominio Hikvision para separar el webhook del resto de APIs.


@router.post("/hikvision/events", status_code=status.HTTP_200_OK)  # Define el endpoint receptor ISAPI del lector biom?trico Hikvision.
def receive_hikvision_event(payload: HikvisionEventPayload, db: Session = Depends(get_db)) -> dict[str, Any]:  # Recibe el payload del biom?trico y la sesi?n de base de datos.
    try:  # Intenta convertir el valor recibido del lector en un datetime v?lido.
        event_time = parse_event_time(payload.eventTime)  # Convierte la marca del lector a datetime para compararlo con el horario.
    except ValueError as exception:  # Captura errores de formato para responder con un error claro al cliente.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El eventTime no tiene un formato v?lido: {exception}") from exception  # Devuelve un error 400 con el detalle del formato incorrecto.
    try:  # Intenta guardar el evento en la base de datos usando la l?gica de negocio del m?dulo.
        attendance_record = save_attendance_event(db, payload.employeeNoString, event_time, payload.deviceId)  # Guarda la asistencia y devuelve el log persistido.
    except LookupError as exception:  # Captura errores cuando no existe usuario o horario configurado.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exception)) from exception  # Devuelve error 404 para se?alar datos faltantes.
    return {  # Devuelve respuesta JSON con la informaci?n del evento procesado.
        "message": "Hikvision event processed successfully.",  # Informa que el evento fue aceptado y registrado.
        "employeeNoString": payload.employeeNoString,  # Repite el identificador del usuario que report? el biom?trico.
        "eventTime": payload.eventTime,  # Expone la marca temporal original del lector para trazabilidad.
        "status": attendance_record.status.value,  # Devuelve el estado final calculado de asistencia.
        "attendance_id": attendance_record.id,  # Expone el identificador del registro de asistencia reci?n creado.
    }  # Cierra el diccionario con la respuesta del webhook.
