<script setup>
import { computed, onMounted, ref } from 'vue'
import { useQuasar } from 'quasar'
import { pacientes as demoPatients } from 'src/data/dummy.js'

const PLAN_KEY = 'smileos-treatment-plans'
const PATIENT_KEY = 'smileos-patients'
const $q = useQuasar()

const patientFilter = ref('')
const patientRecords = ref([])
const plans = ref([])
const phaseDialog = ref(false)
const paymentDialog = ref(false)
const editingPhaseId = ref(null)
const selectedPhase = ref(null)
const phaseForm = ref(emptyPhase())
const paymentForm = ref(emptyPayment())

const statusOptions = [
  { label: 'Propuesto', value: 'propuesto' },
  { label: 'Aprobado', value: 'aprobado' },
  { label: 'En proceso', value: 'en_proceso' },
  { label: 'Completado', value: 'completado' },
]
const paymentMethods = ['Efectivo', 'Tarjeta', 'Transferencia', 'Yappy', 'Otro']

function emptyPhase() {
  return { phase: '', description: '', teeth: [], procedures: '', status: 'propuesto', estimatedCost: 0, startDate: '', endDate: '', notes: '' }
}

function emptyPayment() {
  return { amount: '', date: new Date().toISOString().slice(0, 10), method: '', reference: '', notes: '' }
}

onMounted(() => {
  try {
    const savedPatients = JSON.parse(localStorage.getItem(PATIENT_KEY) || 'null')
    patientRecords.value = Array.isArray(savedPatients) && savedPatients.length
      ? savedPatients.map((patient) => ({
        ...patient,
        id: String(patient.id || patient.cedula),
        nombre: patient.name || patient.fullName || `${patient.firstName || ''} ${patient.lastName || ''}`.trim(),
        cedula: patient.cedula || patient.identificacion || '',
      }))
      : demoPatients.map((patient) => ({
        ...patient,
        id: String(patient.identificacion),
        nombre: patient.nombre,
        cedula: patient.identificacion,
      }))
    const savedPlans = JSON.parse(localStorage.getItem(PLAN_KEY) || '[]')
    plans.value = Array.isArray(savedPlans) ? savedPlans.map(normalizePhase) : []
  } catch (error) {
    console.error('No se pudo cargar el plan de tratamiento', error)
    patientRecords.value = demoPatients.map((patient) => ({ ...patient, id: String(patient.identificacion), nombre: patient.nombre, cedula: patient.identificacion }))
    plans.value = []
  }
})

function normalizePhase(phase) {
  const legacyStatuses = { pendiente: 'propuesto', pospuesto: 'propuesto' }
  return {
    ...phase,
    patientId: String(phase.patientId || phase.pacienteId || ''),
    phase: phase.phase || phase.fase || 'Fase de tratamiento',
    description: phase.description || phase.descripcion || '',
    teeth: Array.isArray(phase.teeth) ? phase.teeth : [],
    procedures: phase.procedures || phase.procedure || phase.descripcion || '',
    status: legacyStatuses[phase.status || phase.estado] || phase.status || phase.estado || 'propuesto',
    estimatedCost: Number(phase.estimatedCost ?? phase.cost ?? 0),
    paidAmount: Number(phase.paidAmount ?? 0),
    payments: Array.isArray(phase.payments) ? phase.payments : [],
    startDate: phase.startDate || phase.fechaInicio || '',
    endDate: phase.endDate || phase.fechaFin || '',
    notes: phase.notes || '',
  }
}

const patientOptions = computed(() => patientRecords.value)
const selectedPatient = computed(() => patientRecords.value.find((patient) => String(patient.id) === String(patientFilter.value)))
const patientPlans = computed(() => plans.value
  .filter((phase) => String(phase.patientId) === String(patientFilter.value))
  .sort((a, b) => Number(a.order || 0) - Number(b.order || 0) || String(a.createdAt || '').localeCompare(String(b.createdAt || ''))))
const totalBudget = computed(() => patientPlans.value.reduce((sum, phase) => sum + Number(phase.estimatedCost || 0), 0))
const totalPaid = computed(() => patientPlans.value.reduce((sum, phase) => sum + Number(phase.paidAmount || 0), 0))
const totalBalance = computed(() => Math.max(0, totalBudget.value - totalPaid.value))
const completedCount = computed(() => patientPlans.value.filter((phase) => phase.status === 'completado').length)
const progressPercent = computed(() => patientPlans.value.length ? Math.round(completedCount.value / patientPlans.value.length * 100) : 0)

function money(value) {
  return new Intl.NumberFormat('es-PA', { style: 'currency', currency: 'USD' }).format(Number(value) || 0)
}

function dateLabel(value) {
  if (!value) return 'Pendiente'
  const date = new Date(`${value}T00:00:00`)
  return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('es-PA', { day: '2-digit', month: 'short', year: 'numeric' }).format(date)
}

function statusText(status) {
  return statusOptions.find((item) => item.value === status)?.label || status
}

function statusClass(status) {
  return `status-${status}`
}

function persistPlans(nextPlans) {
  try {
    localStorage.setItem(PLAN_KEY, JSON.stringify(nextPlans))
    plans.value = nextPlans
    return true
  } catch (error) {
    console.error('No se pudo guardar el plan', error)
    $q.notify({ type: 'negative', message: 'No se pudo guardar el plan en este navegador.' })
    return false
  }
}

function openNewPhase() {
  editingPhaseId.value = null
  phaseForm.value = emptyPhase()
  phaseDialog.value = true
}

function editPhase(phase) {
  editingPhaseId.value = phase.id
  phaseForm.value = { ...emptyPhase(), ...phase, teeth: [...(phase.teeth || [])] }
  phaseDialog.value = true
}

function savePhase() {
  const form = phaseForm.value
  if (!patientFilter.value || !form.phase.trim() || !form.description.trim()) {
    $q.notify({ type: 'warning', message: 'Selecciona un paciente e indica la fase y su propuesta clínica.' })
    return
  }
  const now = new Date().toISOString()
  const existing = plans.value.find((item) => String(item.id) === String(editingPhaseId.value))
  const record = {
    ...form,
    id: editingPhaseId.value || globalThis.crypto?.randomUUID?.() || `plan-${Date.now()}`,
    patientId: String(patientFilter.value),
    phase: form.phase.trim(),
    description: form.description.trim(),
    procedures: form.procedures.trim(),
    teeth: [...new Set(form.teeth.map((tooth) => String(tooth).trim()).filter(Boolean))],
    estimatedCost: Math.max(0, Number(form.estimatedCost) || 0),
    paidAmount: Number(existing?.paidAmount || 0),
    payments: existing?.payments || [],
    createdAt: existing?.createdAt || now,
    updatedAt: now,
  }
  const next = existing
    ? plans.value.map((item) => String(item.id) === String(editingPhaseId.value) ? record : item)
    : [...plans.value, { ...record, order: patientPlans.value.length + 1 }]
  if (persistPlans(next)) {
    phaseDialog.value = false
    $q.notify({ type: 'positive', message: existing ? 'Fase actualizada.' : 'Fase agregada al plan.' })
  }
}

function changePhaseStatus(phase, status) {
  const today = new Date().toISOString().slice(0, 10)
  const updated = {
    ...phase,
    status,
    startDate: status === 'en_proceso' || status === 'completado' ? (phase.startDate || today) : phase.startDate,
    endDate: status === 'completado' ? today : status === 'en_proceso' ? '' : phase.endDate,
    updatedAt: new Date().toISOString(),
  }
  persistPlans(plans.value.map((item) => item.id === phase.id ? updated : item))
}

function openPayment(phase) {
  selectedPhase.value = phase
  paymentForm.value = emptyPayment()
  paymentDialog.value = true
}

function savePayment() {
  const phase = selectedPhase.value
  const amount = Number(paymentForm.value.amount)
  const balance = Math.max(0, Number(phase?.estimatedCost || 0) - Number(phase?.paidAmount || 0))
  if (!phase || !Number.isFinite(amount) || amount <= 0 || !paymentForm.value.date || !paymentForm.value.method) {
    $q.notify({ type: 'warning', message: 'Completa monto, fecha y método de pago.' })
    return
  }
  if (amount > balance) {
    $q.notify({ type: 'warning', message: `El pago supera el saldo pendiente (${money(balance)}).` })
    return
  }
  const payment = {
    id: globalThis.crypto?.randomUUID?.() || `payment-${Date.now()}`,
    amount,
    date: paymentForm.value.date,
    method: paymentForm.value.method,
    reference: paymentForm.value.reference.trim(),
    notes: paymentForm.value.notes.trim(),
    createdAt: new Date().toISOString(),
  }
  const updated = { ...phase, paidAmount: Number(phase.paidAmount || 0) + amount, payments: [...(phase.payments || []), payment], updatedAt: new Date().toISOString() }
  if (persistPlans(plans.value.map((item) => item.id === phase.id ? updated : item))) {
    paymentDialog.value = false
    $q.notify({ type: 'positive', message: 'Pago registrado en el saldo del plan.' })
  }
}

function removePhase(phase) {
  $q.dialog({
    title: 'Eliminar fase',
    message: `¿Eliminar “${phase.phase}”? Se conservarán los registros de evolución, pero se quitará esta fase del plan.`,
    cancel: { flat: true, label: 'Cancelar', noCaps: true },
    ok: { color: 'negative', label: 'Eliminar', noCaps: true },
    persistent: true,
  }).onOk(() => {
    persistPlans(plans.value.filter((item) => item.id !== phase.id))
  })
}
</script>

<template>
  <q-page class="treatment-page futuristic-bg q-pa-md q-pa-lg-lg">
    <section class="page-heading">
      <div><div class="eyebrow">Planificación clínica</div><h1>Plan de tratamiento</h1><p>Organiza las etapas clínicas, sus costos y el avance de cada paciente.</p></div>
    </section>

    <section class="treatment-panel">
      <header class="patient-selector-header">
        <div><div class="eyebrow">Paciente</div><h2>Propuesta por etapas</h2></div>
        <q-select v-model="patientFilter" :options="patientOptions" option-label="nombre" option-value="id" emit-value map-options clearable outlined dark dense label="Selecciona un paciente" class="patient-select" />
      </header>

      <template v-if="selectedPatient">
        <div class="selected-patient-heading"><div><span>Plan clínico de</span><strong>{{ selectedPatient.nombre }}</strong><small>Cédula · {{ selectedPatient.cedula }}</small></div><q-btn unelevated no-caps icon="add" label="Agregar fase" class="primary-action" @click="openNewPhase" /></div>

        <section class="plan-overview">
          <article><span class="overview-icon"><q-icon name="account_tree" /></span><div><small>Fases</small><strong>{{ patientPlans.length }}</strong></div></article>
          <article><span class="overview-icon"><q-icon name="task_alt" /></span><div><small>Completadas</small><strong>{{ completedCount }} <small>de {{ patientPlans.length }}</small></strong></div></article>
          <article><span class="overview-icon"><q-icon name="payments" /></span><div><small>Presupuesto</small><strong>{{ money(totalBudget) }}</strong></div></article>
          <article><span class="overview-icon"><q-icon name="account_balance_wallet" /></span><div><small>Saldo pendiente</small><strong>{{ money(totalBalance) }}</strong></div></article>
        </section>

        <div v-if="patientPlans.length" class="progress-overview"><div><span>Avance del plan</span><strong>{{ progressPercent }}%</strong></div><q-linear-progress :value="progressPercent / 100" rounded color="cyan-4" track-color="blue-grey-10" size="7px" /></div>

        <div v-if="patientPlans.length" class="phase-list">
          <article v-for="(phase, index) in patientPlans" :key="phase.id" class="phase-card">
            <div class="phase-index">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="phase-content">
              <header class="phase-header"><div><span class="phase-label">Etapa {{ index + 1 }}</span><h3>{{ phase.phase }}</h3></div><q-badge :class="['phase-status', statusClass(phase.status)]">{{ statusText(phase.status) }}</q-badge></header>
              <p class="phase-description">{{ phase.description }}</p>
              <div v-if="phase.teeth?.length" class="phase-detail"><span><q-icon name="dentistry" /> Piezas dentales</span><div class="tooth-list"><q-badge v-for="tooth in phase.teeth" :key="tooth" class="tooth-chip">{{ tooth }}</q-badge></div></div>
              <div v-if="phase.procedures" class="phase-detail"><span><q-icon name="medical_services" /> Procedimientos previstos</span><p>{{ phase.procedures }}</p></div>
              <div class="phase-footer">
                <div class="phase-financial"><strong>{{ money(phase.estimatedCost) }}</strong><span>Presupuesto</span><small>Pagado {{ money(phase.paidAmount) }} · Saldo {{ money(Math.max(0, phase.estimatedCost - phase.paidAmount)) }}</small></div>
                <div class="phase-actions"><q-select :model-value="phase.status" :options="statusOptions" emit-value map-options borderless dense options-dense class="phase-status-select" @update:model-value="changePhaseStatus(phase, $event)" /><q-btn flat round dense icon="payments" class="phase-action" aria-label="Registrar pago" :disable="phase.estimatedCost <= phase.paidAmount" @click="openPayment(phase)"><q-tooltip>Registrar pago</q-tooltip></q-btn><q-btn flat round dense icon="edit" class="phase-action" aria-label="Editar fase" @click="editPhase(phase)"><q-tooltip>Editar fase</q-tooltip></q-btn><q-btn flat round dense icon="delete_outline" class="phase-action danger-action" aria-label="Eliminar fase" @click="removePhase(phase)"><q-tooltip>Eliminar fase</q-tooltip></q-btn></div>
              </div>
              <div v-if="phase.payments?.length" class="payment-history"><details><summary>{{ phase.payments.length }} {{ phase.payments.length === 1 ? 'pago registrado' : 'pagos registrados' }}</summary><div v-for="payment in [...phase.payments].reverse()" :key="payment.id" class="payment-row"><span>{{ dateLabel(payment.date) }} · {{ payment.method }}</span><strong>{{ money(payment.amount) }}</strong><small v-if="payment.reference">{{ payment.reference }}</small></div></details></div>
              <div v-if="phase.startDate || phase.endDate" class="phase-dates"><span v-if="phase.startDate">Inicio {{ dateLabel(phase.startDate) }}</span><span v-if="phase.endDate">Finalizada {{ dateLabel(phase.endDate) }}</span></div>
            </div>
          </article>
        </div>
        <div v-else class="empty-plan"><span><q-icon name="assignment_add" /></span><strong>Este paciente aún no tiene fases clínicas</strong><p>Agrega una etapa con procedimientos, piezas dentales y presupuesto estimado.</p><q-btn flat no-caps icon="add" label="Crear primera fase" class="primary-action" @click="openNewPhase" /></div>
      </template>
      <div v-else class="empty-plan patient-prompt"><span><q-icon name="person_search" /></span><strong>Selecciona un paciente</strong><p>Consulta su propuesta por etapas, avance y saldo.</p></div>
    </section>

    <q-dialog v-model="phaseDialog" persistent>
      <q-card class="treatment-dialog">
        <header class="dialog-header"><span class="dialog-icon"><q-icon name="account_tree" /></span><div><div class="eyebrow">Propuesta clínica</div><h2>{{ editingPhaseId ? 'Editar etapa' : 'Agregar etapa' }}</h2><p>{{ selectedPatient?.nombre }} · ordenada dentro del plan del paciente</p></div><q-btn flat round dense icon="close" class="dialog-close" aria-label="Cerrar" @click="phaseDialog = false" /></header>
        <q-form class="treatment-form" @submit.prevent="savePhase">
          <div class="form-grid">
            <q-input v-model.trim="phaseForm.phase" outlined dark label="Nombre de la etapa *" placeholder="Ej. Fase 1 · Control de caries" class="form-full" />
            <q-input v-model.trim="phaseForm.description" outlined dark type="textarea" autogrow label="Objetivo / propuesta clínica *" class="form-full" />
            <q-select v-model="phaseForm.teeth" outlined dark use-input multiple use-chips new-value-mode="add-unique" label="Piezas dentales (FDI)" hint="Escribe un número dental y presiona Enter." class="form-full" />
            <q-input v-model.trim="phaseForm.procedures" outlined dark type="textarea" autogrow label="Procedimientos previstos" class="form-full" />
            <q-select v-model="phaseForm.status" outlined dark emit-value map-options :options="statusOptions" label="Estado de la propuesta" />
            <q-input v-model.number="phaseForm.estimatedCost" outlined dark type="number" min="0" step="0.01" prefix="$" label="Presupuesto estimado (USD)" />
            <q-input v-model="phaseForm.startDate" outlined dark type="date" stack-label label="Fecha de inicio" />
            <q-input v-model="phaseForm.endDate" outlined dark type="date" stack-label label="Fecha estimada/finalización" />
            <q-input v-model.trim="phaseForm.notes" outlined dark type="textarea" autogrow label="Notas" class="form-full" />
          </div>
          <footer class="dialog-footer"><q-btn flat no-caps label="Cancelar" class="subtle-action" @click="phaseDialog = false" /><q-btn unelevated no-caps label="Guardar etapa" icon="check" class="primary-action" type="submit" /></footer>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="paymentDialog" persistent>
      <q-card class="treatment-dialog payment-dialog">
        <header class="dialog-header"><span class="dialog-icon"><q-icon name="payments" /></span><div><div class="eyebrow">Cobro asociado</div><h2>Registrar pago</h2><p>{{ selectedPhase?.phase }} · Saldo {{ money(Math.max(0, (selectedPhase?.estimatedCost || 0) - (selectedPhase?.paidAmount || 0))) }}</p></div><q-btn flat round dense icon="close" class="dialog-close" aria-label="Cerrar" @click="paymentDialog = false" /></header>
        <q-form class="treatment-form" @submit.prevent="savePayment">
          <div class="form-grid">
            <q-input v-model.number="paymentForm.amount" outlined dark type="number" min="0.01" step="0.01" prefix="$" label="Monto recibido *" />
            <q-input v-model="paymentForm.date" outlined dark type="date" stack-label label="Fecha *" />
            <q-select v-model="paymentForm.method" outlined dark :options="paymentMethods" label="Método de pago *" />
            <q-input v-model.trim="paymentForm.reference" outlined dark label="Referencia / recibo" />
            <q-input v-model.trim="paymentForm.notes" outlined dark type="textarea" autogrow label="Observaciones" class="form-full" />
          </div>
          <footer class="dialog-footer"><q-btn flat no-caps label="Cancelar" class="subtle-action" @click="paymentDialog = false" /><q-btn unelevated no-caps label="Guardar pago" icon="check" class="primary-action" type="submit" /></footer>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<style scoped>
.treatment-page { min-height: 100%; color: #e2e8f0; }
.page-heading,.patient-selector-header,.selected-patient-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.page-heading { max-width: 1120px; margin: 4px auto 22px; }
.page-heading h1 { margin: 4px 0; color: #f8fafc; font-size: clamp(26px,4vw,34px); font-weight: 700; }
.page-heading p { margin: 0; color: #94a3b8; font-size: 12px; }
.eyebrow { color: #67e8f9; font-size: 10px; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; }
.treatment-panel { max-width: 1120px; margin: 0 auto; padding: 22px; border: 1px solid rgba(100,140,190,.2); border-radius: 17px; background: rgba(16,19,31,.8); }
.patient-selector-header { flex-wrap: wrap; padding-bottom: 17px; border-bottom: 1px solid rgba(100,140,190,.13); }
.patient-selector-header h2 { margin: 5px 0 0; color: #f1f5f9; font-size: 18px; }
.patient-select { width: min(330px,100%); }
.patient-select :deep(.q-field__control) { border-radius: 9px; background: rgba(15,23,42,.45); }
.patient-select :deep(.q-field__label),.patient-select :deep(.q-field__native),.patient-select :deep(.q-field__marginal) { color: #cbd5e1; }
.selected-patient-heading { margin: 18px 0 14px; }
.selected-patient-heading>div { display: flex; flex-direction: column; gap: 3px; }
.selected-patient-heading span,.selected-patient-heading small { color: #8292a8; font-size: 10px; }
.selected-patient-heading strong { color: #f1f5f9; font-size: 16px; }
.primary-action { min-height: 39px; padding: 0 14px; border: 1px solid rgba(34,211,238,.38); border-radius: 9px; background: linear-gradient(120deg,rgba(8,145,178,.32),rgba(30,64,175,.28)); color: #a5f3fc; }
.plan-overview { display: grid; margin: 14px 0; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 9px; }
.plan-overview article { display: flex; align-items: center; gap: 10px; min-width: 0; padding: 12px; border: 1px solid rgba(100,140,190,.15); border-radius: 11px; background: rgba(15,23,42,.42); }
.overview-icon,.dialog-icon { display: grid; width: 37px; height: 37px; flex: 0 0 37px; place-items: center; border: 1px solid rgba(34,211,238,.18); border-radius: 10px; background: rgba(8,145,178,.1); color: #67e8f9; font-size: 18px; }
.plan-overview article>div { display: flex; min-width: 0; flex-direction: column; gap: 3px; }
.plan-overview article small { color: #8292a8; font-size: 9px; }
.plan-overview article strong { overflow: hidden; color: #e2e8f0; font-size: 15px; text-overflow: ellipsis; white-space: nowrap; }
.plan-overview article strong small { font-size: 9px; font-weight: 400; }
.progress-overview { margin: 17px 0; }
.progress-overview>div { display: flex; justify-content: space-between; margin-bottom: 7px; color: #94a3b8; font-size: 10px; }
.progress-overview strong { color: #67e8f9; }
.phase-list { display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }
.phase-card { display: flex; gap: 14px; padding: 16px; border: 1px solid rgba(100,140,190,.17); border-radius: 13px; background: linear-gradient(110deg,rgba(15,38,58,.56),rgba(15,23,42,.7)); }
.phase-index { display: grid; width: 39px; height: 39px; flex: 0 0 39px; place-items: center; border: 1px solid rgba(34,211,238,.22); border-radius: 11px; background: rgba(8,145,178,.1); color: #67e8f9; font-size: 12px; font-weight: 700; }
.phase-content { min-width: 0; flex: 1; }
.phase-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.phase-label { color: #67e8f9; font-size: 9px; letter-spacing: .09em; text-transform: uppercase; }
.phase-header h3 { margin: 3px 0 0; color: #f1f5f9; font-size: 14px; font-weight: 650; }
.phase-status { border: 1px solid transparent; border-radius: 18px; padding: 5px 9px; font-size: 9px; }
.status-propuesto { border-color: rgba(148,163,184,.25); background: rgba(148,163,184,.1); color: #cbd5e1; }
.status-aprobado { border-color: rgba(34,211,238,.26); background: rgba(8,145,178,.12); color: #a5f3fc; }
.status-en_proceso { border-color: rgba(251,191,36,.25); background: rgba(161,98,7,.12); color: #fcd34d; }
.status-completado { border-color: rgba(34,197,94,.24); background: rgba(34,197,94,.1); color: #86efac; }
.phase-description { margin: 8px 0 12px; color: #a8b4c5; font-size: 11px; line-height: 1.5; }
.phase-detail { display: flex; align-items: flex-start; gap: 10px; margin: 8px 0; }
.phase-detail>span { display: inline-flex; flex: 0 0 155px; align-items: center; gap: 5px; color: #8292a8; font-size: 9px; }
.phase-detail>span .q-icon { color: #67e8f9; font-size: 14px; }
.phase-detail>p { margin: 0; color: #cbd5e1; font-size: 10px; line-height: 1.5; }
.tooth-list { display: flex; flex-wrap: wrap; gap: 5px; }
.tooth-chip { border: 1px solid rgba(34,211,238,.2); border-radius: 6px; background: rgba(8,145,178,.1); color: #a5f3fc; font-size: 9px; }
.phase-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 13px; padding-top: 11px; border-top: 1px solid rgba(100,140,190,.12); }
.phase-financial { display: flex; align-items: baseline; flex-wrap: wrap; gap: 6px 9px; }
.phase-financial strong { color: #e2e8f0; font-size: 13px; }
.phase-financial span,.phase-financial small { color: #8292a8; font-size: 9px; }
.phase-actions { display: flex; align-items: center; gap: 3px; }
.phase-status-select { min-width: 104px; color: #cbd5e1; font-size: 10px; }
.phase-status-select :deep(.q-field__native),.phase-status-select :deep(.q-field__marginal) { color: inherit; }
.phase-action { color: #94a3b8; }
.phase-action:hover { color: #67e8f9; background: rgba(34,211,238,.08); }
.danger-action:hover { color: #fca5a5; }
.payment-history { margin-top: 10px; color: #94a3b8; font-size: 10px; }
.payment-history summary { cursor: pointer; color: #67e8f9; }
.payment-row { display: grid; margin-top: 7px; padding: 8px; grid-template-columns: 1fr auto; gap: 3px 10px; border-radius: 7px; background: rgba(2,6,23,.25); }
.payment-row strong { color: #86efac; }
.payment-row small { grid-column: 1 / -1; color: #64748b; }
.phase-dates { display: flex; gap: 12px; margin-top: 8px; color: #64748b; font-size: 9px; }
.empty-plan { display: flex; min-height: 230px; align-items: center; justify-content: center; flex-direction: column; padding: 22px; text-align: center; }
.empty-plan>span { display: grid; width: 55px; height: 55px; margin-bottom: 12px; place-items: center; border: 1px solid rgba(34,211,238,.18); border-radius: 16px; color: #67e8f9; font-size: 27px; }
.empty-plan>strong { color: #dbeafe; font-size: 13px; }
.empty-plan>p { max-width: 420px; margin: 7px 0 14px; color: #718096; font-size: 11px; }
.patient-prompt { min-height: 300px; }
.treatment-dialog { display: flex; width: min(720px,calc(100vw - 28px)); max-width: 720px; max-height: 90vh; flex-direction: column; overflow: hidden; border: 1px solid rgba(34,211,238,.27); border-radius: 17px; background: radial-gradient(ellipse at 5% 0%,rgba(8,145,178,.15),transparent 42%),#0b1120; color: #e2e8f0; box-shadow: 0 24px 80px rgba(0,0,0,.56); }
.dialog-header { display: flex; align-items: center; gap: 12px; padding: 19px 22px; border-bottom: 1px solid rgba(100,140,190,.14); }
.dialog-header>div { min-width: 0; flex: 1; }
.dialog-header h2 { margin: 4px 0; color: #f8fafc; font-size: 18px; }
.dialog-header p { margin: 0; color: #94a3b8; font-size: 10px; }
.dialog-close { align-self: flex-start; color: #94a3b8; }
.treatment-form { min-height: 0; overflow-y: auto; }
.form-grid { display: grid; padding: 18px 22px; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 11px; }
.form-full { grid-column: 1 / -1; }
.treatment-form :deep(.q-field__control) { border-radius: 9px; background: rgba(15,23,42,.44); }
.treatment-form :deep(.q-field__label),.treatment-form :deep(.q-field__native),.treatment-form :deep(.q-field__marginal),.treatment-form :deep(.q-field__prefix) { color: #b6c4d5; }
.treatment-form :deep(.q-field--outlined .q-field__control:before) { border-color: rgba(100,140,190,.25); }
.treatment-form :deep(.q-field--focused .q-field__control:after) { border-color: #22d3ee; }
.dialog-footer { position: sticky; bottom: 0; display: flex; justify-content: flex-end; gap: 9px; padding: 12px 22px; border-top: 1px solid rgba(100,140,190,.14); background: #0b1120; }
.subtle-action { color: #9fb0c5; }

@media (max-width: 760px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .treatment-panel { padding: 14px; }
  .patient-selector-header,.selected-patient-heading { align-items: stretch; flex-direction: column; }
  .patient-select { width: 100%; }
  .selected-patient-heading .primary-action { width: 100%; justify-content: center; }
  .plan-overview { grid-template-columns: repeat(2,minmax(0,1fr)); }
  .phase-card { gap: 9px; padding: 11px; }
  .phase-index { width: 32px; height: 32px; flex-basis: 32px; }
  .phase-footer { align-items: flex-start; flex-direction: column; }
  .phase-actions { width: 100%; justify-content: flex-end; flex-wrap: wrap; }
  .phase-status-select { margin-right: auto; }
}
@media (max-width: 520px) {
  .phase-header { flex-direction: column; }
  .phase-detail { flex-direction: column; gap: 5px; }
  .phase-detail>span { flex-basis: auto; }
  .form-grid { grid-template-columns: 1fr; padding: 15px; }
  .form-full { grid-column: auto; }
  .dialog-header { padding: 16px; }
  .dialog-footer { padding: 11px 15px; }
}
</style>
