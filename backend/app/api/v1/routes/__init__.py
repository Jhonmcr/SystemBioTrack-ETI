# SUMMARY: Reexporta los routers de la API v1 para incluirlos en la aplicación FastAPI central.
from app.api.v1.routes.attendance import router as attendance_router  # Importa el router de consultas de asistencia.
from app.api.v1.routes.hikvision import router as hikvision_router  # Importa el router del webhook ISAPI de Hikvision.
from app.api.v1.routes.users import router as users_router  # Importa el router de gestión local de usuarios.

__all__ = ["attendance_router", "hikvision_router", "users_router"]  # Publica los routers para registrar endpoints en main.py.
