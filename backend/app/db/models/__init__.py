# SUMMARY: Reexporta los ocho modelos ORM oficiales para su registro y uso en la aplicación.
"""Official ORM models mapped to ``base_de_datos.example.sql``."""

from app.db.models.official_models import (
    Asistencia_Diaria,
    Cargo,
    Empleado,
    Estatus_Asistencia,
    Horario,
    Marcaje_Crudo,
    Rol,
    Usuario,
)

__all__ = [
    "Rol",
    "Cargo",
    "Usuario",
    "Empleado",
    "Horario",
    "Estatus_Asistencia",
    "Marcaje_Crudo",
    "Asistencia_Diaria",
]
