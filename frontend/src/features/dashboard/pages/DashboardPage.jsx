// SUMMARY: Renderiza el Dashboard del Módulo 5 dentro de la interfaz del portal.

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
import './DashboardPage.css'

/** Summary: Crea los filtros iniciales para el mes calendario actual. */
function getDefaultFilters() {
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

  // Summary: Ejecuta ambas consultas en paralelo y cancela las anteriores al cambiar filtros.
  useEffect(() => {
    const controller = new AbortController()

    getDashboardSummary(filters, controller.signal)
      .then(setSummary)
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setSummaryError(error.message || 'No se pudo cargar el resumen estadístico.')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setSummaryLoading(false)
      })

    getTardinessReport(filters, controller.signal)
      .then(setTardiness)
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setTardinessError(error.message || 'No se pudo cargar el reporte de tardanzas.')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setTardinessLoading(false)
      })

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
 * @returns {JSX.Element} Dashboard estadístico adaptable a escritorio y móvil.
 */
export default function DashboardPage() {
  const [filters, setFilters] = useState(getDefaultFilters)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const [openMenu, setOpenMenu] = useState('')

  /** Summary: Restablece el formulario y los datos al rango predeterminado. */
  function resetFilters() {
    const defaultFilters = getDefaultFilters()
    setFilters(defaultFilters)
    return defaultFilters
  }

  /** Summary: Alterna un menú emergente y cierra los demás. */
  function toggleMenu(menuName) {
    setOpenMenu((currentMenu) => (
      currentMenu === menuName ? '' : menuName
    ))
  }

  return (
    <div
      className={[
        'dashboard-app',
        sidebarCollapsed ? 'dashboard-app--collapsed' : '',
        darkMode ? 'dashboard-app--dark' : '',
      ].filter(Boolean).join(' ')}
    >
      <aside className="dashboard-sidebar" aria-label="Navegación principal">
        <div>
          <div className="dashboard-brand">
            <div className="dashboard-brand-mark">
              <span className="material-symbols-outlined" aria-hidden="true">fingerprint</span>
            </div>
            <div>
              <span className="dashboard-brand-name">ETI-Leonardo-Infante</span>
              <span className="dashboard-brand-caption">Portal Biométrico</span>
            </div>
          </div>

          <nav className="dashboard-nav" aria-label="Módulos operativos">
            <p className="dashboard-nav-caption">Módulos Operativos</p>
            <button
              aria-current="page"
              className="dashboard-nav-item dashboard-nav-item--active"
              title="Dashboard Estadístico y Reportes"
              type="button"
            >
              <span className="material-symbols-outlined" aria-hidden="true">bar_chart</span>
              <span className="dashboard-nav-label">Dashboard y Reportes</span>
            </button>
            <button
              aria-disabled="true"
              className="dashboard-nav-item dashboard-nav-item--inactive"
              title="Módulo de Usuarios y Roles no disponible en esta vista"
              type="button"
            >
              <span className="material-symbols-outlined" aria-hidden="true">lock</span>
              <span className="dashboard-nav-label">Usuarios y Roles</span>
            </button>
            <button
              aria-disabled="true"
              className="dashboard-nav-item dashboard-nav-item--inactive"
              title="Módulo Biométrico no disponible en esta vista"
              type="button"
            >
              <span className="material-symbols-outlined" aria-hidden="true">fingerprint</span>
              <span className="dashboard-nav-label">Biométrico</span>
            </button>
            <button
              aria-disabled="true"
              className="dashboard-nav-item dashboard-nav-item--inactive"
              title="Módulo de Personal y Horarios no disponible en esta vista"
              type="button"
            >
              <span className="material-symbols-outlined" aria-hidden="true">group</span>
              <span className="dashboard-nav-label">Personal y Horarios</span>
            </button>
            <button
              aria-disabled="true"
              className="dashboard-nav-item dashboard-nav-item--inactive"
              title="Módulo de Permisos y Justificativos no disponible en esta vista"
              type="button"
            >
              <span className="material-symbols-outlined" aria-hidden="true">description</span>
              <span className="dashboard-nav-label">Permisos y Justificativos</span>
            </button>
          </nav>
        </div>

        <div className="dashboard-session">
          <div className="dashboard-session-card">
            <div className="dashboard-avatar">MD</div>
            <div className="dashboard-session-copy">
              <strong>Lic. Marcos Delgado</strong>
              <span>Rol: Admin / Revisor</span>
            </div>
            <span className="dashboard-session-status" title="Sesión activa" />
          </div>
        </div>
      </aside>

      <div className="dashboard-shell">
        <header className="dashboard-topbar">
          <div className="dashboard-topbar-left">
            <button
              aria-label={sidebarCollapsed ? 'Expandir menú lateral' : 'Colapsar menú lateral'}
              aria-pressed={sidebarCollapsed}
              className="dashboard-icon-button dashboard-sidebar-toggle"
              onClick={() => setSidebarCollapsed((current) => !current)}
              title="Colapsar / Expandir barra lateral"
              type="button"
            >
              <span className="material-symbols-outlined" aria-hidden="true">dock_to_right</span>
            </button>
            <span className="dashboard-topbar-separator" />
            <div className="dashboard-breadcrumb">
              Módulo 5: Dashboard y Reportes
            </div>
          </div>

          <div className="dashboard-topbar-right">
            <span className="dashboard-role">Rol: Admin</span>
            <button
              aria-label={darkMode ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
              aria-pressed={darkMode}
              className="dashboard-icon-button"
              onClick={() => setDarkMode((current) => !current)}
              title="Alternar tema claro / oscuro"
              type="button"
            >
              <span className="material-symbols-outlined" aria-hidden="true">
                {darkMode ? 'dark_mode' : 'light_mode'}
              </span>
            </button>

            <div className="dashboard-popover-wrap">
              <button
                aria-expanded={openMenu === 'notifications'}
                aria-label="Notificaciones"
                className="dashboard-icon-button"
                onClick={() => toggleMenu('notifications')}
                title="Notificaciones"
                type="button"
              >
                <span className="material-symbols-outlined" aria-hidden="true">notifications</span>
                <span className="dashboard-notification-dot">9+</span>
              </button>
              {openMenu === 'notifications' && (
                <div className="dashboard-popover" role="dialog" aria-label="Alertas del sistema">
                  <div className="dashboard-popover-heading">
                    <span>Alertas del Sistema</span>
                    <span>9 pendientes</span>
                  </div>
                  <div className="dashboard-popover-item">
                    <strong>Reposo médico ingresado</strong>
                    <span>Una solicitud espera validación.</span>
                  </div>
                  <div className="dashboard-popover-item">
                    <strong>Retardo detectado</strong>
                    <span>Se registró una llegada tardía reciente.</span>
                  </div>
                  <div className="dashboard-popover-footer">Marcar todo como leído</div>
                </div>
              )}
            </div>

            <div className="dashboard-popover-wrap">
              <button
                aria-expanded={openMenu === 'profile'}
                className="dashboard-profile-button"
                onClick={() => toggleMenu('profile')}
                type="button"
              >
                <span className="dashboard-profile-avatar">MD</span>
                <span className="dashboard-profile-copy">
                  <strong>Lic. Marcos D.</strong>
                  <span>mdelgado@eti...</span>
                </span>
                <span className="material-symbols-outlined" aria-hidden="true">expand_more</span>
              </button>
              {openMenu === 'profile' && (
                <div className="dashboard-popover" role="dialog" aria-label="Menú de usuario">
                  <div className="dashboard-popover-profile">
                    <strong>Lic. Marcos Delgado</strong>
                    <span>mdelgado@eti.edu.ve</span>
                  </div>
                  <div className="dashboard-profile-option">
                    <span className="material-symbols-outlined" aria-hidden="true">person</span>
                    Mi Perfil
                  </div>
                  <div className="dashboard-profile-option">
                    <span className="material-symbols-outlined" aria-hidden="true">shield_person</span>
                    Rol y Permisos
                  </div>
                  <div className="dashboard-profile-option">
                    <span className="material-symbols-outlined" aria-hidden="true">tune</span>
                    Preferencias
                  </div>
                  <div className="dashboard-profile-option">
                    <span className="material-symbols-outlined" aria-hidden="true">logout</span>
                    Cerrar Sesión
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="dashboard-main">
          <div className="dashboard-heading">
            <h1>Dashboard Estadístico y Reportes</h1>
            <p>
              Análisis consolidado de asistencia, índices de ausentismo,
              llegadas tardías y exportación documental en PDF.
            </p>
          </div>

          <div className="dashboard-controls-row">
            <DashboardFilters
              filters={filters}
              onApply={setFilters}
              onReset={resetFilters}
            />
            <ReportExportActions filters={filters} />
          </div>

          <DashboardDataView
            filters={filters}
            key={`${filters.start_date}|${filters.end_date}|${filters.horario_id}`}
          />
        </main>
      </div>
    </div>
  )
}
