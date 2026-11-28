// SUMMARY: Presenta filtros accesibles de fecha y horario para consultar el dashboard.

import { useState } from 'react'

/**
 * Summary: Controla filtros de rango y horario y notifica su aplicación al padre.
 * @param {object} props Filtros actuales y acciones de aplicar o restablecer.
 * @returns {JSX.Element} Formulario controlado de filtros estadísticos.
 */
export default function DashboardFilters({ filters, onApply, onReset }) {
  const [draft, setDraft] = useState(filters)
  const [validationError, setValidationError] = useState('')

  /**
   * Summary: Actualiza un campo del formulario y limpia el error anterior.
   * @param {Event} event Cambio generado por uno de los controles del filtro.
   */
  function updateField(event) {
    const { name, value } = event.target
    // La actualización funcional conserva los valores de los demás filtros.
    setDraft((current) => ({ ...current, [name]: value }))
    setValidationError('')
  }

  /**
   * Summary: Valida el rango y aplica los filtros al dashboard.
   * @param {Event} event Envío del formulario de filtros.
   */
  function submitFilters(event) {
    event.preventDefault()

    // Valida rango y horario antes de solicitar nuevos datos al servidor.
    if (!draft.start_date || !draft.end_date) {
      setValidationError('Seleccione ambas fechas para consultar el reporte.')
      return
    }
    if (draft.start_date > draft.end_date) {
      setValidationError('La fecha inicial debe ser anterior o igual a la final.')
      return
    }
    if (draft.horario_id) {
      const scheduleId = Number(draft.horario_id)
      if (!Number.isInteger(scheduleId) || scheduleId < 1) {
        setValidationError('El identificador del horario debe ser un entero positivo.')
        return
      }
    }

    onApply({
      start_date: draft.start_date,
      end_date: draft.end_date,
      horario_id: draft.horario_id || '',
    })
  }

  /** Summary: Restaura los filtros iniciales y elimina errores de validación. */
  function resetFilters() {
    setValidationError('')
    const resetValues = onReset()
    if (resetValues) setDraft(resetValues)
  }

  return (
    <form className="dashboard-filter-bar" onSubmit={submitFilters}>
      <label className="dashboard-field">
        <span className="material-symbols-outlined" aria-hidden="true">calendar_today</span>
        <input
          aria-label="Fecha inicial"
          name="start_date"
          type="date"
          value={draft.start_date}
          onChange={updateField}
        />
      </label>

      <label className="dashboard-field">
        <span className="material-symbols-outlined" aria-hidden="true">event</span>
        <input
          aria-label="Fecha final"
          name="end_date"
          type="date"
          value={draft.end_date}
          onChange={updateField}
        />
      </label>

      <label className="dashboard-field dashboard-field--schedule">
        <span className="material-symbols-outlined" aria-hidden="true">schedule</span>
        <input
          aria-label="Identificador de horario"
          min="1"
          name="horario_id"
          placeholder="Horario"
          step="1"
          type="number"
          value={draft.horario_id}
          onChange={updateField}
        />
      </label>

      <div className="dashboard-filter-actions">
        <button className="dashboard-button" type="button" onClick={resetFilters}>
          <span className="material-symbols-outlined" aria-hidden="true">restart_alt</span>
          Limpiar
        </button>
        <button className="dashboard-button dashboard-button--primary" type="submit">
          <span className="material-symbols-outlined" aria-hidden="true">filter_alt</span>
          Aplicar
        </button>
      </div>

      {validationError && (
        <p className="dashboard-form-error" role="alert">
          {validationError}
        </p>
      )}
    </form>
  )
}
