// SUMMARY: Orquesta filtros, métricas, gráficos, tardanzas y exportación del Módulo 5.

import { useEffect, useState } from 'react'
import AbsenceByCargoChart from '../components/AbsenceByCargoChart'
import AttendanceTrendChart from '../components/AttendanceTrendChart'
import DashboardFilters from '../components/DashboardFilters'
import DashboardKpiCards from '../components/DashboardKpiCards'
import ReportExportActions from '../components/ReportExportActions'
import TardinessReportTable from '../components/TardinessReportTable'
import {
  getDashboardSummary,
  getTardinessReport,
} from '../services/dashboardService'

const DASHBOARD_STYLES = `
  .dashboard-page {
    box-sizing: border-box;
    width: 100%;
    min-height: 100vh;
    padding: 28px clamp(16px, 3vw, 40px);
    color: #1e293b;
    background: #f1f5f9;
    text-align: left;
    font: 14px/1.5 Inter, system-ui, sans-serif;
  }
  .dashboard-page * { box-sizing: border-box; }
  .dashboard-header, .dashboard-panel-heading, .dashboard-filter-actions,
  .dashboard-export-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  .dashboard-header { margin-bottom: 20px; flex-wrap: wrap; }
  .dashboard-page h1 {
    margin: 0;
    color: #0f172a;
    font-size: clamp(24px, 3vw, 32px);
    font-weight: 750;
    letter-spacing: -0.04em;
  }
  .dashboard-page h2, .dashboard-page h3 { margin: 0; color: #0f172a; }
  .dashboard-page p { margin: 0; }
  .dashboard-intro, .dashboard-panel-subtitle { margin-top: 4px !important; color: #64748b; }
  .dashboard-filter-bar, .dashboard-panel, .dashboard-kpi-card {
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    background: #fff;
    box-shadow: 0 2px 6px rgba(15, 23, 42, .04);
  }
  .dashboard-filter-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: end;
    gap: 12px;
    padding: 16px;
    margin-bottom: 18px;
  }
  .dashboard-field { display: grid; min-width: 150px; gap: 5px; color: #475569; font-size: 12px; font-weight: 650; }
  .dashboard-field input {
    min-height: 38px;
    padding: 7px 10px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    background: #fff;
    color: #0f172a;
    font: inherit;
  }
  .dashboard-field input:focus { outline: 2px solid #93c5fd; outline-offset: 1px; }
  .dashboard-field--schedule { min-width: 180px; }
  .dashboard-filter-actions { justify-content: flex-start; }
  .dashboard-button {
    min-height: 38px;
    padding: 8px 13px;
    border: 1px solid transparent;
    border-radius: 8px;
    cursor: pointer;
    font: inherit;
    font-size: 12px;
    font-weight: 700;
    transition: background .15s ease, opacity .15s ease;
  }
  .dashboard-button:disabled { cursor: wait; opacity: .6; }
  .dashboard-button--primary { background: #881337; color: #fff; }
  .dashboard-button--primary:hover:not(:disabled) { background: #6b102e; }
  .dashboard-button--secondary { border-color: #cbd5e1; background: #fff; color: #334155; }
  .dashboard-button--secondary:hover:not(:disabled) { background: #f8fafc; }
  .dashboard-form-error { flex-basis: 100%; color: #be123c; font-size: 12px; }
  .dashboard-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin-bottom: 18px;
  }
  .dashboard-kpi-card { min-height: 116px; padding: 17px; border-top: 3px solid #0369a1; }
  .dashboard-kpi-card--rose { border-top-color: #be123c; }
  .dashboard-kpi-card--amber { border-top-color: #d97706; }
  .dashboard-kpi-card--teal { border-top-color: #0f766e; }
  .dashboard-kpi-label { color: #64748b; font-size: 12px; font-weight: 700; }
  .dashboard-kpi-value { display: block; margin-top: 10px; color: #0f172a; font-size: 28px; line-height: 1.1; }
  .dashboard-kpi-card--loading { display: grid; align-content: center; gap: 14px; }
  .dashboard-skeleton { display: block; border-radius: 6px; background: #e2e8f0; animation: dashboard-pulse 1.2s ease-in-out infinite alternate; }
  .dashboard-skeleton--label { width: 60%; height: 12px; }
  .dashboard-skeleton--value { width: 42%; height: 28px; }
  @keyframes dashboard-pulse { to { opacity: .45; } }
  .dashboard-content-grid { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr); gap: 16px; }
  .dashboard-panel { min-width: 0; padding: 18px; margin-bottom: 18px; }
  .dashboard-panel-title { font-size: 17px; font-weight: 750; letter-spacing: -.02em; }
  .dashboard-panel-subtitle { font-size: 12px; }
  .dashboard-chart { width: 100%; height: 290px; margin-top: 18px; }
  .dashboard-chart--compact { height: 220px; margin-top: 10px; }
  .dashboard-distribution-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 18px; }
  .dashboard-chart-title { color: #334155 !important; font-size: 13px; font-weight: 700; }
  .dashboard-chart-placeholder, .dashboard-empty, .dashboard-loading-message {
    display: grid;
    min-height: 120px;
    place-items: center;
    padding: 18px;
    color: #64748b;
    text-align: center;
  }
  .dashboard-kpi-empty { min-height: auto; margin-bottom: 18px !important; }
  .dashboard-error {
    padding: 12px 14px;
    margin-bottom: 16px;
    border: 1px solid #fecdd3;
    border-radius: 9px;
    background: #fff1f2;
    color: #9f1239;
  }
  .dashboard-export-actions { justify-content: flex-end; flex-wrap: wrap; }
  .dashboard-export-actions .dashboard-form-error { flex-basis: 100%; text-align: right; }
  .dashboard-table-wrapper { width: 100%; overflow-x: auto; margin-top: 14px; }
  .dashboard-table { width: 100%; border-collapse: collapse; text-align: left; }
  .dashboard-table th, .dashboard-table td { padding: 11px 12px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
  .dashboard-table th { background: #f8fafc; color: #475569; font-size: 11px; text-transform: uppercase; }
  .dashboard-table td { color: #334155; font-size: 13px; }
  @media (max-width: 900px) {
    .dashboard-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .dashboard-content-grid { grid-template-columns: 1fr; }
  }
  @media (max-width: 560px) {
    .dashboard-filter-bar { align-items: stretch; }
    .dashboard-field, .dashboard-field--schedule { width: 100%; }
    .dashboard-filter-actions { width: 100%; }
    .dashboard-filter-actions .dashboard-button { flex: 1; }
    .dashboard-kpi-grid, .dashboard-distribution-grid { grid-template-columns: 1fr; }
    .dashboard-header { align-items: flex-start; }
    .dashboard-export-actions { justify-content: flex-start; }
  }
`

/** Summary: Crea los filtros iniciales para el mes calendario actual. */
function getDefaultFilters() {
  // Al iniciar, el dashboard muestra desde el primer día del mes hasta hoy.
  const today = new Date()
  /** Summary: Formatea una fecha local sin convertirla a otra zona horaria. */
  const toLocalDateString = (date) => {
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${date.getFullYear()}-${month}-${day}`
  }
  const endDate = toLocalDateString(today)
  const startDate = toLocalDateString(
    new Date(today.getFullYear(), today.getMonth(), 1),
  )

  return { start_date: startDate, end_date: endDate, horario_id: '' }
}

/**
 * Summary: Carga resumen y tardanzas en paralelo con estados independientes.
 * @param {object} filters Filtros aplicados por el usuario.
 * @returns {JSX.Element} Indicadores, gráficos y reporte de tardanzas.
 */
function DashboardDataView({ filters }) {
  const [summary, setSummary] = useState(null)
  const [tardiness, setTardiness] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(true)
  const [tardinessLoading, setTardinessLoading] = useState(true)
  const [summaryError, setSummaryError] = useState('')
  const [tardinessError, setTardinessError] = useState('')

  // Summary: Suscribe consultas paralelas y cancela las solicitudes de filtros anteriores.
  // Cada endpoint se resuelve de forma independiente para preservar resultados parciales.
  useEffect(() => {
    const controller = new AbortController()

    getDashboardSummary(filters, controller.signal)
      .then(setSummary)
      .catch((error) => {
        // El error de un endpoint no interrumpe la carga independiente del otro.
        if (error.name !== 'AbortError') {
          setSummaryError(error.message || 'No se pudo cargar el resumen estadístico.')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setSummaryLoading(false)
      })

    // El endpoint actual soporta fecha y horario, los mismos filtros del resumen.
    getTardinessReport(filters, controller.signal)
      .then(setTardiness)
      .catch((error) => {
        // El error se muestra en su propia sección y conserva el resto del dashboard.
        if (error.name !== 'AbortError') {
          setTardinessError(error.message || 'No se pudo cargar el reporte de tardanzas.')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setTardinessLoading(false)
      })

    // La limpieza evita aplicar respuestas de filtros que ya fueron reemplazados.
    return () => controller.abort()
  }, [filters])

  return (
    <>
      {summaryError && (
        <p className="dashboard-error" role="alert">
          Error al cargar indicadores y gráficos: {summaryError}
        </p>
      )}
      {tardinessError && (
        <p className="dashboard-error" role="alert">
          Error al cargar el reporte de tardanzas: {tardinessError}
        </p>
      )}

      <DashboardKpiCards
        loading={summaryLoading}
        metrics={summary?.metrics || null}
      />

      <div className="dashboard-content-grid">
        <AttendanceTrendChart
          data={summary?.series || []}
          loading={summaryLoading}
        />
        <AbsenceByCargoChart
          byCargo={summary?.por_cargo || []}
          causes={summary?.causas_ausencia || []}
          loading={summaryLoading}
        />
      </div>

      <TardinessReportTable loading={tardinessLoading} report={tardiness} />
    </>
  )
}

/**
 * Summary: Coordina filtros, consultas y acciones de exportación del Módulo 5.
 * @returns {JSX.Element} Página estadística con reportes descargables.
 */
export default function DashboardPage() {
  const [filters, setFilters] = useState(getDefaultFilters)

  /** Summary: Restablece el formulario y los datos al rango predeterminado. */
  function resetFilters() {
    const defaultFilters = getDefaultFilters()
    setFilters(defaultFilters)
    return defaultFilters
  }

  return (
    <main className="dashboard-page">
      <style>{DASHBOARD_STYLES}</style>
      <header className="dashboard-header">
        <div>
          <h1>Dashboard Estadístico y Reportes</h1>
          <p className="dashboard-intro">
            Asistencia, ausentismo y llegadas tardías del personal.
          </p>
        </div>
        <ReportExportActions filters={filters} />
      </header>

      <DashboardFilters
        filters={filters}
        key={`${filters.start_date}|${filters.end_date}|${filters.horario_id}`}
        onApply={setFilters}
        onReset={resetFilters}
      />

      <DashboardDataView
        filters={filters}
        key={`${filters.start_date}|${filters.end_date}|${filters.horario_id}`}
      />
    </main>
  )
}
