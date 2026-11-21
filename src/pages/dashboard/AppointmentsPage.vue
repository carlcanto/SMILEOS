<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useQuasar } from 'quasar'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import esLocale from '@fullcalendar/core/locales/es'

// Estados de las citas
const STATUS = {
  confirmada: {
    label: 'Confirmada',
    color: '#22c55e',
    background: 'rgba(34, 197, 94, 0.15)',
  },
  reprogramada: {
    label: 'Reprogramada',
    color: '#94a3b8',
    background: 'rgba(148, 163, 184, 0.15)',
  },
  cancelada: {
    label: 'Cancelada',
    color: '#f87171',
    background: 'rgba(248, 113, 113, 0.15)',
  },
  atendida: {
    label: 'Atendida',
    color: '#60a5fa',
    background: 'rgba(96, 165, 250, 0.15)',
  },
}

// Crea fechas locales sin problemas de zona horaria.
function dateAt(offset, hour, minute = 0) {
  const date = new Date()
  date.setDate(date.getDate() + offset)
  date.setHours(hour, minute, 0, 0)
  return date
}

// Datos ficticios para desarrollar el front-end.
const APPOINTMENT_STORAGE_KEY = 'smileos-appointments'
const PATIENT_STORAGE_KEY = 'smileos-patients'
const $q = useQuasar()

const appointments = ref([
  {
    id: '1',
    patientName: 'María González',
    cedula: '8-123-456',
    patientCode: '8-123-456',
    patientId: '8-123-456',
    start: dateAt(0, 8, 30),
    end: dateAt(0, 9, 0),
    dentistId: 'dentist-1',
    dentistName: 'Dra. Valeria Gómez',
    status: 'confirmada',
    reason: 'Consulta general',
    treatmentType: '',
    description: '',
    observations: '',
  },
  {
    id: '2',
    patientName: 'Carlos Rodríguez',
    cedula: '8-234-567',
    patientCode: '8-234-567',
    patientId: '8-234-567',
    start: dateAt(0, 10, 0),
    end: dateAt(0, 10, 45),
    dentistId: 'dentist-2',
    dentistName: 'Dr. Andrés Castillo',
    status: 'reprogramada',
    reason: 'Limpieza dental',
    treatmentType: 'Profilaxis',
    description: '',
    observations: '',
  },
  {
    id: '3',
    patientName: 'Ana Martínez',
    cedula: '8-345-678',
    patientCode: '8-345-678',
    patientId: '8-345-678',
    start: dateAt(0, 14, 0),
    end: dateAt(0, 14, 30),
    dentistId: 'dentist-1',
    dentistName: 'Dra. Valeria Gómez',
    status: 'cancelada',
    reason: 'Dolor dental',
    treatmentType: '',
    description: '',
    observations: '',
  },
  {
    id: '4',
    patientName: 'José Pérez',
    cedula: '8-456-789',
    patientCode: '8-456-789',
    patientId: '8-456-789',
    start: dateAt(1, 9, 0),
    end: dateAt(1, 10, 0),
    dentistId: 'dentist-2',
    dentistName: 'Dr. Andrés Castillo',
    status: 'confirmada',
    reason: 'Evaluación médica',
    treatmentType: '',
    description: '',
    observations: '',
  },
  {
    id: '5',
    patientName: 'Lucía Torres',
    cedula: '8-567-890',
    patientCode: '8-567-890',
    patientId: '8-567-890',
    start: dateAt(2, 11, 0),
    end: dateAt(2, 11, 30),
    dentistId: 'dentist-1',
    dentistName: 'Dra. Valeria Gómez',
    status: 'reprogramada',
    reason: 'Consulta general',
    treatmentType: '',
    description: '',
    observations: '',
  },
  {
    id: '6',
    patientName: 'Pedro Castillo',
    cedula: '8-678-901',
    patientCode: '8-678-901',
    patientId: '8-678-901',
    start: dateAt(-2, 15, 0),
    end: dateAt(-2, 15, 45),
    dentistId: 'dentist-2',
    dentistName: 'Dr. Andrés Castillo',
    status: 'confirmada',
    reason: 'Control médico',
    treatmentType: '',
    description: '',
    observations: '',
  },
])

const calendarRef = ref(null)
const selectedAppointment = ref(null)
const detailDialog = ref(false)
const appointmentDialog = ref(false)
const cancelDialog = ref(false)
const appointmentMode = ref('create')
const appointmentForm = ref(emptyAppointmentForm())
const patientRecords = ref([])
const patientSearch = ref('')
const patientSearchOpen = ref(false)
const patientSearchTerm = ref('')
const cancelReason = ref('')
const cancelTarget = ref(null)
const cancelFromEdit = ref(false)
const rescheduleReason = ref('')

const dentists = [
  { id: 'dentist-1', name: 'Dra. Valeria Gómez' },
  { id: 'dentist-2', name: 'Dr. Andrés Castillo' },
  { id: 'dentist-3', name: 'Dra. Camila Ríos' },
]
const dentistOptions = dentists.map((dentist) => ({ label: dentist.name, value: dentist.id }))
const reasons = [
  'Consulta general', 'Limpieza dental', 'Dolor dental', 'Extracción', 'Ortodoncia',
  'Endodoncia', 'Restauración', 'Revisión odontológica', 'Otro',
]
// Tarifas provisionales de referencia; reemplazar por el tarifario aprobado de la clínica.
const reasonEstimates = {
  'Consulta general': 25,
  'Limpieza dental': 35,
  'Dolor dental': 25,
  Extracción: 50,
  Ortodoncia: 35,
  Endodoncia: 150,
  Restauración: 45,
  'Revisión odontológica': 20,
  Otro: 0,
}
const reasonOptions = reasons.map((reason) => ({
  label: `${reason} · ${new Intl.NumberFormat('es-PA', { style: 'currency', currency: 'USD' }).format(reasonEstimates[reason])}`,
  value: reason,
}))
const appointmentStatuses = [
  { label: 'Confirmada', value: 'confirmada' },
  { label: 'Reprogramada', value: 'reprogramada' },
  { label: 'Cancelada', value: 'cancelada' },
]

const demoPatients = [
  { id: '8-123-456', patientCode: '8-123-456', firstName: 'María', lastName: 'González', cedula: '8-123-456', birthDate: '1990-05-12', phone: '6000-1234', email: '' },
  { id: '8-234-567', patientCode: '8-234-567', firstName: 'Carlos', lastName: 'Rodríguez', cedula: '8-234-567', birthDate: '1985-09-03', phone: '6000-2345', email: '' },
  { id: '8-345-678', patientCode: '8-345-678', firstName: 'Ana', lastName: 'Martínez', cedula: '8-345-678', birthDate: '2000-02-20', phone: '6000-3456', email: '' },
  { id: '8-456-789', patientCode: '8-456-789', firstName: 'José', lastName: 'Pérez', cedula: '8-456-789', birthDate: '1978-12-05', phone: '6000-4567', email: '' },
  { id: '8-567-890', patientCode: '8-567-890', firstName: 'Lucía', lastName: 'Torres', cedula: '8-567-890', birthDate: '1995-07-17', phone: '6000-5678', email: '' },
  { id: '8-678-901', patientCode: '8-678-901', firstName: 'Pedro', lastName: 'Castillo', cedula: '8-678-901', birthDate: '1968-03-29', phone: '6000-6789', email: '' },
]

function localDateValue(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function emptyAppointmentForm() {
  return {
    patient: null,
    date: localDateValue(),
    startTime: '08:00',
    endTime: '08:30',
    dentistId: '',
    reason: '',
    otherReason: '',
    estimatedPrice: 0,
    treatmentType: '',
    description: '',
    observations: '',
    status: 'confirmada',
  }
}

function fullPatientName(patient) {
  return patient.fullName || patient.name || `${patient.firstName || ''} ${patient.lastName || ''}`.trim()
}

function ageFromBirthDate(date) {
  if (!date) return null
  const birth = new Date(`${date}T00:00:00`)
  if (Number.isNaN(birth.getTime())) return null
  const now = new Date()
  let age = now.getFullYear() - birth.getFullYear()
  if (now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())) age -= 1
  return age >= 0 ? age : null
}

function normalizeSearch(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').trim()
}

function normalizePatient(patient) {
  const cedula = patient.cedula || patient.identificacion || ''
  const fullName = fullPatientName(patient)
  return {
    ...patient,
    id: patient.id ?? patient.patientId ?? cedula,
    patientCode: patient.patientCode || patient.codigo || cedula,
    cedula,
    fullName,
    firstName: patient.firstName || patient.nombres || fullName.split(' ').slice(0, -1).join(' '),
    lastName: patient.lastName || patient.apellidos || fullName.split(' ').slice(-1).join(' '),
    birthDate: patient.birthDate || patient.fechaNacimiento || '',
    phone: patient.phone || patient.telefono || '',
    email: patient.email || patient.correo || '',
  }
}

function normalizeAppointment(appointment) {
  const statusMap = { confirmed: 'confirmada', pending: 'confirmada', cancelled: 'cancelada', rescheduled: 'reprogramada', completed: 'atendida' }
  const dentist = dentists.find((item) => item.id === appointment.dentistId)
  return {
    ...appointment,
    start: new Date(appointment.start),
    end: new Date(appointment.end),
    patientId: appointment.patientId || appointment.cedula,
    patientCode: appointment.patientCode || appointment.cedula,
    dentistId: appointment.dentistId || 'dentist-1',
    dentistName: appointment.dentistName || dentist?.name || 'Odontólogo por asignar',
    status: statusMap[appointment.status] || appointment.status || 'confirmada',
    reason: appointment.reason || 'Consulta general',
    estimatedPrice: Number(appointment.estimatedPrice ?? reasonEstimates[appointment.reason] ?? 0),
    treatmentType: appointment.treatmentType || '',
    description: appointment.description || '',
    observations: appointment.observations || '',
    rescheduledFromId: appointment.rescheduledFromId || null,
    rescheduleReason: appointment.rescheduleReason || '',
    cancellationReason: appointment.cancellationReason || '',
  }
}

onMounted(() => {
  try {
    const savedPatients = JSON.parse(localStorage.getItem(PATIENT_STORAGE_KEY) || 'null')
    patientRecords.value = Array.isArray(savedPatients) && savedPatients.length
      ? savedPatients.map(normalizePatient)
      : demoPatients.map(normalizePatient)
  } catch (error) {
    patientRecords.value = demoPatients.map(normalizePatient)
    console.error('No se pudieron cargar los pacientes guardados', error)
  }

  try {
    const savedAppointments = JSON.parse(localStorage.getItem(APPOINTMENT_STORAGE_KEY) || 'null')
    if (Array.isArray(savedAppointments)) appointments.value = savedAppointments.map(normalizeAppointment)
    else {
      localStorage.setItem(APPOINTMENT_STORAGE_KEY, JSON.stringify(appointments.value.map((appointment) => ({
        ...appointment,
        start: appointment.start.toISOString(),
        end: appointment.end.toISOString(),
      }))))
    }
  } catch (error) {
    $q.notify({ type: 'negative', message: 'No se pudieron cargar las citas guardadas.' })
    console.error('No se pudieron cargar las citas guardadas', error)
  }
})

function formatDate(date) {
  if (!date) return '—'

  return new Intl.DateTimeFormat('es-PA', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function formatMoney(value) {
  return new Intl.NumberFormat('es-PA', { style: 'currency', currency: 'USD' }).format(Number(value) || 0)
}

// Convierte las citas al formato que entiende FullCalendar.
const calendarEvents = computed(() =>
  appointments.value.map((appointment) => {
    const status = STATUS[appointment.status] || STATUS.confirmada

    return {
      id: appointment.id,
      title: appointment.patientName,
      start: appointment.start,
      end: appointment.end,
      backgroundColor: status.background,
      borderColor: status.color,
      textColor: status.color,
      extendedProps: {
        patientName: appointment.patientName,
        cedula: appointment.cedula,
        patientId: appointment.patientId,
        patientCode: appointment.patientCode,
        status: appointment.status,
        reason: appointment.reason,
        estimatedPrice: appointment.estimatedPrice ?? reasonEstimates[appointment.reason] ?? 0,
        treatmentType: appointment.treatmentType,
        description: appointment.description,
        observations: appointment.observations,
        dentistId: appointment.dentistId,
        dentistName: appointment.dentistName,
        rescheduledFromId: appointment.rescheduledFromId,
        rescheduleReason: appointment.rescheduleReason,
        cancellationReason: appointment.cancellationReason,
      },
    }
  }),
)

// Etiqueta emergente personalizada al pasar el cursor.
function onEventDidMount(info) {
  const props = info.event.extendedProps

  const tooltip = document.createElement('div')
  tooltip.className = 'appointment-tooltip'

  const name = document.createElement('strong')
  name.textContent = props.patientName

  const cedula = document.createElement('span')
  cedula.textContent = `Cédula: ${props.cedula}`

  const time = document.createElement('span')
  time.textContent =
    `${info.event.start.toLocaleTimeString('es-PA', {
      hour: '2-digit',
      minute: '2-digit',
    })} - ${info.event.end.toLocaleTimeString('es-PA', {
      hour: '2-digit',
      minute: '2-digit',
    })}`

  const status = document.createElement('span')
  status.textContent = STATUS[props.status]?.label ?? props.status
  status.style.color = STATUS[props.status]?.color ?? '#fff'

  const dentist = document.createElement('span')
  dentist.textContent = props.dentistName || 'Odontólogo por asignar'

  tooltip.append(name, cedula, dentist, time, status)
  document.body.appendChild(tooltip)

  const showTooltip = () => {
    tooltip.style.display = 'flex'
    const eventRect = info.el.getBoundingClientRect()
    const tooltipRect = tooltip.getBoundingClientRect()
    const gap = 8
    const left = Math.min(
      Math.max(gap, eventRect.left),
      window.innerWidth - tooltipRect.width - gap,
    )
    const top = eventRect.bottom + tooltipRect.height + gap <= window.innerHeight
      ? eventRect.bottom + gap
      : Math.max(gap, eventRect.top - tooltipRect.height - gap)

    tooltip.style.left = `${left}px`
    tooltip.style.top = `${top}px`
    tooltip.style.visibility = 'visible'
    tooltip.style.opacity = '1'
  }

  const hideTooltip = () => {
    tooltip.style.visibility = 'hidden'
    tooltip.style.opacity = '0'
    tooltip.style.display = 'none'
  }

  info.el.addEventListener('mouseenter', showTooltip)
  info.el.addEventListener('mouseleave', hideTooltip)
  info.el._appointmentTooltipCleanup = () => {
    info.el.removeEventListener('mouseenter', showTooltip)
    info.el.removeEventListener('mouseleave', hideTooltip)
    tooltip.remove()
  }
}

function onEventWillUnmount(info) {
  info.el._appointmentTooltipCleanup?.()
}

function onEventClick(info) {
  const event = info.event

  openAppointmentDetails({
    id: event.id,
    patientName: event.extendedProps.patientName,
    cedula: event.extendedProps.cedula,
    status: event.extendedProps.status,
    reason: event.extendedProps.reason,
    estimatedPrice: event.extendedProps.estimatedPrice,
    patientId: event.extendedProps.patientId,
    patientCode: event.extendedProps.patientCode,
    treatmentType: event.extendedProps.treatmentType,
    description: event.extendedProps.description,
    observations: event.extendedProps.observations,
    dentistId: event.extendedProps.dentistId,
    dentistName: event.extendedProps.dentistName,
    rescheduledFromId: event.extendedProps.rescheduledFromId,
    rescheduleReason: event.extendedProps.rescheduleReason,
    cancellationReason: event.extendedProps.cancellationReason,
    start: event.start,
    end: event.end,
  })
}

function setCalendarView(view) {
  calendarRef.value?.getApi().changeView(view)
}

const filteredPatients = computed(() => {
  const query = normalizeSearch(patientSearchTerm.value)
  if (!query) return patientRecords.value.slice(0, 8)
  return patientRecords.value.filter((patient) => normalizeSearch(
    `${patient.fullName} ${patient.firstName} ${patient.lastName} ${patient.cedula} ${patient.patientCode}`,
  ).includes(query)).slice(0, 8)
})

const appointmentDialogTitle = computed(() => ({
  create: 'Nueva cita',
  edit: 'Editar cita',
  reschedule: 'Reprogramar cita',
}[appointmentMode.value]))

const selectedAppointmentHistory = computed(() => {
  if (!selectedAppointment.value) return null
  const selected = appointments.value.find((item) => item.id === selectedAppointment.value.id)
    || selectedAppointment.value
  const original = selected.rescheduledFromId
    ? appointments.value.find((item) => item.id === selected.rescheduledFromId)
    : selected
  const replacement = appointments.value.find((item) => item.rescheduledFromId === selected.id)
  if (!original || (!replacement && !selected.rescheduledFromId)) return null
  return {
    original,
    replacement: replacement || selected,
    reason: (replacement || selected).rescheduleReason || original.rescheduleReason || '',
  }
})

function notify(type, message) {
  $q.notify({ type, message, position: 'top', timeout: 2800 })
}

function choosePatient(patient) {
  appointmentForm.value.patient = patient
  patientSearch.value = patient.fullName
  patientSearchTerm.value = patient.fullName
  patientSearchOpen.value = false
}

function clearSelectedPatient() {
  appointmentForm.value.patient = null
  patientSearch.value = ''
  patientSearchTerm.value = ''
  patientSearchOpen.value = true
}

function updateReasonEstimate(reason) {
  appointmentForm.value.estimatedPrice = reasonEstimates[reason] ?? 0
}

function clockValue(date) {
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function openCreateAppointment(date = new Date(), startTime) {
  appointmentMode.value = 'create'
  const start = new Date(date)
  const isWorkdayTime = start.getHours() >= 8 && start.getHours() < 17
  const startMinutes = start.getMinutes() < 30 ? '00' : '30'
  const initialStart = startTime || (isWorkdayTime
    ? `${String(start.getHours()).padStart(2, '0')}:${startMinutes}`
    : '08:00')
  const end = new Date(`2000-01-01T${initialStart}:00`)
  end.setMinutes(end.getMinutes() + 30)
  appointmentForm.value = {
    ...emptyAppointmentForm(),
    date: localDateValue(start),
    startTime: initialStart,
    endTime: clockValue(end),
  }
  patientSearch.value = ''
  patientSearchTerm.value = ''
  patientSearchOpen.value = false
  rescheduleReason.value = ''
  appointmentDialog.value = true
}

function dateClick(info) {
  const date = info.date
  if ([0, 6].includes(date.getDay())) {
    notify('warning', 'La clínica permanece cerrada los sábados y domingos.')
    return
  }
  let startTime
  if (!info.allDay) {
    let startMinutes = date.getMinutes() < 15 ? 0 : date.getMinutes() < 45 ? 30 : 60
    const start = new Date(date)
    start.setMinutes(startMinutes, 0, 0)
    if (start.getHours() < 8) start.setHours(8, 0, 0, 0)
    if (start.getHours() >= 17) start.setHours(16, 30, 0, 0)
    startTime = clockValue(start)
  }
  openCreateAppointment(date, startTime)
}

function appointmentToForm(appointment) {
  const patient = patientRecords.value.find((item) => String(item.id) === String(appointment.patientId)
    || item.cedula === appointment.cedula) || normalizePatient({
      id: appointment.patientId || appointment.cedula,
      patientCode: appointment.patientCode || appointment.cedula,
      name: appointment.patientName,
      cedula: appointment.cedula,
    })
  const reasonIsKnown = reasons.includes(appointment.reason)
  return {
    patient,
    date: localDateValue(appointment.start),
    startTime: clockValue(appointment.start),
    endTime: clockValue(appointment.end),
    dentistId: appointment.dentistId || '',
    reason: reasonIsKnown ? appointment.reason : 'Otro',
    otherReason: reasonIsKnown ? '' : appointment.reason,
    treatmentType: appointment.treatmentType || '',
    estimatedPrice: Number(appointment.estimatedPrice ?? reasonEstimates[appointment.reason] ?? 0),
    description: appointment.description || '',
    observations: appointment.observations || '',
    status: appointment.status || 'confirmada',
  }
}

function openEditAppointment() {
  if (!selectedAppointment.value) return
  appointmentMode.value = 'edit'
  appointmentForm.value = appointmentToForm(selectedAppointment.value)
  patientSearch.value = appointmentForm.value.patient.fullName
  patientSearchTerm.value = appointmentForm.value.patient.fullName
  rescheduleReason.value = ''
  detailDialog.value = false
  appointmentDialog.value = true
}

function openRescheduleAppointment() {
  if (!selectedAppointment.value || selectedAppointment.value.status !== 'confirmada') return
  appointmentMode.value = 'reschedule'
  appointmentForm.value = appointmentToForm(selectedAppointment.value)
  appointmentForm.value.status = 'confirmada'
  patientSearch.value = appointmentForm.value.patient.fullName
  patientSearchTerm.value = appointmentForm.value.patient.fullName
  rescheduleReason.value = ''
  detailDialog.value = false
  appointmentDialog.value = true
}

function appointmentDateTime(date, time) {
  return new Date(`${date}T${time}:00`)
}

function validateAppointmentForm({ ignoreAppointmentId } = {}) {
  const current = appointmentForm.value
  if (!current.patient) {
    notify('warning', 'Selecciona un paciente registrado.')
    return null
  }
  if (!current.dentistId) {
    notify('warning', 'Selecciona el odontólogo responsable.')
    return null
  }
  if (!current.date || !/^\d{4}-\d{2}-\d{2}$/.test(current.date)
    || localDateValue(new Date(`${current.date}T00:00:00`)) !== current.date) {
    notify('warning', 'Ingresa una fecha válida para la cita.')
    return null
  }
  const selectedDate = new Date(`${current.date}T00:00:00`)
  if ([0, 6].includes(selectedDate.getDay())) {
    notify('warning', 'La clínica permanece cerrada los sábados y domingos. Selecciona un día de lunes a viernes.')
    return null
  }
  if (!current.startTime || !current.endTime || !/^\d{2}:\d{2}$/.test(current.startTime)
    || !/^\d{2}:\d{2}$/.test(current.endTime)) {
    notify('warning', 'Completa una hora de inicio y finalización válidas.')
    return null
  }
  const start = appointmentDateTime(current.date, current.startTime)
  const end = appointmentDateTime(current.date, current.endTime)
  const opening = new Date(`${current.date}T08:00:00`)
  const closing = new Date(`${current.date}T17:00:00`)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end <= start) {
    notify('warning', 'La hora de finalización debe ser posterior a la hora de inicio.')
    return null
  }
  if (start < opening || end > closing) {
    notify('warning', 'El horario de atención es de 8:00 a. m. a 5:00 p. m.')
    return null
  }
  if (current.reason === 'Otro' && !current.otherReason.trim()) {
    notify('warning', 'Especifica el motivo de consulta.')
    return null
  }
  const dentistName = dentists.find((dentist) => dentist.id === current.dentistId)?.name || ''
  const reason = current.reason === 'Otro' ? current.otherReason.trim() : current.reason
  const isBlocking = (appointment) => !['cancelada', 'reprogramada', 'atendida'].includes(appointment.status)
  const overlap = appointments.value.find((appointment) => {
    if (appointment.id === ignoreAppointmentId || !isBlocking(appointment)) return false
    const sameDentist = appointment.dentistId === current.dentistId
    const intersects = start < new Date(appointment.end) && end > new Date(appointment.start)
    const duplicatePatientSlot = String(appointment.patientId) === String(current.patient.id)
      && start.getTime() === new Date(appointment.start).getTime()
      && end.getTime() === new Date(appointment.end).getTime()
    return (sameDentist && intersects) || duplicatePatientSlot
  })
  if (overlap) {
    notify('negative', `Conflicto de horario: ${overlap.dentistName || dentistName} ya tiene una cita en ese intervalo.`)
    return null
  }
  return { start, end, dentistName, reason }
}

function appointmentFromForm({ id, status, rescheduledFromId = null, extra = {} }) {
  const current = appointmentForm.value
  const patient = current.patient
  const dentist = dentists.find((item) => item.id === current.dentistId)
  const isRescheduling = appointmentMode.value === 'reschedule'
    || (appointmentMode.value === 'edit' && current.status === 'reprogramada'
      && selectedAppointment.value?.status !== 'reprogramada')
  const validated = validateAppointmentForm({
    ignoreAppointmentId: isRescheduling ? selectedAppointment.value?.id : id,
  })
  if (!validated) return null
  return {
    id,
    patientId: patient.id,
    patientCode: patient.patientCode || patient.cedula,
    patientName: patient.fullName,
    cedula: patient.cedula,
    birthDate: patient.birthDate || '',
    age: ageFromBirthDate(patient.birthDate),
    phone: patient.phone || '',
    email: patient.email || '',
    start: validated.start,
    end: validated.end,
    dentistId: current.dentistId,
    dentistName: dentist?.name || validated.dentistName,
    reason: validated.reason,
    treatmentType: current.treatmentType.trim(),
    estimatedPrice: Math.max(0, Number(current.estimatedPrice) || 0),
    description: current.description.trim(),
    observations: current.observations.trim(),
    status,
    rescheduledFromId,
    ...extra,
  }
}

function newAppointmentId() {
  return globalThis.crypto?.randomUUID?.() || `appt-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

async function commitAppointments(nextAppointments) {
  try {
    const serializable = nextAppointments.map((appointment) => ({
      ...appointment,
      start: new Date(appointment.start).toISOString(),
      end: new Date(appointment.end).toISOString(),
    }))
    localStorage.setItem(APPOINTMENT_STORAGE_KEY, JSON.stringify(serializable))
    appointments.value = nextAppointments
    await nextTick()
    calendarRef.value?.getApi().refetchEvents()
    return true
  } catch (error) {
    notify('negative', 'No se pudo guardar la cita. Intenta nuevamente.')
    console.error('Error al guardar citas localmente', error)
    return false
  }
}

async function saveAppointment() {
  if (appointmentMode.value === 'reschedule'
    || (appointmentMode.value === 'edit' && appointmentForm.value.status === 'reprogramada'
      && selectedAppointment.value?.status !== 'reprogramada')) {
    if (!rescheduleReason.value.trim()) {
      notify('warning', 'Indica el motivo de la reprogramación.')
      return
    }
    saveReschedule()
    return
  }
  if (appointmentMode.value === 'edit' && appointmentForm.value.status === 'cancelada') {
    cancelTarget.value = selectedAppointment.value
    cancelReason.value = ''
    cancelFromEdit.value = true
    appointmentDialog.value = false
    cancelDialog.value = true
    return
  }

  const id = appointmentMode.value === 'edit' ? selectedAppointment.value?.id : newAppointmentId()
  const status = appointmentMode.value === 'edit' ? appointmentForm.value.status : 'confirmada'
  const savedAppointment = appointmentFromForm({ id, status })
  if (!savedAppointment) return
  const next = appointmentMode.value === 'edit'
    ? appointments.value.map((appointment) => appointment.id === id
      ? { ...appointment, ...savedAppointment, updatedAt: new Date().toISOString() }
      : appointment)
    : [
      { ...savedAppointment, createdAt: new Date().toISOString() },
      ...appointments.value,
    ]
  if (await commitAppointments(next)) {
    appointmentDialog.value = false
    detailDialog.value = false
    notify('positive', appointmentMode.value === 'edit' ? 'Cambios guardados correctamente.' : 'Cita guardada correctamente.')
  }
}

async function saveReschedule() {
  const original = selectedAppointment.value
  if (!original) return
  const newAppointment = appointmentFromForm({
    id: newAppointmentId(),
    status: 'confirmada',
    rescheduledFromId: original.id,
    extra: { rescheduleReason: rescheduleReason.value.trim(), createdAt: new Date().toISOString() },
  })
  if (!newAppointment) return
  const next = appointments.value.map((appointment) => appointment.id === original.id
    ? { ...appointment, status: 'reprogramada', rescheduleReason: rescheduleReason.value.trim(), updatedAt: new Date().toISOString() }
    : appointment)
  next.unshift(newAppointment)
  if (await commitAppointments(next)) {
    appointmentDialog.value = false
    detailDialog.value = false
    selectedAppointment.value = newAppointment
    notify('positive', 'Cita reprogramada. Se conservó la cita original en el historial.')
  }
}

function openCancelDialog(appointment = selectedAppointment.value, fromEdit = false) {
  if (!appointment) return
  cancelTarget.value = appointment
  cancelReason.value = ''
  cancelFromEdit.value = fromEdit
  detailDialog.value = false
  appointmentDialog.value = false
  cancelDialog.value = true
}

function dismissCancelDialog() {
  cancelDialog.value = false
  if (cancelFromEdit.value) appointmentDialog.value = true
  else if (cancelTarget.value) detailDialog.value = true
}

async function confirmCancellation() {
  if (!cancelReason.value.trim()) {
    notify('warning', 'Indica el motivo de cancelación.')
    return
  }
  const target = cancelTarget.value
  if (!target) return
  let cancelledAppointment
  if (cancelFromEdit.value) {
    cancelledAppointment = appointmentFromForm({
      id: target.id,
      status: 'cancelada',
      extra: {
        cancellationReason: cancelReason.value.trim(),
        cancelledAt: new Date().toISOString(),
        cancelledBy: 'Personal de SmileOS',
      },
    })
    if (!cancelledAppointment) return
  } else {
    cancelledAppointment = {
      ...target,
      status: 'cancelada',
      cancellationReason: cancelReason.value.trim(),
      cancelledAt: new Date().toISOString(),
      cancelledBy: 'Personal de SmileOS',
    }
  }
  const next = appointments.value.map((appointment) => appointment.id === target.id
    ? { ...appointment, ...cancelledAppointment }
    : appointment)
  if (await commitAppointments(next)) {
    cancelDialog.value = false
    appointmentDialog.value = false
    detailDialog.value = false
    cancelTarget.value = null
    cancelFromEdit.value = false
    notify('positive', 'La cita fue cancelada y permanece en el historial.')
  }
}

function openAppointmentDetails(appointment) {
  selectedAppointment.value = appointment
  detailDialog.value = true
}

function formatSlotTime(date) {
  const hours = date.getHours()
  const hour12 = hours % 12 || 12
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const period = hours < 12 ? 'a.m.' : 'p.m.'

  return `${hour12}:${minutes} ${period}`
}

const calendarOptions = {
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  locales: [esLocale],
  locale: 'es',
  timeZone: 'local',
  initialView: 'dayGridMonth',
  firstDay: 1,
  height: 'auto',
  nowIndicator: true,
  allDaySlot: false,
  slotMinTime: '08:00:00',
  slotMaxTime: '17:00:00',
  slotDuration: '00:30:00',
  slotLabelInterval: '00:30:00',
  slotLabelContent: (info) => {
    const slotEnd = new Date(info.date.getTime() + 30 * 60 * 1000)
    return `${formatSlotTime(info.date)} – ${formatSlotTime(slotEnd)}`
  },
  scrollTime: '08:00:00',
  expandRows: true,
  dayMaxEvents: 4,
  displayEventTime: true,
  eventTimeFormat: {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  },
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: '',
  },
  buttonText: {
    today: 'Hoy',
    month: 'Mes',
    week: 'Semana',
    day: 'Día',
  },
  events: (fetchInfo, successCallback) => {
    const start = fetchInfo.start.getTime()
    const end = fetchInfo.end.getTime()

    successCallback(
      calendarEvents.value.filter((event) => {
        const eventStart = new Date(event.start).getTime()
        const eventEnd = new Date(event.end).getTime()

        return eventStart < end && eventEnd > start
      }),
    )
  },
  eventDidMount: onEventDidMount,
  eventWillUnmount: onEventWillUnmount,
  eventClick: onEventClick,
  dateClick,
}
</script>

<template>
  <q-page class="appointment-page futuristic-bg q-pa-md q-pa-lg-lg">
    <section class="page-heading">
      <div>
        <h1>Citas médicas</h1>
        <p>Consulta y administra la agenda de tus pacientes.</p>
      </div>
      <q-btn no-caps unelevated icon="add" label="Nueva cita" class="new-appointment-button"
        @click="openCreateAppointment()" />
    </section>
    <section class="appointment-calendar">
      <div class="section-heading">
        <div>
          <div class="eyebrow">Agenda</div>
          <h2>Calendario de citas</h2>
        </div>
      </div>
      <div class="mb-5 flex flex-wrap items-center justify-between gap-4">
        <!-- Leyenda de estados a la izquierda -->
        <div class="flex flex-wrap gap-x-5 gap-y-2">
          <span class="legend-item">
            <i class="legend-dot bg-green-400"></i>
            Confirmada
          </span>
          <span class="legend-item">
            <i class="legend-dot bg-gray-400"></i>
            Reprogramada
          </span>
          <span class="legend-item">
            <i class="legend-dot bg-red-400"></i>
            Cancelada
          </span>
          <span class="legend-item">
            <i class="legend-dot" style="background:#60a5fa"></i>
            Atendida
          </span>
        </div>

        <!-- Selector de vista a la derecha -->
        <div class="flex flex-wrap gap-2">
          <q-btn no-caps unelevated label="Diario" icon="view_day" class="view-button"
            @click="setCalendarView('timeGridDay')" />

          <q-btn no-caps unelevated label="Semanal" icon="view_week" class="view-button"
            @click="setCalendarView('timeGridWeek')" />

          <q-btn no-caps unelevated label="Mensual" icon="calendar_month" class="view-button"
            @click="setCalendarView('dayGridMonth')" />
        </div>
      </div>

      <FullCalendar ref="calendarRef" :options="calendarOptions" />
    </section>

    <q-dialog v-model="detailDialog">
      <q-card v-if="selectedAppointment" class="appointment-dialog">
        <header class="appointment-dialog-header">
          <div class="appointment-patient-avatar"><q-icon name="person" size="24px" /></div>
          <div class="appointment-patient-heading">
            <div class="dialog-kicker">Detalle de cita</div>
            <h2>{{ selectedAppointment.patientName }}</h2>
            <span>Cédula · {{ selectedAppointment.cedula }}</span>
          </div>
          <q-btn round flat dense icon="close" aria-label="Cerrar detalle" class="appointment-close" v-close-popup />
        </header>
        <section class="appointment-dialog-content">
          <div class="appointment-info-grid">
            <div class="appointment-info-card">
              <q-icon name="event" />
              <div><span>Inicio</span><strong>{{ formatDate(selectedAppointment.start) }}</strong></div>
            </div>
            <div class="appointment-info-card">
              <q-icon name="schedule" />
              <div><span>Fin</span><strong>{{ formatDate(selectedAppointment.end) }}</strong></div>
            </div>
            <div class="appointment-info-card appointment-reason-card">
              <q-icon name="medical_services" />
              <div><span>Motivo de la cita</span><strong>{{ selectedAppointment.reason }}</strong></div>
            </div>
            <div class="appointment-info-card appointment-dentist-card">
              <q-icon name="medical_services" />
              <div class="appointment-dentist-copy"><span>Odontólogo</span><strong>{{ selectedAppointment.dentistName }}</strong></div>
            </div>
            <div class="appointment-info-card">
              <q-icon name="badge" />
              <div><span>Código del paciente</span><strong>{{ selectedAppointment.patientCode ||
                selectedAppointment.cedula }}</strong></div>
            </div>
            <div class="appointment-info-card">
              <q-icon name="payments" />
              <div><span>Estimación de consulta</span><strong>{{ formatMoney(selectedAppointment.estimatedPrice) }}</strong></div>
            </div>
            <div v-if="selectedAppointment.treatmentType" class="appointment-info-card appointment-reason-card">
              <q-icon name="healing" />
              <div><span>Tratamiento</span><strong>{{ selectedAppointment.treatmentType }}</strong></div>
            </div>
            <div v-if="selectedAppointment.description" class="appointment-info-card appointment-reason-card">
              <q-icon name="description" />
              <div><span>Descripción</span><strong>{{ selectedAppointment.description }}</strong></div>
            </div>
            <div v-if="selectedAppointment.observations" class="appointment-info-card appointment-reason-card">
              <q-icon name="notes" />
              <div><span>Observaciones</span><strong>{{ selectedAppointment.observations }}</strong></div>
            </div>
          </div>
          <div v-if="selectedAppointmentHistory" class="appointment-history">
            <div class="history-heading"><q-icon name="history" /><strong>Historial de reprogramación</strong></div>
            <div class="history-entry">
              <span>Horario anterior</span>
              <strong>{{ formatDate(selectedAppointmentHistory.original.start) }} – {{
                formatDate(selectedAppointmentHistory.original.end) }}</strong>
            </div>
            <div class="history-entry">
              <span>Nueva programación</span>
              <strong>{{ formatDate(selectedAppointmentHistory.replacement.start) }} – {{
                formatDate(selectedAppointmentHistory.replacement.end) }}</strong>
            </div>
            <p v-if="selectedAppointmentHistory.reason">Motivo: {{ selectedAppointmentHistory.reason }}</p>
          </div>
          <div v-if="selectedAppointment.cancellationReason" class="cancellation-note">
            <strong>Motivo de cancelación</strong><span>{{ selectedAppointment.cancellationReason }}</span>
          </div>
          <div class="appointment-status-row">
            <span>Estado de la cita</span>
            <q-badge class="appointment-status-badge" :style="{
              color: STATUS[selectedAppointment.status].color,
              background: STATUS[selectedAppointment.status].background,
              borderColor: STATUS[selectedAppointment.status].color
            }">
              <i :style="{ background: STATUS[selectedAppointment.status].color }"></i>
              {{ STATUS[selectedAppointment.status].label }}
            </q-badge>
          </div>
        </section>
        <footer class="appointment-dialog-footer">
          <span>SmileOS <b>·</b> Agenda clínica</span>
          <div class="dialog-actions">
            <q-btn v-if="selectedAppointment.status === 'confirmada'" flat no-caps label="Reprogramar"
              icon="event_repeat" class="subtle-action" @click="openRescheduleAppointment" />
            <q-btn v-if="['confirmada', 'reprogramada'].includes(selectedAppointment.status)" flat no-caps label="Cancelar cita"
              icon="event_busy" class="danger-action" @click="openCancelDialog()" />
            <q-btn v-if="['confirmada', 'reprogramada'].includes(selectedAppointment.status)" unelevated no-caps label="Editar" icon="edit"
              class="appointment-close-action" @click="openEditAppointment" />
            <q-btn v-if="!['confirmada', 'reprogramada'].includes(selectedAppointment.status)" unelevated no-caps label="Cerrar" icon-right="arrow_forward" class="appointment-close-action"
              v-close-popup />
          </div>
        </footer>
      </q-card>
    </q-dialog>

    <q-dialog v-model="appointmentDialog" persistent>
      <q-card class="appointment-form-dialog">
        <header class="form-dialog-header">
          <div class="form-icon"><q-icon :name="appointmentMode === 'reschedule' ? 'event_repeat' : 'calendar_month'" />
          </div>
          <div>
            <div class="dialog-kicker">Agenda clínica · SmileOS</div>
            <h2>{{ appointmentDialogTitle }}</h2>
            <p>{{ appointmentMode === 'create' ? 'Completa los datos para reservar un espacio en la agenda.' :
              'Actualiza la información y confirma los cambios.' }}</p>
          </div>
          <q-btn round flat dense icon="close" aria-label="Cerrar formulario" class="appointment-close"
            @click="appointmentDialog = false" />
        </header>
        <q-form class="form-dialog-content" @submit.prevent="saveAppointment">
          <section class="form-section">
            <div class="form-section-title"><q-icon name="person_search" /><span>Paciente</span></div>
            <div v-if="!appointmentForm.patient" class="patient-search-wrap">
              <q-input v-model="patientSearchTerm" dark outlined dense label="Buscar por nombre, apellido o cédula"
                class="appointment-input" autocomplete="off" @focus="patientSearchOpen = true"
                @update:model-value="patientSearchOpen = true">
                <template #prepend><q-icon name="search" /></template>
              </q-input>
              <div v-if="patientSearchOpen" class="patient-results">
                <button v-for="patient in filteredPatients" :key="patient.id" type="button" class="patient-result"
                  @click="choosePatient(patient)">
                  <span class="patient-result-avatar"><q-icon name="person" /></span>
                  <span class="patient-result-copy"><strong>{{ patient.fullName }}</strong><small>Cédula {{
                    patient.cedula }} · {{
                        patient.phone || 'Sin teléfono' }}</small></span>
                  <q-icon name="chevron_right" />
                </button>
                <div v-if="!filteredPatients.length" class="patient-empty">No se encontraron pacientes registrados.
                </div>
              </div>
            </div>
            <div v-else class="selected-patient-card">
              <div class="patient-result-avatar"><q-icon name="person" /></div>
              <div class="selected-patient-copy"><strong>{{ appointmentForm.patient.fullName }}</strong>
                <span>{{ appointmentForm.patient.patientCode || appointmentForm.patient.cedula }} · Cédula {{
                  appointmentForm.patient.cedula }}</span>
                <small>{{ ageFromBirthDate(appointmentForm.patient.birthDate) ?? 'Edad no registrada' }}{{
                  ageFromBirthDate(appointmentForm.patient.birthDate) !== null ? ' años' : '' }} · {{
                    appointmentForm.patient.phone
                    || 'Teléfono no registrado' }}</small>
              </div>
              <q-btn flat round dense icon="edit" aria-label="Cambiar paciente" class="subtle-action"
                @click="clearSelectedPatient" />
            </div>
          </section>

          <section v-if="appointmentMode === 'reschedule'" class="previous-slot-banner">
            <q-icon name="history" />
            <div><span>Horario anterior</span><strong>{{ formatDate(selectedAppointment.start) }} – {{
              formatDate(selectedAppointment.end) }}</strong></div>
          </section>

          <section class="form-section">
            <div class="form-section-title"><q-icon name="event_available" /><span>Datos de la cita</span></div>
            <div class="form-grid">
              <q-input v-model="appointmentForm.date" dark outlined dense type="date" label="Fecha" stack-label
                class="appointment-input" />
              <q-select v-model="appointmentForm.dentistId" dark outlined dense emit-value map-options
                :options="dentistOptions" label="Odontólogo responsable" class="appointment-input" />
              <q-input v-model="appointmentForm.startTime" dark outlined dense type="time" label="Hora de inicio"
                stack-label class="appointment-input" />
              <q-input v-model="appointmentForm.endTime" dark outlined dense type="time" label="Hora de finalización"
                stack-label class="appointment-input" />
              <q-select v-model="appointmentForm.reason" dark outlined dense emit-value map-options :options="reasonOptions"
                label="Motivo de consulta" class="appointment-input" @update:model-value="updateReasonEstimate" />
              <q-input v-model.number="appointmentForm.estimatedPrice" dark outlined dense type="number" min="0"
                step="0.01" prefix="$" label="Costo estimado (USD)" hint="Tarifa provisional editable"
                class="appointment-input" />
              <q-input v-if="appointmentForm.reason === 'Otro'" v-model="appointmentForm.otherReason" dark outlined
                dense label="Especifica el motivo" class="appointment-input" />
              <q-input v-model="appointmentForm.treatmentType" dark outlined dense label="Tipo de tratamiento"
                class="appointment-input" />
              <q-select v-if="appointmentMode === 'edit'" v-model="appointmentForm.status" dark outlined dense
                emit-value map-options :options="appointmentStatuses" label="Estado" class="appointment-input">
                <template #selected-item="scope"><span class="status-select-value"
                    :style="{ color: STATUS[scope.opt.value].color }">{{ scope.opt.label }}</span></template>
              </q-select>
              <q-input v-model="appointmentForm.description" dark outlined dense type="textarea" autogrow
                label="Descripción adicional" class="appointment-input form-full" />
              <q-input v-model="appointmentForm.observations" dark outlined dense type="textarea" autogrow
                label="Observaciones" class="appointment-input form-full" />
              <q-input
                v-if="appointmentMode === 'reschedule' || (appointmentMode === 'edit' && appointmentForm.status === 'reprogramada')"
                v-model="rescheduleReason" dark outlined dense type="textarea" autogrow
                label="Motivo de la reprogramación" class="appointment-input form-full" />
            </div>
            <p class="hours-hint"><q-icon name="info" /> Horario de atención: 8:00 a. m. a 5:00 p. m.</p>
          </section>
          <footer class="form-dialog-footer">
            <q-btn flat no-caps label="Cancelar" class="subtle-action" @click="appointmentDialog = false" />
            <q-btn unelevated no-caps
              :label="appointmentMode === 'create' ? 'Guardar cita' : appointmentMode === 'reschedule' ? 'Confirmar reprogramación' : 'Guardar cambios'"
              :icon="appointmentMode === 'reschedule' ? 'event_repeat' : 'check'" class="appointment-close-action"
              type="submit" />
          </footer>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="cancelDialog" persistent>
      <q-card class="cancel-dialog">
        <header class="cancel-dialog-header">
          <div class="cancel-icon"><q-icon name="event_busy" /></div>
          <div>
            <div class="dialog-kicker danger-kicker">Confirmación requerida</div>
            <h2>Cancelar cita</h2>
            <p>La cita se conservará en el historial clínico.</p>
          </div>
        </header>
        <div v-if="cancelTarget" class="cancel-summary">
          <strong>{{ cancelTarget.patientName }}</strong><span>Cédula {{ cancelTarget.cedula }}</span>
          <span>{{ formatDate(cancelTarget.start) }} – {{ formatDate(cancelTarget.end) }}</span><span>{{
            cancelTarget.dentistName }}</span>
        </div>
        <q-input v-model="cancelReason" dark outlined type="textarea" autogrow label="Motivo de cancelación"
          class="appointment-input cancel-reason-input" />
        <footer class="form-dialog-footer"><q-btn flat no-caps label="Volver" class="subtle-action"
            @click="dismissCancelDialog" />
          <q-btn unelevated no-caps label="Confirmar cancelación" icon="event_busy" class="confirm-cancel-button"
            @click="confirmCancellation" />
        </footer>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<style scoped>
.appointment-page {
  min-height: 100%;
  color: #e2e8f0;
}

.page-heading,
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.page-heading {
  max-width: 1120px;
  margin: 4px auto 24px;
}

.page-heading h1 {
  margin: 3px 0 5px;
  color: #f8fafc;
  font-size: clamp(26px, 4vw, 34px);
  font-weight: 700;
}

.page-heading p {
  margin: 0;
  color: #94a3b8;
  font-size: 13px;
}

.eyebrow {
  color: #67e8f9;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .18em;
  text-transform: uppercase;
}

.section-heading {
  margin-bottom: 20px;
}

.section-heading h2 {
  margin: 5px 0 0;
  color: #f1f5f9;
  font-size: 18px;
  font-weight: 650;
}

.appointment-stat {
  padding: 18px;
  border: 1px solid rgba(100, 140, 190, 0.18);
  border-radius: 14px;
  background: rgba(16, 19, 31, 0.78);
  box-shadow: 0 0 25px rgba(37, 99, 235, 0.035);
  color: #94a3b8;
  font-size: 13px;
}

.appointment-stat strong {
  display: block;
  margin-top: 12px;
  color: #f1f5f9;
  font-size: 30px;
  line-height: 1.2;
}

.appointment-stat small {
  display: block;
  margin-top: 6px;
  color: #64748b;
}

.appointment-calendar {
  max-width: 1120px;
  margin: 0 auto;
  padding: 24px;
  border: 1px solid rgba(100, 140, 190, 0.22);
  border-radius: 18px;
  background: rgba(16, 19, 31, 0.82);
  box-shadow: 0 0 35px rgba(37, 99, 235, 0.06);
}

.new-appointment-button {
  min-height: 42px;
  padding: 0 16px;
  border: 1px solid rgba(34, 211, 238, .42);
  border-radius: 10px;
  background: linear-gradient(120deg, rgba(8, 145, 178, .34), rgba(30, 64, 175, .32));
  color: #a5f3fc;
  box-shadow: 0 0 24px rgba(6, 182, 212, .1);
}

.appointment-form-dialog,
.cancel-dialog {
  width: min(760px, calc(100vw - 28px));
  max-width: 760px;
  max-height: min(90vh, 900px);
  overflow: hidden;
  border: 1px solid rgba(34, 211, 238, .28);
  border-radius: 18px;
  background: radial-gradient(ellipse at 5% 0%, rgba(8, 145, 178, .17), transparent 42%), #0b1120;
  color: #e2e8f0;
  box-shadow: 0 24px 80px rgba(0, 0, 0, .58), 0 0 38px rgba(6, 182, 212, .1);
  animation: dialog-enter 180ms ease-out;
}

.appointment-form-dialog {
  display: flex;
  min-height: 0;
  flex-direction: column;
}

.appointment-form-dialog>.form-dialog-header {
  flex: 0 0 auto;
}

.form-dialog-header,
.cancel-dialog-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 22px 24px 18px;
  border-bottom: 1px solid rgba(100, 140, 190, .14);
}

.form-icon,
.cancel-icon {
  display: grid;
  width: 46px;
  height: 46px;
  flex: 0 0 46px;
  place-items: center;
  border: 1px solid rgba(103, 232, 249, .3);
  border-radius: 13px;
  background: rgba(8, 145, 178, .16);
  color: #67e8f9;
  font-size: 23px;
}

.form-dialog-header>div:nth-child(2),
.cancel-dialog-header>div:nth-child(2) {
  flex: 1;
}

.form-dialog-header h2,
.cancel-dialog-header h2 {
  margin: 4px 0;
  color: #f8fafc;
  font-size: 20px;
  font-weight: 650;
}

.form-dialog-header p,
.cancel-dialog-header p {
  margin: 0;
  color: #94a3b8;
  font-size: 12px;
}

.form-dialog-content {
  display: flex;
  min-height: 0;
  flex: 1 1 auto;
  flex-direction: column;
  overflow-y: auto;
}

.form-section {
  padding: 18px 24px;
}

.form-section+.form-section {
  border-top: 1px solid rgba(100, 140, 190, .12);
}

.form-section-title {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 14px;
  color: #cbd5e1;
  font-size: 13px;
  font-weight: 650;
}

.form-section-title .q-icon {
  color: #67e8f9;
  font-size: 19px;
}

.patient-search-wrap {
  position: relative;
}

.appointment-input :deep(.q-field__control) {
  border-radius: 9px;
  background: rgba(15, 23, 42, .5);
}

.appointment-input :deep(.q-field__label),
.appointment-input :deep(.q-field__native),
.appointment-input :deep(.q-field__marginal) {
  color: #b6c4d5;
}

.appointment-input :deep(.q-field--outlined .q-field__control:before) {
  border-color: rgba(100, 140, 190, .28);
}

.appointment-input :deep(.q-field--focused .q-field__control:after) {
  border-color: #22d3ee;
}

.patient-results {
  position: absolute;
  z-index: 20;
  top: calc(100% + 6px);
  right: 0;
  left: 0;
  max-height: 240px;
  overflow: auto;
  padding: 5px;
  border: 1px solid rgba(34, 211, 238, .28);
  border-radius: 11px;
  background: #0b1120;
  box-shadow: 0 16px 36px rgba(0, 0, 0, .45);
}

.patient-result {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #cbd5e1;
  text-align: left;
  cursor: pointer;
}

.patient-result:hover {
  background: rgba(8, 145, 178, .15);
}

.patient-result-avatar {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  place-items: center;
  border: 1px solid rgba(103, 232, 249, .25);
  border-radius: 10px;
  background: rgba(8, 145, 178, .12);
  color: #67e8f9;
}

.patient-result-copy,
.selected-patient-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 3px;
}

.patient-result-copy strong,
.selected-patient-copy strong {
  overflow: hidden;
  color: #f1f5f9;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.patient-result-copy small,
.selected-patient-copy span,
.selected-patient-copy small {
  color: #94a3b8;
  font-size: 10px;
}

.patient-empty {
  padding: 18px 10px;
  color: #94a3b8;
  font-size: 12px;
  text-align: center;
}

.selected-patient-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid rgba(34, 211, 238, .2);
  border-radius: 12px;
  background: rgba(8, 145, 178, .08);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.form-full {
  grid-column: 1 / -1;
}

.hours-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 12px 0 0;
  color: #64748b;
  font-size: 10px;
}

.hours-hint .q-icon {
  color: #67e8f9;
}

.previous-slot-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 24px 0;
  padding: 12px 14px;
  border: 1px solid rgba(148, 163, 184, .24);
  border-radius: 10px;
  background: rgba(148, 163, 184, .08);
  color: #cbd5e1;
}

.previous-slot-banner>.q-icon {
  color: #94a3b8;
  font-size: 20px;
}

.previous-slot-banner div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.previous-slot-banner span {
  color: #94a3b8;
  font-size: 10px;
}

.previous-slot-banner strong {
  font-size: 12px;
}

.form-dialog-footer {
  position: sticky;
  z-index: 4;
  bottom: 0;
  display: flex;
  flex: 0 0 auto;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px;
  border-top: 1px solid rgba(100, 140, 190, .14);
  background: rgba(2, 6, 23, .3);
}

.appointment-form-dialog .form-dialog-footer {
  background: #0b1120;
  box-shadow: 0 -8px 20px rgba(2, 6, 23, .42);
}

.dialog-actions {
  display: flex;
  align-items: center;
  gap: 7px;
}

.subtle-action {
  color: #9fb0c5;
}

.danger-action {
  color: #f87171;
}

.confirm-cancel-button {
  border-radius: 9px;
  background: rgba(220, 38, 38, .18);
  border: 1px solid rgba(248, 113, 113, .48);
  color: #fca5a5;
}

.cancel-dialog {
  width: min(480px, calc(100vw - 28px));
}

.cancel-dialog-header {
  border-bottom: 0;
}

.cancel-icon {
  border-color: rgba(248, 113, 113, .34);
  background: rgba(220, 38, 38, .13);
  color: #f87171;
}

.danger-kicker {
  color: #f87171;
}

.cancel-summary {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0 24px 16px;
  padding: 14px;
  border: 1px solid rgba(248, 113, 113, .18);
  border-radius: 10px;
  background: rgba(127, 29, 29, .1);
}

.cancel-summary strong {
  color: #f8fafc;
  font-size: 14px;
}

.cancel-summary span {
  color: #a8b4c5;
  font-size: 11px;
}

.cancel-reason-input {
  display: block;
  margin: 0 24px 18px;
  width: calc(100% - 48px);
}

.appointment-history {
  margin-top: 14px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, .2);
  border-radius: 11px;
  background: rgba(148, 163, 184, .06);
}

.history-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: #cbd5e1;
  font-size: 12px;
}

.history-heading .q-icon {
  color: #94a3b8;
}

.history-entry {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 0;
  color: #94a3b8;
  font-size: 10px;
}

.history-entry strong {
  color: #cbd5e1;
  font-weight: 500;
  text-align: right;
}

.appointment-history p {
  margin: 6px 0 0;
  color: #94a3b8;
  font-size: 10px;
}

.cancellation-note {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 12px;
  padding: 12px;
  border: 1px solid rgba(248, 113, 113, .22);
  border-radius: 10px;
  background: rgba(127, 29, 29, .1);
  font-size: 11px;
}

.cancellation-note strong {
  color: #fca5a5;
}

.cancellation-note span {
  color: #cbd5e1;
}

.status-select-value {
  font-size: 12px;
}

@keyframes dialog-enter {
  from {
    opacity: 0;
    transform: translateY(8px) scale(.99);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.view-button {
  min-height: 38px;
  border: 1px solid rgba(34, 211, 238, .28);
  border-radius: 9px;
  background: rgba(23, 36, 59, .78);
  color: #cbd5e1;
  transition: border-color 160ms ease, background 160ms ease, color 160ms ease;
}

.view-button:hover {
  border-color: rgba(34, 211, 238, .56);
  background: rgba(8, 145, 178, .2);
  color: #67e8f9;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
  font-size: 12px;
}

.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.appointment-dialog {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 560px;
  border: 1px solid rgba(34, 211, 238, .3);
  border-radius: 18px;
  background: radial-gradient(ellipse at 8% 0%, rgba(8, 145, 178, .2), transparent 45%), #0b1120;
  color: #e2e8f0;
  box-shadow: 0 0 0 1px rgba(34, 211, 238, .06), 0 24px 80px rgba(0, 0, 0, .58), 0 0 36px rgba(6, 182, 212, .12);
}

.appointment-dialog::before {
  position: absolute;
  top: 0;
  right: 24px;
  left: 24px;
  height: 1px;
  background: linear-gradient(90deg, transparent, #67e8f9, transparent);
  content: '';
}

.appointment-dialog-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 24px 24px 20px;
}

.appointment-patient-avatar {
  display: grid;
  width: 52px;
  height: 52px;
  flex: 0 0 52px;
  place-items: center;
  border: 1px solid rgba(103, 232, 249, .38);
  border-radius: 15px;
  background: rgba(8, 145, 178, .17);
  box-shadow: 0 0 22px rgba(34, 211, 238, .12);
  color: #67e8f9;
}

.appointment-patient-heading {
  min-width: 0;
  flex: 1;
}

.dialog-kicker {
  color: #67e8f9;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .18em;
  text-transform: uppercase;
}

.appointment-patient-heading h2 {
  overflow-wrap: anywhere;
  margin: 5px 0 3px;
  color: #f8fafc;
  font-size: 20px;
  font-weight: 650;
  line-height: 1.25;
}

.appointment-patient-heading span {
  color: #94a3b8;
  font-size: 11px;
}

.appointment-close {
  align-self: flex-start;
  color: #94a3b8;
}

.appointment-close:hover {
  background: rgba(34, 211, 238, .1);
  color: #67e8f9;
}

.appointment-dialog-content {
  padding: 4px 24px 22px;
}

.appointment-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.appointment-info-card {
  display: flex;
  min-width: 0;
  align-items: flex-start;
  gap: 11px;
  padding: 14px;
  border: 1px solid rgba(34, 211, 238, .15);
  border-radius: 12px;
  background: linear-gradient(110deg, rgba(15, 38, 58, .83), rgba(15, 23, 42, .78));
}

.appointment-info-card>.q-icon {
  flex: 0 0 auto;
  margin-top: 1px;
  color: #67e8f9;
}

.appointment-dentist-card {
  flex-direction: row;
  align-items: center;
}

.appointment-dentist-card>.q-icon {
  width: 20px;
  height: 20px;
  font-size: 20px;
}

.appointment-info-card>.appointment-dentist-copy {
  flex: 1;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
}

.appointment-info-card>div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
}

.appointment-info-card span {
  color: #64748b;
  font-size: 10px;
  letter-spacing: .09em;
  text-transform: uppercase;
}

.appointment-info-card strong {
  overflow-wrap: anywhere;
  color: #e2e8f0;
  font-size: 12px;
  font-weight: 550;
  line-height: 1.45;
}

.appointment-reason-card {
  grid-column: 1 / -1;
}

.appointment-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  padding: 12px 14px;
  border: 1px solid rgba(100, 140, 190, .14);
  border-radius: 10px;
  background: rgba(2, 6, 23, .25);
  color: #94a3b8;
  font-size: 11px;
}

.appointment-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: 1px solid;
  border-radius: 20px;
  padding: 6px 10px;
  font-size: 10px;
}

.appointment-status-badge i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  box-shadow: 0 0 9px currentColor;
}

.appointment-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 64px;
  padding: 12px 24px;
  border-top: 1px solid rgba(100, 140, 190, .14);
  background: rgba(2, 6, 23, .35);
}

.appointment-dialog-footer>span {
  color: #64748b;
  font-size: 10px;
  letter-spacing: .05em;
}

.appointment-dialog-footer b {
  color: #22d3ee;
}

.appointment-close-action {
  border: 1px solid rgba(34, 211, 238, .4);
  border-radius: 8px;
  background: rgba(8, 145, 178, .17);
  color: #a5f3fc;
}

/* FullCalendar */
:deep(.fc) {
  --fc-page-bg-color: transparent;
  --fc-neutral-bg-color: rgba(255, 255, 255, 0.025);
  --fc-border-color: rgba(148, 163, 184, 0.15);
  --fc-today-bg-color: rgba(6, 182, 212, 0.07);
  --fc-now-indicator-color: #00d9ff;
  color: #cbd5e1;
}

:deep(.fc .fc-toolbar-title) {
  color: #f1f5f9;
  font-size: 1.2rem;
  font-weight: 600;
}

:deep(.fc .fc-col-header-cell-cushion),
:deep(.fc .fc-daygrid-day-number),
:deep(.fc .fc-timegrid-slot-label-cushion) {
  color: #94a3b8;
  text-decoration: none;
}

:deep(.fc .fc-timegrid-axis-cushion) {
  max-width: none;
}

:deep(.fc .fc-button) {
  border: 1px solid #304568;
  background: #17243b;
  color: #cbd5e1;
  box-shadow: none;
  text-transform: capitalize;
}

:deep(.fc .fc-button:hover),
:deep(.fc .fc-button-active) {
  border-color: #0891b2;
  background: #164e63;
}

:deep(.fc .fc-button:focus) {
  box-shadow: 0 0 0 2px rgba(34, 211, 238, 0.2);
}

:deep(.fc .fc-event) {
  position: relative;
  border-radius: 5px;
  padding: 2px 4px;
  cursor: pointer;
  transition: filter 160ms ease;
}

:deep(.fc .fc-event:hover) {
  filter: brightness(1.25);
  z-index: 20;
}

:deep(.fc .fc-daygrid-day-frame) {
  overflow: visible;
}

:deep(.fc .fc-daygrid-day-events) {
  position: relative;
  z-index: 2;
}

:global(.appointment-tooltip) {
  position: fixed;
  z-index: 9999;
  flex-direction: column;
  gap: 5px;
  width: max-content;
  max-width: min(260px, 75vw);
  max-height: 70vh;
  overflow-y: auto;
  padding: 12px 14px;
  border: 1px solid rgba(34, 211, 238, 0.4);
  border-radius: 10px;
  background: #0b1120;
  box-shadow: 0 10px 35px rgba(0, 0, 0, 0.4);
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.4;
  white-space: normal;
  display: none;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transition: opacity 150ms ease;
}

:global(.appointment-tooltip strong) {
  color: #f1f5f9;
  font-size: 13px;
}

@media (max-width: 640px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .new-appointment-button {
    align-self: stretch;
    justify-content: center;
  }

  .appointment-calendar {
    padding: 12px;
  }

  .section-heading h2 {
    font-size: 16px;
  }

  :deep(.fc .fc-toolbar) {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  :deep(.fc .fc-toolbar-title) {
    font-size: 1rem;
  }

  .appointment-dialog-header {
    padding: 20px 18px 16px;
  }

  .appointment-dialog-content {
    padding: 4px 18px 18px;
  }

  .appointment-dialog-footer {
    padding: 11px 18px;
  }

  .form-dialog-header,
  .cancel-dialog-header {
    padding: 18px;
  }

  .form-section {
    padding: 16px 18px;
  }

  .form-dialog-footer {
    padding: 12px 18px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-full {
    grid-column: auto;
  }

  .dialog-actions {
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .appointment-dialog-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .appointment-dialog-footer .dialog-actions {
    width: 100%;
  }
}

@media (max-width: 400px) {
  .appointment-info-grid {
    grid-template-columns: 1fr;
  }

  .appointment-reason-card {
    grid-column: auto;
  }

  .appointment-patient-avatar {
    width: 44px;
    height: 44px;
    flex-basis: 44px;
  }

  .appointment-patient-heading h2 {
    font-size: 17px;
  }

  .history-entry {
    flex-direction: column;
    gap: 3px;
  }

  .history-entry strong {
    text-align: left;
  }
}

@media (prefers-reduced-motion: reduce) {

  :deep(.fc .fc-event),
  :deep(.appointment-tooltip) {
    transition: none;
  }

  .appointment-form-dialog,
  .cancel-dialog {
    animation: none;
  }
}
</style>
