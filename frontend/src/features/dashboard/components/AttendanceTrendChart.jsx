// SUMMARY: Grafica la evolución diaria de puntualidad, retardos e inasistencias.

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

/**
 * Summary: Dibuja la serie diaria de asistencia recibida desde el dashboard.
 * @param {Array<object>} data Puntos con fecha, puntualidad, tardanzas e inasistencias.
 * @param {boolean} loading Indica si los datos de la serie están cargando.
 * @returns {JSX.Element} Panel de barras agrupadas o mensaje de estado.
 */
export default function AttendanceTrendChart({ data = [], loading }) {
  // El panel de carga conserva el espacio del gráfico mientras se consulta la serie.
  if (loading) {
    return (
      <section className="dashboard-panel" aria-busy="true">
        <h2 className="dashboard-panel-title">Evolución diaria</h2>
        <div className="dashboard-chart-placeholder">
          Cargando evolución de asistencia...
        </div>
      </section>
    )
  }

  // Los datos vacíos se notifican antes de crear ejes sin puntos.
  if (!data.length) {
    return (
      <section className="dashboard-panel">
        <h2 className="dashboard-panel-title">Evolución diaria</h2>
        <p className="dashboard-empty">No hay registros para graficar en este rango.</p>
      </section>
    )
  }

  // Las fechas se muestran en formato corto y las métricas se conservan como conteos.
  // Summary: Añade una etiqueta de fecha localizada a cada punto de la serie.
  const chartData = data.map((point) => ({
    ...point,
    fecha_label: new Date(`${point.fecha}T00:00:00`).toLocaleDateString('es-VE', {
      day: '2-digit',
      month: '2-digit',
    }),
  }))

  return (
    <section className="dashboard-panel">
      <div className="dashboard-panel-heading">
        <div>
          <h2 className="dashboard-panel-title">Evolución de asistencia</h2>
          <p className="dashboard-panel-subtitle">
            Registros diarios por estado dentro del rango seleccionado.
          </p>
        </div>
      </div>
      <div className="dashboard-chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 12, left: -16, bottom: 4 }}>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="fecha_label" tick={{ fill: '#64748b', fontSize: 12 }} />
            <YAxis allowDecimals={false} tick={{ fill: '#64748b', fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="asistencias_puntuales" name="Puntuales" fill="#0f766e" />
            <Bar dataKey="retardos" name="Retardos" fill="#d97706" />
            <Bar dataKey="inasistencias" name="Inasistencias" fill="#be123c" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
