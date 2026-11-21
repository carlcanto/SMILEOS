<script setup>
import { computed, onMounted, ref } from 'vue'
import { useQuasar } from 'quasar'
import { pacientes as demoPatients } from 'src/data/dummy.js'

const EVOLUTIONS_KEY = 'smileos-evolutions'
const APPOINTMENTS_KEY = 'smileos-appointments'
const PATIENTS_KEY = 'smileos-patients'
const PLANS_KEY = 'smileos-treatment-plans'
const $q = useQuasar()

const evolutions = ref([])
const appointments = ref([])
const patients = ref([])
const plans = ref([])
const patientFilter = ref('')
const searchQuery = ref('')
const showForm = ref(false)
const selectedAppointmentId = ref('')
const selectedEvolution = ref(null)
const detailsDialog = ref(false)
const form = ref(emptyForm())

function emptyForm() {
  return {
    appointmentId: '', patientId: '', patientName: '', patientCedula: '',
    date: '', dentistName: '', reason: '', findings: '', procedure: '', instructions: '',
    treatmentPhaseId: '', planProgress: 'en_proceso', signature: '', validated: false,
  }
}

function readArray(key) {
  try {
    const result = JSON.parse(localStorage.getItem(key) || '[]')
    return Array.isArray(result) ? result : []
  } catch {
    return []
  }
}

function localDate(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

onMounted(() => {
  evolutions.value = readArray(EVOLUTIONS_KEY)
  appointments.value = readArray(APPOINTMENTS_KEY).map((item) => ({
    ...item,
    start: new Date(item.start),
    end: new Date(item.end),
  }))
  const savedPatients = readArray(PATIENTS_KEY)
  patients.value = savedPatients.length ? savedPatients : demoPatients.map((patient) => ({
    id: String(patient.identificacion),
    cedula: patient.identificacion,
    patientCode: patient.identificacion,
    name: patient.nombre,
    firstName: patient.nombre,
    phone: patient.telefono,
  }))

  plans.value = readArray(PLANS_KEY)
})

function fullName(patient) {
  return patient.name || patient.fullName || `${patient.firstName || ''} ${patient.lastName || ''}`.trim() || 'Paciente'
}

function appointmentPatientId(appointment) {
  return String(appointment.patientId || appointment.cedula || '')
}

const eligibleAppointments = computed(() => appointments.value
  .filter((appointment) => appointment.status === 'confirmada'
    && appointment.start instanceof Date
    && !Number.isNaN(appointment.start.getTime())
    && appointment.start <= new Date()
    && !evolutions.value.some((evolution) => String(evolution.appointmentId) === String(appointment.id)))
  .sort((a, b) => b.start - a.start))

const appointmentOptions = computed(() => eligibleAppointments.value.map((appointment) => ({
  label: `${appointment.patientName} · ${formatDate(appointment.start)} · ${appointment.reason || 'Consulta'}`,
  value: String(appointment.id),
})))

const selectedAppointment = computed(() => appointments.value.find((appointment) => String(appointment.id) === String(selectedAppointmentId.value)))

const patientOptions = computed(() => {
  const source = new Map()
  appointments.value.forEach((appointment) => {
    const id = appointmentPatientId(appointment)
    if (id) source.set(id, { id, name: appointment.patientName, cedula: appointment.cedula || id })
  })
  patients.value.forEach((patient) => {
    const id = String(patient.id || patient.cedula || '')
    if (id) source.set(id, { id, name: fullName(patient), cedula: patient.cedula || id })
  })
  return [...source.values()]
})
const patientFilterOptions = computed(() => patientOptions.value.map((item) => ({ label: item.name, value: item.id })))

const phasesForPatient = computed(() => plans.value.filter((phase) => String(phase.patientId) === String(form.value.patientId)
  && (phase.status || phase.estado) !== 'completado'))
const selectedTreatmentPhase = computed(() => phasesForPatient.value.find((phase) => String(phase.id) === String(form.value.treatmentPhaseId)))
const phaseOptions = computed(() => phasesForPatient.value.map((phase) => ({
  label: `${phase.fase} · ${phase.descripcion}`,
  value: String(phase.id),
})))

const filteredEvolutions = computed(() => {
  const query = normalize(searchQuery.value)
  return [...evolutions.value]
    .filter((evolution) => !patientFilter.value || String(evolution.patientId) === String(patientFilter.value))
    .filter((evolution) => !query || normalize(`${evolution.patientName} ${evolution.patientCedula} ${evolution.dentistName} ${evolution.reason} ${evolution.procedure}`).includes(query))
    .sort((a, b) => String(b.date).localeCompare(String(a.date)) || String(b.createdAt).localeCompare(String(a.createdAt)))
})

const todayCount = computed(() => evolutions.value.filter((item) => item.date === localDate()).length)

function normalize(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').trim()
}

function formatDate(value) {
  if (!value) return '—'
  const date = value instanceof Date ? value : new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('es-PA', { day: '2-digit', month: 'long', year: 'numeric' }).format(date)
}

function openNewEvolution() {
  form.value = emptyForm()
  selectedAppointmentId.value = ''
  showForm.value = true
}

function applyAppointment(appointmentId) {
  const appointment = appointments.value.find((item) => String(item.id) === String(appointmentId))
  if (!appointment) return
  const patientId = appointmentPatientId(appointment)
  const phase = plans.value.find((item) => String(item.patientId) === patientId && (item.status || item.estado) !== 'completado')
  form.value = {
    ...emptyForm(),
    appointmentId: String(appointment.id),
    patientId,
    patientName: appointment.patientName,
    patientCedula: appointment.cedula || patientId,
    date: localDate(appointment.start),
    dentistName: appointment.dentistName || 'Odontólogo por asignar',
    reason: appointment.reason || 'Consulta general',
    procedure: appointment.treatmentType || phase?.procedures || appointment.reason || '',
    treatmentPhaseId: phase ? String(phase.id) : '',
  }
}

function applyTreatmentPhase(phaseId) {
  const phase = phasesForPatient.value.find((item) => String(item.id) === String(phaseId))
  if (phase && !form.value.procedure.trim()) form.value.procedure = phase.procedures || phase.description || ''
}

function validateForm() {
  if (!selectedAppointment.value) {
    $q.notify({ type: 'warning', message: 'Selecciona una cita atendida para iniciar la evolución.' })
    return false
  }
  if (!form.value.findings.trim() || !form.value.procedure.trim()) {
    $q.notify({ type: 'warning', message: 'Completa los hallazgos y el procedimiento realizado.' })
    return false
  }
  if (!form.value.signature.trim() || !form.value.validated) {
    $q.notify({ type: 'warning', message: 'Registra la firma del profesional y confirma la validación.' })
    return false
  }
  if (!form.value.instructions.trim()) {
    $q.notify({ type: 'warning', message: 'Registra las indicaciones postoperatorias o indica que no aplican.' })
    return false
  }
  if (phasesForPatient.value.length && !form.value.treatmentPhaseId) {
    $q.notify({ type: 'warning', message: 'Selecciona la fase del plan que se actualizó durante esta consulta.' })
    return false
  }
  return true
}

function saveEvolution() {
  if (!validateForm()) return
  const appointment = selectedAppointment.value
  const now = new Date().toISOString()
  const evolution = {
    id: globalThis.crypto?.randomUUID?.() || `evo-${Date.now()}`,
    appointmentId: String(appointment.id),
    patientId: appointmentPatientId(appointment),
    patientName: appointment.patientName,
    patientCedula: appointment.cedula || appointmentPatientId(appointment),
    date: localDate(appointment.start),
    dentistName: appointment.dentistName || form.value.dentistName,
    reason: appointment.reason || form.value.reason,
    findings: form.value.findings.trim(),
    procedure: form.value.procedure.trim(),
    instructions: form.value.instructions.trim(),
    signature: form.value.signature.trim(),
    validated: true,
    signedAt: now,
    treatmentPhaseId: form.value.treatmentPhaseId || null,
    createdAt: now,
  }

  const nextEvolutions = [evolution, ...evolutions.value]
  const nextAppointments = appointments.value.map((item) => String(item.id) === String(appointment.id)
    ? { ...item, status: 'atendida', evolutionId: evolution.id, attendedAt: now }
    : item)
  let nextPlans = plans.value
  if (form.value.treatmentPhaseId) {
    nextPlans = plans.value.map((phase) => String(phase.id) === String(form.value.treatmentPhaseId)
      ? {
        ...phase,
        status: form.value.planProgress,
        startDate: phase.startDate || phase.fechaInicio || evolution.date,
        endDate: form.value.planProgress === 'completado' ? evolution.date : '',
        estado: form.value.planProgress,
        fechaInicio: phase.fechaInicio || evolution.date,
        fechaFin: form.value.planProgress === 'completado' ? evolution.date : null,
        lastEvolutionId: evolution.id,
        updatedAt: now,
      }
      : phase)
  }

  try {
    localStorage.setItem(EVOLUTIONS_KEY, JSON.stringify(nextEvolutions))
    localStorage.setItem(APPOINTMENTS_KEY, JSON.stringify(nextAppointments))
    if (form.value.treatmentPhaseId) localStorage.setItem(PLANS_KEY, JSON.stringify(nextPlans))
    evolutions.value = nextEvolutions
    appointments.value = nextAppointments.map((item) => ({ ...item, start: new Date(item.start), end: new Date(item.end) }))
    plans.value = nextPlans
    showForm.value = false
    $q.notify({ type: 'positive', message: 'Evolución guardada; la cita quedó marcada como atendida.' })
  } catch (error) {
    console.error('No se pudo guardar la evolución', error)
    $q.notify({ type: 'negative', message: 'No se pudo guardar el registro en este navegador.' })
  }
}

function showEvolution(evolution) {
  selectedEvolution.value = evolution
  detailsDialog.value = true
}

function formatTime(value) {
  if (!value) return ''
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString('es-PA', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <q-page class="evolutions-page futuristic-bg q-pa-md q-pa-lg-lg">
    <section class="page-heading">
      <div>
        <div class="eyebrow">Historial clínico</div>
        <h1>Evoluciones</h1>
        <p>Registro cronológico de consultas y sesiones atendidas.</p>
      </div>
      <q-btn unelevated no-caps icon="add" label="Registrar evolución" class="primary-action" :disable="!eligibleAppointments.length" @click="openNewEvolution" />
    </section>

    <section class="evolution-stats">
      <article><span class="stat-icon"><q-icon name="timeline" /></span><div><small>Registros clínicos</small><strong>{{ evolutions.length }}</strong></div></article>
      <article><span class="stat-icon"><q-icon name="event_available" /></span><div><small>Citas atendidas hoy</small><strong>{{ todayCount }}</strong></div></article>
      <article><span class="stat-icon"><q-icon name="verified_user" /></span><div><small>Validadas</small><strong>{{ evolutions.filter((item) => item.validated).length }}</strong></div></article>
    </section>

    <section class="evolutions-panel">
      <header class="panel-heading">
        <div><div class="eyebrow">Cronología</div><h2>Atenciones registradas</h2></div>
        <div class="timeline-filters">
          <q-select v-model="patientFilter" outlined dark dense clearable emit-value map-options :options="patientFilterOptions" label="Todos los pacientes" class="filter-select" />
          <q-input v-model="searchQuery" outlined dark dense clearable label="Buscar en el historial" class="filter-search"><template #prepend><q-icon name="search" /></template></q-input>
        </div>
      </header>

      <div v-if="filteredEvolutions.length" class="timeline-list">
        <article v-for="evolution in filteredEvolutions" :key="evolution.id" class="timeline-card" role="button" tabindex="0" @click="showEvolution(evolution)" @keydown.enter="showEvolution(evolution)">
          <div class="timeline-marker"><q-icon name="medical_services" /></div>
          <div class="timeline-card-content">
            <div class="timeline-card-top">
              <div><span class="patient-name">{{ evolution.patientName }}</span><span class="patient-cedula">Cédula · {{ evolution.patientCedula }}</span></div>
              <div class="timeline-date">{{ formatDate(evolution.date) }}</div>
            </div>
            <div class="timeline-meta"><span><q-icon name="person" />{{ evolution.dentistName }}</span><span><q-icon name="help_outline" />{{ evolution.reason }}</span></div>
            <p class="procedure-preview"><strong>Procedimiento:</strong> {{ evolution.procedure }}</p>
            <div class="timeline-card-bottom"><q-badge class="validated-badge"><q-icon name="verified" />Firmada y validada</q-badge><span class="view-record">Ver registro <q-icon name="arrow_forward" /></span></div>
          </div>
        </article>
      </div>
      <div v-else class="empty-state"><span class="empty-icon"><q-icon name="assignment_add" /></span><strong>No hay evoluciones que mostrar</strong><p>{{ eligibleAppointments.length ? 'Registra la evolución de una cita atendida para iniciar el historial.' : 'Las citas atendidas estarán disponibles aquí para registrar su evolución.' }}</p></div>
    </section>

    <q-dialog v-model="showForm" persistent>
      <q-card class="evolution-dialog">
        <header class="dialog-header"><span class="dialog-icon"><q-icon name="clinical_notes" /></span><div><div class="eyebrow">Nueva atención</div><h2>Registrar evolución clínica</h2><p>El registro quedará asociado a la cita y al historial del paciente.</p></div><q-btn flat round dense icon="close" class="dialog-close" aria-label="Cerrar" @click="showForm = false" /></header>
        <q-form class="evolution-form" @submit.prevent="saveEvolution">
          <section class="form-section">
            <div class="form-section-title"><q-icon name="event_note" /><span>Cita atendida</span></div>
            <q-select v-model="selectedAppointmentId" outlined dark emit-value map-options :options="appointmentOptions" label="Selecciona la cita atendida *" @update:model-value="applyAppointment" />
            <div v-if="selectedAppointment" class="appointment-summary">
              <div><span>Paciente</span><strong>{{ selectedAppointment.patientName }}</strong><small>Cédula · {{ selectedAppointment.cedula }}</small></div>
              <div><span>Fecha y hora</span><strong>{{ formatDate(selectedAppointment.start) }}</strong><small>{{ formatTime(selectedAppointment.start) }} – {{ formatTime(selectedAppointment.end) }}</small></div>
              <div><span>Odontólogo responsable</span><strong>{{ selectedAppointment.dentistName }}</strong></div>
              <div><span>Motivo</span><strong>{{ selectedAppointment.reason }}</strong></div>
            </div>
          </section>
          <section class="form-section">
            <div class="form-section-title"><q-icon name="medical_information" /><span>Nota clínica</span></div>
            <div class="form-grid">
              <q-input :model-value="form.reason" outlined dark readonly label="Motivo de consulta" />
              <q-input :model-value="form.dentistName" outlined dark readonly label="Odontólogo responsable" />
              <q-input v-model.trim="form.findings" outlined dark type="textarea" autogrow label="Hallazgos *" class="form-full" />
              <q-input v-model.trim="form.procedure" outlined dark type="textarea" autogrow label="Procedimiento realizado *" class="form-full" />
              <q-input v-model.trim="form.instructions" outlined dark type="textarea" autogrow label="Indicaciones postoperatorias (o indicar “No aplica”) *" class="form-full" />
            </div>
          </section>
          <section v-if="phasesForPatient.length" class="form-section">
            <div class="form-section-title"><q-icon name="assignment" /><span>Avance del plan de tratamiento</span></div>
            <div class="form-grid">
              <q-select v-model="form.treatmentPhaseId" outlined dark emit-value map-options :options="phaseOptions" label="Fase relacionada *" clearable class="form-full" @update:model-value="applyTreatmentPhase" />
              <q-select v-if="form.treatmentPhaseId" v-model="form.planProgress" outlined dark emit-value map-options :options="[{ label: 'En progreso', value: 'en_proceso' }, { label: 'Completada', value: 'completado' }]" label="Estado de la fase" class="form-full" />
            </div>
            <div v-if="selectedTreatmentPhase" class="planned-phase-preview">
              <strong>{{ selectedTreatmentPhase.phase || selectedTreatmentPhase.fase }}</strong>
              <span>{{ selectedTreatmentPhase.description || selectedTreatmentPhase.descripcion }}</span>
              <small v-if="selectedTreatmentPhase.teeth?.length">Piezas: {{ selectedTreatmentPhase.teeth.join(', ') }}</small>
              <small v-if="selectedTreatmentPhase.procedures">Previsto: {{ selectedTreatmentPhase.procedures }}</small>
            </div>
            <p class="form-hint">Selecciona la fase trabajada para actualizar su avance junto con la evolución.</p>
          </section>
          <section class="form-section">
            <div class="form-section-title"><q-icon name="draw" /><span>Firma y validación</span></div>
            <q-input v-model.trim="form.signature" outlined dark label="Nombre del profesional que firma *" hint="La firma se registra como validación escrita en este prototipo." />
            <q-checkbox v-model="form.validated" dark color="cyan-4" label="Confirmo que la nota clínica es correcta y está completa *" class="validation-check" />
          </section>
          <footer class="dialog-footer"><span><q-icon name="lock" /> Registro clínico asociado a la cita</span><div><q-btn flat no-caps label="Cancelar" class="subtle-action" @click="showForm = false" /><q-btn unelevated no-caps label="Guardar evolución" icon="verified" class="primary-action" type="submit" /></div></footer>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="detailsDialog">
      <q-card v-if="selectedEvolution" class="evolution-dialog detail-dialog">
        <header class="dialog-header"><span class="dialog-icon"><q-icon name="medical_information" /></span><div><div class="eyebrow">Evolución clínica</div><h2>{{ selectedEvolution.patientName }}</h2><p>{{ selectedEvolution.patientCedula }} · {{ formatDate(selectedEvolution.date) }}</p></div><q-btn flat round dense icon="close" class="dialog-close" aria-label="Cerrar" v-close-popup /></header>
        <div class="detail-content">
          <div class="detail-meta"><span><small>Odontólogo</small><strong>{{ selectedEvolution.dentistName }}</strong></span><span><small>Motivo</small><strong>{{ selectedEvolution.reason }}</strong></span></div>
          <div class="detail-block"><small>Hallazgos</small><p>{{ selectedEvolution.findings }}</p></div>
          <div class="detail-block"><small>Procedimiento realizado</small><p>{{ selectedEvolution.procedure }}</p></div>
          <div class="detail-block"><small>Indicaciones postoperatorias</small><p>{{ selectedEvolution.instructions }}</p></div>
          <div class="signature-block"><q-icon name="verified_user" /><div><small>Firma / Validación</small><strong>{{ selectedEvolution.signature }}</strong><span>Validado · {{ formatDate(String(selectedEvolution.signedAt).slice(0, 10)) }}</span></div><q-icon name="verified" class="verified-mark" /></div>
        </div>
        <footer class="dialog-footer detail-footer"><span>SmileOS · Historial clínico</span><q-btn unelevated no-caps label="Cerrar" icon-right="arrow_forward" class="primary-action" v-close-popup /></footer>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<style scoped>
.evolutions-page { min-height: 100%; color: #e2e8f0; }
.page-heading,.panel-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.page-heading { max-width: 1120px; margin: 4px auto 22px; }
.page-heading h1 { margin: 4px 0; color: #f8fafc; font-size: clamp(26px,4vw,34px); font-weight: 700; }
.page-heading p,.dialog-header p { margin: 0; color: #94a3b8; font-size: 12px; }
.eyebrow { color: #67e8f9; font-size: 10px; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; }
.primary-action { min-height: 40px; padding: 0 15px; border: 1px solid rgba(34,211,238,.4); border-radius: 9px; background: linear-gradient(120deg,rgba(8,145,178,.32),rgba(30,64,175,.28)); color: #a5f3fc; }
.evolution-stats { display: grid; max-width: 1120px; margin: 0 auto 16px; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 12px; }
.evolution-stats article { display: flex; align-items: center; gap: 12px; padding: 16px; border: 1px solid rgba(100,140,190,.18); border-radius: 13px; background: rgba(16,19,31,.76); }
.stat-icon,.timeline-marker,.dialog-icon { display: grid; width: 42px; height: 42px; flex: 0 0 42px; place-items: center; border: 1px solid rgba(34,211,238,.22); border-radius: 12px; background: rgba(8,145,178,.11); color: #67e8f9; font-size: 20px; }
.evolution-stats article>div { display: flex; flex-direction: column; gap: 3px; }
.evolution-stats small,.detail-block small,.detail-meta small,.signature-block small { color: #8292a8; font-size: 10px; }
.evolution-stats strong { color: #f1f5f9; font-size: 20px; }
.evolutions-panel { max-width: 1120px; margin: 0 auto; padding: 22px; border: 1px solid rgba(100,140,190,.2); border-radius: 17px; background: rgba(16,19,31,.8); }
.panel-heading { flex-wrap: wrap; margin-bottom: 18px; }
.panel-heading h2 { margin: 5px 0 0; color: #f1f5f9; font-size: 18px; font-weight: 650; }
.timeline-filters { display: flex; gap: 9px; width: min(590px,100%); }
.filter-select,.filter-search { flex: 1; min-width: 160px; }
.filter-select :deep(.q-field__control),.filter-search :deep(.q-field__control) { border-radius: 9px; background: rgba(15,23,42,.46); }
.filter-select :deep(.q-field__native),.filter-select :deep(.q-field__label),.filter-select :deep(.q-field__marginal),.filter-search :deep(.q-field__native),.filter-search :deep(.q-field__label),.filter-search :deep(.q-field__marginal) { color: #b6c4d5; }
.timeline-list { position: relative; display: flex; flex-direction: column; gap: 12px; }
.timeline-list::before { position: absolute; top: 26px; bottom: 26px; left: 20px; width: 1px; background: linear-gradient(rgba(34,211,238,.36),rgba(100,140,190,.08)); content: ''; }
.timeline-card { position: relative; display: flex; gap: 14px; padding: 15px; border: 1px solid rgba(100,140,190,.17); border-radius: 13px; background: linear-gradient(110deg,rgba(15,38,58,.65),rgba(15,23,42,.72)); cursor: pointer; transition: border-color 160ms ease,transform 160ms ease; }
.timeline-card:hover { transform: translateY(-1px); border-color: rgba(34,211,238,.4); }
.timeline-marker { position: relative; z-index: 1; width: 40px; height: 40px; flex-basis: 40px; border-radius: 50%; }
.timeline-card-content { min-width: 0; flex: 1; }
.timeline-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.timeline-card-top>div:first-child { display: flex; min-width: 0; flex-direction: column; gap: 3px; }
.patient-name { color: #f1f5f9; font-size: 13px; font-weight: 650; }
.patient-cedula { color: #8292a8; font-size: 10px; }
.timeline-date { flex: 0 0 auto; color: #94a3b8; font-family: monospace; font-size: 10px; }
.timeline-meta { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 12px; color: #a8b4c5; font-size: 10px; }
.timeline-meta span { display: flex; align-items: center; gap: 5px; }
.timeline-meta .q-icon { color: #67e8f9; font-size: 14px; }
.procedure-preview { margin: 10px 0; color: #cbd5e1; font-size: 11px; line-height: 1.5; }
.procedure-preview strong { color: #94a3b8; font-weight: 550; }
.timeline-card-bottom { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.validated-badge { display: inline-flex; align-items: center; gap: 5px; border: 1px solid rgba(34,197,94,.2); border-radius: 20px; background: rgba(34,197,94,.09); color: #86efac; font-size: 9px; }
.validated-badge .q-icon { font-size: 12px; }
.view-record { display: flex; align-items: center; gap: 5px; color: #67e8f9; font-size: 10px; }
.empty-state { display: flex; min-height: 240px; align-items: center; justify-content: center; flex-direction: column; padding: 25px; border: 1px dashed rgba(100,140,190,.24); border-radius: 13px; background: rgba(2,6,23,.15); text-align: center; }
.empty-icon { display: grid; width: 55px; height: 55px; margin-bottom: 14px; place-items: center; border: 1px solid rgba(34,211,238,.17); border-radius: 16px; color: #67e8f9; font-size: 27px; }
.empty-state strong { color: #cbd5e1; font-size: 13px; }
.empty-state p { max-width: 420px; margin: 7px 0 0; color: #718096; font-size: 11px; }
.evolution-dialog { display: flex; width: min(760px,calc(100vw - 28px)); max-width: 760px; max-height: 91vh; flex-direction: column; overflow: hidden; border: 1px solid rgba(34,211,238,.28); border-radius: 17px; background: radial-gradient(ellipse at 5% 0%,rgba(8,145,178,.16),transparent 42%),#0b1120; color: #e2e8f0; box-shadow: 0 24px 80px rgba(0,0,0,.56); }
.dialog-header { display: flex; align-items: flex-start; gap: 13px; padding: 20px 22px; border-bottom: 1px solid rgba(100,140,190,.14); }
.dialog-header>div { min-width: 0; flex: 1; }
.dialog-header h2 { margin: 4px 0; color: #f8fafc; font-size: 19px; font-weight: 650; }
.dialog-icon { font-size: 22px; }
.dialog-close { color: #94a3b8; }
.evolution-form { display: flex; min-height: 0; flex: 1 1 auto; flex-direction: column; max-height: calc(91vh - 85px); overflow-y: auto; }
.form-section { padding: 17px 22px; border-bottom: 1px solid rgba(100,140,190,.1); }
.form-section-title { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; color: #cbd5e1; font-size: 12px; font-weight: 650; }
.form-section-title .q-icon { color: #67e8f9; font-size: 18px; }
.appointment-summary { display: grid; margin-top: 12px; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 8px; }
.appointment-summary>div,.detail-block,.detail-meta>span { display: flex; min-width: 0; flex-direction: column; gap: 4px; padding: 11px; border: 1px solid rgba(34,211,238,.12); border-radius: 9px; background: rgba(15,23,42,.45); }
.appointment-summary span { color: #8292a8; font-size: 9px; text-transform: uppercase; letter-spacing: .06em; }
.appointment-summary strong { color: #e2e8f0; font-size: 11px; font-weight: 550; }
.appointment-summary small { color: #718096; font-size: 9px; }
.form-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 11px; }
.form-full { grid-column: 1 / -1; }
.evolution-form :deep(.q-field__control) { border-radius: 9px; background: rgba(15,23,42,.44); }
.evolution-form :deep(.q-field__label),.evolution-form :deep(.q-field__native),.evolution-form :deep(.q-field__marginal) { color: #b6c4d5; }
.evolution-form :deep(.q-field--outlined .q-field__control:before) { border-color: rgba(100,140,190,.25); }
.evolution-form :deep(.q-field--focused .q-field__control:after) { border-color: #22d3ee; }
.form-hint { margin: 8px 0 0; color: #718096; font-size: 10px; }
.planned-phase-preview { display: flex; flex-direction: column; gap: 4px; margin-top: 10px; padding: 10px 12px; border: 1px solid rgba(34,211,238,.14); border-radius: 9px; background: rgba(8,145,178,.07); }
.planned-phase-preview strong { color: #a5f3fc; font-size: 11px; }
.planned-phase-preview span,.planned-phase-preview small { color: #94a3b8; font-size: 10px; line-height: 1.4; }
.validation-check { margin-top: 8px; color: #cbd5e1; font-size: 11px; }
.dialog-footer { position: sticky; z-index: 3; bottom: 0; display: flex; flex: 0 0 auto; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 22px; border-top: 1px solid rgba(100,140,190,.18); background: #0b1120; box-shadow: 0 -8px 20px rgba(2,6,23,.42); }
.dialog-footer>span { display: flex; align-items: center; gap: 6px; color: #64748b; font-size: 9px; }
.dialog-footer>span .q-icon { color: #67e8f9; }
.dialog-footer>div { display: flex; gap: 8px; }
.subtle-action { color: #9fb0c5; }
.detail-content { max-height: 65vh; overflow-y: auto; padding: 18px 22px; }
.detail-meta { display: grid; margin-bottom: 10px; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 9px; }
.detail-meta strong,.signature-block strong { color: #e2e8f0; font-size: 11px; font-weight: 550; }
.detail-block { margin-top: 9px; }
.detail-block p { margin: 0; color: #cbd5e1; font-size: 11px; line-height: 1.6; white-space: pre-wrap; }
.signature-block { display: flex; align-items: center; gap: 10px; margin-top: 13px; padding: 12px; border: 1px solid rgba(34,197,94,.2); border-radius: 10px; background: rgba(20,83,45,.1); color: #86efac; }
.signature-block>div { display: flex; flex: 1; flex-direction: column; gap: 3px; }
.signature-block span { color: #8292a8; font-size: 9px; }
.verified-mark { color: #4ade80; }
.detail-footer { border-top: 0; }

@media (max-width: 700px) {
  .page-heading,.panel-heading { align-items: flex-start; flex-direction: column; }
  .page-heading .primary-action { width: 100%; justify-content: center; }
  .evolution-stats { grid-template-columns: 1fr; gap: 8px; }
  .evolution-stats article { padding: 12px; }
  .evolutions-panel { padding: 14px; }
  .timeline-filters { flex-direction: column; width: 100%; }
  .filter-select,.filter-search { width: 100%; }
  .timeline-card { gap: 10px; padding: 12px; }
  .timeline-list::before { left: 19px; }
  .timeline-card-top { flex-direction: column; }
  .timeline-date { order: -1; }
  .form-grid,.appointment-summary,.detail-meta { grid-template-columns: 1fr; }
  .form-full { grid-column: auto; }
  .dialog-header,.form-section { padding: 15px; }
  .dialog-footer { align-items: flex-start; flex-direction: column; padding: 12px 15px; }
  .dialog-footer>div { width: 100%; justify-content: flex-end; }
}
</style>
