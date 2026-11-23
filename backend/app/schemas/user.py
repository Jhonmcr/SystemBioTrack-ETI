# SUMMARY: Define contratos de usuario centrados en empleados y sin campos académicos.
"""Esquemas Pydantic para usuarios vinculados al personal institucional."""

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    """Summary: Valida los datos básicos requeridos para un usuario empleado."""

    # Se conservan los nombres HTTP existentes, pero solo con datos de personal.
    employee_no: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Número de empleado o identificación institucional.",
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del empleado.",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Apellido del empleado.",
    )
    is_active: bool = Field(
        default=True,
        description="Indica si el usuario está activo y habilitado para asistencia.",
    )


class UserRead(BaseModel):
    """Summary: Representa los datos de usuario de personal expuestos por la API."""

    # La configuración acepta entidades ORM y no incluye grado ni sección académica.
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_no: str
    first_name: str
    last_name: str
    is_active: bool
