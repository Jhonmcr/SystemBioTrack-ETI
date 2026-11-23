# SUMMARY: Expone las funciones existentes del servicio de asistencia.
"""API pública de los servicios del backend."""

# Se reexportan únicamente los símbolos definidos por el servicio oficial.
from app.services.attendance_service import (
    Minutos_Desde_Medianoche,
    Procesar_Marcaje_En_Tiempo_Real,
)

# La lista explícita evita publicar referencias a servicios inexistentes.
__all__ = [
    "Minutos_Desde_Medianoche",
    "Procesar_Marcaje_En_Tiempo_Real",
]
