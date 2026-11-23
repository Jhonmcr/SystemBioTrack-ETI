"""Summary: Reexporta los modelos ORM oficiales para su registro en la aplicación."""
"""Official ORM models mapped to ``base_de_datos.example.sql``."""

from app.db.models.official_models import (
    Ausencia,
    Asistencia_Diaria,
    Cargo,
    Empleado,
    Estatus_Asistencia,
    Horario,
    Marcaje_Crudo,
    Rol,
    TipoAusencia,
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
    "TipoAusencia",
    "Ausencia",
]
