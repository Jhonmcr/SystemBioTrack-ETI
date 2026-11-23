"""Summary: Implementa validación, persistencia y flujo de decisión de ausencias."""

from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Ausencia, Empleado, TipoAusencia, Usuario
from app.schemas.absence import AusenciaCreate, EstadoAprobacion

TAMANO_MAXIMO_PDF_BYTES = 5 * 1024 * 1024
DIRECTORIO_ADJUNTOS = (
    Path(__file__).resolve().parents[2] / "storage" / "justificativos"
)


class EmpleadoNoEncontradoError(Exception):
    """Summary: Señala que el empleado solicitado no existe."""


class TipoAusenciaNoEncontradoError(Exception):
    """Summary: Señala que el tipo de ausencia solicitado no existe."""


class AusenciaNoEncontradaError(Exception):
    """Summary: Señala que la solicitud indicada no existe."""


class UsuarioRevisorNoEncontradoError(Exception):
    """Summary: Señala que el usuario revisor indicado no existe."""


class DecisionAusenciaConflictError(Exception):
    """Summary: Señala que una solicitud ya no está pendiente de decisión."""


class AdjuntoPDFInvalidoError(Exception):
    """Summary: Señala que un adjunto no cumple los requisitos de PDF."""


class AlmacenamientoAdjuntoError(Exception):
    """Summary: Señala un error explícito al guardar o limpiar un adjunto."""


def Validar_Adjunto_PDF(
    Nombre_Archivo: str,
    Tipo_Contenido: str,
    Contenido: bytes,
) -> None:
    """Summary: Valida extensión, MIME, firma y tamaño máximo del PDF recibido."""
    # La validación no confía solamente en el nombre enviado por el cliente.
    if Path(Nombre_Archivo).suffix.casefold() != ".pdf":
        raise AdjuntoPDFInvalidoError("El archivo adjunto debe tener extensión .pdf.")
    if Tipo_Contenido != "application/pdf":
        raise AdjuntoPDFInvalidoError(
            "El tipo de contenido del adjunto debe ser application/pdf."
        )
    if len(Contenido) > TAMANO_MAXIMO_PDF_BYTES:
        raise AdjuntoPDFInvalidoError("El archivo PDF no puede superar 5 MB.")
    if not Contenido.startswith(b"%PDF-"):
        raise AdjuntoPDFInvalidoError("El contenido del archivo no tiene firma PDF.")


def Eliminar_Adjunto_Si_Existe(Ruta_Archivo: Path) -> None:
    """Summary: Elimina un archivo parcial o huérfano sin ocultar fallos de disco."""
    # La ruta la construye el servicio dentro del directorio controlado del backend.
    try:
        Ruta_Archivo.unlink(missing_ok=True)
    except OSError as Error:
        raise AlmacenamientoAdjuntoError(
            "No se pudo limpiar el archivo PDF después de un error."
        ) from Error


def Crear_Ausencia(
    Db_Sesion: Session,
    Datos_Ausencia: AusenciaCreate,
    Contenido_PDF: bytes | None = None,
    Nombre_Archivo: str | None = None,
    Tipo_Contenido: str | None = None,
) -> Ausencia:
    """Summary: Verifica referencias y crea una solicitud pendiente con adjunto opcional."""
    # Las referencias se validan primero para evitar escribir archivos de solicitudes inválidas.
    if not Db_Sesion.query(Empleado.id).filter(
        Empleado.id == Datos_Ausencia.empleado_id
    ).first():
        raise EmpleadoNoEncontradoError("El empleado indicado no existe.")
    if not Db_Sesion.query(TipoAusencia.id).filter(
        TipoAusencia.id == Datos_Ausencia.tipo_ausencia_id
    ).first():
        raise TipoAusenciaNoEncontradoError("El tipo de ausencia indicado no existe.")

    Ruta_Archivo: Path | None = None
    Nombre_Interno: str | None = None
    if Contenido_PDF is not None:
        if Nombre_Archivo is None or Tipo_Contenido is None:
            raise AdjuntoPDFInvalidoError(
                "Se requieren nombre y tipo de contenido para el adjunto."
            )
        Validar_Adjunto_PDF(Nombre_Archivo, Tipo_Contenido, Contenido_PDF)
        Nombre_Interno = f"{uuid4().hex}.pdf"
        Ruta_Archivo = DIRECTORIO_ADJUNTOS / Nombre_Interno

    Nueva_Ausencia = Ausencia(
        empleado_id=Datos_Ausencia.empleado_id,
        tipo_ausencia_id=Datos_Ausencia.tipo_ausencia_id,
        fecha_inicio=Datos_Ausencia.fecha_inicio,
        fecha_fin=Datos_Ausencia.fecha_fin,
        descripcion=Datos_Ausencia.descripcion,
        archivo_pdf_ruta=Nombre_Interno,
        estado_aprobacion=EstadoAprobacion.Pendiente.value,
        fecha_solicitud=datetime.now(),
    )

    try:
        # El nombre generado evita rutas controladas por el cliente y colisiones previsibles.
        if Ruta_Archivo is not None and Contenido_PDF is not None:
            DIRECTORIO_ADJUNTOS.mkdir(parents=True, exist_ok=True)
            Ruta_Archivo.write_bytes(Contenido_PDF)
        Db_Sesion.add(Nueva_Ausencia)
        Db_Sesion.commit()
    except OSError as Error:
        Db_Sesion.rollback()
        if Ruta_Archivo is not None:
            Eliminar_Adjunto_Si_Existe(Ruta_Archivo)
        raise AlmacenamientoAdjuntoError(
            "No se pudo guardar el archivo PDF adjunto."
        ) from Error
    except SQLAlchemyError:
        # Si la transacción falla, se quita el archivo que aún no tiene registro asociado.
        Db_Sesion.rollback()
        if Ruta_Archivo is not None:
            Eliminar_Adjunto_Si_Existe(Ruta_Archivo)
        raise
    return Nueva_Ausencia


def Listar_Ausencias(
    Db_Sesion: Session,
    Empleado_Id: int | None,
    Estado_Aprobacion: EstadoAprobacion | None,
    Fecha_Desde: date | None,
    Fecha_Hasta: date | None,
    Limite: int,
    Desplazamiento: int,
) -> tuple[list[Ausencia], int]:
    """Summary: Lista solicitudes paginadas aplicando filtros de estado, empleado y fechas."""
    # El rango incluye solicitudes que se solapan con cualquier día del intervalo consultado.
    Consulta = Db_Sesion.query(Ausencia)
    if Empleado_Id is not None:
        Consulta = Consulta.filter(Ausencia.empleado_id == Empleado_Id)
    if Estado_Aprobacion is not None:
        Consulta = Consulta.filter(
            Ausencia.estado_aprobacion == Estado_Aprobacion.value
        )
    if Fecha_Desde is not None:
        Consulta = Consulta.filter(Ausencia.fecha_fin >= Fecha_Desde)
    if Fecha_Hasta is not None:
        Consulta = Consulta.filter(Ausencia.fecha_inicio <= Fecha_Hasta)
    Total = Consulta.count()
    Items = (
        Consulta.order_by(Ausencia.fecha_solicitud.desc(), Ausencia.id.desc())
        .offset(Desplazamiento)
        .limit(Limite)
        .all()
    )
    return Items, Total


def Obtener_Ausencia(Db_Sesion: Session, Ausencia_Id: int) -> Ausencia | None:
    """Summary: Busca una solicitud por su identificador principal."""
    # La ruta decide el código HTTP cuando la consulta no encuentra una fila.
    return Db_Sesion.query(Ausencia).filter(Ausencia.id == Ausencia_Id).first()


def Obtener_Archivo_PDF(
    Db_Sesion: Session,
    Ausencia_Id: int,
) -> tuple[Ausencia, Path] | None:
    """Summary: Resuelve el adjunto de una solicitud dentro del directorio permitido."""
    # La base solo conserva el nombre generado; nunca se interpreta como una ruta absoluta.
    Registro_Ausencia = Obtener_Ausencia(Db_Sesion, Ausencia_Id)
    if Registro_Ausencia is None or not Registro_Ausencia.archivo_pdf_ruta:
        return None
    Nombre_Archivo = Registro_Ausencia.archivo_pdf_ruta
    if Path(Nombre_Archivo).name != Nombre_Archivo:
        return None
    Directorio_Seguro = DIRECTORIO_ADJUNTOS.resolve()
    Ruta_Archivo = (Directorio_Seguro / Nombre_Archivo).resolve()
    if Ruta_Archivo.parent != Directorio_Seguro or not Ruta_Archivo.is_file():
        return None
    return Registro_Ausencia, Ruta_Archivo


def Decidir_Ausencia(
    Db_Sesion: Session,
    Ausencia_Id: int,
    Estado_Final: EstadoAprobacion,
    Usuario_Revisor_Id: int,
) -> Ausencia:
    """Summary: Aprueba o rechaza atómicamente una solicitud que siga pendiente."""
    # El identificador temporal se valida contra usuario sin afirmar que autentica al cliente.
    if not Db_Sesion.query(Usuario.id).filter(
        Usuario.id == Usuario_Revisor_Id
    ).first():
        raise UsuarioRevisorNoEncontradoError("El usuario revisor indicado no existe.")

    try:
        Resultado = Db_Sesion.execute(
            update(Ausencia)
            .where(
                Ausencia.id == Ausencia_Id,
                Ausencia.estado_aprobacion == EstadoAprobacion.Pendiente.value,
            )
            .values(
                estado_aprobacion=Estado_Final.value,
                aprobado_por_usuario_id=Usuario_Revisor_Id,
            )
            .execution_options(synchronize_session="fetch")
        )
        if Resultado.rowcount == 0:
            Db_Sesion.rollback()
            if not Db_Sesion.query(Ausencia.id).filter(
                Ausencia.id == Ausencia_Id
            ).first():
                raise AusenciaNoEncontradaError(
                    "La solicitud de ausencia no existe."
                )
            raise DecisionAusenciaConflictError(
                "Solo se pueden decidir solicitudes en estado Pendiente."
            )
        Db_Sesion.commit()
    except SQLAlchemyError:
        Db_Sesion.rollback()
        raise
    Registro_Ausencia = Obtener_Ausencia(Db_Sesion, Ausencia_Id)
    if Registro_Ausencia is None:
        raise AusenciaNoEncontradaError("La solicitud de ausencia no existe.")
    return Registro_Ausencia
