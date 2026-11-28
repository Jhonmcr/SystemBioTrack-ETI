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

  function updateField(event) {
    const { name, value } = event.target
    setDraft((current) => ({ ...current, [name]: value }))
    setValidationError('')
  }

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

  function resetFilters() {
    setValidationError('')
    const resetValues = onReset()
    if (resetValues) setDraft(resetValues)
  }

  return (
    <form className="dashboard-filter-bar" onSubmit={submitFilters}>
      <label className="dashboard-field">
        <span>Desde</span>
        <input
          aria-label="Fecha inicial"
          name="start_date"
          type="date"
          value={draft.start_date}
          onChange={updateField}
        />
      </label>

      <label className="dashboard-field">
        <span>Hasta</span>
        <input
          aria-label="Fecha final"
          name="end_date"
          type="date"
          value={draft.end_date}
          onChange={updateField}
        />
      </label>

      <label className="dashboard-field dashboard-field--schedule">
        <span>ID de horario (opcional)</span>
        <input
          aria-label="Identificador de horario"
          min="1"
          name="horario_id"
          placeholder="Todos"
          step="1"
          type="number"
          value={draft.horario_id}
          onChange={updateField}
        />
      </label>

      <div className="dashboard-filter-actions">
        <button className="dashboard-button dashboard-button--secondary" type="button" onClick={resetFilters}>
          Restablecer
        </button>
        <button className="dashboard-button dashboard-button--primary" type="submit">
          Aplicar filtros
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
