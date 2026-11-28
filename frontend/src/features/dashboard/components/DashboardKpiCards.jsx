// SUMMARY: Muestra tarjetas de indicadores de asistencia con estado de carga y vacío.

const KPI_DEFINITIONS = [
  {
    key: 'total_registros',
    label: 'Registros del periodo',
    color: 'blue',
    format: (value) => value.toLocaleString('es-VE'),
  },
  {
    key: 'tasa_ausentismo',
    label: 'Tasa de ausentismo',
    color: 'rose',
    format: (value) => `${Number(value).toFixed(2)}%`,
  },
  {
    key: 'total_retardos',
    label: 'Llegadas tardías',
    color: 'amber',
    format: (value) => value.toLocaleString('es-VE'),
  },
  {
    key: 'ausencias_justificadas',
    label: 'Ausencias justificadas',
    color: 'teal',
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
      {KPI_DEFINITIONS.map(({ key, label, color, format }) => (
        <article className={`dashboard-kpi-card dashboard-kpi-card--${color}`} key={key}>
          <p className="dashboard-kpi-label">{label}</p>
          <strong className="dashboard-kpi-value">
            {format(Number(metrics[key] ?? 0))}
          </strong>
        </article>
      ))}
    </section>
  )
}
