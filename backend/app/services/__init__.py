# SUMMARY: Expone la capa de servicios para que la app importe la lógica de negocio centralizada por dominio.
from app.services.attendance_service import get_attendance_reports, get_today_attendance_summary, save_attendance_event  # Importa las funciones reales de negocio que serán consumidas por la API.

attendance_summary_service = get_today_attendance_summary  # Alias de compatibilidad para exponer la función de resumen bajo el nombre esperado por el proyecto.

__all__ = ["attendance_summary_service", "get_today_attendance_summary", "get_attendance_reports", "save_attendance_event"]  # Publica los servicios del backend para uso en rutas y otros módulos.
