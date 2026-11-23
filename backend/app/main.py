# SUMMARY: Inicializa la aplicación FastAPI, registra routers y centraliza el punto de entrada del backend modular.
"""Summary: Configura la aplicación FastAPI y registra los routers de la API v1."""

from fastapi import FastAPI  # Importa FastAPI para crear la instancia principal de la API.
from fastapi.middleware.cors import CORSMiddleware  # Habilita llamadas del frontend local a la API.
from app.api.v1.routes import Router_Asistencia, Router_Ausencias, Router_Hikvision, Router_Usuarios  # Importa los routers de cada dominio funcional.

app = FastAPI(title="SystemBioTrack ETI API", version="1.0.0", description="Backend modular para asistencia escolar y biometría.")  # Crea la instancia principal de FastAPI con metadata del proyecto.

# Se limita CORS al origen local de Vite y a los métodos/cabeceras usados por la API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(Router_Asistencia, prefix="/api/v1", tags=["attendance"])  # Registra los endpoints de consulta de asistencia bajo la versión v1.
app.include_router(Router_Ausencias, prefix="/api/v1", tags=["absences"])  # Registra los endpoints de permisos y justificativos bajo la versión v1.
app.include_router(Router_Usuarios, prefix="/api/v1", tags=["users"])  # Registra los endpoints de gestión local de usuarios bajo la versión v1.
app.include_router(Router_Hikvision, prefix="/api/v1", tags=["hikvision"])  # Registra el webhook de eventos biométricos bajo la versión v1.


@app.get("/health")  # Define endpoint de salud para verificar que la app responde correctamente.
def health_check() -> dict[str, str]:  # Retorna estado básico del servicio para monitoreo.
    """Summary: Devuelve el estado básico de salud del servicio."""
    return {"status": "ok", "service": "systembiotrack-api"}  # Devuelve un payload minimalista para validación operativa.
