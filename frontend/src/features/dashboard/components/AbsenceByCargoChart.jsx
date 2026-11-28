// SUMMARY: Presenta el ausentismo por cargo y las causas aprobadas del catálogo.

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
  // Ambos gráficos comparten la carga del endpoint de resumen.
  if (loading) {
    return (
      <section className="dashboard-panel dashboard-panel--distribution" aria-busy="true">
        <h2 className="dashboard-panel-title">Ausentismo y retardos por estamento</h2>
        <div className="dashboard-chart-placeholder">Cargando distribución...</div>
      </section>
    )
  }

  const hasCargoData = byCargo.length > 0
  const hasCauseData = causes.length > 0

  if (!hasCargoData && !hasCauseData) {
    return (
      <section className="dashboard-panel dashboard-panel--distribution">
        <h2 className="dashboard-panel-title">Ausentismo y retardos por estamento</h2>
        <p className="dashboard-empty">No hay datos de ausentismo para mostrar.</p>
      </section>
    )
  }

  // Se muestran solo datos recibidos; el catálogo define las causas disponibles.
  return (
    <section className="dashboard-panel dashboard-panel--distribution">
      <div className="dashboard-panel-heading">
        <div>
          <h2 className="dashboard-panel-title">Ausentismo y retardos por estamento</h2>
          <p className="dashboard-panel-subtitle">
            Distribución de ausentismo y causas justificadas del período.
          </p>
        </div>
      </div>

      <div className="dashboard-distribution-grid">
        <div className="dashboard-chart-block">
          <h3 className="dashboard-chart-title">Tasa de ausentismo por cargo</h3>
          {hasCargoData ? (
            <div className="dashboard-cargo-list">
              {byCargo.map((item, index) => {
                const rate = Number(item.tasa_ausentismo) || 0
                const progress = Math.max(0, Math.min(rate, 100))

                return (
                  <div className="dashboard-cargo-item" key={`${item.cargo}-${index}`}>
                    <div className="dashboard-cargo-heading">
                      <span>{item.cargo}</span>
                      <span>{rate.toFixed(1)}%</span>
                    </div>
                    <div
                      className="dashboard-cargo-track"
                      role="progressbar"
                      aria-label={`Tasa de ausentismo: ${item.cargo}`}
                      aria-valuemin="0"
                      aria-valuemax="100"
                      aria-valuenow={progress}
                    >
                      <span style={{ width: `${progress}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="dashboard-empty">No hay registros agrupados por cargo.</p>
          )}
        </div>

        <div className="dashboard-chart-block">
          <h3 className="dashboard-chart-title">Principales causas de ausentismo</h3>
          {hasCauseData ? (
            <div className="dashboard-causes-grid">
              {causes.map((cause) => (
                <div className="dashboard-cause-card" key={cause.tipo_ausencia_id}>
                  <span>{cause.tipo_ausencia}</span>
                  <strong>{cause.total}</strong>
                </div>
              ))}
            </div>
          ) : (
            <p className="dashboard-empty">No hay ausencias aprobadas en este rango.</p>
          )}
        </div>
      </div>
    </section>
  )
}
