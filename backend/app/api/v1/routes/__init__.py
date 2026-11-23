"""Summary: Reexporta los routers de la API v1 para la aplicación FastAPI central."""
from app.api.v1.routes.attendance import Router_Asistencia  # Importa el router de consultas de asistencia.
from app.api.v1.routes.absences import Router_Ausencias  # Importa el router de permisos y justificativos.
from app.api.v1.routes.hikvision import Router_Hikvision  # Importa el router del webhook ISAPI de Hikvision.
from app.api.v1.routes.users import Router_Usuarios  # Importa el router de gestión local de usuarios.

__all__ = ["Router_Asistencia", "Router_Ausencias", "Router_Hikvision", "Router_Usuarios"]  # Publica los routers para registrar endpoints en main.py.
