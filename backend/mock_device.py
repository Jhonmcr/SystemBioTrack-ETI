"""
=============================================================================
SUMMARY DEL MÓDULO
-----------------------------------------------------------------------------
Proyecto: Sistema de Control de Asistencia Biométrico (SystemBioTrack-ETI)
Módulo: Módulo 3 - Motor Biométrico y Asistencia (Core)
Responsables: Pablo 
Archivo: mock_device.py
Descripción: Emulador en software del terminal biométrico Hikvision DS-K1A8503MF-B.
             Expone los endpoints del protocolo ISAPI (XML y JSON) para permitir
             el desarrollo y pruebas de integración sin requerir el hardware físico.
=============================================================================
"""

import uvicorn
from fastapi import FastAPI, Response
from datetime import datetime

# Instancia principal del servidor simulador
App_Servidor = FastAPI(
    title="Simulador Hikvision DS-K1A8503MF-B",
    description="Servidor Mock de ISAPI para pruebas del Módulo 3",
    version="1.0.0"
)

# Estructura XML devuelta por el terminal físico ante consultas de información de hardware
Xml_Informacion_Dispositivo = """<?xml version="1.0" encoding="UTF-8"?>
<DeviceInfo version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <deviceName>Terminal_Entrada_Principal</deviceName>
    <deviceID>DS-K1A8503MF-B</deviceID>
    <model>DS-K1A8503MF-B</model>
    <serialNumber>J79190080</serialNumber>
    <macAddress>44:19:b6:aa:bb:cc</macAddress>
    <firmwareVersion>V1.3.4</firmwareVersion>
    <supportAttendanceStatus>true</supportAttendanceStatus>
</DeviceInfo>
"""

@App_Servidor.get("/ISAPI/System/deviceInfo")
def Obtener_Info_Dispositivo():
    """
    Endpoint simulado que devuelve la ficha técnica del captahuellas.
    Retorna:
        Response: Documento XML con cabeceras de texto plano application/xml.
    """
    # Retorna la carga estática XML emulando la respuesta ISAPI
    return Response(content=Xml_Informacion_Dispositivo, media_type="application/xml")


@App_Servidor.post("/ISAPI/AccessControl/AcsEvent")
def Consultar_Eventos_Acs():
    """
    Endpoint simulado para la descarga de marcajes offline retenidos en memoria.
    Retorna:
        dict: Estructura JSON con el historial de eventos autenticados.
    """
    # Construcción de la estructura de eventos en memoria no volátil
    Respuesta_Eventos = {
        "AcsEventSearchResult": {
            "numOfMatches": 2,
            "totalMatches": 2,
            "MatchList": [
                {
                    "major": 5,                                # 5: Evento de control de acceso
                    "minor": 75,                               # 75: Verificación de huella aprobada
                    "time": datetime.now().isoformat(),        # Estampa de tiempo del marcaje
                    "employeeNoString": "V-20123456",          # Cédula/Identificador de empleado
                    "attendanceStatus": "checkIn"              # Estado de entrada
                },
                {
                    "major": 5,
                    "minor": 75,
                    "time": datetime.now().isoformat(),
                    "employeeNoString": "V-18999888",
                    "attendanceStatus": "checkIn"
                }
            ]
        }
    }
    return Respuesta_Eventos


if __name__ == "__main__":
    # Host y puerto local asignados para el mock
    Host_Simulador = "127.0.0.1"
    Puerto_Simulador = 8080

    print(f"[*] Iniciando Simulador Hikvision en http://{Host_Simulador}:{Puerto_Simulador}")
    uvicorn.run(App_Servidor, host=Host_Simulador, port=Puerto_Simulador)