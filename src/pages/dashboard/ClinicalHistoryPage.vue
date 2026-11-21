<script setup>
import { computed, onMounted, ref } from 'vue'
import { useQuasar } from 'quasar'

const PATIENTS_KEY = 'smileos-patients'
const HISTORY_KEY = 'smileos-clinical-histories'
const APPOINTMENTS_KEY = 'smileos-appointments'
const $q = useQuasar()

const patients = ref([])
const histories = ref([])
const appointments = ref([])
const selectedPatientId = ref('')
const patientSearch = ref('')
const historyDialog = ref(false)
const activeTab = ref('medical')
const draft = ref(emptyHistory())

const conditionOptions = [
  'Diabetes', 'Hipertensión arterial', 'Enfermedad cardíaca', 'Asma', 'Epilepsia',
  'Trastorno de coagulación', 'Enfermedad renal', 'Enfermedad hepática', 'Osteoporosis',
  'Enfermedad tiroidea', 'Inmunosupresión', 'Embarazo', 'Otra',
]
const severityOptions = ['Leve', 'Moderada', 'Grave', 'Anafilaxia']
const smokingOptions = ['Nunca', 'Exfumador/a', 'Ocasional', 'Diario', 'Sin confirmar']
const frequencyOptions = ['Nunca', 'Ocasional', 'Frecuente', 'Diario', 'Sin confirmar']
const oralHygieneOptions = ['1 vez al día', '2 veces al día', '3 o más veces al día', 'Irregular', 'Sin confirmar']
const demoPatients = [
  { id: '8-123-456', cedula: '8-123-456', patientCode: '8-123-456', firstName: 'María', lastName: 'González', phone: '6000-1234' },
  { id: '8-234-567', cedula: '8-234-567', patientCode: '8-234-567', firstName: 'Carlos', lastName: 'Rodríguez', phone: '6000-2345' },
  { id: '8-345-678', cedula: '8-345-678', patientCode: '8-345-678', firstName: 'Ana', lastName: 'Martínez', phone: '6000-3456' },
  { id: '8-456-789', cedula: '8-456-789', patientCode: '8-456-789', firstName: 'José', lastName: 'Pérez', phone: '6000-4567' },
  { id: '8-567-890', cedula: '8-567-890', patientCode: '8-567-890', firstName: 'Lucía', lastName: 'Torres', phone: '6000-5678' },
  { id: '8-678-901', cedula: '8-678-901', patientCode: '8-678-901', firstName: 'Pedro', lastName: 'Castillo', phone: '6000-6789' },
]

function emptyHistory() {
  return {
    conditions: [], familyHistory: '', medicalHistory: '', surgeries: '', hospitalizations: '',
    allergies: [], noKnownAllergies: false, medications: [],
    smoking: 'Sin confirmar', alcohol: 'Sin confirmar', tobacco: 'Sin confirmar',
    bruxism: 'Sin confirmar', oralHygiene: 'Sin confirmar', flossing: 'Sin confirmar',
    otherHabits: '', clinicalAlerts: '', emergencyNotes: '', reviewedBy: '', reviewedAt: '',
  }
}

function readArray(key) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || '[]')
    return Array.isArray(value) ? value : []
  } catch {
    return []
  }
}

function fullName(patient) {
  return patient.name || patient.fullName || `${patient.firstName || ''} ${patient.lastName || ''}`.trim() || 'Paciente'
}

function joinConditions(conditions) {
  return conditions.join(' · ')
}

onMounted(() => {
  const savedPatients = readArray(PATIENTS_KEY)
  patients.value = savedPatients.length ? savedPatients : demoPatients
  histories.value = readArray(HISTORY_KEY)
  appointments.value = readArray(APPOINTMENTS_KEY).map((appointment) => ({
    ...appointment,
    start: new Date(appointment.start),
  }))
  if (patients.value.length) selectedPatientId.value = String(patients.value[0].cedula || patients.value[0].id)
})

const filteredPatients = computed(() => {
  const query = normalize(patientSearch.value)
  return patients.value.filter((patient) => !query || normalize(`${fullName(patient)} ${patient.cedula} ${patient.patientCode} ${patient.phone}`).includes(query))
})

const selectedPatient = computed(() => patients.value.find((patient) => String(patient.cedula || patient.id) === String(selectedPatientId.value)))
const selectedHistory = computed(() => histories.value.find((history) => String(history.patientId) === String(selectedPatientId.value)))
const patientAppointments = computed(() => appointments.value
  .filter((appointment) => String(appointment.patientId || appointment.cedula) === String(selectedPatientId.value)
    && appointment.status === 'confirmada' && appointment.start >= new Date())
  .sort((a, b) => a.start - b.start))

const alertItems = computed(() => {
  const history = selectedHistory.value
  const patient = selectedPatient.value
  if (!history && !patient) return []
  const items = []
  if (history?.allergies?.length) {
    history.allergies.forEach((allergy) => items.push({ title: `Alergia: ${allergy.substance}`, detail: `${allergy.reaction || 'Reacción sin registrar'} · ${allergy.severity || 'Severidad sin indicar'}`, icon: 'warning', tone: 'critical' }))
  } else if (history && !history.noKnownAllergies) {
    items.push({ title: 'Alergias sin confirmar', detail: 'Confirma este dato antes de iniciar un procedimiento.', icon: 'help', tone: 'caution' })
  } else if (!history && patient?.allergyDescription && patient.allergyDescription !== 'Ninguna') {
    items.push({ title: `Alergia: ${patient.allergyDescription}`, detail: 'Dato importado de la ficha del paciente; valida la reacción y severidad.', icon: 'warning', tone: 'critical' })
  }
  if (history?.clinicalAlerts?.trim()) items.push({ title: 'Alerta clínica', detail: history.clinicalAlerts, icon: 'notification_important', tone: 'critical' })
  if (history?.conditions?.length) items.push({ title: 'Antecedentes relevantes', detail: history.conditions.join(' · '), icon: 'medical_information', tone: 'caution' })
  if (history?.medications?.length) items.push({ title: 'Medicación actual', detail: history.medications.map((medication) => medication.name).filter(Boolean).join(', '), icon: 'medication', tone: 'info' })
  return items
})

const summary = computed(() => {
  const history = selectedHistory.value
  const patient = selectedPatient.value
  return {
    conditions: history?.conditions?.length || (patient?.conditions?.length || 0),
    allergies: history?.allergies?.length || (patient?.allergyDescription && patient.allergyDescription !== 'Ninguna' ? 1 : 0),
    medications: history?.medications?.filter((item) => item.name).length || (patient?.medications ? 1 : 0),
    alerts: alertItems.value.length,
  }
})

function normalize(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').trim()
}

function formatDate(value) {
  if (!value) return 'Sin registrar'
  const date = value instanceof Date ? value : new Date(value.length === 10 ? `${value}T00:00:00` : value)
  if (Number.isNaN(date.getTime())) return 'Sin registrar'
  return new Intl.DateTimeFormat('es-PA', { day: '2-digit', month: 'short', year: 'numeric' }).format(date)
}

function selectPatient(patient) {
  selectedPatientId.value = String(patient.cedula || patient.id)
}

function editHistory() {
  if (!selectedPatient.value) return
  const saved = selectedHistory.value
  const patient = selectedPatient.value
  const patientAllergy = patient.allergyDescription && patient.allergyDescription !== 'Ninguna'
    ? [{ substance: patient.allergyDescription, reaction: '', severity: '' }]
    : []
  const patientMedication = patient.medications
    ? [{ name: patient.medications, dose: '', frequency: '', route: '', prescriber: '' }]
    : []
  draft.value = {
    ...emptyHistory(),
    conditions: Array.isArray(patient.conditions) ? [...patient.conditions] : [],
    medicalHistory: patient.medicalNotes || '',
    surgeries: patient.surgeries || '',
    hospitalizations: patient.hospitalizations || '',
    noKnownAllergies: patient.hasAllergies === 'No' && !patient.allergyDescription,
    ...saved,
    allergies: saved?.allergies ? saved.allergies.map((item) => ({ ...item })) : patientAllergy,
    medications: saved?.medications ? saved.medications.map((item) => ({ ...item })) : patientMedication,
    reviewedBy: saved?.reviewedBy || patient.registeredBy || '',
  }
  activeTab.value = 'medical'
  historyDialog.value = true
}

function addAllergy() {
  draft.value.allergies.push({ substance: '', reaction: '', severity: '' })
  draft.value.noKnownAllergies = false
}

function removeAllergy(index) {
  draft.value.allergies.splice(index, 1)
}

function addMedication() {
  draft.value.medications.push({ name: '', dose: '', frequency: '', route: '', prescriber: '' })
}

function removeMedication(index) {
  draft.value.medications.splice(index, 1)
}

function setNoKnownAllergies(value) {
  if (value) draft.value.allergies = []
}

function saveHistory() {
  const patient = selectedPatient.value
  if (!patient) return
  if (!draft.value.reviewedBy.trim()) {
    $q.notify({ type: 'warning', message: 'Indica quién revisó y validó el historial clínico.' })
    activeTab.value = 'alerts'
    return
  }
  if (draft.value.allergies.some((allergy) => !allergy.substance.trim())) {
    $q.notify({ type: 'warning', message: 'Completa la sustancia de cada alergia o elimina la fila vacía.' })
    activeTab.value = 'allergies'
    return
  }
  const patientId = String(patient.cedula || patient.id)
  const previous = histories.value.find((history) => String(history.patientId) === patientId)
  const now = new Date().toISOString()
  const history = {
    ...draft.value,
    patientId,
    patientName: fullName(patient),
    patientCedula: patient.cedula || patientId,
    noKnownAllergies: Boolean(draft.value.noKnownAllergies),
    allergies: draft.value.allergies.filter((item) => item.substance.trim()),
    medications: draft.value.medications.filter((item) => item.name.trim()),
    reviewedBy: draft.value.reviewedBy.trim(),
    reviewedAt: now,
    createdAt: previous?.createdAt || now,
    updatedAt: now,
  }
  const nextHistories = previous
    ? histories.value.map((item) => String(item.patientId) === patientId ? history : item)
    : [history, ...histories.value]
  const allergySummary = history.noKnownAllergies ? 'Ninguna' : history.allergies.map((item) => `${item.substance}${item.reaction ? ` (${item.reaction})` : ''}`).join(', ')
  const medicationSummary = history.medications.map((item) => `${item.name}${item.dose ? ` · ${item.dose}` : ''}`).join(', ')
  const nextPatients = patients.value.map((item) => String(item.cedula || item.id) === patientId
    ? {
      ...item,
      conditions: history.conditions,
      allergyDescription: allergySummary,
      hasAllergies: history.noKnownAllergies ? 'No' : history.allergies.length ? 'Sí' : '',
      medications: medicationSummary,
      medicalNotes: history.medicalHistory,
      surgeries: history.surgeries,
      hospitalizations: history.hospitalizations,
      clinicalHistoryReviewedAt: now,
      clinicalHistoryReviewedBy: history.reviewedBy,
    }
    : item)
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistories))
    localStorage.setItem(PATIENTS_KEY, JSON.stringify(nextPatients))
    histories.value = nextHistories
    patients.value = nextPatients
    historyDialog.value = false
    $q.notify({ type: 'positive', message: 'Historial clínico actualizado y vinculado a la ficha del paciente.' })
  } catch (error) {
    console.error('No se pudo guardar el historial clínico', error)
    $q.notify({ type: 'negative', message: 'No se pudo guardar el historial en este navegador.' })
  }
}
</script>

<template>
  <q-page class="clinical-history-page futuristic-bg q-pa-md q-pa-lg-lg">
    <section class="page-heading">
      <div>
        <div class="eyebrow">Seguridad del paciente</div>
        <h1>Historial Clínico</h1>
        <p>Antecedentes y alertas para revisar antes de cada atención.</p>
      </div>
    </section>

    <section class="history-workspace">
      <aside class="patient-directory">
        <div class="directory-heading">
          <div>
            <div class="eyebrow">Directorio</div>
            <h2>Pacientes</h2>
          </div><q-badge>{{ patients.length }}</q-badge>
        </div>
        <q-input v-model="patientSearch" outlined dark dense clearable label="Buscar paciente"
          class="patient-search"><template #prepend><q-icon name="search" /></template></q-input>
        <div class="patient-list">
          <button v-for="patient in filteredPatients" :key="patient.id || patient.cedula" type="button"
            :class="['patient-option', { selected: String(patient.cedula || patient.id) === selectedPatientId }]"
            @click="selectPatient(patient)">
            <span class="patient-avatar"><q-icon name="person" /></span><span class="patient-option-copy"><strong>{{
              fullName(patient) }}</strong><small>{{ patient.cedula || patient.patientCode || 'Sin cédula'
                }}</small></span><q-icon name="chevron_right" />
          </button>
          <div v-if="!filteredPatients.length" class="directory-empty">No hay pacientes que coincidan con la búsqueda.
          </div>
        </div>
      </aside>

      <main v-if="selectedPatient" class="history-main">
        <header class="patient-heading">
          <div class="patient-heading-main"><span class="patient-avatar large"><q-icon
                name="medical_information" /></span>
            <div>
              <div class="eyebrow">Ficha preconsulta</div>
              <h2>{{ fullName(selectedPatient) }}</h2>
              <p><span>{{ selectedPatient.cedula || selectedPatient.patientCode }}</span><i>·</i>
                <span v-if="selectedPatient.phone">{{ selectedPatient.phone }}</span>
                <span v-else>Teléfono sin registrar</span>
              </p>
            </div>
          </div>
          <q-btn unelevated no-caps icon="edit_note" label="Editar historial" class="primary-action"
            @click="editHistory" />
        </header>

        <div v-if="selectedHistory" class="review-stamp"><q-icon name="verified_user" /><span>Revisado por <strong>{{
          selectedHistory.reviewedBy }}</strong> · {{ formatDate(selectedHistory.reviewedAt) }}</span></div>
        <div v-else class="review-stamp needs-review"><q-icon name="pending_actions" /><span>Este paciente aún no tiene
            un
            historial clínico completo. Revisa la información antes de atenderlo.</span></div>

        <section v-if="alertItems.length" class="clinical-alerts">
          <div class="alerts-heading"><q-icon name="notification_important" /><strong>Alertas para la
              atención</strong><q-badge>{{ alertItems.length }}</q-badge></div>
          <article v-for="(alert, index) in alertItems" :key="`${alert.title}-${index}`"
            :class="['clinical-alert', `alert-${alert.tone}`]">
            <q-icon :name="alert.icon" />
            <div><strong>{{ alert.title }}</strong><span>{{ alert.detail }}</span></div>
          </article>
        </section>

        <section class="clinical-summary">
          <article><span class="summary-icon"><q-icon name="medical_information" /></span>
            <div><small>Antecedentes</small><strong>{{ summary.conditions }}</strong></div>
          </article>
          <article :class="{ 'summary-attention': summary.allergies }"><span class="summary-icon"><q-icon
                name="warning_amber" /></span>
            <div><small>Alergias</small>
              <strong v-if="summary.allergies">{{ summary.allergies }}</strong>
              <strong v-else-if="selectedHistory?.noKnownAllergies">Ninguna</strong>
              <strong v-else>Sin confirmar</strong>
            </div>
          </article>
          <article><span class="summary-icon"><q-icon name="medication" /></span>
            <div><small>Medicamentos</small><strong>{{ summary.medications }}</strong></div>
          </article>
          <article :class="{ 'summary-attention': summary.alerts }"><span class="summary-icon"><q-icon
                name="notification_important" /></span>
            <div><small>Alertas activas</small><strong>{{ summary.alerts }}</strong></div>
          </article>
        </section>

        <div class="history-sections">
          <section class="history-card">
            <header><span class="section-icon"><q-icon name="health_and_safety" /></span>
              <div>
                <h3>Antecedentes médicos</h3>
                <p>Condiciones y eventos de salud relevantes</p>
              </div>
            </header>
            <div v-if="selectedHistory?.conditions?.length" class="chip-list"><q-badge
                v-for="condition in selectedHistory.conditions" :key="condition" class="clinical-chip">{{ condition
                }}</q-badge></div>
            <p v-else-if="selectedPatient.conditions?.length" class="detail-text">{{
              joinConditions(selectedPatient.conditions) }}
            </p>
            <p v-else class="muted-empty">Sin antecedentes confirmados.</p>
            <div v-if="selectedHistory?.medicalHistory || selectedPatient.medicalNotes" class="detail-block">
              <small>Historia y
                observaciones médicas</small>
              <p>{{ selectedHistory?.medicalHistory || selectedPatient.medicalNotes }}</p>
            </div>
            <div v-if="selectedHistory?.familyHistory" class="detail-block"><small>Antecedentes familiares</small>
              <p>{{ selectedHistory.familyHistory }}</p>
            </div>
            <div v-if="selectedHistory?.surgeries || selectedPatient.surgeries" class="detail-block">
              <small>Cirugías</small>
              <p>{{ selectedHistory?.surgeries || selectedPatient.surgeries }}</p>
            </div>
            <div v-if="selectedHistory?.hospitalizations || selectedPatient.hospitalizations" class="detail-block">
              <small>Hospitalizaciones</small>
              <p>{{ selectedHistory?.hospitalizations || selectedPatient.hospitalizations }}</p>
            </div>
          </section>

          <section class="history-card">
            <header><span class="section-icon allergy-icon"><q-icon name="vaccines" /></span>
              <div>
                <h3>Alergias</h3>
                <p>Reacción y nivel de severidad</p>
              </div>
            </header>
            <div v-if="selectedHistory?.allergies?.length" class="list-stack">
              <article v-for="(allergy, index) in selectedHistory.allergies" :key="`${allergy.substance}-${index}`"
                class="record-row">
                <div><strong>{{ allergy.substance }}</strong><span>{{ allergy.reaction || 'Reacción sin registrar'
                }}</span>
                </div><q-badge :class="['severity-badge', `severity-${normalize(allergy.severity)}`]">{{
                  allergy.severity ||
                  'Severidad pendiente' }}</q-badge>
              </article>
            </div>
            <p v-else-if="selectedHistory?.noKnownAllergies" class="confirmed-none"><q-icon name="check_circle" />
              Paciente
              confirma que no tiene alergias conocidas.</p>
            <p v-else-if="selectedPatient.allergyDescription && selectedPatient.allergyDescription !== 'Ninguna'"
              class="detail-text">{{ selectedPatient.allergyDescription }} <small>· Reacción y severidad por
                confirmar</small>
            </p>
            <p v-else class="muted-empty">Alergias aún sin confirmar.</p>
          </section>

          <section class="history-card">
            <header><span class="section-icon medication-icon"><q-icon name="medication" /></span>
              <div>
                <h3>Medicación actual</h3>
                <p>Tratamientos farmacológicos en curso</p>
              </div>
            </header>
            <div v-if="selectedHistory?.medications?.length" class="list-stack">
              <article v-for="(medication, index) in selectedHistory.medications" :key="`${medication.name}-${index}`"
                class="record-row medication-row">
                <div><strong>{{ medication.name }}</strong><span>{{ [medication.dose, medication.frequency,
                medication.route].filter(Boolean).join(' · ') || 'Dosis y frecuencia sin registrar' }}</span></div>
                <small v-if="medication.prescriber">{{ medication.prescriber }}</small>
              </article>
            </div>
            <p v-else-if="selectedPatient.medications" class="detail-text">{{ selectedPatient.medications }}</p>
            <p v-else class="muted-empty">Sin medicación registrada.</p>
          </section>

          <section class="history-card">
            <header><span class="section-icon habits-icon"><q-icon name="self_improvement" /></span>
              <div>
                <h3>Hábitos y factores de riesgo</h3>
                <p>Información relevante para la salud oral</p>
              </div>
            </header>
            <div v-if="selectedHistory" class="habit-grid">
              <div><small>Tabaquismo</small><strong>{{ selectedHistory.smoking }}</strong></div>
              <div><small>Alcohol</small><strong>{{ selectedHistory.alcohol }}</strong></div>
              <div><small>Otro tabaco</small><strong>{{ selectedHistory.tobacco }}</strong></div>
              <div><small>Bruxismo</small><strong>{{ selectedHistory.bruxism }}</strong></div>
              <div><small>Higiene oral</small><strong>{{ selectedHistory.oralHygiene }}</strong></div>
              <div><small>Hilo dental</small><strong>{{ selectedHistory.flossing }}</strong></div>
            </div>
            <p v-else class="muted-empty">Hábitos pendientes de registrar.</p>
            <div v-if="selectedHistory?.otherHabits" class="detail-block"><small>Otros hábitos</small>
              <p>{{ selectedHistory.otherHabits }}</p>
            </div>
          </section>

          <section class="history-card">
            <header><span class="section-icon alert-icon"><q-icon name="notification_important" /></span>
              <div>
                <h3>Alertas clínicas y precauciones</h3>
                <p>Notas que deben revisarse antes del procedimiento</p>
              </div>
            </header>
            <p v-if="selectedHistory?.clinicalAlerts" class="alert-detail">{{ selectedHistory.clinicalAlerts }}</p>
            <p v-else class="muted-empty">Sin alertas adicionales registradas.</p>
            <div v-if="selectedHistory?.emergencyNotes" class="detail-block"><small>Indicaciones ante emergencia</small>
              <p>{{ selectedHistory.emergencyNotes }}</p>
            </div>
          </section>

          <section class="history-card appointments-card">
            <header><span class="section-icon appointment-icon"><q-icon name="event_available" /></span>
              <div>
                <h3>Próximas citas</h3>
                <p>Agenda asociada al paciente</p>
              </div>
            </header>
            <div v-if="patientAppointments.length" class="list-stack">
              <article v-for="appointment in patientAppointments" :key="appointment.id" class="record-row">
                <div><strong>{{ appointment.reason || 'Consulta odontológica' }}</strong><span>{{
                  appointment.dentistName
                }}</span></div><q-badge class="appointment-date-badge">{{ formatDate(appointment.start) }}</q-badge>
              </article>
            </div>
            <p v-else class="muted-empty">No hay citas próximas confirmadas.</p>
          </section>
        </div>
      </main>
    </section>

    <q-dialog v-model="historyDialog" maximized persistent>
      <q-card class="history-dialog">
        <header class="dialog-header">
          <div>
            <div class="eyebrow">Ficha preconsulta · {{ selectedPatient && fullName(selectedPatient) }}</div>
            <h2>Historial Clínico</h2>
            <p>Completa y revisa los datos antes de atender al paciente.</p>
          </div><q-btn flat round dense icon="close" class="dialog-close" aria-label="Cerrar"
            @click="historyDialog = false" />
        </header>
        <q-tabs v-model="activeTab" dense no-caps align="left" class="history-tabs" active-color="cyan-3"
          indicator-color="cyan-4" outside-arrows mobile-arrows>
          <q-tab name="medical" icon="health_and_safety" label="Antecedentes" /><q-tab name="allergies" icon="vaccines"
            label="Alergias" /><q-tab name="medications" icon="medication" label="Medicamentos" /><q-tab name="habits"
            icon="self_improvement" label="Hábitos" /><q-tab name="alerts" icon="notification_important"
            label="Alertas y revisión" />
        </q-tabs>
        <q-form class="history-form" @submit.prevent="saveHistory">
          <q-tab-panels v-model="activeTab" animated class="history-panels">
            <q-tab-panel name="medical">
              <div class="form-section-heading"><span>01</span>
                <div>
                  <h3>Antecedentes médicos</h3>
                  <p>Registra condiciones actuales y antecedentes personales y familiares.</p>
                </div>
              </div>
              <div class="form-grid">
                <q-select v-model="draft.conditions" outlined dark multiple use-chips use-input
                  new-value-mode="add-unique" :options="conditionOptions" label="Condiciones médicas conocidas"
                  hint="Puedes agregar diagnósticos que no estén en la lista." class="form-full" />
                <q-input v-model.trim="draft.medicalHistory" outlined dark type="textarea" autogrow
                  label="Antecedentes médicos personales" class="form-full" />
                <q-input v-model.trim="draft.familyHistory" outlined dark type="textarea" autogrow
                  label="Antecedentes médicos familiares" class="form-full" />
                <q-input v-model.trim="draft.surgeries" outlined dark type="textarea" autogrow
                  label="Cirugías previas" />
                <q-input v-model.trim="draft.hospitalizations" outlined dark type="textarea" autogrow
                  label="Hospitalizaciones previas" />
              </div>
            </q-tab-panel>
            <q-tab-panel name="allergies">
              <div class="form-section-heading"><span>02</span>
                <div>
                  <h3>Alergias y reacciones</h3>
                  <p>No marques “sin alergias” sin confirmarlo con el paciente.</p>
                </div>
              </div>
              <q-checkbox v-model="draft.noKnownAllergies" dark color="cyan-4"
                label="El paciente confirma que no tiene alergias conocidas"
                @update:model-value="setNoKnownAllergies" />
              <div v-for="(allergy, index) in draft.allergies" :key="index" class="dynamic-record">
                <div class="dynamic-record-heading"><strong>Alergia {{ index + 1 }}</strong><q-btn flat round dense
                    icon="delete_outline" class="remove-record" aria-label="Eliminar alergia"
                    @click="removeAllergy(index)" /></div>
                <div class="form-grid"><q-input v-model.trim="allergy.substance" outlined dark
                    label="Sustancia / alimento / medicamento *" /><q-input v-model.trim="allergy.reaction" outlined
                    dark label="Reacción observada" /><q-select v-model="allergy.severity" outlined dark
                    :options="severityOptions" label="Severidad" /><q-input v-model.trim="allergy.notes" outlined dark
                    label="Notas" /></div>
              </div>
              <q-btn flat no-caps icon="add" label="Agregar alergia" class="add-record-button" @click="addAllergy" />
            </q-tab-panel>
            <q-tab-panel name="medications">
              <div class="form-section-heading"><span>03</span>
                <div>
                  <h3>Medicación actual</h3>
                  <p>Incluye fármacos prescritos y productos que el paciente consume actualmente.</p>
                </div>
              </div>
              <div v-for="(medication, index) in draft.medications" :key="index" class="dynamic-record">
                <div class="dynamic-record-heading"><strong>Medicamento {{ index + 1 }}</strong><q-btn flat round dense
                    icon="delete_outline" class="remove-record" aria-label="Eliminar medicamento"
                    @click="removeMedication(index)" /></div>
                <div class="form-grid"><q-input v-model.trim="medication.name" outlined dark
                    label="Nombre del medicamento" /><q-input v-model.trim="medication.dose" outlined dark label="Dosis"
                    placeholder="Ej. 500 mg" /><q-input v-model.trim="medication.frequency" outlined dark
                    label="Frecuencia" placeholder="Ej. cada 8 horas" /><q-input v-model.trim="medication.route"
                    outlined dark label="Vía de administración" /><q-input v-model.trim="medication.prescriber" outlined
                    dark label="Prescriptor" class="form-full" /></div>
              </div>
              <q-btn flat no-caps icon="add" label="Agregar medicamento" class="add-record-button"
                @click="addMedication" />
            </q-tab-panel>
            <q-tab-panel name="habits">
              <div class="form-section-heading"><span>04</span>
                <div>
                  <h3>Hábitos y factores de riesgo</h3>
                  <p>Hábitos que pueden influir en la salud oral o en la atención clínica.</p>
                </div>
              </div>
              <div class="form-grid">
                <q-select v-model="draft.smoking" outlined dark :options="smokingOptions" label="Tabaquismo" /><q-select
                  v-model="draft.tobacco" outlined dark :options="frequencyOptions" label="Otros productos de tabaco" />
                <q-select v-model="draft.alcohol" outlined dark :options="frequencyOptions"
                  label="Consumo de alcohol" /><q-select v-model="draft.bruxism" outlined dark
                  :options="['Sí', 'No', 'Sin confirmar']" label="Bruxismo / rechinamiento" />
                <q-select v-model="draft.oralHygiene" outlined dark :options="oralHygieneOptions"
                  label="Frecuencia de higiene oral" /><q-select v-model="draft.flossing" outlined dark
                  :options="frequencyOptions" label="Uso de hilo dental" />
                <q-input v-model.trim="draft.otherHabits" outlined dark type="textarea" autogrow
                  label="Otros hábitos relevantes" class="form-full" />
              </div>
            </q-tab-panel>
            <q-tab-panel name="alerts">
              <div class="form-section-heading"><span>05</span>
                <div>
                  <h3>Alertas clínicas y revisión</h3>
                  <p>Información prioritaria para el equipo antes de iniciar cualquier procedimiento.</p>
                </div>
              </div>
              <div class="form-grid">
                <q-input v-model.trim="draft.clinicalAlerts" outlined dark type="textarea" autogrow
                  label="Alertas clínicas / precauciones"
                  hint="Ej. anticoagulantes, riesgo de endocarditis, ansiedad severa." class="form-full" />
                <q-input v-model.trim="draft.emergencyNotes" outlined dark type="textarea" autogrow
                  label="Indicaciones ante una emergencia" class="form-full" />
                <q-input v-model.trim="draft.reviewedBy" outlined dark label="Profesional que revisa el historial *"
                  class="form-full" />
              </div>
              <div class="review-confirmation"><q-icon name="fact_check" /><span>Al guardar se registrará la fecha y se
                  actualizarán los antecedentes relevantes en la ficha del paciente.</span></div>
            </q-tab-panel>
          </q-tab-panels>
          <footer class="history-dialog-footer"><span><q-icon name="lock" /> Información clínica vinculada a {{
            selectedPatient && fullName(selectedPatient) }}</span>
            <div><q-btn flat no-caps label="Cancelar" class="subtle-action" @click="historyDialog = false" /><q-btn
                v-if="activeTab !== 'alerts'" flat no-caps icon="arrow_forward" label="Siguiente"
                class="secondary-action"
                @click="activeTab = ({ medical: 'allergies', allergies: 'medications', medications: 'habits', habits: 'alerts' })[activeTab]" /><q-btn
                v-else unelevated no-caps label="Guardar historial" icon="verified" class="primary-action"
                type="submit" />
            </div>
          </footer>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<style scoped>
.clinical-history-page {
  min-height: 100%;
  color: #e2e8f0;
}

.page-heading {
  max-width: 1240px;
  margin: 4px auto 22px;
}

.page-heading h1 {
  margin: 4px 0;
  color: #f8fafc;
  font-size: clamp(26px, 4vw, 34px);
  font-weight: 700;
}

.page-heading p {
  margin: 0;
  color: #94a3b8;
  font-size: 12px;
}

.eyebrow {
  color: #67e8f9;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .18em;
  text-transform: uppercase;
}

.history-workspace {
  display: grid;
  max-width: 1240px;
  min-height: 620px;
  margin: 0 auto;
  grid-template-columns: 265px minmax(0, 1fr);
  gap: 15px;
}

.patient-directory,
.history-main {
  min-width: 0;
  border: 1px solid rgba(100, 140, 190, .2);
  border-radius: 16px;
  background: rgba(16, 19, 31, .8);
}

.patient-directory {
  display: flex;
  max-height: calc(100vh - 190px);
  flex-direction: column;
  padding: 16px 12px;
}

.directory-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px 13px;
}

.directory-heading h2 {
  margin: 4px 0 0;
  color: #e2e8f0;
  font-size: 15px;
}

.directory-heading :deep(.q-badge) {
  border: 1px solid rgba(34, 211, 238, .2);
  background: rgba(8, 145, 178, .1);
  color: #a5f3fc;
}

.patient-search :deep(.q-field__control) {
  border-radius: 9px;
  background: rgba(15, 23, 42, .46);
}

.patient-search :deep(.q-field__label),
.patient-search :deep(.q-field__native),
.patient-search :deep(.q-field__marginal) {
  color: #b6c4d5;
}

.patient-list {
  display: flex;
  overflow: auto;
  flex-direction: column;
  gap: 5px;
  margin-top: 11px;
}

.patient-option {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 9px;
  padding: 9px;
  border: 1px solid transparent;
  border-radius: 9px;
  background: transparent;
  color: #cbd5e1;
  text-align: left;
  cursor: pointer;
}

.patient-option:hover,
.patient-option.selected {
  border-color: rgba(34, 211, 238, .2);
  background: rgba(8, 145, 178, .1);
}

.patient-avatar {
  display: grid;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  place-items: center;
  border: 1px solid rgba(103, 232, 249, .18);
  border-radius: 10px;
  background: rgba(8, 145, 178, .1);
  color: #67e8f9;
}

.patient-avatar.large {
  width: 48px;
  height: 48px;
  flex-basis: 48px;
  border-radius: 13px;
  font-size: 23px;
}

.patient-option-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 3px;
}

.patient-option-copy strong {
  overflow: hidden;
  color: #e2e8f0;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.patient-option-copy small {
  color: #718096;
  font-size: 9px;
}

.patient-option>.q-icon:last-child {
  color: #52627a;
  font-size: 16px;
}

.directory-empty {
  padding: 20px 8px;
  color: #718096;
  font-size: 10px;
  text-align: center;
}

.history-main {
  padding: 20px;
}

.patient-heading,
.patient-heading-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.patient-heading {
  justify-content: space-between;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(100, 140, 190, .13);
}

.patient-heading-main {
  min-width: 0;
}

.patient-heading h2 {
  margin: 3px 0;
  color: #f1f5f9;
  font-size: 18px;
  font-weight: 650;
}

.patient-heading p {
  margin: 0;
  color: #94a3b8;
  font-size: 10px;
}

.patient-heading i {
  color: #22d3ee;
  font-style: normal;
}

.primary-action {
  min-height: 39px;
  padding: 0 13px;
  border: 1px solid rgba(34, 211, 238, .4);
  border-radius: 9px;
  background: linear-gradient(120deg, rgba(8, 145, 178, .3), rgba(30, 64, 175, .25));
  color: #a5f3fc;
}

.review-stamp {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 13px 0;
  padding: 9px 11px;
  border: 1px solid rgba(34, 197, 94, .19);
  border-radius: 8px;
  background: rgba(20, 83, 45, .09);
  color: #94a3b8;
  font-size: 10px;
}

.review-stamp>.q-icon {
  color: #4ade80;
}

.review-stamp strong {
  color: #cbd5e1;
  font-weight: 550;
}

.review-stamp.needs-review {
  border-color: rgba(251, 191, 36, .22);
  background: rgba(120, 83, 12, .09);
}

.review-stamp.needs-review>.q-icon {
  color: #fbbf24;
}

.clinical-alerts {
  margin: 12px 0;
  padding: 12px;
  border: 1px solid rgba(248, 113, 113, .22);
  border-radius: 11px;
  background: rgba(127, 29, 29, .07);
}

.alerts-heading {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 8px;
  color: #fca5a5;
  font-size: 11px;
}

.alerts-heading>.q-icon {
  font-size: 17px;
}

.alerts-heading :deep(.q-badge) {
  border-radius: 12px;
  background: rgba(248, 113, 113, .17);
  color: #fca5a5;
}

.clinical-alert {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  border-top: 1px solid rgba(248, 113, 113, .1);
}

.clinical-alert>.q-icon {
  flex: 0 0 auto;
  color: #f87171;
  font-size: 17px;
}

.clinical-alert>div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.clinical-alert strong {
  color: #fecaca;
  font-size: 10px;
}

.clinical-alert span {
  color: #cbd5e1;
  font-size: 10px;
  line-height: 1.45;
}

.alert-caution>.q-icon {
  color: #fbbf24;
}

.alert-info>.q-icon {
  color: #67e8f9;
}

.clinical-summary {
  display: grid;
  margin: 12px 0;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.clinical-summary article {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 10px;
  border: 1px solid rgba(100, 140, 190, .14);
  border-radius: 10px;
  background: rgba(15, 23, 42, .4);
}

.summary-icon,
.section-icon {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  place-items: center;
  border: 1px solid rgba(34, 211, 238, .17);
  border-radius: 9px;
  background: rgba(8, 145, 178, .1);
  color: #67e8f9;
}

.clinical-summary article>div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.clinical-summary small {
  color: #8292a8;
  font-size: 8px;
}

.clinical-summary strong {
  overflow: hidden;
  color: #e2e8f0;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-attention {
  border-color: rgba(248, 113, 113, .22) !important;
}

.summary-attention .summary-icon {
  border-color: rgba(248, 113, 113, .2);
  background: rgba(127, 29, 29, .1);
  color: #fca5a5;
}

.history-sections {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.history-card {
  min-width: 0;
  padding: 13px;
  border: 1px solid rgba(100, 140, 190, .15);
  border-radius: 11px;
  background: linear-gradient(115deg, rgba(15, 38, 58, .42), rgba(15, 23, 42, .52));
}

.history-card>header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.history-card>header h3 {
  margin: 0;
  color: #dbeafe;
  font-size: 11px;
  font-weight: 650;
}

.history-card>header p {
  margin: 3px 0 0;
  color: #718096;
  font-size: 9px;
}

.allergy-icon {
  color: #fca5a5;
  border-color: rgba(248, 113, 113, .19);
  background: rgba(127, 29, 29, .1);
}

.medication-icon {
  color: #c4b5fd;
  border-color: rgba(167, 139, 250, .19);
  background: rgba(91, 33, 182, .1);
}

.habits-icon {
  color: #fcd34d;
}

.alert-icon {
  color: #fca5a5;
}

.appointment-icon {
  color: #86efac;
}

.appointments-card {
  grid-column: 1 / -1;
}

.chip-list,
.list-stack {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.clinical-chip {
  width: fit-content;
  border: 1px solid rgba(34, 211, 238, .19);
  border-radius: 14px;
  background: rgba(8, 145, 178, .09);
  color: #a5f3fc;
  font-size: 9px;
}

.record-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px;
  border: 1px solid rgba(100, 140, 190, .11);
  border-radius: 8px;
  background: rgba(2, 6, 23, .2);
}

.record-row>div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.record-row strong {
  color: #e2e8f0;
  font-size: 10px;
  font-weight: 550;
}

.record-row span,
.record-row small {
  color: #8292a8;
  font-size: 9px;
}

.severity-badge {
  border-radius: 12px;
  background: rgba(251, 191, 36, .1);
  color: #fcd34d;
  font-size: 8px;
}

.severity-grave,
.severity-anafilaxia {
  background: rgba(248, 113, 113, .16);
  color: #fca5a5;
}

.severity-moderada {
  background: rgba(251, 146, 60, .13);
  color: #fdba74;
}

.confirmed-none {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #86efac;
  font-size: 10px;
}

.confirmed-none .q-icon {
  font-size: 16px;
}

.detail-text,
.alert-detail {
  margin: 0;
  color: #cbd5e1;
  font-size: 10px;
  line-height: 1.5;
}

.detail-text small {
  color: #fcd34d;
  font-size: 9px;
}

.muted-empty {
  margin: 0;
  color: #64748b;
  font-size: 10px;
  font-style: italic;
}

.detail-block {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid rgba(100, 140, 190, .1);
}

.detail-block small {
  color: #8292a8;
  font-size: 9px;
}

.detail-block p {
  margin: 4px 0 0;
  color: #cbd5e1;
  font-size: 10px;
  line-height: 1.45;
  white-space: pre-wrap;
}

.alert-detail {
  padding: 10px;
  border: 1px solid rgba(248, 113, 113, .14);
  border-radius: 8px;
  background: rgba(127, 29, 29, .08);
}

.appointment-date-badge {
  border: 1px solid rgba(34, 197, 94, .19);
  border-radius: 12px;
  background: rgba(34, 197, 94, .08);
  color: #86efac;
  font-size: 8px;
}

.history-dialog {
  display: flex;
  width: 100%;
  height: 100%;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(34, 211, 238, .26);
  background: radial-gradient(ellipse at 5% 0%, rgba(8, 145, 178, .14), transparent 40%), #0b1120;
  color: #e2e8f0;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 19px 24px;
  border-bottom: 1px solid rgba(100, 140, 190, .14);
}

.dialog-header h2 {
  margin: 4px 0;
  color: #f8fafc;
  font-size: 20px;
}

.dialog-header p {
  margin: 0;
  color: #94a3b8;
  font-size: 11px;
}

.dialog-close {
  color: #94a3b8;
}

.history-tabs {
  flex: 0 0 auto;
  border-bottom: 1px solid rgba(100, 140, 190, .12);
  color: #94a3b8;
}

.history-form {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
}

.history-panels {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  background: transparent;
  color: inherit;
}

.history-panels :deep(.q-tab-panel) {
  max-width: 1000px;
  margin: 0 auto;
  padding: 27px 30px;
}

.form-section-heading {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 20px;
}

.form-section-heading>span {
  display: grid;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  place-items: center;
  border: 1px solid rgba(34, 211, 238, .23);
  border-radius: 10px;
  background: rgba(8, 145, 178, .1);
  color: #67e8f9;
  font-size: 10px;
  font-weight: 700;
}

.form-section-heading h3 {
  margin: 0;
  color: #f1f5f9;
  font-size: 15px;
}

.form-section-heading p {
  margin: 5px 0 0;
  color: #8292a8;
  font-size: 10px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 13px;
}

.form-full {
  grid-column: 1 / -1;
}

.history-form :deep(.q-field__control) {
  border-radius: 9px;
  background: rgba(15, 23, 42, .46);
}

.history-form :deep(.q-field__label),
.history-form :deep(.q-field__native),
.history-form :deep(.q-field__marginal) {
  color: #b6c4d5;
}

.history-form :deep(.q-field--outlined .q-field__control:before) {
  border-color: rgba(100, 140, 190, .25);
}

.history-form :deep(.q-field--focused .q-field__control:after) {
  border-color: #22d3ee;
}

.dynamic-record {
  margin-top: 14px;
  padding: 13px;
  border: 1px solid rgba(100, 140, 190, .16);
  border-radius: 11px;
  background: rgba(15, 23, 42, .34);
}

.dynamic-record-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  color: #cbd5e1;
  font-size: 11px;
}

.remove-record {
  color: #f87171;
}

.add-record-button {
  margin-top: 12px;
  color: #67e8f9;
}

.review-confirmation {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 18px;
  padding: 12px;
  border: 1px solid rgba(34, 211, 238, .16);
  border-radius: 9px;
  background: rgba(8, 145, 178, .07);
  color: #94a3b8;
  font-size: 10px;
}

.review-confirmation .q-icon {
  color: #67e8f9;
  font-size: 19px;
}

.history-dialog-footer {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 24px;
  border-top: 1px solid rgba(100, 140, 190, .15);
  background: #0b1120;
  box-shadow: 0 -6px 18px rgba(2, 6, 23, .4);
}

.history-dialog-footer>span {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #718096;
  font-size: 9px;
}

.history-dialog-footer>span .q-icon {
  color: #67e8f9;
}

.history-dialog-footer>div {
  display: flex;
  gap: 8px;
}

.secondary-action,
.subtle-action {
  color: #a8b4c5;
}

@media (max-width: 950px) {
  .history-workspace {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  .clinical-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .history-workspace {
    grid-template-columns: 1fr;
  }

  .patient-directory {
    max-height: 250px;
  }

  .patient-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .patient-option {
    min-width: 0;
  }

  .history-main {
    padding: 14px;
  }

  .patient-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .patient-heading .primary-action {
    width: 100%;
    justify-content: center;
  }

  .history-sections {
    grid-template-columns: 1fr;
  }

  .appointments-card {
    grid-column: auto;
  }
}

@media (max-width: 520px) {
  .patient-list {
    grid-template-columns: 1fr;
  }

  .clinical-summary {
    gap: 6px;
  }

  .clinical-summary article {
    align-items: flex-start;
    flex-direction: column;
  }

  .history-dialog-footer {
    align-items: stretch;
    flex-direction: column;
    padding: 11px 14px;
  }

  .history-dialog-footer>div {
    justify-content: flex-end;
  }

  .history-panels :deep(.q-tab-panel) {
    padding: 18px 14px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-full {
    grid-column: auto;
  }

  .dialog-header {
    padding: 16px;
  }
}
</style>
