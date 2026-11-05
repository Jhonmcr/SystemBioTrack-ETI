# SUMMARY: Define los contratos Pydantic de entrada y salida para el registro y consulta de usuarios del sistema escolar.
from __future__ import annotations  # Permite usar tipos modernos con validación de FastAPI/Pydantic sin conflictos de compatibilidad.
from pydantic import BaseModel, Field  # Importa BaseModel y Field para definir validaciones del payload de usuario.


class UserCreate(BaseModel):  # Define el payload requerido para crear un usuario local dentro del sistema.
    employee_no: str = Field(..., min_length=1, max_length=50, description="Número de empleado o identificación del usuario.")  # Guarda el número único del usuario según el sistema institucional.
    first_name: str = Field(..., min_length=1, max_length=100, description="Nombre del estudiante o personal.")  # Guarda el nombre primario del usuario.
    last_name: str = Field(..., min_length=1, max_length=100, description="Apellido del estudiante o personal.")  # Guarda el apellido principal del usuario.
    grade: str | None = Field(default=None, max_length=20, description="Grado académico cuando el usuario aplica a una sección escolar.")  # Guarda el nivel académico del usuario si existe.
    section: str | None = Field(default=None, max_length=20, description="Sección o grupo del usuario si corresponde a matrícula escolar.")  # Guarda la sección del usuario para agrupación visual y reportes.
    is_active: bool = Field(default=True, description="Indica si el usuario está activo y habilitado para asistencia.")  # Guarda el estado activo/inactivo del usuario para control de acceso.


class UserRead(BaseModel):  # Define el payload de respuesta del usuario para serializarlo desde la base de datos.
    id: int  # Expone el identificador primario del usuario.
    employee_no: str  # Expone el número de empleado o identificador único del usuario.
    first_name: str  # Expone el nombre del usuario.
    last_name: str  # Expone el apellido del usuario.
    grade: str | None  # Expone el grado académico si está presente.
    section: str | None  # Expone la sección si está presente.
    is_active: bool  # Expone el estado activo del usuario.

    class Config:  # Define la configuración de serialización del esquema.
        from_attributes = True  # Permite mapear atributos del modelo SQLAlchemy directamente al esquema de respuesta.
