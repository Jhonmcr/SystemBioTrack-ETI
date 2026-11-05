# SUMMARY: Reexporta los modelos de la capa de persistencia para facilitar importaciones centralizadas en servicios y endpoints.
from app.db.models.user import User  # Importa el modelo principal de usuarios para registrar estudiantes o personal.
from app.db.models.schedule import Schedule  # Importa el modelo de horarios y reglas de asistencia.
from app.db.models.attendance_log import AttendanceLog  # Importa el modelo de registros de asistencia consolidada.

__all__ = ["User", "Schedule", "AttendanceLog"]  # Expone los modelos a la aplicación para inicialización y consultas.
