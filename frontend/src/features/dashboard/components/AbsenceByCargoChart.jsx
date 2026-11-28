// SUMMARY: Presenta el ausentismo por cargo y las causas aprobadas del catálogo.

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const CAUSE_COLORS = ['#881337', '#0369a1', '#0f766e', '#d97706', '#6d28d9', '#475569']

/**
 * Summary: Renderiza distribución por cargo y causas de ausencias aprobadas.
 * @param {Array<object>} byCargo Registros agregados con ausentismo por cargo.
 * @param {Array<object>} causes Conteo dinámico de tipos de ausencia aprobados.
 * @param {boolean} loading Indica si los datos estadísticos están cargando.
 * @returns {JSX.Element} Panel con barras por cargo y gráfico circular de causas.
 */
export default function AbsenceByCargoChart({
  byCargo = [],
  causes = [],
  loading,
}) {
  if (loading) {
    return (
      <section className="dashboard-panel" aria-busy="true">
        <h2 className="dashboard-panel-title">Ausentismo por cargo y causas</h2>
        <div className="dashboard-chart-placeholder">Cargando distribución...</div>
      </section>
    )
  }

  const hasCargoData = byCargo.length > 0
  const hasCauseData = causes.length > 0

  if (!hasCargoData && !hasCauseData) {
    return (
      <section className="dashboard-panel">
        <h2 className="dashboard-panel-title">Ausentismo por cargo y causas</h2>
        <p className="dashboard-empty">No hay datos de ausentismo para mostrar.</p>
      </section>
    )
  }

  // Se muestran solo datos recibidos; el catálogo define las causas disponibles.
  return (
    <section className="dashboard-panel">
      <div className="dashboard-panel-heading">
        <div>
          <h2 className="dashboard-panel-title">Ausentismo por cargo y causas</h2>
          <p className="dashboard-panel-subtitle">
            Registros de asistencia y solicitudes aprobadas en el rango.
          </p>
        </div>
      </div>

      <div className="dashboard-distribution-grid">
        <div className="dashboard-chart-block">
          <h3 className="dashboard-chart-title">Tasa de ausentismo por cargo</h3>
          {hasCargoData ? (
            <div className="dashboard-chart dashboard-chart--compact">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={byCargo}
                  layout="vertical"
                  margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
                >
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" horizontal={false} />
                  <XAxis
                    allowDecimals
                    tickFormatter={(value) => `${value}%`}
                    type="number"
                    tick={{ fill: '#64748b', fontSize: 12 }}
                  />
                  <YAxis
                    dataKey="cargo"
                    type="category"
                    width={110}
                    tick={{ fill: '#475569', fontSize: 12 }}
                  />
                  <Tooltip />
                  <Bar dataKey="tasa_ausentismo" name="Ausentismo (%)" fill="#be123c" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="dashboard-empty">No hay registros agrupados por cargo.</p>
          )}
        </div>

        <div className="dashboard-chart-block">
          <h3 className="dashboard-chart-title">Causas aprobadas</h3>
          {hasCauseData ? (
            <div className="dashboard-chart dashboard-chart--compact">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={causes}
                    dataKey="total"
                    nameKey="tipo_ausencia"
                    outerRadius={88}
                    paddingAngle={2}
                  >
                    {causes.map((cause, index) => (
                      <Cell
                        fill={CAUSE_COLORS[index % CAUSE_COLORS.length]}
                        key={cause.tipo_ausencia_id}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="dashboard-empty">No hay ausencias aprobadas en este rango.</p>
          )}
        </div>
      </div>
    </section>
  )
}
