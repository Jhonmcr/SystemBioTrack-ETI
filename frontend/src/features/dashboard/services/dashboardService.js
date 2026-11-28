// SUMMARY: Centraliza las consultas HTTP y las descargas del dashboard estadístico.

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const API_V1_URL = `${API_BASE_URL}/api/v1`

/**
 * Summary: Convierte filtros de dashboard en parámetros de URL sin valores vacíos.
 * @param {object} filters Filtros de fecha y horario aplicados por el usuario.
 * @returns {URLSearchParams} Parámetros listos para una solicitud GET.
 */
function createFilterParams(filters) {
  const params = new URLSearchParams()

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.set(key, String(value))
    }
  })

  return params
}

/**
 * Summary: Construye un error legible a partir de respuestas HTTP no exitosas.
 * @param {Response} response Respuesta recibida desde FastAPI.
 * @returns {Promise<Error>} Error con el detalle enviado por el servidor.
 */
async function createHttpError(response) {
  const responseText = await response.text()
  let message

  // FastAPI suele enviar el error como JSON; el texto original se conserva si no lo es.
  try {
    const body = JSON.parse(responseText)
    message =
      typeof body.detail === 'string' ? body.detail : response.statusText
  } catch {
    message = responseText || response.statusText
  }

  return new Error(message || `La solicitud falló (${response.status}).`)
}

/**
 * Summary: Consulta el resumen de indicadores y series para los filtros recibidos.
 * @param {object} filters Rango de fechas y horario.
 * @param {AbortSignal} [signal] Señal opcional para cancelar solicitudes obsoletas.
 * @returns {Promise<object>} Datos agregados del dashboard.
 */
export async function getDashboardSummary(filters, signal) {
  const params = createFilterParams(filters)
  const response = await fetch(`${API_V1_URL}/dashboard/summary?${params}`, {
    signal,
  })

  if (!response.ok) {
    throw await createHttpError(response)
  }

  return response.json()
}

/**
 * Summary: Obtiene el consolidado de tardanzas agrupado por empleado.
 * @param {object} filters Rango de fechas y horario admitidos por el endpoint.
 * @param {AbortSignal} [signal] Señal opcional para cancelar solicitudes obsoletas.
 * @returns {Promise<object>} Resumen y detalle de llegadas tardías.
 */
export async function getTardinessReport(filters, signal) {
  const params = createFilterParams(filters)
  const response = await fetch(
    `${API_V1_URL}/attendance/reports/tardiness?${params}`,
    { signal },
  )

  if (!response.ok) {
    throw await createHttpError(response)
  }

  return response.json()
}

/**
 * Summary: Descarga el informe del dashboard como PDF o libro XLSX.
 * @param {'pdf'|'xlsx'} format Formato solicitado al endpoint de exportación.
 * @param {object} filters Rango de fechas y horario que se exportarán.
 * @returns {Promise<{blob: Blob, filename: string}>} Archivo y nombre sugerido.
 */
export async function downloadDashboardReport(format, filters) {
  const params = createFilterParams({ ...filters, format })
  const response = await fetch(`${API_V1_URL}/dashboard/export?${params}`)

  if (!response.ok) {
    throw await createHttpError(response)
  }

  // El servidor define el nombre; se usa uno local si el encabezado no está presente.
  const disposition = response.headers.get('Content-Disposition') || ''
  const filenameMatch = disposition.match(/filename="?([^";]+)"?/i)
  const fallbackFilename = `dashboard.${format}`

  return {
    blob: await response.blob(),
    filename: filenameMatch?.[1] || fallbackFilename,
  }
}
