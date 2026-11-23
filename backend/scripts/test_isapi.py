# SUMMARY: Comprueba conectividad ISAPI con un dispositivo usando autenticación HTTP Digest.
"""
=============================================================================
SUMMARY DEL MÓDULO
-----------------------------------------------------------------------------
Proyecto: Sistema de Control de Asistencia Biométrico (SystemBioTrack-ETI)
Módulo: Módulo 3 - Motor Biométrico y Asistencia (Core)
Responsables: Pablo
Archivo: test_isapi.py
Descripción: Cliente de verificación de comunicación con el terminal biométrico.
             Implementa el protocolo HTTP con esquema de autenticación Digest
             para validar conectividad y lectura de parámetros de hardware.
=============================================================================
"""

import os
import requests
from requests.auth import HTTPDigestAuth
from dotenv import load_dotenv

# Carga de las variables de entorno locales
load_dotenv()

# Variables de configuración del biométrico
Ip_Biometrico = os.getenv("BIOMETRIC_IP", "127.0.0.1")
Puerto_Biometrico = os.getenv("BIOMETRIC_PORT", "8080")
Usuario_Biometrico = os.getenv("BIOMETRIC_USER", "admin")
Password_Biometrico = os.getenv("BIOMETRIC_PASS", "admin12345")


def Ejecutar_Validacion_Conexion():
    """
    Ejecuta una petición GET al endpoint deviceInfo del terminal biométrico
    empleando HTTP Digest Authentication para verificar disponibilidad.
    """
    # Construcción de la URL de destino
    Url_Destino = f"http://{Ip_Biometrico}:{Puerto_Biometrico}/ISAPI/System/deviceInfo"
    print(f"[*] Intentando comunicar con: {Url_Destino} ...")

    try:
        # Petición HTTP con autenticación Digest
        Respuesta_Terminal = requests.get(
            Url_Destino,
            auth=HTTPDigestAuth(Usuario_Biometrico, Password_Biometrico),
            timeout=5
        )

        # Validación del código de estado HTTP
        if Respuesta_Terminal.status_code == 200:
            print("\n[✔] Conexión establecida exitosamente.")
            print("=" * 60)
            print(Respuesta_Terminal.text)
            print("=" * 60)
        elif Respuesta_Terminal.status_code == 401:
            print("\n[✖] Error 401: Credenciales inválidas o rechazo por autenticación Digest.")
        else:
            print(f"\n[!] Código de estado imprevisto: {Respuesta_Terminal.status_code}")

    except requests.exceptions.ConnectionError:
        print("\n[✖] Error: No se pudo conectar al terminal. Verifica si el servicio está activo.")
    except requests.exceptions.Timeout:
        print("\n[✖] Error: Tiempo de espera agotado al consultar el dispositivo.")
    except Exception as Error_Inesperado:
        print(f"\n[✖] Excepción no controlada: {Error_Inesperado}")


if __name__ == "__main__":
    Ejecutar_Validacion_Conexion()