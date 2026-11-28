# SUMMARY: Genera archivos Excel y PDF a partir del contrato estadístico del dashboard.
"""Summary: Construye exportaciones XLSX y PDF sin acoplarlas a las rutas HTTP."""

from html import escape
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.dashboard import DashboardSummaryResponse


def _Valor_Excel_Seguro(Valor: str | int | float) -> str | int | float:
    """Summary: Evita que texto de etiquetas se interprete como fórmula en Excel."""
    # Los valores textuales externos que inician con prefijos de fórmula se escapan.
    if isinstance(Valor, str) and Valor.startswith(("=", "+", "-", "@")):
        return "'" + Valor
    return Valor


def Generar_Reporte_XLSX(Resumen: DashboardSummaryResponse) -> BytesIO:
    """Summary: Crea un libro XLSX con indicadores, series, cargos y causas."""
    # Cada grupo de datos se entrega en su propia hoja para facilitar el análisis.
    Libro = Workbook()
    Hoja_KPI = Libro.active
    Hoja_KPI.title = "Indicadores"
    Hoja_KPI.append(["Indicador", "Valor"])
    Hoja_KPI.append(["Desde", Resumen.filters.start_date.isoformat()])
    Hoja_KPI.append(["Hasta", Resumen.filters.end_date.isoformat()])
    Hoja_KPI.append(["Horario ID", Resumen.filters.horario_id or "Todos"])
    Hoja_KPI.append(["Cargo ID", Resumen.filters.cargo_id or "Todos"])
    Hoja_KPI.append(["Total de registros", Resumen.metrics.total_registros])
    Hoja_KPI.append(["Asistencias puntuales", Resumen.metrics.asistencias_puntuales])
    Hoja_KPI.append(["Inasistencias", Resumen.metrics.inasistencias])
    Hoja_KPI.append(["Tasa de ausentismo (%)", Resumen.metrics.tasa_ausentismo])
    Hoja_KPI.append(["Llegadas tardías", Resumen.metrics.total_retardos])
    Hoja_KPI.append(["Ausencias justificadas", Resumen.metrics.ausencias_justificadas])

    Hoja_Serie = Libro.create_sheet("Evolución diaria")
    Hoja_Serie.append(
        ["Fecha", "Asistencias puntuales", "Retardos", "Inasistencias"]
    )
    for Punto in Resumen.series:
        Hoja_Serie.append(
            [
                Punto.fecha.isoformat(),
                Punto.asistencias_puntuales,
                Punto.retardos,
                Punto.inasistencias,
            ]
        )

    Hoja_Cargos = Libro.create_sheet("Por cargo")
    Hoja_Cargos.append(
        [
            "Cargo",
            "Total de registros",
            "Inasistencias",
            "Tasa de ausentismo (%)",
            "Retardos",
        ]
    )
    for Cargo in Resumen.por_cargo:
        Hoja_Cargos.append(
            [
                _Valor_Excel_Seguro(Cargo.cargo),
                Cargo.total_registros,
                Cargo.inasistencias,
                Cargo.tasa_ausentismo,
                Cargo.retardos,
            ]
        )

    Hoja_Causas = Libro.create_sheet("Causas de ausencia")
    Hoja_Causas.append(["Tipo de ausencia", "Total aprobado"])
    for Causa in Resumen.causas_ausencia:
        Hoja_Causas.append([_Valor_Excel_Seguro(Causa.tipo_ausencia), Causa.total])

    # El formato uniforme mejora la lectura sin cambiar los valores exportados.
    for Hoja in Libro.worksheets:
        Hoja.freeze_panes = "A2"
        Hoja.auto_filter.ref = Hoja.dimensions
        for Celda in Hoja[1]:
            Celda.font = Font(bold=True, color="FFFFFF")
            Celda.fill = PatternFill("solid", fgColor="881337")
        for Columna in Hoja.columns:
            Ancho = min(
                max(
                    len(str(Celda.value or ""))
                    for Celda in Columna
                )
                + 2,
                40,
            )
            Hoja.column_dimensions[Columna[0].column_letter].width = max(Ancho, 12)

    Archivo = BytesIO()
    Libro.save(Archivo)
    Archivo.seek(0)
    return Archivo


def Generar_Reporte_PDF(Resumen: DashboardSummaryResponse) -> BytesIO:
    """Summary: Crea un PDF legible con los KPI y desgloses del dashboard."""
    # El PDF apaisado permite presentar las tablas de cargos en una sola página.
    Archivo = BytesIO()
    Documento = SimpleDocTemplate(
        Archivo,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Reporte estadístico de asistencia",
    )
    Estilos = getSampleStyleSheet()
    Elementos: list[object] = [
        Paragraph("Dashboard Estadístico y Reportes", Estilos["Title"]),
        Paragraph(
            (
                f"Rango: {Resumen.filters.start_date.isoformat()} a "
                f"{Resumen.filters.end_date.isoformat()}"
            ),
            Estilos["Normal"],
        ),
        Spacer(1, 8 * mm),
        Paragraph("Indicadores", Estilos["Heading2"]),
    ]

    # La tabla resume los valores sin incluir datos personales en la exportación.
    Filas_KPI = [
        ["Indicador", "Valor"],
        ["Total de registros", str(Resumen.metrics.total_registros)],
        ["Asistencias puntuales", str(Resumen.metrics.asistencias_puntuales)],
        ["Inasistencias", str(Resumen.metrics.inasistencias)],
        ["Tasa de ausentismo", f"{Resumen.metrics.tasa_ausentismo:.2f}%"],
        ["Llegadas tardías", str(Resumen.metrics.total_retardos)],
        ["Ausencias justificadas", str(Resumen.metrics.ausencias_justificadas)],
    ]
    Elementos.extend(
        [
            _Crear_Tabla_PDF(Filas_KPI),
            Spacer(1, 5 * mm),
            Paragraph("Asistencia por cargo", Estilos["Heading2"]),
        ]
    )

    # Las etiquetas procedentes del catálogo se escapan antes de insertarse como XML.
    Filas_Cargos = [
        [
            "Cargo",
            "Registros",
            "Inasistencias",
            "Ausentismo (%)",
            "Retardos",
        ]
    ]
    for Cargo in Resumen.por_cargo:
        Filas_Cargos.append(
            [
                Paragraph(escape(Cargo.cargo), Estilos["BodyText"]),
                str(Cargo.total_registros),
                str(Cargo.inasistencias),
                f"{Cargo.tasa_ausentismo:.2f}",
                str(Cargo.retardos),
            ]
        )
    Elementos.extend(
        [
            _Crear_Tabla_PDF(Filas_Cargos),
            Spacer(1, 5 * mm),
            Paragraph("Causas de ausencia aprobadas", Estilos["Heading2"]),
        ]
    )

    Filas_Causas = [["Tipo de ausencia", "Total aprobado"]]
    for Causa in Resumen.causas_ausencia:
        Filas_Causas.append(
            [
                Paragraph(escape(Causa.tipo_ausencia), Estilos["BodyText"]),
                str(Causa.total),
            ]
        )
    Elementos.append(_Crear_Tabla_PDF(Filas_Causas))
    Documento.build(Elementos)
    Archivo.seek(0)
    return Archivo


def _Crear_Tabla_PDF(Filas: list[list[object]]) -> Table:
    """Summary: Aplica formato tabular común a secciones del documento PDF."""
    # La primera fila funciona como encabezado y se repite si la tabla ocupa varias páginas.
    Tabla = Table(Filas, repeatRows=1, hAlign="LEFT")
    Tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#881337")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F8FAFC")],
                ),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return Tabla
