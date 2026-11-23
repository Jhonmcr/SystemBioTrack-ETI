# SUMMARY: Define los endpoints REST para registrar y gestionar usuarios locales del sistema escolar.
from __future__ import annotations  # Permite utilizar tipado moderno y tipos complejos en la API.
from fastapi import APIRouter, Depends, HTTPException, status  # Importa componentes de FastAPI para manejo de errores y status HTTP.
from sqlalchemy.orm import Session  # Importa Session para acceder a la base de datos desde la ruta.
from app.db.session import get_db  # Importa la dependencia de base de datos del proyecto.
from app.schemas.user import UserCreate, UserRead  # Importa los esquemas Pydantic de entrada y salida del usuario.

Router_Usuarios = APIRouter()  # Crea el router del dominio de usuarios.


@Router_Usuarios.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)  # Define el endpoint para registrar nuevos usuarios locales.
def create_user(Datos_Usuario: UserCreate, Db_Sesion: Session = Depends(get_db)) -> UserRead:  # Recibe el payload del formulario y la sesión de base de datos.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="User creation logic is pending implementation.")  # Mantiene el endpoint listo para futura lógica real, evitando respuestas ambiguas.
