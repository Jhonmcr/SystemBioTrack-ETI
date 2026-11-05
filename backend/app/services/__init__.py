# SUMMARY: Expone la capa de servicios para que la app importe la lógica de negocio centralizada por dominio.
from app.services.attendance_service import attendance_summary_service  # Importa el servicio base de resumen de asistencia.

__all__ = ["attendance_summary_service"]  # Publica los servicios del backend para uso en rutas y en otros dominios.
