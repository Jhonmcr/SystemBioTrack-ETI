# SUMMARY: Procesa marcajes y calcula asistencia diaria contra los modelos y horarios oficiales.
"""Motor de asistencia diaria basado en los modelos oficiales de la base de datos."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import (
    Asistencia_Diaria,
    Empleado,
    Estatus_Asistencia,
    Horario,
    Marcaje_Crudo,
)


def Minutos_Desde_Medianoche(Hora_Referencia: time) -> int:
    """Summary: Convierte una hora a minutos desde medianoche para comparar horarios."""
    return Hora_Referencia.hour * 60 + Hora_Referencia.minute


def Procesar_Marcaje_En_Tiempo_Real(
    Id_Biometrico_Int: int | None,
    Fecha_Hora_Evento: datetime,
    Db_Sesion: Session,
    Empleado_Id: int | None = None,
    Tipo_Marcaje: str = "biometrico",
) -> dict[str, int | str]:
    """Summary: Procesa la asistencia y recibe el método sin alterar el cálculo diario."""
    # La modalidad se conserva como contexto; las reglas de asistencia son independientes.
    # La ventana excluye marcajes repetidos recientes sin incluir el evento actual.
    Fecha_Evento = Fecha_Hora_Evento.date()
    Hora_Evento = Fecha_Hora_Evento.time()
    Limite_Inferior = Fecha_Hora_Evento - timedelta(minutes=3)
    Condiciones_Empleado = []
    if Id_Biometrico_Int is not None:
        Condiciones_Empleado.append(
            Marcaje_Crudo.id_empleado_biometrico == Id_Biometrico_Int
        )
    if Empleado_Id is not None:
        Condiciones_Empleado.append(Marcaje_Crudo.empleado_id == Empleado_Id)
    if not Condiciones_Empleado:
        raise ValueError("A biometric or internal employee ID is required.")
    Marcaje_Previo = (
        Db_Sesion.query(Marcaje_Crudo)
        .filter(
            or_(*Condiciones_Empleado),
            Marcaje_Crudo.fecha_hora_marcaje >= Limite_Inferior,
            Marcaje_Crudo.fecha_hora_marcaje < Fecha_Hora_Evento,
        )
        .first()
    )
    if Marcaje_Previo:
        print(
            f"[ANTIRREBOTE] Marcaje repetido descartado "
            f"para empleado #{Empleado_Id or Id_Biometrico_Int} "
            f"| Método: {Tipo_Marcaje}"
        )
        return {"resultado": "rebote_ignorado"}

    # La relación biométrica localiza al empleado y su horario asignado.
    Consulta_Empleado = Db_Sesion.query(Empleado)
    if Empleado_Id is not None:
        Consulta_Empleado = Consulta_Empleado.filter(Empleado.id == Empleado_Id)
    else:
        Consulta_Empleado = Consulta_Empleado.filter(
            Empleado.id_empleado_biometrico == Id_Biometrico_Int
        )
    Empleado_Encontrado = Consulta_Empleado.first()
    if not Empleado_Encontrado:
        print(
            f"[ADVERTENCIA] Empleado #{Empleado_Id or Id_Biometrico_Int} "
            f"no existe en tabla empleado. | Método: {Tipo_Marcaje}"
        )
        return {"resultado": "empleado_no_encontrado"}

    # Si falta el horario asignado, se mantiene el horario institucional existente.
    Horario_Asignado = (
        Db_Sesion.query(Horario)
        .filter(Horario.id == Empleado_Encontrado.horario_id)
        .first()
    )
    Hora_Entrada_Teorica = (
        Horario_Asignado.hora_entrada_teorica
        if Horario_Asignado
        else time(7, 0, 0)
    )
    Tolerancia_Minutos = 30

    # El registro diario determina si el evento inicializa una entrada o completa la salida.
    Registro_Asistencia = (
        Db_Sesion.query(Asistencia_Diaria)
        .filter(
            Asistencia_Diaria.empleado_id == Empleado_Encontrado.id,
            Asistencia_Diaria.fecha == Fecha_Evento,
        )
        .first()
    )

    if not Registro_Asistencia:
        # La tolerancia pertenece al estado "A Tiempo"; solo su exceso produce retraso.
        Segundos_Marcaje = (
            Minutos_Desde_Medianoche(Hora_Evento) * 60 + Hora_Evento.second
        )
        Segundos_Teoricos = (
            Minutos_Desde_Medianoche(Hora_Entrada_Teorica) * 60
            + Hora_Entrada_Teorica.second
        )

        if Segundos_Marcaje <= Segundos_Teoricos + Tolerancia_Minutos * 60:
            Id_Estatus = 1
            Minutos_Tarde = 0
        else:
            Id_Estatus = 2
            Segundos_Retraso = Segundos_Marcaje - Segundos_Teoricos
            Minutos_Tarde = (Segundos_Retraso + 59) // 60

        # La validación anticipada convierte un estatus semilla faltante en un error explícito.
        Estatus_Encontrado = (
            Db_Sesion.query(Estatus_Asistencia)
            .filter(Estatus_Asistencia.id == Id_Estatus)
            .first()
        )
        if not Estatus_Encontrado:
            raise RuntimeError(
                f"No existe el estatus de asistencia con ID {Id_Estatus}."
            )

        # Se guarda la primera hora del día y se conserva el esquema oficial de estados.
        Nuevo_Registro = Asistencia_Diaria(
            empleado_id=Empleado_Encontrado.id,
            fecha=Fecha_Evento,
            hora_entrada=Hora_Evento,
            hora_salida=None,
            minutos_tarde=Minutos_Tarde,
            estatus_id=Id_Estatus,
            modificado_manualmente=False,
        )
        Db_Sesion.add(Nuevo_Registro)
        Db_Sesion.commit()
        print(
            f"[ENTRADA REGISTRADA] Empleado: {Empleado_Encontrado.nombre} "
            f"{Empleado_Encontrado.apellido} | Estatus: {Id_Estatus} | "
            f"Retardo: {Minutos_Tarde} min | Método: {Tipo_Marcaje}"
        )
        return {
            "resultado": "entrada_registrada",
            "minutos_tarde": Minutos_Tarde,
        }

    # Una salida ya fijada no se modifica con nuevos eventos posteriores al antirrebote.
    if Registro_Asistencia.hora_salida is not None:
        return {"resultado": "salida_ya_registrada"}
    if Registro_Asistencia.hora_entrada is None:
        raise RuntimeError(
            "No se puede calcular la jornada: el registro diario no tiene hora de entrada."
        )

    # La diferencia se interpreta como jornada nocturna cuando la salida es al día siguiente.
    Fecha_Hora_Entrada = datetime.combine(
        Fecha_Evento, Registro_Asistencia.hora_entrada
    )
    Fecha_Hora_Salida = datetime.combine(Fecha_Evento, Hora_Evento)
    if Fecha_Hora_Salida < Fecha_Hora_Entrada:
        Fecha_Hora_Salida += timedelta(days=1)
    Duracion_Trabajada = Fecha_Hora_Salida - Fecha_Hora_Entrada

    # La hora de salida y la duración se calculan antes de confirmar la transacción.
    Registro_Asistencia.hora_salida = Hora_Evento
    Db_Sesion.commit()
    print(
        f"[SALIDA REGISTRADA] Empleado: {Empleado_Encontrado.nombre} "
        f"{Empleado_Encontrado.apellido} | Salida: {Hora_Evento} "
        f"| Método: {Tipo_Marcaje}"
    )
    return {
        "resultado": "salida_registrada",
        "duracion_trabajada": str(Duracion_Trabajada),
    }


def Procesar_Inasistencias_Diarias(
    Fecha_Objetivo: date,
    Db_Sesion: Session,
    Horario_Id: int | None = None,
) -> dict[str, int | str]:
    """Summary: Crea inasistencias para empleados de un horario sin asistencia."""
    # El filtro de horario limita cierres parciales sin afectar los turnos posteriores.
    Consulta_Empleados = Db_Sesion.query(Empleado).filter(
        ~Db_Sesion.query(Asistencia_Diaria.id)
        .filter(
            Asistencia_Diaria.empleado_id == Empleado.id,
            Asistencia_Diaria.fecha == Fecha_Objetivo,
        )
        .exists()
    )
    if Horario_Id is not None:
        Consulta_Empleados = Consulta_Empleados.filter(
            Empleado.horario_id == Horario_Id
        )
    Empleados_Sin_Asistencia = Consulta_Empleados.all()
    if not Empleados_Sin_Asistencia:
        Resultado_Cierre: dict[str, int | str] = {
            "resultado": "cierre_diario_completado",
            "fecha": Fecha_Objetivo.isoformat(),
            "inasistencias_creadas": 0,
        }
        if Horario_Id is not None:
            Resultado_Cierre["horario_id"] = Horario_Id
        return Resultado_Cierre

    # El estatus 3 es exclusivo de ausencias y debe existir en el catálogo oficial.
    Estatus_Inasistente = (
        Db_Sesion.query(Estatus_Asistencia)
        .filter(Estatus_Asistencia.id == 3)
        .first()
    )
    if not Estatus_Inasistente:
        raise RuntimeError(
            "No existe el estatus de asistencia con ID 3 (Inasistente)."
        )

    # Los empleados sin registro reciben una fila vacía en horas y con cero minutos tarde.
    for Empleado_Sin_Asistencia in Empleados_Sin_Asistencia:
        Db_Sesion.add(
            Asistencia_Diaria(
                empleado_id=Empleado_Sin_Asistencia.id,
                fecha=Fecha_Objetivo,
                hora_entrada=None,
                hora_salida=None,
                minutos_tarde=0,
                estatus_id=3,
                modificado_manualmente=False,
            )
        )
    Db_Sesion.commit()
    Resultado_Cierre = {
        "resultado": "cierre_diario_completado",
        "fecha": Fecha_Objetivo.isoformat(),
        "inasistencias_creadas": len(Empleados_Sin_Asistencia),
    }
    if Horario_Id is not None:
        Resultado_Cierre["horario_id"] = Horario_Id
    return Resultado_Cierre
