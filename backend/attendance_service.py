"""
=============================================================================
SUMMARY DEL MÓDULO
-----------------------------------------------------------------------------
Proyecto: Sistema de Control de Asistencia Biométrico (SystemBioTrack-ETI)
Módulo: Módulo 3 - Motor Biométrico y Asistencia (Core)
Responsables: Pablo y Jhon
Archivo: attendance_service.py
Descripción: Lógica del cálculo de asistencia diaria acoplada al esquema oficial.
             Aplica filtro antirrebote de 180 segundos, tolerancia de 30 minutos
             y cálculo de retardos contra horario teórico.
=============================================================================
"""

from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from models import Marcaje_Crudo, Asistencia_Diaria, Empleado, Horario


def Minutos_Desde_Medianoche(Hora_Referencia: time) -> int:
    """Calcula minutos totales del día para comparaciones precisas."""
    return Hora_Referencia.hour * 60 + Hora_Referencia.minute


def Procesar_Marcaje_En_Tiempo_Real(
    Id_Biometrico_Int: int,
    Fecha_Hora_Evento: datetime,
    Db_Sesion: Session
) -> dict:
    """
    Procesa el marcaje recibido evaluando duplicados por rebote y calculando
    la jornada en asistencia_diaria según el horario teórico del empleado.
    """
    Fecha_Evento = Fecha_Hora_Evento.date()
    Hora_Evento = Fecha_Hora_Evento.time()

    # 1. FILTRO ANTIRREBOTE (Ventana de 3 minutos / 180s en marcaje_crudo)
    Limite_Inferior = Fecha_Hora_Evento - timedelta(minutes=3)
    Marcaje_Previo = (
        Db_Sesion.query(Marcaje_Crudo)
        .filter(
            Marcaje_Crudo.id_empleado_biometrico == Id_Biometrico_Int,
            Marcaje_Crudo.fecha_hora_marcaje >= Limite_Inferior,
            Marcaje_Crudo.fecha_hora_marcaje < Fecha_Hora_Evento
        )
        .first()
    )

    if Marcaje_Previo:
        print(f"[🛡️ ANTIRREBOTE] Marcaje repetido descartado para empleado #{Id_Biometrico_Int}")
        return {"resultado": "rebote_ignorado"}

    # 2. VINCULACIÓN CON EMPLEADO
    Empleado_Encontrado = (
        Db_Sesion.query(Empleado)
        .filter(Empleado.id_empleado_biometrico == Id_Biometrico_Int)
        .first()
    )

    if not Empleado_Encontrado:
        print(f"[⚠️ ADVERTENCIA] Empleado #{Id_Biometrico_Int} no existe en tabla empleado.")
        return {"resultado": "empleado_no_encontrado"}

    # 3. CONSULTA DEL HORARIO TEÓRICO (Tolerancia institucional de 30 minutos)
    Horario_Asignado = (
        Db_Sesion.query(Horario)
        .filter(Horario.id == Empleado_Encontrado.horario_id)
        .first()
    )
    Hora_Entrada_Teorica = Horario_Asignado.hora_entrada_teorica if Horario_Asignado else time(7, 0, 0)
    Tolerancia_Minutos = 30

    # 4. REGISTRO O ACTUALIZACIÓN EN ASISTENCIA_DIARIA
    Registro_Asistencia = (
        Db_Sesion.query(Asistencia_Diaria)
        .filter(
            Asistencia_Diaria.empleado_id == Empleado_Encontrado.id,
            Asistencia_Diaria.fecha == Fecha_Evento
        )
        .first()
    )

    if not Registro_Asistencia:
        # PRIMER INGRESO DEL DÍA (Entrada)
        Minutos_Marcaje = Minutos_Desde_Medianoche(Hora_Evento)
        Minutos_Teoricos = Minutos_Desde_Medianoche(Hora_Entrada_Teorica)

        if Minutos_Marcaje <= Minutos_Teoricos:
            Id_Estatus = 1  # Puntual
            Minutos_Tarde = 0
        elif Minutos_Marcaje <= (Minutos_Teoricos + Tolerancia_Minutos):
            Id_Estatus = 2  # Puntual con Tolerancia
            Minutos_Tarde = 0
        else:
            Id_Estatus = 3  # Retardo
            Minutos_Tarde = Minutos_Marcaje - Minutos_Teoricos

        Nuevo_Registro = Asistencia_Diaria(
            empleado_id=Empleado_Encontrado.id,
            fecha=Fecha_Evento,
            hora_entrada=Hora_Evento,
            hora_salida=None,
            minutos_tarde=Minutos_Tarde,
            estatus_id=Id_Estatus,
            modificado_manualmente=False
        )
        Db_Sesion.add(Nuevo_Registro)
        Db_Sesion.commit()
        print(f"[✅ ENTRADA REGISTRADA] Empleado: {Empleado_Encontrado.nombre} {Empleado_Encontrado.apellido} | Estatus: {Id_Estatus} | Retardo: {Minutos_Tarde} min")
        return {"resultado": "entrada_registrada", "minutos_tarde": Minutos_Tarde}

    else:
        # MARCAJE POSTERIOR EN EL DÍA (Salida)
        Registro_Asistencia.hora_salida = Hora_Evento
        Db_Sesion.commit()
        print(f"[🚪 SALIDA REGISTRADA] Empleado: {Empleado_Encontrado.nombre} {Empleado_Encontrado.apellido} | Salida: {Hora_Evento}")
        return {"resultado": "salida_registrada"}