// SUMMARY: Proporciona acciones de descarga PDF y XLSX con feedback de la solicitud.

import { useState } from 'react'
import { downloadDashboardReport } from '../services/dashboardService'

/**
 * Summary: Solicita una exportación y dispara la descarga del archivo recibido.
 * @param {object} filters Filtros actuales aplicados al dashboard.
 * @returns {JSX.Element} Acciones PDF/XLSX y mensajes de estado.
 */
export default function ReportExportActions({ filters }) {
  const [exportingFormat, setExportingFormat] = useState('')
  const [exportError, setExportError] = useState('')

  async function exportReport(format) {
    setExportingFormat(format)
    setExportError('')

    try {
      // El archivo descargado usa los filtros vigentes y el nombre del backend.
      const { blob, filename } = await downloadDashboardReport(format, filters)
      const objectUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = objectUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
    } catch (error) {
      setExportError(error.message || 'No se pudo generar el archivo.')
    } finally {
      setExportingFormat('')
    }
  }

  return (
    <div className="dashboard-export-actions">
      <button
        className="dashboard-button dashboard-button--secondary"
        disabled={Boolean(exportingFormat)}
        onClick={() => exportReport('xlsx')}
        type="button"
      >
        {exportingFormat === 'xlsx' ? 'Generando Excel...' : 'Exportar Excel'}
      </button>
      <button
        className="dashboard-button dashboard-button--primary"
        disabled={Boolean(exportingFormat)}
        onClick={() => exportReport('pdf')}
        type="button"
      >
        {exportingFormat === 'pdf' ? 'Generando PDF...' : 'Exportar PDF'}
      </button>
      {exportError && (
        <p className="dashboard-form-error" role="alert">
          {exportError}
        </p>
      )}
    </div>
  )
}
