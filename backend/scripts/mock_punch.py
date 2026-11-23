# SUMMARY: Envía una secuencia de marcajes simulados al webhook modular de Hikvision.
"""Simulador de entrada, antirrebote, retraso y salida para el módulo de asistencia."""

from datetime import date, datetime, time

import requests


Url_Webhook_Destino = "http://localhost:8000/api/v1/hikvision/events"


def Enviar_Marcaje(
    Id_Empleado_Biometrico: int,
    Fecha_Hora_Evento: datetime,
    Tipo_Marcaje: str,
) -> bool:
    """Summary: Publica un marcaje Hikvision y muestra la respuesta recibida."""
    # La estructura replica la envoltura ISAPI que acepta el esquema compartido.
    Carga_Util_Evento = {
        "dateTime": Fecha_Hora_Evento.isoformat(),
        "eventType": "AccessControl",
        "AccessControllerEvent": {
            "employeeNoString": str(Id_Empleado_Biometrico),
            "attendanceStatus": Tipo_Marcaje,
        },
    }
    print(
        f"Enviando {Tipo_Marcaje} para empleado "
        f"#{Id_Empleado_Biometrico} a las {Fecha_Hora_Evento.isoformat()}..."
    )

    # El endpoint responde 202 al aceptar cada evento, incluso si el servicio lo descarta.
    try:
        Respuesta_Servidor = requests.post(
            Url_Webhook_Destino,
            json=Carga_Util_Evento,
            timeout=5,
        )
    except requests.exceptions.RequestException as Error_Conexion:
        print(f"Error al conectar con el backend: {Error_Conexion}")
        return False

    if Respuesta_Servidor.status_code != 202:
        print(
            f"Error HTTP {Respuesta_Servidor.status_code}: "
            f"{Respuesta_Servidor.text}"
        )
        return False

    print(f"Respuesta del backend: {Respuesta_Servidor.json()}")
    return True


def Leer_Id_Empleado(
    Mensaje: str,
    Id_Por_Defecto: int,
) -> int:
    """Summary: Solicita un identificador biométrico positivo desde la consola."""
    # El valor predeterminado agiliza la demostración, pero puede ajustarse a la BD local.
    while True:
        Texto_Id = input(f"{Mensaje} [{Id_Por_Defecto}]: ").strip()
        try:
            Id_Empleado_Biometrico = (
                int(Texto_Id) if Texto_Id else Id_Por_Defecto
            )
        except ValueError:
            print("El identificador debe ser un número entero positivo.")
            continue
        if Id_Empleado_Biometrico > 0:
            return Id_Empleado_Biometrico
        print("El identificador debe ser un número entero positivo.")


def Simular_Secuencia_Prueba() -> None:
    """Summary: Simula llegada puntual, rebote, llegada tardía y salida."""
    # Se solicitan IDs existentes para que el webhook pueda relacionarlos con empleados.
    Id_Empleado_A_Tiempo = Leer_Id_Empleado(
        "ID biométrico para la entrada a tiempo",
        20123456,
    )
    Id_Empleado_Retrasado = Leer_Id_Empleado(
        "ID biométrico para la entrada con retardo",
        Id_Empleado_A_Tiempo + 1,
    )
    Fecha_Prueba = date.today()

    # Las horas usan la jornada de ejemplo: entrada teórica 07:00 y salida 15:00.
    Enviar_Marcaje(
        Id_Empleado_A_Tiempo,
        datetime.combine(Fecha_Prueba, time(7, 0)),
        "checkIn",
    )
    Enviar_Marcaje(
        Id_Empleado_A_Tiempo,
        datetime.combine(Fecha_Prueba, time(7, 2)),
        "checkIn",
    )
    Enviar_Marcaje(
        Id_Empleado_Retrasado,
        datetime.combine(Fecha_Prueba, time(7, 31)),
        "checkIn",
    )
    Enviar_Marcaje(
        Id_Empleado_A_Tiempo,
        datetime.combine(Fecha_Prueba, time(15, 0)),
        "checkOut",
    )


def Ejecutar_Menu() -> None:
    """Summary: Presenta la opción de ejecutar la secuencia completa de prueba."""
    # El menú mantiene la ejecución interactiva limitada a la demostración solicitada.
    print("=== Simulador de marcajes del Módulo 3 ===")
    print("1. Ejecutar secuencia de prueba")
    print("0. Salir")
    Opcion_Seleccionada = input("Seleccione una opción: ").strip()
    if Opcion_Seleccionada == "1":
        Simular_Secuencia_Prueba()
    elif Opcion_Seleccionada != "0":
        print("Opción no válida.")


if __name__ == "__main__":
    Ejecutar_Menu()
