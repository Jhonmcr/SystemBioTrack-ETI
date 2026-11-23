# SUMMARY: Implementa el registro local de usuarios para estudiantes y personal del sistema escolar.
from __future__ import annotations  # Habilita el uso de tipos modernos con FastAPI y SQLAlchemy.
from fastapi import APIRouter, Depends, HTTPException, status  # Importa los componentes principales para manejar rutas y errores HTTP.
from sqlalchemy.orm import Session  # Importa Session para acceder a la base de datos dentro del endpoint.
from app.db.models.user import User  # Importa el modelo SQLAlchemy de usuarios para persistencia en PostgreSQL.
from app.db.session import get_db  # Importa la dependencia de sesi?n de base de datos del proyecto.
from app.schemas.user import UserCreate, UserRead  # Importa los schemas Pydantic de entrada y salida del usuario.

router = APIRouter()  # Crea el router para los endpoints de gesti?n de usuarios.


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)  # Define el endpoint para registrar un usuario local del sistema.
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:  # Recibe el payload del cliente y la sesi?n activa de base de datos.
    existing_user = db.query(User).filter(User.employee_no == payload.employee_no).first()  # Busca si ya existe un usuario con el mismo employee_no para evitar duplicados.
    if existing_user is not None:  # Valida si ya existe el usuario para denegar la creaci?n.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El employee_no ya est? registrado.")  # Devuelve un error claro al cliente.
    new_user = User(  # Crea la entidad SQLAlchemy con los datos del usuario.
        employee_no=payload.employee_no,  # Asigna el n?mero de empleado o documento institucional.
        first_name=payload.first_name,  # Asigna el nombre del usuario.
        last_name=payload.last_name,  # Asigna el apellido del usuario.
        grade=payload.grade,  # Asigna el grado si se especific?.
        section=payload.section,  # Asigna la secci?n si se especific?.
        is_active=payload.is_active,  # Asigna el estado de actividad del usuario.
    )
    db.add(new_user)  # Agrega el usuario a la sesi?n de trabajo.
    db.commit()  # Guarda la inserci?n en PostgreSQL.
    db.refresh(new_user)  # Recarga el objeto desde la base de datos para obtener su ID.
    return new_user  # Devuelve el usuario creado en el formato del modelo SQLAlchemy.
