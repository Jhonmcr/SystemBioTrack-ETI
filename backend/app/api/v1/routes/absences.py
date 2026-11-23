"""Summary: Expone los endpoints HTTP del módulo de permisos y justificativos."""

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.models import TipoAusencia
from app.db.session import get_db
from app.schemas.absence import (
    AusenciaCreate,
    AusenciaDecision,
    AusenciaPage,
    AusenciaRead,
    EstadoAprobacion,
    TipoAusenciaRead,
)
from app.services.absence_service import (
    TAMANO_MAXIMO_PDF_BYTES,
    AdjuntoPDFInvalidoError,
    AlmacenamientoAdjuntoError,
    AusenciaNoEncontradaError,
    DecisionAusenciaConflictError,
    EmpleadoNoEncontradoError,
    TipoAusenciaNoEncontradoError,
    UsuarioRevisorNoEncontradoError,
    Crear_Ausencia,
    Decidir_Ausencia,
    Listar_Ausencias,
    Obtener_Archivo_PDF,
    Obtener_Ausencia,
)

Router_Ausencias = APIRouter()


def Obtener_Usuario_Revisor_Temporal(
    aprobado_por_usuario_id: int = Query(..., gt=0),
) -> int:
    """Summary: Obtiene temporalmente el ID de revisor desde un parámetro de consulta."""
    # TODO: reemplazar por usuario autenticado del Módulo 1.
    return aprobado_por_usuario_id


@Router_Ausencias.get(
    "/absence-types",
    response_model=list[TipoAusenciaRead],
    summary="Listar tipos de ausencia",
)
def Obtener_Tipos_Ausencia(
    Db_Sesion: Session = Depends(get_db),
) -> list[TipoAusencia]:
    """Summary: Devuelve el catálogo de tipos de ausencia ordenado por identificador."""
    # El endpoint solo expone el catálogo existente; no crea tipos implícitamente.
    return Db_Sesion.query(TipoAusencia).order_by(TipoAusencia.id).all()


@Router_Ausencias.post(
    "/absences",
    response_model=AusenciaRead,
    status_code=201,
    summary="Crear una solicitud de ausencia",
)
async def Crear_Solicitud_Ausencia(
    empleado_id: int = Form(..., gt=0),
    tipo_ausencia_id: int = Form(..., gt=0),
    fecha_inicio: date = Form(...),
    fecha_fin: date = Form(...),
    descripcion: str | None = Form(default=None),
    archivo_pdf: UploadFile | None = File(default=None),
    Db_Sesion: Session = Depends(get_db),
) -> AusenciaRead:
    """Summary: Valida el formulario multipart y persiste solicitud y PDF opcional."""
    # El modelo Pydantic aplica la misma regla de fechas antes de tocar la base de datos.
    try:
        Datos_Ausencia = AusenciaCreate(
            empleado_id=empleado_id,
            tipo_ausencia_id=tipo_ausencia_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            descripcion=descripcion,
        )
    except ValidationError as Error:
        raise HTTPException(status_code=422, detail=str(Error)) from Error

    Contenido_PDF: bytes | None = None
    Nombre_Archivo: str | None = None
    Tipo_Contenido: str | None = None
    if archivo_pdf is not None:
        # Se limita la lectura a un byte sobre el máximo para detectar archivos grandes.
        try:
            Contenido_PDF = await archivo_pdf.read(TAMANO_MAXIMO_PDF_BYTES + 1)
        finally:
            await archivo_pdf.close()
        Nombre_Archivo = archivo_pdf.filename or ""
        Tipo_Contenido = archivo_pdf.content_type or ""

    try:
        Registro_Ausencia = Crear_Ausencia(
            Db_Sesion,
            Datos_Ausencia,
            Contenido_PDF=Contenido_PDF,
            Nombre_Archivo=Nombre_Archivo,
            Tipo_Contenido=Tipo_Contenido,
        )
    except (EmpleadoNoEncontradoError, TipoAusenciaNoEncontradoError) as Error:
        raise HTTPException(status_code=404, detail=str(Error)) from Error
    except AdjuntoPDFInvalidoError as Error:
        raise HTTPException(status_code=400, detail=str(Error)) from Error
    except AlmacenamientoAdjuntoError as Error:
        raise HTTPException(status_code=500, detail=str(Error)) from Error
    return AusenciaRead.model_validate(Registro_Ausencia)


@Router_Ausencias.get(
    "/absences",
    response_model=AusenciaPage,
    summary="Listar solicitudes de ausencia",
)
def Obtener_Solicitudes_Ausencia(
    empleado_id: int | None = Query(default=None, gt=0),
    estado_aprobacion: EstadoAprobacion | None = Query(default=None),
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    Db_Sesion: Session = Depends(get_db),
) -> AusenciaPage:
    """Summary: Consulta solicitudes con filtros de empleado, estado, fechas y página."""
    # Los rangos invertidos se rechazan para evitar una consulta vacía ambigua.
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=422,
            detail="fecha_desde debe ser menor o igual que fecha_hasta.",
        )
    Registros, Total = Listar_Ausencias(
        Db_Sesion,
        empleado_id,
        estado_aprobacion,
        fecha_desde,
        fecha_hasta,
        limit,
        offset,
    )
    return AusenciaPage(
        items=[AusenciaRead.model_validate(Registro) for Registro in Registros],
        total=Total,
        limit=limit,
        offset=offset,
    )


@Router_Ausencias.get(
    "/absences/{ausencia_id}",
    response_model=AusenciaRead,
    summary="Consultar una solicitud de ausencia",
)
def Obtener_Solicitud_Ausencia(
    ausencia_id: int,
    Db_Sesion: Session = Depends(get_db),
) -> AusenciaRead:
    """Summary: Devuelve el detalle de una solicitud o HTTP 404 si no existe."""
    # La ruta no expone la ruta física del adjunto; solo su indicador de disponibilidad.
    Registro_Ausencia = Obtener_Ausencia(Db_Sesion, ausencia_id)
    if Registro_Ausencia is None:
        raise HTTPException(status_code=404, detail="La solicitud de ausencia no existe.")
    return AusenciaRead.model_validate(Registro_Ausencia)


@Router_Ausencias.get(
    "/absences/{ausencia_id}/pdf",
    summary="Descargar el PDF adjunto de una solicitud",
)
def Descargar_Adjunto_Ausencia(
    ausencia_id: int,
    Db_Sesion: Session = Depends(get_db),
) -> FileResponse:
    """Summary: Entrega el PDF existente desde el almacenamiento privado del backend."""
    # Solo se permite resolver nombres generados dentro del directorio controlado.
    Adjunto = Obtener_Archivo_PDF(Db_Sesion, ausencia_id)
    if Adjunto is None:
        raise HTTPException(
            status_code=404,
            detail="La solicitud o su archivo PDF no existe.",
        )
    Registro_Ausencia, Ruta_Archivo = Adjunto
    return FileResponse(
        path=Ruta_Archivo,
        media_type="application/pdf",
        filename=f"justificativo_{Registro_Ausencia.id}.pdf",
    )


@Router_Ausencias.patch(
    "/absences/{ausencia_id}/decision",
    response_model=AusenciaRead,
    summary="Aprobar o rechazar una solicitud",
)
def Decidir_Solicitud_Ausencia(
    ausencia_id: int,
    decision: AusenciaDecision,
    Usuario_Revisor_Id: int = Depends(Obtener_Usuario_Revisor_Temporal),
    Db_Sesion: Session = Depends(get_db),
) -> AusenciaRead:
    """Summary: Registra la decisión final de una solicitud que siga pendiente."""
    # No se modifica asistencia_diaria; el efecto de una aprobación queda fuera del alcance.
    try:
        Registro_Ausencia = Decidir_Ausencia(
            Db_Sesion,
            ausencia_id,
            EstadoAprobacion(decision.estado_aprobacion),
            Usuario_Revisor_Id,
        )
    except UsuarioRevisorNoEncontradoError as Error:
        raise HTTPException(status_code=404, detail=str(Error)) from Error
    except AusenciaNoEncontradaError as Error:
        raise HTTPException(status_code=404, detail=str(Error)) from Error
    except DecisionAusenciaConflictError as Error:
        raise HTTPException(status_code=409, detail=str(Error)) from Error
    return AusenciaRead.model_validate(Registro_Ausencia)
