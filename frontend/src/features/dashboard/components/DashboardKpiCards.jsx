// SUMMARY: Muestra tarjetas de indicadores de asistencia con estado de carga y vacío.

const KPI_DEFINITIONS = [
  {
    key: 'total_registros',
    label: 'Registros en el período',
    color: 'blue',
    icon: 'fact_check',
    /** Summary: Formatea conteos con separadores según la configuración regional. */
    format: (value) => value.toLocaleString('es-VE'),
  },
  {
    key: 'tasa_ausentismo',
    label: 'Índice de ausentismo',
    color: 'rose',
    icon: 'trending_down',
    /** Summary: Presenta la tasa como porcentaje con dos decimales. */
    format: (value) => `${Number(value).toFixed(2)}%`,
  },
  {
    key: 'total_retardos',
    label: 'Llegadas tardías',
    color: 'amber',
    icon: 'schedule',
    /** Summary: Formatea el total de retardos como conteo localizado. */
    format: (value) => value.toLocaleString('es-VE'),
  },
  {
    key: 'ausencias_justificadas',
    label: 'Reposos y permisos',
    color: 'teal',
    icon: 'medical_services',
    /** Summary: Formatea el total aprobado como conteo localizado. */
    format: (value) => value.toLocaleString('es-VE'),
  },
]

/**
 * Summary: Renderiza indicadores clave o estados de carga y ausencia de resultados.
 * @param {object|null} metrics Indicadores agregados del servicio.
 * @param {boolean} loading Indica si el resumen se está consultando.
 * @returns {JSX.Element} Cuadrícula de KPI con contenido accesible.
 */
export default function DashboardKpiCards({ metrics, loading }) {
  // El estado de carga mantiene el espacio de cada indicador mientras llega la API.
  if (loading) {
    return (
      <div aria-label="Cargando indicadores" className="dashboard-kpi-grid" aria-live="polite">
        {KPI_DEFINITIONS.map((item) => (
          <div className="dashboard-kpi-card dashboard-kpi-card--loading" key={item.key}>
            <span className="dashboard-skeleton dashboard-skeleton--label" />
            <span className="dashboard-skeleton dashboard-skeleton--value" />
          </div>
        ))}
      </div>
    )
  }

  // La ausencia de respuesta se diferencia de un KPI cuyo valor real sea cero.
  if (!metrics) {
    return (
      <p className="dashboard-empty dashboard-kpi-empty">
        No hay indicadores disponibles para este periodo.
      </p>
    )
  }

  // Se evita mostrar valores ficticios: cada tarjeta se alimenta del KPI de la API.
  return (
    <section aria-label="Indicadores principales" className="dashboard-kpi-grid">
      {/* Summary: Renderiza las tarjetas configuradas usando valores del servidor. */}
      {KPI_DEFINITIONS.map(({ key, label, color, format, icon }) => (
        <article className={`dashboard-kpi-card dashboard-kpi-card--${color}`} key={key}>
          <div className="dashboard-kpi-copy">
            <p className="dashboard-kpi-label">{label}</p>
            <strong className="dashboard-kpi-value">
              {format(Number(metrics[key] ?? 0))}
            </strong>
          </div>
          <span className="dashboard-kpi-icon material-symbols-outlined" aria-hidden="true">
            {icon}
          </span>
        </article>
      ))}
    </section>
  )
}
