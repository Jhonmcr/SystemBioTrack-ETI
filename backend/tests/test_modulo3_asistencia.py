# SUMMARY: Verifica configuración, webhook biométrico y consultas/correcciones de asistencia con SQLite.
"""Suite de integración incremental del Módulo 3 de asistencia."""

from collections.abc import Iterator
from datetime import date, datetime, time, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.models import (
    Asistencia_Diaria,
    Cargo,
    Empleado,
    Estatus_Asistencia,
    Horario,
    Marcaje_Crudo,
)
from app.db.session import get_db
from app.main import app as App_Principal
from app.schemas.hikvision import HikvisionEventPayload


@pytest.fixture
def Engine_Pruebas() -> Iterator[Engine]:
    """Summary: Crea una base SQLite en memoria aislada para cada prueba."""
    # StaticPool conserva la misma conexión SQLite entre el cliente y las sesiones.
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
    """Summary: Abre y cierra una sesión de prueba sobre SQLite en memoria."""
    # La sesión comparte el motor aislado usado por el TestClient.
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
def Datos_Iniciales(Db_Sesion: Session) -> tuple[int, int]:
    """Summary: Inserta catálogos y empleados requeridos por las rutas del módulo."""
    # Los IDs de estados reproducen exactamente los valores semilla del SQL oficial.
    Db_Sesion.add_all(
        [
            Cargo(id=1, nombre_cargo="Administrativo"),
            Horario(
                id=1,
                nombre_horario="Mañana",
                hora_entrada_teorica=time(7, 0),
                hora_salida_teorica=time(15, 0),
            ),
            Estatus_Asistencia(id=1, nombre_estatus="A Tiempo"),
            Estatus_Asistencia(id=2, nombre_estatus="Retrasado"),
            Estatus_Asistencia(id=3, nombre_estatus="Inasistente"),
            Empleado(
                id=1,
                nombre="Ana",
                apellido="Prueba",
                cedula="TEST-001",
                id_empleado_biometrico=1001,
                cargo_id=1,
                horario_id=1,
            ),
            Empleado(
                id=2,
                nombre="Luis",
                apellido="Prueba",
                cedula="TEST-002",
                id_empleado_biometrico=1002,
                cargo_id=1,
                horario_id=1,
            ),
        ]
    )
    Db_Sesion.commit()
    return (1, 2)


@pytest.fixture
def Cliente_Test(Db_Sesion: Session) -> Iterator[TestClient]:
    """Summary: Sobrescribe get_db para dirigir la API a la sesión SQLite de prueba."""
    # La dependencia queda restaurada al terminar para no contaminar otras suites.
    def Proveer_Sesion_Prueba() -> Iterator[Session]:
        """Summary: Provee la sesión aislada a los endpoints durante la prueba."""
        yield Db_Sesion

    App_Principal.dependency_overrides[get_db] = Proveer_Sesion_Prueba
    Cliente_Prueba = TestClient(App_Principal)
    try:
        yield Cliente_Prueba
    finally:
        Cliente_Prueba.close()
        App_Principal.dependency_overrides.pop(get_db, None)


def Publicar_Evento_Hikvision(
    Cliente: TestClient,
    Id_Biometrico: int,
    Fecha_Hora: datetime,
    Evento_Anidado: bool = True,
) -> Any:
    """Summary: Envía un evento Hikvision anidado o plano al webhook de pruebas."""
    # Ambas representaciones cubren AccessControllerEvent y aliases de timestamp.
    if Evento_Anidado:
        Datos_Evento = {
            "dateTime": Fecha_Hora.isoformat(),
            "AccessControllerEvent": {
                "employeeNoString": str(Id_Biometrico),
            },
        }
    else:
        Datos_Evento = {
            "employeeNoString": str(Id_Biometrico),
            "eventTime": Fecha_Hora.isoformat(),
        }
    return Cliente.post("/api/v1/hikvision/events", json=Datos_Evento)


def test_esquema_hikvision_acepta_datetime_y_id_convertible() -> None:
    """Summary: Valida la normalización del timestamp y del ID biométrico textual."""
    # Algunos firmwares entregan dateTime y employeeNoString como cadenas.
    Datos_Evento = HikvisionEventPayload.model_validate(
        {
            "employeeNoString": "1001",
            "dateTime": "2026-04-01T07:00:00",
        }
    )
    assert Datos_Evento.employeeNoString == 1001
    assert Datos_Evento.eventTime == datetime(2026, 4, 1, 7, 0)


def test_app_carga_configuracion_con_variables_extra() -> None:
    """Summary: Comprueba la importación de app.main y carga de .env tolerante a extras."""
    # La importación al recolectar esta suite falla si la app no puede construir Settings.
    get_settings.cache_clear()
    Configuracion = get_settings()
    assert isinstance(App_Principal, FastAPI)
    assert Configuracion.app_name == "SystemBioTrack ETI"


def test_webhook_procesa_entrada_rebote_retraso_y_salidas(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: tuple[int, int],
) -> None:
    """Summary: Verifica los estados biométricos, antirrebote y duración de jornada."""
    # La fixture devuelve las llaves primarias de ambos empleados sembrados.
    assert Datos_Iniciales == (1, 2)

    # La llegada teórica se registra en estado A Tiempo con cero minutos de retraso.
    Fecha_Base = datetime(2026, 4, 1, 7, 0)
    Respuesta_Entrada = Publicar_Evento_Hikvision(
        Cliente_Test, 1001, Fecha_Base
    )
    assert Respuesta_Entrada.status_code == 202
    assert Respuesta_Entrada.json()["calculo_asistencia"] == {
        "resultado": "entrada_registrada",
        "minutos_tarde": 0,
    }

    # El segundo marcaje dentro de tres minutos se persiste, pero no cambia asistencia.
    Respuesta_Rebote = Publicar_Evento_Hikvision(
        Cliente_Test, 1001, Fecha_Base + timedelta(minutes=2)
    )
    assert Respuesta_Rebote.json()["calculo_asistencia"] == {
        "resultado": "rebote_ignorado"
    }
    Registro_A_Tiempo = (
        Db_Sesion.query(Asistencia_Diaria)
        .filter(Asistencia_Diaria.empleado_id == 1)
        .one()
    )
    assert Registro_A_Tiempo.estatus_id == 1
    assert Db_Sesion.query(Asistencia_Diaria).count() == 1

    # La llegada fuera de la tolerancia se clasifica como retrasada y conserva minutos exactos.
    Respuesta_Retraso = Publicar_Evento_Hikvision(
        Cliente_Test,
        1002,
        datetime(2026, 4, 1, 7, 31),
        Evento_Anidado=False,
    )
    assert Respuesta_Retraso.json()["calculo_asistencia"] == {
        "resultado": "entrada_registrada",
        "minutos_tarde": 31,
    }
    Registro_Retrasado = (
        Db_Sesion.query(Asistencia_Diaria)
        .filter(Asistencia_Diaria.empleado_id == 2)
        .one()
    )
    assert Registro_Retrasado.estatus_id == 2
    assert Registro_Retrasado.minutos_tarde == 31

    # La salida calcula la jornada y un marcaje posterior no altera la hora consolidada.
    Respuesta_Salida = Publicar_Evento_Hikvision(
        Cliente_Test, 1001, datetime(2026, 4, 1, 15, 0)
    )
    assert Respuesta_Salida.json()["calculo_asistencia"] == {
        "resultado": "salida_registrada",
        "duracion_trabajada": "8:00:00",
    }
    Respuesta_Salida_Repetida = Publicar_Evento_Hikvision(
        Cliente_Test, 1001, datetime(2026, 4, 1, 15, 10)
    )
    assert Respuesta_Salida_Repetida.json()["calculo_asistencia"] == {
        "resultado": "salida_ya_registrada"
    }
    Db_Sesion.refresh(Registro_A_Tiempo)
    assert Registro_A_Tiempo.hora_salida == time(15, 0)


def test_get_attendance_today_y_reports_aplican_filtros(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: tuple[int, int],
) -> None:
    """Summary: Comprueba las consultas de hoy y los filtros públicos de reportes."""
    # La fixture devuelve las llaves primarias usadas por los filtros del reporte.
    assert Datos_Iniciales == (1, 2)

    # Los datos cubren dos estados en la fecha actual y una fecha fuera del rango.
    Fecha_Hoy = date.today()
    Db_Sesion.add_all(
        [
            Asistencia_Diaria(
                empleado_id=1,
                fecha=Fecha_Hoy,
                hora_entrada=time(7, 0),
                estatus_id=1,
                minutos_tarde=0,
                modificado_manualmente=False,
            ),
            Asistencia_Diaria(
                empleado_id=2,
                fecha=Fecha_Hoy,
                hora_entrada=time(7, 31),
                estatus_id=2,
                minutos_tarde=31,
                modificado_manualmente=False,
            ),
            Asistencia_Diaria(
                empleado_id=1,
                fecha=Fecha_Hoy - timedelta(days=1),
                hora_entrada=time(7, 0),
                estatus_id=1,
                minutos_tarde=0,
                modificado_manualmente=False,
            ),
        ]
    )
    Db_Sesion.commit()

    # La ruta today restringe la fecha y los reportes respetan todos los alias HTTP.
    Respuesta_Hoy = Cliente_Test.get("/api/v1/attendance/today")
    assert Respuesta_Hoy.status_code == 200
    assert len(Respuesta_Hoy.json()["items"]) == 2
    assert Respuesta_Hoy.json()["date"] == Fecha_Hoy.isoformat()

    Parametros_Reporte = {
        "start_date": Fecha_Hoy.isoformat(),
        "end_date": Fecha_Hoy.isoformat(),
        "student_id": 1,
        "status": "A Tiempo",
    }
    Respuesta_Reporte = Cliente_Test.get(
        "/api/v1/attendance/reports",
        params=Parametros_Reporte,
    )
    Datos_Reporte = Respuesta_Reporte.json()
    assert Respuesta_Reporte.status_code == 200
    assert len(Datos_Reporte["items"]) == 1
    assert Datos_Reporte["items"][0]["empleado_id"] == 1
    assert Datos_Reporte["filters"] == Parametros_Reporte

    # El estado también admite filtrar por ID del catálogo SQL.
    Respuesta_Estatus_Id = Cliente_Test.get(
        "/api/v1/attendance/reports",
        params={"status": "2"},
    )
    assert [
        Item_Asistencia["estatus_id"]
        for Item_Asistencia in Respuesta_Estatus_Id.json()["items"]
    ] == [2]


def test_patch_attendance_actualiza_y_marca_edicion_manual(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: tuple[int, int],
) -> None:
    """Summary: Verifica la corrección manual de horas y estado de asistencia."""
    # La fixture devuelve la llave primaria del empleado asociado al registro.
    assert Datos_Iniciales == (1, 2)

    # Se crea un registro base para comprobar todas las columnas permitidas en un PATCH.
    Registro_Asistencia = Asistencia_Diaria(
        empleado_id=1,
        fecha=date.today(),
        hora_entrada=time(7, 0),
        hora_salida=time(15, 0),
        minutos_tarde=0,
        estatus_id=1,
        modificado_manualmente=False,
    )
    Db_Sesion.add(Registro_Asistencia)
    Db_Sesion.commit()
    Db_Sesion.refresh(Registro_Asistencia)

    # El contrato conserva los campos ORM y marca el registro tras validar el nuevo estado.
    Respuesta_Actualizacion = Cliente_Test.patch(
        f"/api/v1/attendance/{Registro_Asistencia.id}",
        json={
            "hora_entrada": "07:15:00",
            "hora_salida": "15:30:00",
            "estatus_id": 2,
        },
    )
    assert Respuesta_Actualizacion.status_code == 200
    Datos_Actualizados = Respuesta_Actualizacion.json()
    assert Datos_Actualizados["hora_entrada"] == "07:15:00"
    assert Datos_Actualizados["hora_salida"] == "15:30:00"
    assert Datos_Actualizados["estatus_id"] == 2
    assert Datos_Actualizados["modificado_manualmente"] is True

    Db_Sesion.refresh(Registro_Asistencia)
    assert Registro_Asistencia.hora_entrada == time(7, 15)
    assert Registro_Asistencia.hora_salida == time(15, 30)
    assert Registro_Asistencia.modificado_manualmente is True


def test_close_day_crea_inasistencias_sin_duplicar(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: tuple[int, int],
) -> None:
    """Summary: Verifica que el cierre marque ausentes una vez por empleado y fecha."""
    # Ana ya tiene asistencia en la fecha objetivo; solo Luis debe quedar inasistente.
    Fecha_Objetivo = date(2026, 4, 2)
    Db_Sesion.add(
        Asistencia_Diaria(
            empleado_id=Datos_Iniciales[0],
            fecha=Fecha_Objetivo,
            hora_entrada=time(7, 0),
            hora_salida=None,
            minutos_tarde=0,
            estatus_id=1,
            modificado_manualmente=False,
        )
    )
    Db_Sesion.commit()

    # Repetir el endpoint confirma idempotencia sin modificar el registro de Ana.
    Respuesta_Primer_Cierre = Cliente_Test.post(
        "/api/v1/attendance/close-day",
        params={"fecha": Fecha_Objetivo.isoformat()},
    )
    Respuesta_Segundo_Cierre = Cliente_Test.post(
        "/api/v1/attendance/close-day",
        params={"fecha": Fecha_Objetivo.isoformat()},
    )
    assert Respuesta_Primer_Cierre.status_code == 200
    assert Respuesta_Primer_Cierre.json() == {
        "resultado": "cierre_diario_completado",
        "fecha": Fecha_Objetivo.isoformat(),
        "inasistencias_creadas": 1,
    }
    assert Respuesta_Segundo_Cierre.json()["inasistencias_creadas"] == 0

    Registro_Inasistente = (
        Db_Sesion.query(Asistencia_Diaria)
        .filter(
            Asistencia_Diaria.empleado_id == Datos_Iniciales[1],
            Asistencia_Diaria.fecha == Fecha_Objetivo,
        )
        .one()
    )
    assert Registro_Inasistente.estatus_id == 3
    assert Registro_Inasistente.minutos_tarde == 0
    assert Registro_Inasistente.hora_entrada is None
    assert (
        Db_Sesion.query(Asistencia_Diaria)
        .filter(Asistencia_Diaria.fecha == Fecha_Objetivo)
        .count()
        == 2
    )


def test_webhook_rechaza_payload_invalido_y_maneja_id_desconocido(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: tuple[int, int],
) -> None:
    """Summary: Valida la respuesta ante un identificador inválido o sin empleado."""
    # El esquema rechaza IDs no numéricos antes de crear marcajes crudos.
    Respuesta_Payload_Invalido = Cliente_Test.post(
        "/api/v1/hikvision/events",
        json={
            "dateTime": "2026-04-03T07:00:00",
            "AccessControllerEvent": {"employeeNoString": "no-es-numero"},
        },
    )
    assert Respuesta_Payload_Invalido.status_code == 422
    assert Db_Sesion.query(Marcaje_Crudo).count() == 0

    # Un ID numérico desconocido se persiste, y el motor reporta que no hay empleado.
    Respuesta_Empleado_Inexistente = Publicar_Evento_Hikvision(
        Cliente_Test,
        99999,
        datetime(2026, 4, 3, 7, 0),
    )
    assert Respuesta_Empleado_Inexistente.status_code == 202
    assert Respuesta_Empleado_Inexistente.json()["calculo_asistencia"] == {
        "resultado": "empleado_no_encontrado"
    }
    assert Db_Sesion.query(Marcaje_Crudo).count() == 1
    assert Datos_Iniciales == (1, 2)


def test_close_day_usa_hoy_cuando_no_se_indica_fecha(
    Cliente_Test: TestClient,
    Datos_Iniciales: tuple[int, int],
) -> None:
    """Summary: Comprueba que el cierre diario usa la fecha actual por defecto."""
    # Al omitir el query parameter, las dos personas sin marcaje quedan inasistentes hoy.
    Respuesta_Cierre = Cliente_Test.post("/api/v1/attendance/close-day")
    assert Respuesta_Cierre.status_code == 200
    assert Respuesta_Cierre.json()["fecha"] == date.today().isoformat()
    assert Respuesta_Cierre.json()["inasistencias_creadas"] == len(Datos_Iniciales)


def test_asistencia_multiples_horarios(
    Cliente_Test: TestClient,
    Db_Sesion: Session,
    Datos_Iniciales: tuple[int, int],
) -> None:
    """Summary: Verifica puntualidad y retraso según los turnos mañana y tarde."""
    # Se configura el catálogo oficial con dos horarios y un tercer empleado de tarde.
    Horario_Manana = Db_Sesion.query(Horario).filter(Horario.id == 1).one()
    Horario_Manana.nombre_horario = "Turno Mañana"
    Horario_Manana.hora_entrada_teorica = time(7, 0)
    Horario_Manana.hora_salida_teorica = time(13, 0)
    Db_Sesion.add(
        Horario(
            id=2,
            nombre_horario="Turno Tarde",
            hora_entrada_teorica=time(13, 0),
            hora_salida_teorica=time(18, 0),
        )
    )
    Empleado_Tarde_Puntual = (
        Db_Sesion.query(Empleado)
        .filter(Empleado.id == Datos_Iniciales[1])
        .one()
    )
    Empleado_Tarde_Puntual.horario_id = 2
    Db_Sesion.add(
        Empleado(
            id=3,
            nombre="Marta",
            apellido="Prueba",
            cedula="TEST-003",
            id_empleado_biometrico=1003,
            cargo_id=1,
            horario_id=2,
        )
    )
    Db_Sesion.commit()

    # 07:25 queda dentro de la tolerancia de mañana y 13:20 dentro de la de tarde.
    Respuesta_Manana = Publicar_Evento_Hikvision(
        Cliente_Test,
        1001,
        datetime(2026, 4, 4, 7, 25),
    )
    Respuesta_Tarde_Puntual = Publicar_Evento_Hikvision(
        Cliente_Test,
        1002,
        datetime(2026, 4, 4, 13, 20),
    )
    assert Respuesta_Manana.status_code == 202
    assert Respuesta_Manana.json()["calculo_asistencia"] == {
        "resultado": "entrada_registrada",
        "minutos_tarde": 0,
    }
    assert Respuesta_Tarde_Puntual.status_code == 202
    assert Respuesta_Tarde_Puntual.json()["calculo_asistencia"] == {
        "resultado": "entrada_registrada",
        "minutos_tarde": 0,
    }

    # 13:40 excede en 40 minutos la hora de entrada teórica del turno tarde.
    Respuesta_Tarde_Retrasado = Publicar_Evento_Hikvision(
        Cliente_Test,
        1003,
        datetime(2026, 4, 4, 13, 40),
    )
    assert Respuesta_Tarde_Retrasado.status_code == 202
    assert Respuesta_Tarde_Retrasado.json()["calculo_asistencia"] == {
        "resultado": "entrada_registrada",
        "minutos_tarde": 40,
    }

    # Se inspeccionan los estados persistidos además del JSON de respuesta.
    Registros_Asistencia = {
        Registro_Asistencia.empleado_id: Registro_Asistencia
        for Registro_Asistencia in Db_Sesion.query(Asistencia_Diaria)
        .filter(Asistencia_Diaria.fecha == date(2026, 4, 4))
        .all()
    }
    assert Registros_Asistencia[Datos_Iniciales[0]].estatus_id == 1
    assert Registros_Asistencia[Datos_Iniciales[0]].minutos_tarde == 0
    assert Registros_Asistencia[Datos_Iniciales[1]].estatus_id == 1
    assert Registros_Asistencia[Datos_Iniciales[1]].minutos_tarde == 0
    assert Registros_Asistencia[3].estatus_id == 2
    assert Registros_Asistencia[3].minutos_tarde == 40
