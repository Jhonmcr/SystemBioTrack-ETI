"""
=============================================================================
SUMMARY DEL MÓDULO
-----------------------------------------------------------------------------
Proyecto: Sistema de Control de Asistencia Biométrico (SystemBioTrack-ETI)
Módulo: Módulo 3 - Motor Biométrico y Asistencia (Core)
Responsables: Pablo y Jhon
Archivo: mock_punch.py
Descripción: Disparador de eventos push en tiempo real emulando la lectura
             de huella en el terminal Hikvision con ID numérico.
=============================================================================
"""

import requests
from datetime import datetime

Url_Webhook_Destino = "http://127.0.0.1:8000/api/v1/biometric/event-listener"


def Simular_Paso_De_Huella(Id_Empleado: str = "20123456", Tipo_Marcaje: str = "checkIn"):
    """Envía un marcaje con identificador numérico compatible con PostgreSQL INTEGER."""
    Carga_Util_Evento = {
        "ipAddress": "192.168.1.201",
        "dateTime": datetime.now().isoformat(),
        "eventType": "AccessControl",
        "AccessControllerEvent": {
            "deviceName": "Terminal_Entrada_Principal",
            "majorEventType": 5,
            "subEventType": 75,
            "employeeNoString": Id_Empleado,
            "attendanceStatus": Tipo_Marcaje,
            "verifyNo": 1
        }
    }

    print(f"[*] Enviando marcaje de: Empleado ID #{Id_Empleado} ({Tipo_Marcaje}) ...")

    try:
        Respuesta_Servidor = requests.post(Url_Webhook_Destino, json=Carga_Util_Evento, timeout=4)
        if Respuesta_Servidor.status_code == 201:
            print(f"[✔] Respuesta de la API: {Respuesta_Servidor.json()}")
        else:
            print(f"[!] Respuesta HTTP {Respuesta_Servidor.status_code}: {Respuesta_Servidor.text}")
    except requests.exceptions.ConnectionError:
        print("[✖] Error de conexión: main.py no está corriendo en el puerto 8000.")


if __name__ == "__main__":
    # Prueba con ID numérico según base de datos oficial
    Simular_Paso_De_Huella(Id_Empleado="20123456", Tipo_Marcaje="checkIn")