// SUMMARY: Resume las llegadas tardías por empleado con búsqueda y estados de carga.

import { useState } from 'react'

/**
 * Summary: Muestra frecuencia y minutos acumulados de tardanza por empleado.
 * @param {object|null} report Respuesta del endpoint de reportes de tardanza.
 * @param {boolean} loading Indica si se está consultando el endpoint.
 * @returns {JSX.Element} Tabla accesible o el estado correspondiente.
 */
export default function TardinessReportTable({ report, loading }) {
  const [search, setSearch] = useState('')

  // La tabla solo representa datos cuando la solicitud ya terminó correctamente.
  if (loading) {
    return (
      <section className="dashboard-panel dashboard-table-panel" aria-busy="true">
        <h2 className="dashboard-panel-title">Reporte Consolidado por Empleado</h2>
        <p className="dashboard-loading-message">Cargando reporte de tardanzas...</p>
      </section>
    )
  }

  if (!report) {
    return (
      <section className="dashboard-panel dashboard-table-panel">
        <h2 className="dashboard-panel-title">Reporte Consolidado por Empleado</h2>
        <p className="dashboard-empty">El reporte no está disponible.</p>
      </section>
    )
  }

  const employees = report.empleados || []

  if (!employees.length) {
    return (
      <section className="dashboard-panel dashboard-table-panel">
        <div className="dashboard-panel-heading">
          <div>
            <h2 className="dashboard-panel-title">Reporte Consolidado por Empleado</h2>
            <p className="dashboard-panel-subtitle">No se registraron tardanzas en el periodo.</p>
          </div>
        </div>
        <p className="dashboard-empty">No hay empleados con retardos para estos filtros.</p>
      </section>
    )
  }

  const normalizedSearch = search.trim().toLocaleLowerCase('es-VE')
  const filteredEmployees = employees.filter((item) => {
    const employeeName =
      `${item.empleado.nombre} ${item.empleado.apellido}`.toLocaleLowerCase('es-VE')
    const scheduleName = (item.horario?.nombre_horario || '').toLocaleLowerCase('es-VE')

    return employeeName.includes(normalizedSearch) || scheduleName.includes(normalizedSearch)
  })

  // Los nombres se componen desde los campos estructurados del contrato de tardanzas.
  return (
    <section className="dashboard-panel dashboard-table-panel">
      <div className="dashboard-table-heading">
        <div>
          <h2 className="dashboard-panel-title">Reporte Consolidado por Empleado</h2>
          <p className="dashboard-panel-subtitle">
            {report.total_retardos ?? 0} llegadas tardías · {report.minutos_tarde_acumulados ?? 0} minutos acumulados
          </p>
        </div>
        <label className="dashboard-table-search">
          <span className="material-symbols-outlined" aria-hidden="true">search</span>
          <input
            aria-label="Buscar por nombre u horario"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por nombre..."
            type="search"
            value={search}
          />
        </label>
      </div>

      <div className="dashboard-table-wrapper">
        <table className="dashboard-table">
          <thead>
            <tr>
              <th scope="col">Empleado</th>
              <th scope="col">Horario</th>
              <th scope="col">Llegadas tardías</th>
              <th scope="col">Minutos acumulados</th>
            </tr>
          </thead>
          <tbody>
            {/* Summary: Construye una fila por empleado del resumen de tardanzas. */}
            {filteredEmployees.map((item) => (
              <tr key={item.empleado.id}>
                <td>
                  {item.empleado.nombre} {item.empleado.apellido}
                </td>
                <td>{item.horario?.nombre_horario || 'Sin horario'}</td>
                <td>{item.total_retardos}</td>
                <td>{item.minutos_tarde_acumulados}</td>
              </tr>
            ))}
            {!filteredEmployees.length && (
              <tr>
                <td className="dashboard-table-empty" colSpan="4">
                  No se encontraron empleados que coincidan con la búsqueda.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
