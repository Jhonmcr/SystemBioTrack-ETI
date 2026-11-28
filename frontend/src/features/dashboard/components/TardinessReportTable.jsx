// SUMMARY: Resume las llegadas tardías por empleado con estados de carga y vacío.

/**
 * Summary: Muestra frecuencia y minutos acumulados de tardanza por empleado.
 * @param {object|null} report Respuesta del endpoint de reportes de tardanza.
 * @param {boolean} loading Indica si se está consultando el endpoint.
 * @returns {JSX.Element} Tabla accesible o el estado correspondiente.
 */
export default function TardinessReportTable({ report, loading }) {
  // La tabla solo representa datos cuando la solicitud ya terminó correctamente.
  if (loading) {
    return (
      <section className="dashboard-panel" aria-busy="true">
        <h2 className="dashboard-panel-title">Reporte de llegadas tardías</h2>
        <p className="dashboard-loading-message">Cargando reporte de tardanzas...</p>
      </section>
    )
  }

  if (!report) {
    return (
      <section className="dashboard-panel">
        <h2 className="dashboard-panel-title">Reporte de llegadas tardías</h2>
        <p className="dashboard-empty">El reporte no está disponible.</p>
      </section>
    )
  }

  const employees = report.empleados || []

  if (!employees.length) {
    return (
      <section className="dashboard-panel">
        <div className="dashboard-panel-heading">
          <div>
            <h2 className="dashboard-panel-title">Reporte de llegadas tardías</h2>
            <p className="dashboard-panel-subtitle">No se registraron tardanzas en el periodo.</p>
          </div>
        </div>
        <p className="dashboard-empty">No hay empleados con retardos para estos filtros.</p>
      </section>
    )
  }

  // Los nombres se componen desde los campos estructurados del contrato de tardanzas.
  return (
    <section className="dashboard-panel">
      <div className="dashboard-panel-heading">
        <div>
          <h2 className="dashboard-panel-title">Reporte de llegadas tardías</h2>
          <p className="dashboard-panel-subtitle">
            {report.total_retardos ?? 0} retardos · {report.minutos_tarde_acumulados ?? 0} minutos acumulados
          </p>
        </div>
      </div>

      <div className="dashboard-table-wrapper">
        <table className="dashboard-table">
          <thead>
            <tr>
              <th scope="col">Empleado</th>
              <th scope="col">Horario</th>
              <th scope="col">Retardos</th>
              <th scope="col">Minutos acumulados</th>
            </tr>
          </thead>
          <tbody>
            {/* Summary: Construye una fila por empleado del resumen de tardanzas. */}
            {employees.map((item) => (
              <tr key={item.empleado.id}>
                <td>
                  {item.empleado.nombre} {item.empleado.apellido}
                </td>
                <td>{item.horario?.nombre_horario || 'Sin horario'}</td>
                <td>{item.total_retardos}</td>
                <td>{item.minutos_tarde_acumulados}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
