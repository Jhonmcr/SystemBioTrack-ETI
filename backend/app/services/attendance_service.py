# SUMMARY: Implementa la l?gica de negocio para evaluar el estado de asistencia seg?n el horario y guardar registros hist?ricos en PostgreSQL.
from __future__ import annotations  # Habilita anotaciones modernas para tipado expl?cito en servicios y endpoints.
from datetime import datetime, timedelta  # Importa datetime y timedelta para parsear tiempos y calcular margen de tolerancia.
from typing import Any  # Importa Any para devolver diccionarios din?micos con datos de negocio.
from sqlalchemy.orm import Session  # Importa Session para ejecutar consultas de base de datos en servicios.
from app.db.models.attendance_log import AttendanceLog, AttendanceStatus  # Importa el modelo y enum de asistencia para persistencia y evaluaci?n.
from app.db.models.schedule import Schedule  # Importa el horario base para evaluar la entrada del usuario.
from app.db.models.user import User  # Importa el usuario del sistema para validar identidad y estado activo.


def parse_event_time(raw_time: str) -> datetime:  # Define la funci?n para convertir cadenas del lector biom?trico en datetime v?lido.
    normalized_value = raw_time.strip()  # Elimina espacios en blanco alrededor del valor para evitar errores de parseo.
    if normalized_value.endswith("Z"):  # Detecta timestamps ISO con sufijo Z para convertirlos a formato offset-aware.
        normalized_value = normalized_value[:-1] + "+00:00"  # Reemplaza la marca Z por offset UTC compatible con Python.
    try:  # Intenta parsear el valor con ISO 8601 est?ndar del lector.
        parsed_time = datetime.fromisoformat(normalized_value)  # Convierte el valor a datetime con soporte de timezone.
    except ValueError:  # Maneja valores de fecha no ISO, como cadenas de texto legibles de pruebas locales.
        parsed_time = datetime.strptime(normalized_value, "%Y-%m-%d %H:%M:%S")  # Intenta parsear el patr?n alternativo de fecha y hora.
    return parsed_time  # Devuelve el datetime normalizado para c?lculo de asistencia.


def resolve_attendance_status(event_time: datetime, schedule: Schedule) -> AttendanceStatus:  # Eval?a si el acceso fue puntual o tard?o seg?n el horario configurado.
    entry_datetime = datetime.combine(event_time.date(), schedule.entry_time)  # Construye la fecha y hora exacta de entrada te?rica para el d?a del evento.
    grace_deadline = entry_datetime + timedelta(minutes=schedule.grace_period_minutes)  # Calcula el l?mite final permitido antes de considerar tardanza.
    if event_time <= entry_datetime:  # Si la marca lleg? antes o en la hora te?rica, es asistencia puntual.
        return AttendanceStatus.PRESENTE  # Devuelve el estado de presente para entradas sin demora.
    if event_time <= grace_deadline:  # Si la marca qued? dentro del margen de gracia, se considera asistencia en regla.
        return AttendanceStatus.PRESENTE  # Devuelve presente cuando se cumple la tolerancia del horario.
    return AttendanceStatus.LLEGADA_TARDIA  # Devuelve tard?a cuando excede la hora de entrada y la tolerancia.


def save_attendance_event(db: Session, employee_no: str, event_time: datetime, device_id: str | None = None) -> AttendanceLog:  # Guarda el evento del lector en la tabla de historial de asistencia.
    user = db.query(User).filter(User.employee_no == employee_no, User.is_active.is_(True)).first()  # Busca el usuario activo con el employee_no reportado por el lector.
    if user is None:  # Valida que exista el usuario antes de guardar la asistencia.
        raise LookupError(f"No existe un usuario activo con employee_no={employee_no}.")  # Lanza error para indicar que la persona no est? registrada.
    schedule = db.query(Schedule).order_by(Schedule.id.asc()).first()  # Busca el primer horario configurado cuando no existe una relaci?n directa por grado o secci?n.
    if schedule is None:  # Verifica que exista al menos un horario para calcular la asistencia.
        raise LookupError("No hay un horario configurado para evaluar la asistencia.")  # Lanza error para forzar configuraci?n previa del plan escolar.
    attendance_status = resolve_attendance_status(event_time, schedule)  # Eval?a el estado seg?n la hora de entrada y la tolerancia del horario.
    attendance_log = AttendanceLog(  # Crea el registro final de asistencia para persistir en la base de datos.
        user_id=user.id,  # Asigna el usuario asociado al evento biom?trico.
        timestamp=event_time,  # Guarda la hora exacta del evento recibido por el dispositivo.
        status=attendance_status,  # Asigna el estado calculado por la l?gica del horario.
        device_id=device_id,  # Registra el identificador del lector si fue enviado en el payload.
    )
    db.add(attendance_log)  # Agrega el registro a la sesi?n activa de SQLAlchemy.
    db.commit()  # Guarda la transacci?n en PostgreSQL.
    db.refresh(attendance_log)  # Reconsulta el registro para incluir su ID generado en la base de datos.
    return attendance_log  # Devuelve el registro persistido para reportarlo en la respuesta del endpoint.


def get_today_attendance_summary(db: Session) -> list[dict[str, Any]]:  # Genera el resumen del d?a actual agrupado por grado o secci?n.
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())  # Define el inicio del d?a actual en UTC para filtrar registros del d?a.
    today_end = today_start + timedelta(days=1)  # Define el fin del d?a actual para usar como rango de consulta.
    attendance_rows = (  # Consulta la asistencia del d?a actual con el nombre del usuario, su grado y su secci?n.
        db.query(AttendanceLog, User)  # Selecciona registros de asistencia y su usuario relacionado.
        .join(User, User.id == AttendanceLog.user_id)  # Une cada log con su usuario para obtener metadata del estudiante.
        .filter(AttendanceLog.timestamp >= today_start, AttendanceLog.timestamp < today_end)  # Filtra solo los registros del d?a actual.
        .all()  # Ejecuta la consulta y devuelve todas las filas resultantes.
    )
    summaries: list[dict[str, Any]] = []  # Crea la lista inicial donde se acumular?n los res?menes por secci?n o grado.
    for attendance, user in attendance_rows:  # Recorre cada registro del d?a para generar el payload de resumen.
        group_key = user.section or user.grade or "Sin grupo"  # Determina la clave de agrupaci?n seg?n secci?n o grado disponible.
        existing = next((item for item in summaries if item["group"] == group_key), None)  # Busca si ya existe un grupo con la misma clave.
        if existing is None:  # Crea un nuevo grupo cuando a?n no existe para la clave.
            existing = {"group": group_key, "present": 0, "late": 0, "absent": 0, "justified": 0, "total": 0}  # Inicializa la estructura del resumen.
            summaries.append(existing)  # Agrega el grupo a la salida final.
        existing["total"] += 1  # Incrementa el total de registros por grupo.
        if attendance.status == AttendanceStatus.PRESENTE:  # Cuenta los presentes dentro del grupo.
            existing["present"] += 1  # Incrementa la cantidad de asistencias puntuales.
        elif attendance.status == AttendanceStatus.LLEGADA_TARDIA:  # Cuenta las llegadas tard?as dentro del grupo.
            existing["late"] += 1  # Incrementa la cantidad de llegadas tard?as.
        elif attendance.status == AttendanceStatus.JUSTIFICADO:  # Cuenta las justificaciones dentro del grupo.
            existing["justified"] += 1  # Incrementa el total de asistencias justificadas.
        else:  # Cuenta las ausencias dentro del grupo.
            existing["absent"] += 1  # Incrementa la cantidad de ausencias registradas.
    return summaries  # Devuelve el resumen final del d?a para consumo de la API web.


def get_attendance_reports(db: Session, start_date: str | None, end_date: str | None, student_id: int | None, status: str | None) -> list[dict[str, Any]]:  # Genera reportes de asistencia seg?n filtros de fecha, estudiante y estado.
    query = db.query(AttendanceLog, User).join(User, User.id == AttendanceLog.user_id)  # Inicializa la consulta base con historial y usuario asociado.
    if start_date:  # Aplica filtro por fecha inicial cuando la API lo env?a.
        start_value = datetime.fromisoformat(start_date)  # Convierte la fecha inicial a datetime para SQLAlchemy.
        query = query.filter(AttendanceLog.timestamp >= start_value)  # Filtra registros desde la fecha inicial indicada.
    if end_date:  # Aplica filtro por fecha final cuando la API lo env?a.
        end_value = datetime.fromisoformat(end_date)  # Convierte la fecha final a datetime para SQLAlchemy.
        query = query.filter(AttendanceLog.timestamp <= end_value)  # Filtra registros hasta la fecha final indicada.
    if student_id is not None:  # Aplica filtro por estudiante cuando el cliente pide un usuario espec?fico.
        query = query.filter(User.id == student_id)  # Filtra ?nicamente los registros del estudiante solicitado.
    if status:  # Aplica filtro por estado de asistencia cuando se especifica.
        query = query.filter(AttendanceLog.status == status.upper())  # Filtra la consulta por el estado solicitado normalizado a may?sculas.
    rows = query.order_by(AttendanceLog.timestamp.desc()).all()  # Ordena los resultados m?s recientes primero para reportes relevantes.
    report_rows: list[dict[str, Any]] = []  # Crea la lista final de resultados para la API de reportes.
    for attendance, user in rows:  # Recorre cada registro para devolverlo en formato serializable.
        report_rows.append({  # Agrega una fila con los datos relevantes del reporte.
            "id": attendance.id,  # Expone el ID del log interno de asistencia.
            "user_id": user.id,  # Expone el identificador del usuario relacionado.
            "employee_no": user.employee_no,  # Expone el n?mero de empleado asociado al registro.
            "full_name": f"{user.first_name} {user.last_name}",  # Construye el nombre completo para reportes visuales.
            "grade": user.grade,  # Expone el grado del estudiante o personal.
            "section": user.section,  # Expone la secci?n del estudiante o personal.
            "timestamp": attendance.timestamp.isoformat(),  # Serializa la marca temporal del evento para la API.
            "status": attendance.status.value,  # Expone el valor textual del estado de asistencia.
            "device_id": attendance.device_id,  # Expone el lector que gener? el evento.
        })  # Cierra el diccionario del reporte.
    return report_rows  # Devuelve la colecci?n de reportes para la respuesta HTTP.
