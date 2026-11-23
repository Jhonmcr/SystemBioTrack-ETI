# SUMMARY: Implementa la consulta de asistencia del d?a y los reportes filtrados por rango, estudiante y estado.
from __future__ import annotations  # Habilita el uso de tipos modernos en la firma de endpoints de FastAPI.
from typing import Any  # Importa Any para devolver diccionarios con estructuras din?micas en la API.
from fastapi import APIRouter, Depends, Query, status  # Importa componentes de FastAPI para endpoints y validaci?n de query params.
from sqlalchemy.orm import Session  # Importa Session para consultar la base de datos dentro del endpoint.
from app.db.session import get_db  # Importa la dependencia de base de datos del proyecto.
from app.services.attendance_service import get_attendance_reports, get_today_attendance_summary  # Importa los servicios de asistencia requeridos por la API.

router = APIRouter()  # Crea el router espec?fico para consultar asistencia y reportes.


@router.get("/attendance/today", status_code=status.HTTP_200_OK)  # Define el endpoint para consultar la asistencia del d?a actual.
def get_attendance_today(db: Session = Depends(get_db)) -> dict[str, Any]:  # Recibe la sesi?n activa de base de datos para consultar registros del d?a.
    summary = get_today_attendance_summary(db)  # Obtiene el resumen del d?a actual agrupado por grado/secci?n.
    return {  # Devuelve la respuesta JSON con el resumen del d?a.
        "message": "Attendance summary loaded successfully.",  # Informa que el resumen fue generado correctamente.
        "items": summary,  # Expone el arreglo con resultados agrupados por grupo.
    }  # Cierra el diccionario de respuesta.


@router.get("/attendance/reports", status_code=status.HTTP_200_OK)  # Define el endpoint para consultar reportes filtrados por fechas, estudiante o estado.
def get_attendance_report(
    start_date: str | None = Query(default=None, description="Fecha inicial del rango del reporte."),  # Recibe la fecha inicial para filtrar rango de reportes.
    end_date: str | None = Query(default=None, description="Fecha final del rango del reporte."),  # Recibe la fecha final para filtrar rango de reportes.
    student_id: int | None = Query(default=None, description="Identificador del estudiante para filtrar su asistencia."),  # Recibe el estudiante espec?fico cuando se desea un filtro puntual.
    status: str | None = Query(default=None, description="Estado de asistencia: PRESENTE o LLEGADA_TARDIA."),  # Recibe el estado para filtrar los registros reportados.
    db: Session = Depends(get_db),  # Inyecta la sesi?n activa de PostgreSQL para ejecutar la consulta.
) -> dict[str, Any]:  # Define la respuesta con datos de reportes y filtros aplicados.
    report_rows = get_attendance_reports(db, start_date, end_date, student_id, status)  # Obtiene los registros filtrados por la l?gica del servicio.
    return {  # Devuelve el payload final del reporte solicitado.
        "message": "Attendance reports loaded successfully.",  # Informa que el reporte fue generado correctamente.
        "filters": {  # Repite los filtros aplicados para trazabilidad.
            "start_date": start_date,  # Expone la fecha inicial sobre la cual se filtr?.
            "end_date": end_date,  # Expone la fecha final sobre la cual se filtr?.
            "student_id": student_id,  # Expone el estudiante filtrado si exist?a.
            "status": status,  # Expone el estado filtrado si exist?a.
        },  # Cierra la estructura de filtros.
        "items": report_rows,  # Expone la lista de resultados del reporte.
    }  # Cierra el diccionario final del endpoint.
