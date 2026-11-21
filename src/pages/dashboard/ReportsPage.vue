<script setup>
import { computed, onMounted, ref } from 'vue'

const APPOINTMENTS_KEY = 'smileos-appointments'
const PLANS_KEY = 'smileos-treatment-plans'
const PATIENTS_KEY = 'smileos-patients'

const appointments = ref([])
const plans = ref([])
const patients = ref([])
const periodType = ref('month')
const customStart = ref(localDate(new Date(new Date().getFullYear(), new Date().getMonth(), 1)))
const customEnd = ref(localDate())
const showAllAppointments = ref(false)

const periodOptions = [
  { label: 'Hoy', value: 'day' },
  { label: 'Esta semana', value: 'week' },
  { label: 'Este mes', value: 'month' },
  { label: 'Periodo personalizado', value: 'custom' },
]

const statusInfo = {
  confirmada: { label: 'Agendada', color: '#22c55e' },
  atendida: { label: 'Atendida', color: '#60a5fa' },
  reprogramada: { label: 'Reprogramada', color: '#94a3b8' },
  cancelada: { label: 'Cancelada', color: '#f87171' },
}

function localDate(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function readArray(key) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || '[]')
    return Array.isArray(value) ? value : []
  } catch {
    return []
  }
}

onMounted(() => {
  appointments.value = readArray(APPOINTMENTS_KEY).map((appointment) => ({
    ...appointment,
    start: new Date(appointment.start),
    end: new Date(appointment.end),
    status: normalizeStatus(appointment.status),
  }))
  plans.value = readArray(PLANS_KEY)
  patients.value = readArray(PATIENTS_KEY)
})

function normalizeStatus(status) {
  const map = { confirmed: 'confirmada', pending: 'confirmada', cancelled: 'cancelada', rescheduled: 'reprogramada', completed: 'atendida' }
  return map[status] || status || 'confirmada'
}

function dateKey(value) {
  if (!value) return ''
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)) return value
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? String(value).slice(0, 10) : localDate(date)
}

const range = computed(() => {
  const now = new Date()
  if (periodType.value === 'day') {
    const today = localDate(now)
    return { start: today, end: today }
  }
  if (periodType.value === 'week') {
    const start = new Date(now)
    const day = start.getDay() || 7
    start.setDate(start.getDate() - day + 1)
    const end = new Date(start)
    end.setDate(start.getDate() + 6)
    return { start: localDate(start), end: localDate(end) }
  }
  if (periodType.value === 'custom') {
    return { start: customStart.value, end: customEnd.value }
  }
  return {
    start: localDate(new Date(now.getFullYear(), now.getMonth(), 1)),
    end: localDate(new Date(now.getFullYear(), now.getMonth() + 1, 0)),
  }
})

const rangeValid = computed(() => Boolean(range.value.start && range.value.end && range.value.start <= range.value.end))
const rangeAppointments = computed(() => rangeValid.value
  ? appointments.value.filter((appointment) => {
    const day = dateKey(appointment.start)
    return day >= range.value.start && day <= range.value.end
  })
  : [])
const scheduledCount = computed(() => rangeAppointments.value.filter((item) => item.status === 'confirmada').length)
const attendedCount = computed(() => rangeAppointments.value.filter((item) => item.status === 'atendida').length)
const rescheduledCount = computed(() => rangeAppointments.value.filter((item) => item.status === 'reprogramada').length)
const cancelledCount = computed(() => rangeAppointments.value.filter((item) => item.status === 'cancelada').length)

const statusRows = computed(() => Object.entries(statusInfo).map(([status, info]) => {
  const count = rangeAppointments.value.filter((appointment) => appointment.status === status).length
  const total = rangeAppointments.value.length
  return { status, label: info.label, color: info.color, count, percentage: total ? count / total * 100 : 0 }
}))

const activeAppointmentEstimate = computed(() => rangeAppointments.value
  .filter((item) => ['confirmada', 'atendida'].includes(item.status))
  .reduce((sum, item) => sum + Number(item.estimatedPrice || 0), 0))

function planDate(plan) {
  return dateKey(plan.createdAt || plan.startDate || plan.fechaInicio || plan.updatedAt)
}

const rangePlans = computed(() => rangeValid.value
  ? plans.value.filter((plan) => {
    const date = planDate(plan)
    return date && date >= range.value.start && date <= range.value.end
  })
  : [])
const planBudget = computed(() => rangePlans.value.reduce((sum, plan) => sum + Number(plan.estimatedCost ?? plan.cost ?? 0), 0))
const allPlanBalance = computed(() => plans.value.reduce((sum, plan) => sum + Math.max(0, Number(plan.estimatedCost ?? plan.cost ?? 0) - Number(plan.paidAmount || 0)), 0))
const paymentRows = computed(() => {
  if (!rangeValid.value) return []
  return plans.value.flatMap((plan) => (Array.isArray(plan.payments) ? plan.payments : [])
    .filter((payment) => payment.date >= range.value.start && payment.date <= range.value.end)
    .map((payment) => ({ ...payment, phase: plan.phase || plan.fase || 'Fase del tratamiento', patientId: plan.patientId || plan.pacienteId })))
    .sort((a, b) => String(b.date).localeCompare(String(a.date)))
})
const collectedInPeriod = computed(() => paymentRows.value.reduce((sum, payment) => sum + Number(payment.amount || 0), 0))

const reasonRows = computed(() => {
  const totals = new Map()
  rangeAppointments.value.forEach((appointment) => {
    const reason = appointment.reason || 'Sin motivo'
    totals.set(reason, (totals.get(reason) || 0) + 1)
  })
  return [...totals.entries()].map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count).slice(0, 5)
})

const dentistRows = computed(() => {
  const totals = new Map()
  rangeAppointments.value.forEach((appointment) => {
    const dentist = appointment.dentistName || 'Sin asignar'
    totals.set(dentist, (totals.get(dentist) || 0) + 1)
  })
  return [...totals.entries()].map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count)
})

const timeBuckets = computed(() => {
  const days = Math.ceil((new Date(`${range.value.end}T00:00:00`) - new Date(`${range.value.start}T00:00:00`)) / 86400000) + 1
  const useMonths = days > 35
  const buckets = new Map()
  rangeAppointments.value.forEach((appointment) => {
    const date = dateKey(appointment.start)
    const key = useMonths ? date.slice(0, 7) : date
    buckets.set(key, (buckets.get(key) || 0) + 1)
  })
  return [...buckets.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([key, count]) => ({
    key,
    label: useMonths
      ? new Intl.DateTimeFormat('es-PA', { month: 'short', year: '2-digit' }).format(new Date(`${key}-01T00:00:00`))
      : new Intl.DateTimeFormat('es-PA', { day: '2-digit', month: 'short' }).format(new Date(`${key}T00:00:00`)),
    count,
  }))
})
const maxBucketCount = computed(() => Math.max(1, ...timeBuckets.value.map((bucket) => bucket.count)))

const appointmentRows = computed(() => [...rangeAppointments.value].sort((a, b) => a.start - b.start))
const visibleAppointments = computed(() => showAllAppointments.value ? appointmentRows.value : appointmentRows.value.slice(0, 8))
const rangeLabel = computed(() => `${formatDate(range.value.start)} – ${formatDate(range.value.end)}`)
const appointmentColumns = [
  { name: 'date', label: 'Fecha', field: (row) => dateKey(row.start), align: 'left', sortable: true },
  { name: 'time', label: 'Hora', field: (row) => formatTime(row.start), align: 'left' },
  { name: 'patient', label: 'Paciente', field: (row) => patientName(row), align: 'left' },
  { name: 'dentist', label: 'Odontólogo', field: 'dentistName', align: 'left' },
  { name: 'reason', label: 'Motivo', field: 'reason', align: 'left' },
  { name: 'status', label: 'Estado', field: 'status', align: 'left' },
  { name: 'estimate', label: 'Estimación', field: 'estimatedPrice', align: 'right' },
]

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('es-PA', { day: '2-digit', month: 'short', year: 'numeric' }).format(date)
}

function formatTime(value) {
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleTimeString('es-PA', { hour: '2-digit', minute: '2-digit' })
}

function money(value) {
  return new Intl.NumberFormat('es-PA', { style: 'currency', currency: 'USD' }).format(Number(value) || 0)
}

function patientName(appointment) {
  return appointment.patientName || patients.value.find((patient) => String(patient.id || patient.cedula) === String(appointment.patientId))?.name || 'Paciente sin identificar'
}

function statusClass(status) {
  return `status-${status}`
}

function updatePeriod(value) {
  periodType.value = value
  if (value === 'custom' && (!customStart.value || !customEnd.value)) {
    customStart.value = localDate(new Date(new Date().getFullYear(), new Date().getMonth(), 1))
    customEnd.value = localDate(new Date())
  }
  showAllAppointments.value = false
}

function exportCsv() {
  const rows = [
    ['Fecha', 'Hora', 'Paciente', 'Cédula', 'Odontólogo', 'Motivo', 'Estado', 'Estimación USD'],
    ...appointmentRows.value.map((appointment) => [
      dateKey(appointment.start), formatTime(appointment.start), patientName(appointment), appointment.cedula || '',
      appointment.dentistName || '', appointment.reason || '', statusInfo[appointment.status]?.label || appointment.status,
      Number(appointment.estimatedPrice || 0).toFixed(2),
    ]),
    [],
    ['Resumen financiero del periodo'],
    ['Estimación de citas (USD)', activeAppointmentEstimate.value.toFixed(2)],
    ['Presupuesto de fases creadas (USD)', planBudget.value.toFixed(2)],
    ['Pagos registrados en el periodo (USD)', collectedInPeriod.value.toFixed(2)],
    ['Saldo pendiente actual de planes (USD)', allPlanBalance.value.toFixed(2)],
    [],
    ['Fecha', 'Fase', 'Método de pago', 'Referencia', 'Monto USD'],
    ...paymentRows.value.map((payment) => [payment.date, payment.phase, payment.method, payment.reference || '', Number(payment.amount || 0).toFixed(2)]),
  ]
  const csv = rows.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\r\n')
  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `smileos-reporte-${range.value.start}-${range.value.end}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

function printReport() {
  window.print()
}
</script>

<template>
  <q-page class="reports-page futuristic-bg q-pa-md q-pa-lg-lg">
    <section class="page-heading">
      <div><div class="eyebrow">Analítica clínica</div><h1>Reportes</h1><p>Resumen de actividad, agenda y finanzas de SmileOS.</p></div>
      <div class="header-actions"><q-btn flat no-caps icon="print" label="Imprimir" class="secondary-action" @click="printReport" /><q-btn unelevated no-caps icon="download" label="Exportar CSV" class="primary-action" :disable="!rangeValid" @click="exportCsv" /></div>
    </section>

    <section class="report-panel period-panel">
      <div class="period-heading"><span class="period-icon"><q-icon name="date_range" /></span><div><small>Periodo del informe</small><strong>{{ rangeValid ? rangeLabel : 'Rango no válido' }}</strong></div></div>
      <div class="period-controls"><q-btn-toggle :model-value="periodType" :options="periodOptions" no-caps unelevated toggle-color="cyan-10" toggle-text-color="cyan-2" class="period-toggle" @update:model-value="updatePeriod" />
        <div v-if="periodType === 'custom'" class="custom-range"><q-input v-model="customStart" dark outlined dense type="date" label="Desde" stack-label class="date-input" /><q-icon name="east" /><q-input v-model="customEnd" dark outlined dense type="date" label="Hasta" stack-label class="date-input" /></div>
      </div>
      <p v-if="periodType === 'custom' && !rangeValid" class="range-error">La fecha inicial debe ser anterior o igual a la fecha final.</p>
    </section>

    <div class="report-section-label"><span class="eyebrow">Agenda</span><span>{{ rangeAppointments.length }} citas en el periodo</span></div>
    <section class="report-stats appointment-stats">
      <article class="report-stat"><span class="stat-icon icon-total"><q-icon name="event_note" /></span><div><small>Citas en el periodo</small><strong>{{ rangeAppointments.length }}</strong><span>Todos los estados</span></div></article>
      <article class="report-stat"><span class="stat-icon icon-confirmed"><q-icon name="event_available" /></span><div><small>Agendadas</small><strong>{{ scheduledCount }}</strong><span>Confirmadas</span></div></article>
      <article class="report-stat"><span class="stat-icon icon-attended"><q-icon name="task_alt" /></span><div><small>Atendidas</small><strong>{{ attendedCount }}</strong><span>Consulta realizada</span></div></article>
      <article class="report-stat"><span class="stat-icon icon-rescheduled"><q-icon name="event_repeat" /></span><div><small>Reprogramadas</small><strong>{{ rescheduledCount }}</strong><span>Conservan historial</span></div></article>
      <article class="report-stat"><span class="stat-icon icon-cancelled"><q-icon name="event_busy" /></span><div><small>Canceladas</small><strong>{{ cancelledCount }}</strong><span>Cancelación lógica</span></div></article>
    </section>

    <section class="report-grid">
      <article class="report-panel chart-panel">
        <header class="panel-heading"><div><div class="eyebrow">Distribución</div><h2>Citas por estado</h2></div><q-icon name="donut_large" class="panel-heading-icon" /></header>
        <div class="status-bars"><div v-for="item in statusRows" :key="item.status" class="status-bar-row"><div class="bar-label"><span><i :style="{ background: item.color }"></i>{{ item.label }}</span><strong>{{ item.count }}</strong></div><div class="bar-track"><span :style="{ width: `${item.percentage}%`, background: item.color }"></span></div></div></div>
      </article>
      <article class="report-panel chart-panel">
        <header class="panel-heading"><div><div class="eyebrow">Tendencia</div><h2>Volumen de citas</h2></div><q-icon name="bar_chart" class="panel-heading-icon" /></header>
        <div v-if="timeBuckets.length" class="activity-chart"><div v-for="bucket in timeBuckets" :key="bucket.key" class="activity-column"><span class="activity-count">{{ bucket.count }}</span><div class="activity-bar-wrap"><span class="activity-bar" :style="{ height: `${Math.max(8, bucket.count / maxBucketCount * 100)}%` }"></span></div><small>{{ bucket.label }}</small></div></div>
        <div v-else class="chart-empty">Sin citas registradas en este periodo.</div>
      </article>
      <article class="report-panel summary-panel">
        <header class="panel-heading"><div><div class="eyebrow">Atención</div><h2>Motivos frecuentes</h2></div><q-icon name="medical_services" class="panel-heading-icon" /></header>
        <div v-if="reasonRows.length" class="ranking-list"><div v-for="(item, index) in reasonRows" :key="item.label" class="ranking-row"><span class="ranking-index">{{ String(index + 1).padStart(2, '0') }}</span><span class="ranking-name">{{ item.label }}</span><q-badge>{{ item.count }}</q-badge></div></div>
        <div v-else class="chart-empty">Sin datos para mostrar.</div>
      </article>
      <article class="report-panel summary-panel">
        <header class="panel-heading"><div><div class="eyebrow">Equipo</div><h2>Citas por odontólogo</h2></div><q-icon name="dentistry" class="panel-heading-icon" /></header>
        <div v-if="dentistRows.length" class="ranking-list"><div v-for="item in dentistRows" :key="item.label" class="ranking-row"><span class="dentist-dot"><q-icon name="person" /></span><span class="ranking-name">{{ item.label }}</span><q-badge>{{ item.count }}</q-badge></div></div>
        <div v-else class="chart-empty">Sin datos para mostrar.</div>
      </article>
    </section>

    <div class="report-section-label"><span class="eyebrow">Finanzas</span><span>Montos en dólares estadounidenses</span></div>
    <section class="report-stats financial-stats">
      <article class="report-stat"><span class="stat-icon icon-budget"><q-icon name="request_quote" /></span><div><small>Estimación de citas</small><strong>{{ money(activeAppointmentEstimate) }}</strong><span>Agendadas + atendidas; no son cobros</span></div></article>
      <article class="report-stat"><span class="stat-icon icon-plan"><q-icon name="account_tree" /></span><div><small>Presupuesto de planes</small><strong>{{ money(planBudget) }}</strong><span>{{ rangePlans.length }} fases creadas en el periodo</span></div></article>
      <article class="report-stat"><span class="stat-icon icon-collected"><q-icon name="payments" /></span><div><small>Pagos registrados</small><strong>{{ money(collectedInPeriod) }}</strong><span>{{ paymentRows.length }} pagos en el periodo</span></div></article>
      <article class="report-stat"><span class="stat-icon icon-balance"><q-icon name="account_balance_wallet" /></span><div><small>Saldo pendiente actual</small><strong>{{ money(allPlanBalance) }}</strong><span>De los planes almacenados</span></div></article>
    </section>

    <section class="report-panel data-panel">
      <header class="panel-heading"><div><div class="eyebrow">Detalle</div><h2>Citas del periodo</h2><p>La estimación no representa un pago recibido.</p></div><q-badge class="table-count">{{ appointmentRows.length }} registros</q-badge></header>
      <q-table :rows="visibleAppointments" :columns="appointmentColumns" row-key="id" dark flat
        :pagination="{ rowsPerPage: showAllAppointments ? 0 : 8 }" class="report-table">
        <template #body-cell-date="props"><q-td :props="props">{{ formatDate(dateKey(props.row.start)) }}</q-td></template>
        <template #body-cell-time="props"><q-td :props="props">{{ formatTime(props.row.start) }} – {{ formatTime(props.row.end) }}</q-td></template>
        <template #body-cell-patient="props"><q-td :props="props"><div class="table-patient"><strong>{{ patientName(props.row) }}</strong><small>{{ props.row.cedula }}</small></div></q-td></template>
        <template #body-cell-status="props"><q-td :props="props"><span :class="['status-pill', statusClass(props.row.status)]">{{ statusInfo[props.row.status]?.label || props.row.status }}</span></q-td></template>
        <template #body-cell-estimate="props"><q-td :props="props">{{ money(props.row.estimatedPrice) }}</q-td></template>
        <template #no-data><div class="chart-empty">No hay citas para este periodo.</div></template>
      </q-table>
      <div v-if="appointmentRows.length > 8" class="table-more"><q-btn flat no-caps :label="showAllAppointments ? 'Mostrar menos' : `Ver las ${appointmentRows.length} citas`" class="secondary-action" @click="showAllAppointments = !showAllAppointments" /></div>
    </section>

    <section class="report-panel payment-panel">
      <header class="panel-heading"><div><div class="eyebrow">Cobros</div><h2>Pagos registrados en el periodo</h2><p>Pagos vinculados a fases del plan de tratamiento.</p></div><q-badge class="table-count">{{ paymentRows.length }} pagos</q-badge></header>
      <div v-if="paymentRows.length" class="payment-list"><article v-for="payment in paymentRows" :key="payment.id" class="payment-row"><span class="payment-icon"><q-icon name="receipt_long" /></span><div><strong>{{ payment.phase }}</strong><small>{{ formatDate(payment.date) }} · {{ payment.method }}<template v-if="payment.reference"> · {{ payment.reference }}</template></small></div><b>{{ money(payment.amount) }}</b></article></div>
      <div v-else class="chart-empty">No hay pagos registrados durante este periodo.</div>
    </section>
    <div class="report-footnote"><q-icon name="info" /> Los reportes usan los registros guardados en este navegador. Los importes de citas son estimaciones y los pagos solo incluyen cobros registrados en Plan de Tratamiento.</div>
  </q-page>
</template>

<style scoped>
.reports-page { min-height: 100%; color: #e2e8f0; }
.page-heading,.panel-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.page-heading { max-width: 1200px; margin: 4px auto 20px; }
.page-heading h1 { margin: 4px 0; color: #f8fafc; font-size: clamp(26px,4vw,34px); font-weight: 700; }
.page-heading p,.panel-heading p { margin: 4px 0 0; color: #94a3b8; font-size: 11px; }
.eyebrow { color: #67e8f9; font-size: 10px; font-weight: 700; letter-spacing: .17em; text-transform: uppercase; }
.header-actions { display: flex; gap: 8px; }
.primary-action,.secondary-action { min-height: 39px; padding: 0 13px; border: 1px solid rgba(34,211,238,.36); border-radius: 9px; background: rgba(8,145,178,.18); color: #a5f3fc; }
.secondary-action { border-color: rgba(100,140,190,.2); background: rgba(15,23,42,.36); color: #cbd5e1; }
.report-panel { min-width: 0; border: 1px solid rgba(100,140,190,.19); border-radius: 14px; background: rgba(16,19,31,.8); }
.period-panel { display: flex; max-width: 1200px; align-items: center; justify-content: space-between; gap: 15px; margin: 0 auto 22px; padding: 15px 18px; }
.period-heading { display: flex; align-items: center; gap: 10px; }
.period-icon,.stat-icon,.payment-icon,.dentist-dot { display: grid; width: 40px; height: 40px; flex: 0 0 40px; place-items: center; border: 1px solid rgba(34,211,238,.2); border-radius: 11px; background: rgba(8,145,178,.1); color: #67e8f9; font-size: 19px; }
.period-heading>div { display: flex; flex-direction: column; gap: 3px; }
.period-heading small { color: #8292a8; font-size: 9px; }
.period-heading strong { color: #e2e8f0; font-size: 12px; }
.period-controls { display: flex; align-items: center; justify-content: flex-end; gap: 12px; }
.period-toggle { padding: 3px; border: 1px solid rgba(100,140,190,.15); border-radius: 10px; background: rgba(2,6,23,.25); }
.period-toggle :deep(.q-btn) { min-height: 32px; border-radius: 7px; color: #94a3b8; font-size: 10px; }
.custom-range { display: flex; align-items: center; gap: 7px; }
.custom-range>.q-icon { color: #64748b; }
.date-input { width: 145px; }
.date-input :deep(.q-field__control) { border-radius: 8px; background: rgba(15,23,42,.4); }
.date-input :deep(.q-field__native),.date-input :deep(.q-field__label),.date-input :deep(.q-field__marginal) { color: #cbd5e1; }
.range-error { position: absolute; margin-top: 71px; color: #fca5a5; font-size: 9px; }
.report-section-label { display: flex; max-width: 1200px; align-items: center; justify-content: space-between; margin: 0 auto 9px; }
.report-section-label>span:last-child { color: #718096; font-size: 9px; }
.report-stats { display: grid; max-width: 1200px; margin: 0 auto 18px; grid-template-columns: repeat(5,minmax(0,1fr)); gap: 9px; }
.financial-stats { grid-template-columns: repeat(4,minmax(0,1fr)); }
.report-stat { display: flex; min-width: 0; align-items: center; gap: 10px; padding: 13px; border: 1px solid rgba(100,140,190,.17); border-radius: 12px; background: rgba(16,19,31,.76); }
.report-stat>div { display: flex; min-width: 0; flex-direction: column; gap: 3px; }
.report-stat small { color: #94a3b8; font-size: 9px; }
.report-stat strong { overflow: hidden; color: #f1f5f9; font-size: 19px; text-overflow: ellipsis; white-space: nowrap; }
.report-stat>div>span { color: #64748b; font-size: 8px; line-height: 1.3; }
.stat-icon { width: 35px; height: 35px; flex-basis: 35px; font-size: 17px; }
.icon-total { color: #67e8f9; }.icon-confirmed { color: #4ade80; border-color: rgba(34,197,94,.2); background: rgba(34,197,94,.08); }.icon-attended,.icon-collected { color: #60a5fa; border-color: rgba(96,165,250,.2); background: rgba(96,165,250,.08); }.icon-rescheduled { color: #cbd5e1; border-color: rgba(148,163,184,.2); background: rgba(148,163,184,.08); }.icon-cancelled { color: #f87171; border-color: rgba(248,113,113,.2); background: rgba(127,29,29,.1); }.icon-budget,.icon-plan { color: #c4b5fd; border-color: rgba(167,139,250,.2); background: rgba(91,33,182,.1); }.icon-balance { color: #fbbf24; border-color: rgba(251,191,36,.2); background: rgba(120,83,12,.1); }
.report-grid { display: grid; max-width: 1200px; margin: 0 auto 21px; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 12px; }
.chart-panel,.summary-panel { padding: 17px; }
.panel-heading { margin-bottom: 14px; }
.panel-heading h2 { margin: 4px 0 0; color: #e2e8f0; font-size: 14px; font-weight: 650; }
.panel-heading-icon { color: #67e8f9; font-size: 19px; }
.status-bars { display: flex; flex-direction: column; gap: 13px; }
.status-bar-row { display: flex; flex-direction: column; gap: 6px; }
.bar-label { display: flex; align-items: center; justify-content: space-between; color: #cbd5e1; font-size: 10px; }
.bar-label>span { display: inline-flex; align-items: center; gap: 7px; }.bar-label i { width: 7px; height: 7px; border-radius: 50%; }
.bar-label strong { color: #f1f5f9; font-size: 11px; }
.bar-track { height: 6px; overflow: hidden; border-radius: 6px; background: rgba(100,116,139,.16); }.bar-track>span { display: block; height: 100%; border-radius: inherit; transition: width 200ms ease; }
.activity-chart { display: flex; height: 150px; align-items: flex-end; gap: 7px; overflow-x: auto; padding: 5px 1px 0; }
.activity-column { display: flex; min-width: 24px; height: 100%; flex: 1 0 24px; align-items: center; justify-content: flex-end; flex-direction: column; gap: 5px; }
.activity-count { color: #94a3b8; font-size: 8px; }.activity-bar-wrap { display: flex; width: min(26px,100%); height: 105px; align-items: flex-end; justify-content: center; }.activity-bar { width: 100%; min-height: 4px; border: 1px solid rgba(103,232,249,.25); border-radius: 5px 5px 2px 2px; background: linear-gradient(180deg,rgba(34,211,238,.75),rgba(8,145,178,.25)); }.activity-column small { color: #718096; font-size: 8px; white-space: nowrap; }
.chart-empty { display: grid; min-height: 108px; place-items: center; color: #718096; font-size: 10px; text-align: center; }
.ranking-list { display: flex; flex-direction: column; gap: 7px; }.ranking-row { display: flex; align-items: center; gap: 9px; padding: 8px; border: 1px solid rgba(100,140,190,.11); border-radius: 8px; background: rgba(2,6,23,.16); }.ranking-index { color: #67e8f9; font-family: monospace; font-size: 9px; }.ranking-name { overflow: hidden; flex: 1; color: #cbd5e1; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }.ranking-row :deep(.q-badge) { border: 1px solid rgba(34,211,238,.18); background: rgba(8,145,178,.1); color: #a5f3fc; font-size: 9px; }.dentist-dot { width: 27px; height: 27px; flex-basis: 27px; border-radius: 8px; font-size: 13px; }
.data-panel,.payment-panel { max-width: 1200px; margin: 0 auto 16px; padding: 17px; }.data-panel .panel-heading { align-items: center; }.table-count { border: 1px solid rgba(34,211,238,.16); border-radius: 20px; background: rgba(8,145,178,.1); color: #a5f3fc; font-size: 9px; }.report-table { background: transparent; color: #cbd5e1; }.report-table :deep(thead tr th) { color: #67e8f9; font-size: 9px; font-weight: 700; text-transform: uppercase; }.report-table :deep(tbody td) { border-color: rgba(100,140,190,.11); font-size: 10px; }.report-table :deep(.q-table__bottom) { color: #94a3b8; }.table-patient { display: flex; flex-direction: column; gap: 3px; }.table-patient strong { color: #e2e8f0; font-size: 10px; font-weight: 550; }.table-patient small { color: #718096; font-size: 8px; }.status-pill { display: inline-flex; padding: 4px 7px; border: 1px solid transparent; border-radius: 20px; font-size: 8px; white-space: nowrap; }.status-confirmada { border-color: rgba(34,197,94,.22); background: rgba(34,197,94,.08); color: #86efac; }.status-atendida { border-color: rgba(96,165,250,.24); background: rgba(96,165,250,.1); color: #93c5fd; }.status-reprogramada { border-color: rgba(148,163,184,.22); background: rgba(148,163,184,.08); color: #cbd5e1; }.status-cancelada { border-color: rgba(248,113,113,.23); background: rgba(127,29,29,.1); color: #fca5a5; }.table-more { display: flex; justify-content: center; padding-top: 8px; }
.payment-list { display: flex; flex-direction: column; gap: 7px; }.payment-row { display: flex; align-items: center; gap: 10px; padding: 10px; border: 1px solid rgba(100,140,190,.12); border-radius: 9px; background: rgba(2,6,23,.18); }.payment-icon { width: 33px; height: 33px; flex-basis: 33px; border-radius: 9px; font-size: 16px; }.payment-row>div { display: flex; min-width: 0; flex: 1; flex-direction: column; gap: 3px; }.payment-row strong { color: #e2e8f0; font-size: 10px; font-weight: 550; }.payment-row small { color: #8292a8; font-size: 9px; }.payment-row>b { color: #86efac; font-size: 11px; }
.report-footnote { display: flex; max-width: 1200px; align-items: flex-start; gap: 7px; margin: 0 auto 14px; color: #718096; font-size: 9px; line-height: 1.5; }.report-footnote .q-icon { flex: 0 0 auto; color: #67e8f9; font-size: 15px; }

@media (max-width: 1000px) { .report-stats { grid-template-columns: repeat(3,minmax(0,1fr)); }.financial-stats { grid-template-columns: repeat(2,minmax(0,1fr)); }.period-panel { align-items: flex-start; flex-direction: column; }.period-controls { width: 100%; justify-content: space-between; } }
@media (max-width: 700px) { .page-heading { align-items: flex-start; flex-direction: column; }.header-actions { width: 100%; }.header-actions .q-btn { flex: 1; }.period-controls { align-items: stretch; flex-direction: column; }.period-toggle { width: 100%; }.period-toggle :deep(.q-btn) { flex: 1; }.custom-range { justify-content: space-between; }.date-input { width: calc(50% - 18px); }.report-stats,.financial-stats { grid-template-columns: repeat(2,minmax(0,1fr)); }.report-grid { grid-template-columns: 1fr; }.report-section-label { align-items: flex-start; flex-direction: column; gap: 4px; }.data-panel,.payment-panel { padding: 12px; }.report-table :deep(.q-table__middle) { overflow-x: auto; } }
@media (max-width: 420px) { .report-stat { align-items: flex-start; flex-direction: column; }.report-stat strong { font-size: 16px; }.period-panel { padding: 13px; }.custom-range { gap: 4px; }.date-input { width: calc(50% - 14px); }.data-panel .panel-heading { align-items: flex-start; flex-direction: column; }.payment-row { align-items: flex-start; flex-wrap: wrap; }.payment-row>b { margin-left: 43px; } }
@media print { .reports-page { padding: 0!important; background: #fff!important; color: #111827!important; }.page-heading,.report-panel,.report-stat { break-inside: avoid; }.header-actions,.period-controls,.table-more { display: none!important; }.report-panel,.report-stat { background: #fff!important; border-color: #d1d5db!important; }.page-heading h1,.panel-heading h2,.report-stat strong,.table-patient strong { color: #111827!important; }.eyebrow,.report-stat small,.report-stat>div>span,.report-footnote { color: #4b5563!important; }.report-grid { grid-template-columns: repeat(2,1fr); }.report-table { color: #111827!important; } }
</style>
