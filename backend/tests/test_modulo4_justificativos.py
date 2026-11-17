"""Summary: Prueba los contratos HTTP y la persistencia del módulo de justificativos."""

from collections.abc import Iterator
from datetime import time
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import (
    Ausencia,
    Asistencia_Diaria,
    Cargo,
    Empleado,
    Horario,
    Rol,
    TipoAusencia,
    Usuario,
)
from app.db.session import get_db
from app.main import app as App_Principal
from app.schemas.absence import AusenciaCreate
from app.services import absence_service as Servicio_Ausencia


@pytest.fixture
def Engine_Pruebas() -> Iterator[Engine]:
    """Summary: Crea una base SQLite en memoria aislada para cada prueba."""
    # StaticPool comparte la conexión entre el cliente y las sesiones de la prueba.
    Motor_Prueba = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=Motor_Prueba)
    yield Motor_Prueba
    Motor_Prueba.dispose()


@pytest.fixture
def Db_Sesion(Engine_Pruebas: Engine) -> Iterator[Session]:
    """Summary: Abre y cierra una sesión ORM vinculada a la base de prueba."""
    # La sesión mantiene el mismo motor SQLite usado por TestClient.
    Fabrica_Sesion = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=Engine_Pruebas,
    )
    Sesion_Prueba = Fabrica_Sesion()
    try:
        yield Sesion_Prueba
    finally:
        Sesion_Prueba.close()


@pytest.fixture
def Datos_Iniciales(Db_Sesion: Session) -> None:
    """Summary: Inserta empleados, usuario revisor y tipos requeridos por el módulo."""
    # Los identificadores explícitos simplifican la comprobación de las claves foráneas.
    Db_Sesion.add_all(
        [
            Rol(id=1, nombre_rol="Administrador"),
            Cargo(id=1, nombre_cargo="Docente"),
            Horario(
                id=1,
                nombre_horario="Mañana",
                hora_entrada_teorica=time(7, 0),
                hora_salida_teorica=time(13, 0),
            ),
            Empleado(
                id=1,
                nombre="Ana",
                apellido="Prueba",
                cedula="TEST-001",
                cargo_id=1,
                horario_id=1,
            ),
            Empleado(
                id=2,
                nombre="Luis",
                apellido="Prueba",
                cedula="TEST-002",
                cargo_id=1,
                horario_id=1,
            ),
            Usuario(
                id=1,
                empleado_id=1,
                correo="revisor@example.test",
                contrasena_hash="hash-de-prueba",
                rol_id=1,
            ),
            TipoAusencia(id=1, nombre_tipo="Permiso"),
            TipoAusencia(id=2, nombre_tipo="Reposo"),
        ]
    )
    Db_Sesion.commit()


@pytest.fixture
def Cliente_Test(Db_Sesion: Session) -> Iterator[TestClient]:
    """Summary: Redirige las solicitudes HTTP a la sesión SQLite de prueba."""
    # El override se elimina al terminar para no afectar otras suites de integración.
    def Proveer_Sesion_Prueba() -> Iterator[Session]:
        """Summary: Provee la sesión aislada a los endpoints del cliente."""
        yield Db_Sesion

    App_Principal.dependency_overrides[get_db] = Proveer_Sesion_Prueba
    Cliente_Prueba = TestClient(App_Principal)
    try:
        yield Cliente_Prueba
    finally:
        Cliente_Prueba.close()
        App_Principal.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def Directorio_Adjuntos_Test(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Summary: Aísla los archivos adjuntos dentro del directorio temporal de pytest."""
    # Ninguna prueba escribe PDFs dentro del repositorio o del directorio frontend.
    monkeypatch.setattr(
        Servicio_Ausencia,
        "DIRECTORIO_ADJUNTOS",
        tmp_path / "justificativos",
    )


@pytest.fixture
def Datos_Formulario() -> dict[str, str]:
    """Summary: Devuelve el formulario multipart mínimo para una solicitud válida."""
    # Las fechas se envían en el formato ISO admitido por los campos Form.
    return {
        "empleado_id": "1",
        "tipo_ausencia_id": "1",
        "fecha_inicio": "2026-04-10",
        "fecha_fin": "2026-04-11",
        "descripcion": "Trámite personal",
    }


def Enviar_Solicitud(
    Cliente: TestClient,
    Datos: dict[str, str],
) -> Any:
    """Summary: Publica un formulario sin archivo para reutilizarlo en las pruebas."""
    # La función concentra la ruta pública y el formato multipart del endpoint.
    return Cliente.post("/api/v1/absences", data=Datos)


def test_listar_tipos_de_ausencia(
    Cliente_Test: TestClient,
    Datos_Iniciales: None,
) -> None:
    """Summary: Comprueba que se devuelve el catálogo de tipos ordenado por ID."""
    # El catálogo seeded debe exponer sus nombres y no crear filas adicionales.
    Respuesta = Cliente_Test.get("/api/v1/absence-types")
    assert Respuesta.status_code == 200
    assert [Tipo["nombre_tipo"] for Tipo in Respuesta.json()] == [
        "Permiso",
        "Reposo",
    ]


def test_cors_permite_el_frontend_local(Cliente_Test: TestClient) -> None:
    """Summary: Comprueba el preflight CORS para el origen local de Vite."""
    # El navegador debe poder solicitar GET desde localhost:5173 sin abrir CORS globalmente.
    Respuesta = Cliente_Test.options(
        "/api/v1/absence-types",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert Respuesta.status_code == 200
    assert Respuesta.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "GET" in Respuesta.headers["access-control-allow-methods"]


def test_crear_solicitud_valida_sin_pdf(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: None,
    Datos_Formulario: dict[str, str],
) -> None:
    """Summary: Verifica que una solicitud sin adjunto queda pendiente y fechada."""
    # La fecha de solicitud se asigna automáticamente y no se devuelve una ruta interna.
    Respuesta = Enviar_Solicitud(Cliente_Test, Datos_Formulario)
    assert Respuesta.status_code == 201
    Datos_Respuesta = Respuesta.json()
    assert Datos_Respuesta["estado_aprobacion"] == "Pendiente"
    assert Datos_Respuesta["tiene_archivo_pdf"] is False
    assert Datos_Respuesta["fecha_solicitud"] is not None
    assert "archivo_pdf_ruta" not in Datos_Respuesta
    assert Db_Sesion.query(Ausencia).count() == 1


def test_crear_solicitud_valida_con_pdf_y_descargarlo(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: None,
    Datos_Formulario: dict[str, str],
) -> None:
    """Summary: Guarda el PDF con nombre interno y permite su descarga controlada."""
    # Se usa una firma PDF mínima para verificar el flujo sin depender de librerías externas.
    Contenido_PDF = b"%PDF-1.4\ncontenido de prueba\n%%EOF"
    Respuesta_Creacion = Cliente_Test.post(
        "/api/v1/absences",
        data=Datos_Formulario,
        files={"archivo_pdf": ("respaldo.pdf", Contenido_PDF, "application/pdf")},
    )
    assert Respuesta_Creacion.status_code == 201
    Datos_Respuesta = Respuesta_Creacion.json()
    assert Datos_Respuesta["tiene_archivo_pdf"] is True
    assert "archivo_pdf_ruta" not in Datos_Respuesta

    Registro_Ausencia = Db_Sesion.query(Ausencia).one()
    assert Registro_Ausencia.archivo_pdf_ruta is not None
    assert Path(Registro_Ausencia.archivo_pdf_ruta).name == (
        Registro_Ausencia.archivo_pdf_ruta
    )
    Respuesta_Descarga = Cliente_Test.get(
        f"/api/v1/absences/{Registro_Ausencia.id}/pdf"
    )
    assert Respuesta_Descarga.status_code == 200
    assert Respuesta_Descarga.headers["content-type"] == "application/pdf"
    assert Respuesta_Descarga.content == Contenido_PDF


def test_rechazar_fechas_invertidas(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: None,
    Datos_Formulario: dict[str, str],
) -> None:
    """Summary: Rechaza formularios cuya fecha final precede a la fecha inicial."""
    # La validación ocurre antes de insertar cualquier ausencia.
    Datos_Formulario["fecha_inicio"] = "2026-04-12"
    Datos_Formulario["fecha_fin"] = "2026-04-11"
    Respuesta = Enviar_Solicitud(Cliente_Test, Datos_Formulario)
    assert Respuesta.status_code == 422
    assert Db_Sesion.query(Ausencia).count() == 0


def test_rechazar_claves_foraneas_inexistentes(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: None,
    Datos_Formulario: dict[str, str],
) -> None:
    """Summary: Devuelve 404 para empleado o tipo de ausencia inexistentes."""
    # La validación de referencias no depende de que SQLite active las FK por defecto.
    Datos_Empleado_Inexistente = {**Datos_Formulario, "empleado_id": "999"}
    Respuesta_Empleado = Enviar_Solicitud(
        Cliente_Test,
        Datos_Empleado_Inexistente,
    )
    Datos_Tipo_Inexistente = {**Datos_Formulario, "tipo_ausencia_id": "999"}
    Respuesta_Tipo = Enviar_Solicitud(Cliente_Test, Datos_Tipo_Inexistente)
    assert Respuesta_Empleado.status_code == 404
    assert Respuesta_Tipo.status_code == 404
    assert Db_Sesion.query(Ausencia).count() == 0


def test_rechazar_adjunto_que_no_es_pdf(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: None,
    Datos_Formulario: dict[str, str],
) -> None:
    """Summary: Rechaza adjuntos por extensión, MIME o firma PDF inválidos."""
    # Los casos cubren extensión, MIME y firma de contenido incorrectos.
    Respuesta_Extension = Cliente_Test.post(
        "/api/v1/absences",
        data=Datos_Formulario,
        files={"archivo_pdf": ("respaldo.txt", b"texto", "text/plain")},
    )
    Respuesta_MIME = Cliente_Test.post(
        "/api/v1/absences",
        data=Datos_Formulario,
        files={
            "archivo_pdf": (
                "respaldo.pdf",
                b"%PDF-1.4\n%%EOF",
                "application/octet-stream",
            )
        },
    )
    Respuesta_Firma = Cliente_Test.post(
        "/api/v1/absences",
        data=Datos_Formulario,
        files={"archivo_pdf": ("respaldo.pdf", b"no es pdf", "application/pdf")},
    )
    assert Respuesta_Extension.status_code == 400
    assert Respuesta_MIME.status_code == 400
    assert Respuesta_Firma.status_code == 400
    assert Db_Sesion.query(Ausencia).count() == 0


def test_rechazar_pdf_mayor_a_cinco_mb(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: None,
    Datos_Formulario: dict[str, str],
) -> None:
    """Summary: Impide guardar un archivo PDF que exceda el límite configurado."""
    # El contenido supera el máximo en un byte para probar el límite exacto.
    Contenido_Grande = b"%PDF-" + b"x" * (5 * 1024 * 1024 - 4)
    Respuesta = Cliente_Test.post(
        "/api/v1/absences",
        data=Datos_Formulario,
        files={"archivo_pdf": ("grande.pdf", Contenido_Grande, "application/pdf")},
    )
    assert Respuesta.status_code == 400
    assert Db_Sesion.query(Ausencia).count() == 0


def test_fallo_de_transaccion_limpia_el_pdf_guardado(
    Db_Sesion: Session,
    Datos_Iniciales: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Summary: Elimina el archivo temporal si falla el commit de una solicitud."""
    # Se fuerza un error de base de datos después de escribir el PDF para verificar rollback.
    def Fallar_Commit() -> None:
        """Summary: Simula un fallo de persistencia durante la transacción."""
        raise SQLAlchemyError("Fallo de commit simulado.")

    monkeypatch.setattr(Db_Sesion, "commit", Fallar_Commit)
    Datos_Ausencia = AusenciaCreate(
        empleado_id=1,
        tipo_ausencia_id=1,
        fecha_inicio="2026-04-10",
        fecha_fin="2026-04-11",
        descripcion="Respaldo de prueba",
    )
    with pytest.raises(SQLAlchemyError):
        Servicio_Ausencia.Crear_Ausencia(
            Db_Sesion,
            Datos_Ausencia,
            Contenido_PDF=b"%PDF-1.4\n%%EOF",
            Nombre_Archivo="respaldo.pdf",
            Tipo_Contenido="application/pdf",
        )
    assert list(Servicio_Ausencia.DIRECTORIO_ADJUNTOS.glob("*.pdf")) == []
    assert Db_Sesion.query(Ausencia).count() == 0


def test_listar_solicitudes_con_filtros_y_paginacion(
    Cliente_Test: TestClient,
    Datos_Iniciales: None,
    Datos_Formulario: dict[str, str],
) -> None:
    """Summary: Filtra solicitudes por empleado, estado, intervalo y límite de página."""
    # Dos solicitudes coinciden con el rango solapado; otra queda fuera por empleado.
    Enviar_Solicitud(Cliente_Test, Datos_Formulario)
    Segunda_Solicitud = {
        **Datos_Formulario,
        "fecha_inicio": "2026-04-11",
        "fecha_fin": "2026-04-13",
    }
    Enviar_Solicitud(Cliente_Test, Segunda_Solicitud)
    Solicitud_Otro_Empleado = {**Datos_Formulario, "empleado_id": "2"}
    Enviar_Solicitud(Cliente_Test, Solicitud_Otro_Empleado)

    Respuesta = Cliente_Test.get(
        "/api/v1/absences",
        params={
            "empleado_id": 1,
            "estado_aprobacion": "Pendiente",
            "fecha_desde": "2026-04-11",
            "fecha_hasta": "2026-04-11",
            "limit": 1,
            "offset": 0,
        },
    )
    assert Respuesta.status_code == 200
    assert Respuesta.json()["total"] == 2
    assert Respuesta.json()["limit"] == 1
    assert len(Respuesta.json()["items"]) == 1
    assert Respuesta.json()["items"][0]["empleado_id"] == 1


def test_decidir_solicitud_y_rechazar_transiciones_invalidas(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: None,
    Datos_Formulario: dict[str, str],
) -> None:
    """Summary: Permite decidir una solicitud pendiente una sola vez."""
    # Una segunda decisión no puede sobrescribir la decisión ya persistida.
    Respuesta_Creacion = Enviar_Solicitud(Cliente_Test, Datos_Formulario)
    Id_Ausencia = Respuesta_Creacion.json()["id"]
    Respuesta_Aprobacion = Cliente_Test.patch(
        f"/api/v1/absences/{Id_Ausencia}/decision?aprobado_por_usuario_id=1",
        json={"estado_aprobacion": "Aprobado"},
    )
    assert Respuesta_Aprobacion.status_code == 200
    assert Respuesta_Aprobacion.json()["estado_aprobacion"] == "Aprobado"
    assert Respuesta_Aprobacion.json()["aprobado_por_usuario_id"] == 1
    assert Db_Sesion.query(Ausencia).one().estado_aprobacion == "Aprobado"

    Respuesta_Decision_Duplicada = Cliente_Test.patch(
        f"/api/v1/absences/{Id_Ausencia}/decision?aprobado_por_usuario_id=1",
        json={"estado_aprobacion": "Rechazado"},
    )
    Respuesta_Estado_No_Final = Cliente_Test.patch(
        f"/api/v1/absences/{Id_Ausencia}/decision?aprobado_por_usuario_id=1",
        json={"estado_aprobacion": "Pendiente"},
    )
    Respuesta_Usuario_Inexistente = Cliente_Test.patch(
        f"/api/v1/absences/{Id_Ausencia}/decision?aprobado_por_usuario_id=999",
        json={"estado_aprobacion": "Rechazado"},
    )
    assert Respuesta_Decision_Duplicada.status_code == 409
    assert Respuesta_Estado_No_Final.status_code == 422
    assert Respuesta_Usuario_Inexistente.status_code == 404
    assert Db_Sesion.query(Ausencia).one().estado_aprobacion == "Aprobado"

    # El rechazo también es una decisión final válida para una solicitud pendiente.
    Segunda_Creacion = Enviar_Solicitud(
        Cliente_Test,
        {**Datos_Formulario, "fecha_inicio": "2026-04-20", "fecha_fin": "2026-04-20"},
    )
    Id_Segunda_Ausencia = Segunda_Creacion.json()["id"]
    Respuesta_Rechazo = Cliente_Test.patch(
        f"/api/v1/absences/{Id_Segunda_Ausencia}/decision?aprobado_por_usuario_id=1",
        json={"estado_aprobacion": "Rechazado"},
    )
    assert Respuesta_Rechazo.status_code == 200
    assert Respuesta_Rechazo.json()["estado_aprobacion"] == "Rechazado"

    # El módulo 4 no cambia ni crea filas en la tabla de asistencia diaria.
    assert Db_Sesion.query(Asistencia_Diaria).count() == 0


def test_descarga_devuelve_404_si_solicitud_no_tiene_pdf(
    Cliente_Test: TestClient,
    Datos_Iniciales: None,
    Datos_Formulario: dict[str, str],
) -> None:
    """Summary: Devuelve 404 si la solicitud o su adjunto no está disponible."""
    # La creación sin archivo no genera un enlace o una ruta de descarga válida.
    Respuesta_Creacion = Enviar_Solicitud(Cliente_Test, Datos_Formulario)
    Id_Ausencia = Respuesta_Creacion.json()["id"]
    Respuesta = Cliente_Test.get(f"/api/v1/absences/{Id_Ausencia}/pdf")
    Respuesta_Sin_Solicitud = Cliente_Test.get("/api/v1/absences/999/pdf")
    assert Respuesta.status_code == 404
    assert Respuesta_Sin_Solicitud.status_code == 404
