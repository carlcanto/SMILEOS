<template>
  <q-page class="patients-page futuristic-bg q-pa-md q-pa-lg-lg">
    <section class="page-heading">
      <div>
        <h1>Pacientes</h1>
        <p>Busca, consulta y administra las fichas de tus pacientes.</p>
      </div>
      <q-btn unelevated no-caps icon="person_add" label="Registrar paciente" class="primary-action"
        @click="openRegistration" />
    </section>

    <section class="patients-panel">
      <div class="section-heading">
        <div>
          <div class="eyebrow">Directorio</div>
          <h2>Búsqueda de pacientes</h2>
        </div>
        <q-badge class="patient-count">{{ patients.length }} registros</q-badge>
      </div>
      <q-input v-model="searchQuery" outlined dark clearable
        label="Buscar por nombre, apellido, cédula, código o teléfono"
        placeholder="Empieza a escribir para ver resultados" class="patient-search">
        <template #prepend><q-icon name="search" /></template>
      </q-input>

      <div v-if="searchQuery.trim()" class="patient-results" aria-live="polite">
        <div v-if="filteredPatients.length" class="results-caption">
          {{ filteredPatients.length }} {{ filteredPatients.length === 1 ? 'paciente encontrado' :
            'pacientesencontrados' }}
        </div>
        <button v-for="patient in filteredPatients" :key="patient.cedula" type="button" class="patient-row"
          @click="showPatientDetails(patient)">
          <q-avatar size="48px" class="result-avatar">
            <img v-if="patient.photo" :src="patient.photo" :alt="`Fotografía de ${fullName(patient)}`" />
            <q-icon v-else name="person" />
          </q-avatar>
          <div class="patient-main">
            <strong>{{ fullName(patient) }}</strong>
            <span>{{ patient.cedula }} <i>·</i> {{ patient.phone || 'Sin teléfono' }}</span>
          </div>
          <div class="patient-meta"><span>{{ ageOf(patient.birthDate) ?? '—' }} años</span><small>{{
            formatDate(patient.registeredAt) }}</small></div>
          <q-badge :class="['status-badge', patient.status === 'Activo' ? 'is-active' : 'is-inactive']">{{
            patient.status
          }}</q-badge>
          <q-icon name="chevron_right" class="row-chevron" />
        </button>
        <div v-if="!filteredPatients.length" class="empty-state">No se encontraron pacientes con esos datos.</div>
      </div>
      <div v-else class="empty-state">Ingresa un nombre, apellido, cédula o teléfono para buscar.</div>
    </section>

    <!-- Registro de paciente por secciones -->
    <q-dialog v-model="registrationDialog" maximized>
      <q-card class="registration-dialog">
        <header class="registration-header">
          <div>
            <div class="eyebrow">Nuevo registro</div>
            <h2>{{ editingCedula ? 'Editar paciente' : 'Ficha del paciente' }}</h2>
            <p v-if="editingCedula">Actualiza la información clínica y administrativa.</p>
            <p v-else>Completa la información clínica y administrativa.</p>

          </div>
          <q-btn round flat icon="close" aria-label="Cerrar registro" class="dialog-close" @click="closeRegistration" />
        </header>

        <q-tabs v-model="activeTab" align="left" dense no-caps class="registration-tabs" active-color="cyan-3"
          indicator-color="cyan-4" outside-arrows mobile-arrows>
          <q-tab name="personal" icon="badge" label="Datos personales" />
          <q-tab name="contact" icon="contact_phone" label="Contacto" />
          <q-tab name="emergency" icon="emergency" label="Emergencia" />
          <q-tab name="medical" icon="medical_information" label="Antecedentes médicos" />
          <q-tab name="dental" icon="dentistry" label="Antecedentes odontológicos" class="dental-tab" />
          <q-tab name="odontogram" icon="grid_view" label="Odontograma" class="dental-tab" />
          <q-tab name="consents" icon="fact_check" label="Consentimientos" />
          <q-tab name="admin" icon="manage_accounts" label="Administrativo" />
        </q-tabs>

        <q-form class="registration-form" @submit.prevent="savePatient">
          <q-tab-panels v-model="activeTab" animated class="registration-panels">
            <q-tab-panel name="personal">
              <div class="form-section-title"><span>01</span>
                <div>
                  <h3>Datos personales</h3>
                  <p>Identificación y datos demográficos del paciente.</p>
                </div>
              </div>
              <div class="form-grid">
                <q-input v-model.trim="form.cedula" outlined dark label="Cédula *" :rules="[requiredRule]"
                  @update:model-value="form.patientCode = form.cedula" />
                <q-input :model-value="form.cedula" outlined dark readonly
                  label="Código del paciente (igual a la cédula)" />
                <q-input v-model.trim="form.firstName" outlined dark label="Nombres *" :rules="[requiredRule]" />
                <q-input v-model.trim="form.lastName" outlined dark label="Apellidos *" :rules="[requiredRule]" />
                <q-input v-model="form.birthDate" outlined dark type="date" label="Fecha de nacimiento *"
                  :rules="[requiredRule]">
                  <template #append><q-icon name="event" /></template>
                </q-input>
                <q-input :model-value="ageOf(form.birthDate) ?? ''" outlined dark readonly label="Edad calculada"
                  suffix="años" />
                <q-select v-model="form.sex" outlined dark label="Sexo"
                  :options="['Femenino', 'Masculino', 'Otro', 'Prefiere no indicar']" />
                <q-input v-model.trim="form.nationality" outlined dark label="Nacionalidad" />
                <q-select v-model="form.maritalStatus" outlined dark label="Estado civil"
                  :options="['Soltero/a', 'Casado/a', 'Unión libre', 'Divorciado/a', 'Viudo/a', 'Otro']" />
                <q-input v-model.trim="form.occupation" outlined dark label="Ocupación" />
                <div class="photo-field">
                  <label for="patient-photo">Fotografía (opcional)</label>
                  <input id="patient-photo" type="file" accept="image/*" @change="onPhotoChange" />
                  <img v-if="photoPreview" :src="photoPreview" alt="Vista previa de fotografía" class="photo-preview" />
                </div>
              </div>
            </q-tab-panel>

            <q-tab-panel name="contact">
              <div class="form-section-title"><span>02</span>
                <div>
                  <h3>Información de contacto</h3>
                  <p>Medios para comunicarnos con el paciente.</p>
                </div>
              </div>
              <div class="form-grid">
                <q-input v-model.trim="form.phone" outlined dark label="Teléfono principal *" type="tel"
                  :rules="[requiredRule]" />
                <q-input v-model.trim="form.phoneSecondary" outlined dark label="Teléfono secundario" type="tel" />
                <q-input v-model.trim="form.email" outlined dark label="Correo electrónico" type="email" />
                <q-select v-model="form.province" outlined dark use-input label="Provincia" :options="provinceOptions"
                  @filter="filterProvinces" />
                <q-input v-model.trim="form.district" outlined dark label="Distrito" />
                <q-input v-model.trim="form.township" outlined dark label="Corregimiento" />
                <q-input v-model.trim="form.address" outlined dark label="Dirección completa" type="textarea" autogrow
                  class="full-width" />
              </div>
            </q-tab-panel>

            <q-tab-panel name="emergency">
              <div class="form-section-title"><span>03</span>
                <div>
                  <h3>Contacto de emergencia</h3>
                  <p>Persona a contactar en caso de emergencia.</p>
                </div>
              </div>
              <div class="form-grid">
                <q-input v-model.trim="form.emergencyName" outlined dark label="Nombre completo" />
                <q-input v-model.trim="form.emergencyRelationship" outlined dark label="Parentesco" />
                <q-input v-model.trim="form.emergencyPhone" outlined dark label="Teléfono principal" type="tel" />
                <q-input v-model.trim="form.emergencyPhoneAlt" outlined dark label="Teléfono alternativo (opcional)"
                  type="tel" />
              </div>
            </q-tab-panel>

            <q-tab-panel name="medical">
              <div class="form-section-title"><span>04</span>
                <div>
                  <h3>Antecedentes médicos</h3>
                  <p>Respuestas y detalles sobre la salud general.</p>
                </div>
              </div>
              <div class="form-grid">
                <q-select v-model="form.conditions" outlined dark multiple use-chips label="Condiciones médicas"
                  :options="conditionOptions" use-input new-value-mode="add-unique" class="full-width"
                  hint="Selecciona varias o escribe una condición personalizada." />
                <div class="yes-no-grid full-width">
                  <q-select v-model="form.hasDisease" outlined dark label="¿Padece alguna enfermedad?"
                    :options="yesNoOptions" />
                  <q-select v-model="form.hasAllergies" outlined dark label="¿Tiene alergias?"
                    :options="yesNoOptions" />
                  <q-select v-model="form.takesMedication" outlined dark label="¿Consume medicamentos actualmente?"
                    :options="yesNoOptions" />
                  <q-select v-model="form.hadSurgery" outlined dark label="¿Ha sido sometido/a a alguna cirugía?"
                    :options="yesNoOptions" />
                  <q-select v-model="form.hadHospitalization" outlined dark label="¿Ha tenido hospitalizaciones?"
                    :options="yesNoOptions" />
                  <q-select v-model="form.hasOtherCondition" outlined dark label="¿Presenta otra condición médica?"
                    :options="yesNoOptions" />
                </div>
                <q-input v-model.trim="form.allergyDescription" outlined dark label="Descripción de alergias"
                  type="textarea" autogrow />
                <q-input v-model.trim="form.medications" outlined dark label="Medicamentos actuales" type="textarea"
                  autogrow />
                <q-input v-model.trim="form.surgeries" outlined dark label="Descripción de cirugías" type="textarea"
                  autogrow />
                <q-input v-model.trim="form.hospitalizations" outlined dark label="Antecedentes de hospitalización"
                  type="textarea" autogrow />
                <q-input v-model.trim="form.medicalNotes" outlined dark label="Observaciones médicas" type="textarea"
                  autogrow class="full-width" />
              </div>
            </q-tab-panel>

            <q-tab-panel name="dental">
              <div class="form-section-title"><span>05</span>
                <div>
                  <h3>Antecedentes odontológicos</h3>
                  <p>Historial de tratamientos y estado de salud bucal.</p>
                </div>
              </div>
              <div class="form-grid">
                <q-select v-model="form.hadDentalTreatment" outlined dark
                  label="¿Ha recibido tratamientos odontológicos?" :options="yesNoOptions" />
                <q-input v-model="form.lastDentalVisit" outlined dark type="date"
                  label="Fecha de la última visita al odontólogo" />
                <q-select v-model="form.hadExtractions" outlined dark label="¿Ha tenido extracciones dentales?"
                  :options="yesNoOptions" />
                <q-select v-model="form.usedOrthodontics" outlined dark label="¿Ha utilizado ortodoncia?"
                  :options="yesNoOptions" />
                <q-select v-model="form.hasDentalPain" outlined dark label="¿Presenta dolor dental actualmente?"
                  :options="yesNoOptions" />
                <q-select v-model="form.hasSensitivity" outlined dark label="¿Presenta sensibilidad dental?"
                  :options="yesNoOptions" />
                <q-select v-model="form.hasGumBleeding" outlined dark label="¿Tiene sangrado de encías?"
                  :options="yesNoOptions" />
                <q-select v-model="form.hasOralProblem" outlined dark label="¿Presenta algún problema bucal?"
                  :options="yesNoOptions" />
                <q-input v-model.trim="form.dentalTreatments" outlined dark
                  label="Tratamientos odontológicos anteriores" type="textarea" autogrow />
                <q-input v-model.trim="form.oralProblems" outlined dark label="Problemas bucales actuales"
                  type="textarea" autogrow />
                <q-input v-model.trim="form.dentalNotes" outlined dark label="Observaciones odontológicas"
                  type="textarea" autogrow class="full-width" />
              </div>
            </q-tab-panel>

            <q-tab-panel name="odontogram">
              <div class="form-section-title"><span>06</span>
                <div>
                  <h3>Odontograma del paciente</h3>
                  <p>Registra el estado dental; se asociará al guardarse con la cédula indicada en datos personales.</p>
                </div>
              </div>
              <q-banner v-if="!form.cedula" rounded class="odontogram-notice">
                Ingresa primero la cédula del paciente en la pestaña «Datos personales» para abrir su odontograma.
              </q-banner>
              <div v-else class="odontogram-launch-card">
                <p>El odontograma quedará asociado a la cédula {{ form.cedula }} y guardará sus cambios automáticamente.
                </p>
                <q-btn unelevated no-caps label="Abrir odontograma" class="primary-action"
                  @click="openRegistrationOdontogram" />
              </div>
            </q-tab-panel>

            <q-tab-panel name="consents">
              <div class="form-section-title"><span>07</span>
                <div>
                  <h3>Consentimientos y documentación</h3>
                  <p>Registra la aceptación explícita y los documentos recibidos.</p>
                </div>
              </div>
              <div class="consent-list">
                <q-checkbox v-model="form.dataConsent" dark color="cyan-4"
                  label="Consentimiento para el tratamiento de datos personales" />
                <q-checkbox v-model="form.dentalConsent" dark color="cyan-4"
                  label="Consentimiento informado para procedimientos odontológicos" />
                <q-checkbox v-model="form.guardianConsent" dark color="cyan-4"
                  label="Autorización del padre, madre o tutor legal (cuando corresponda)" />
              </div>
              <div class="consent-date-row">
                <q-input v-model="form.consentAcceptedAt" outlined dark type="date" label="Fecha de aceptación" />
                <p>Las casillas no se marcan automáticamente. Marca cada consentimiento solo después de recibir la
                  aceptación correspondiente.</p>
              </div>
              <div class="attachment-field">
                <label for="patient-documents">Documentos adjuntos</label>
                <input id="patient-documents" type="file" multiple @change="onDocumentsChange" />
                <div v-if="form.documents.length" class="file-list"><span v-for="file in form.documents" :key="file">{{
                  file
                    }}</span></div>
              </div>
            </q-tab-panel>

            <q-tab-panel name="admin">
              <div class="form-section-title"><span>08</span>
                <div>
                  <h3>Información administrativa</h3>
                  <p>Estado y clasificación del registro.</p>
                </div>
              </div>
              <div class="form-grid">
                <q-input :model-value="form.cedula || 'Se genera con la cédula'" outlined dark readonly
                  label="Código único del paciente" />
                <q-input :model-value="formatDate(form.registeredAt)" outlined dark readonly
                  label="Fecha de registro automática" />
                <q-select v-model="form.status" outlined dark label="Estado del paciente"
                  :options="['Activo', 'Inactivo']" />
                <q-select v-model="form.patientType" outlined dark label="Tipo de paciente"
                  :options="['Nuevo', 'Recurrente']" />
                <q-input v-model.trim="form.registeredBy" outlined dark label="Usuario que realizó el registro" />
                <q-input v-model.trim="form.adminNotes" outlined dark label="Observaciones generales" type="textarea"
                  autogrow class="full-width" />
              </div>
            </q-tab-panel>
          </q-tab-panels>

          <footer class="registration-footer">
            <div class="footer-hint">Los campos con * son obligatorios.</div>
            <div class="footer-actions">
              <q-btn flat no-caps label="Cancelar" class="cancel-action" @click="closeRegistration" />
              <q-btn v-if="activeTab !== 'personal'" flat no-caps icon="arrow_back" label="Anterior"
                class="secondary-action" @click="goPrevious" />
              <q-btn v-if="activeTab !== 'admin'" unelevated no-caps icon-right="arrow_forward" label="Siguiente"
                class="primary-action" @click="goNext" />
              <q-btn v-else unelevated no-caps icon="save" label="Guardar paciente" type="submit"
                class="primary-action" />
            </div>
          </footer>
        </q-form>
      </q-card>
    </q-dialog>

    <!-- Ficha individual -->
    <q-dialog v-model="detailsDialog">
      <q-card v-if="selectedPatient" class="patient-dialog">
        <q-card-section class="patient-dialog-header flex items-start justify-between gap-4">
          <div class="flex items-center gap-3">
            <q-avatar size="52px" class="patient-dialog-avatar"><img v-if="selectedPatient.photo"
                :src="selectedPatient.photo" :alt="fullName(selectedPatient)" /><q-icon v-else
                name="person" /></q-avatar>
            <div>
              <div class="patient-dialog-kicker">Ficha del paciente</div>
              <h2 class="patient-dialog-name">{{ fullName(selectedPatient) }}</h2>
            </div>
          </div>
          <q-btn round flat dense icon="close" aria-label="Cerrar" class="dialog-close" v-close-popup />
        </q-card-section>
        <q-card-section class="profile-content">
          <div class="profile-summary">
            <div><span>Código del paciente</span><strong>{{ selectedPatient.cedula }}</strong></div>
            <div><span>Cédula</span><strong>{{ selectedPatient.cedula }}</strong></div>
            <div><span>Edad</span><strong>{{ ageOf(selectedPatient.birthDate) ?? '—' }} años</strong></div>
            <div><span>Estado</span><strong>{{ selectedPatient.status }}</strong></div>
            <div><span>Teléfono</span><strong>{{ selectedPatient.phone || '—' }}</strong></div>
            <div><span>Fecha de registro</span><strong>{{ formatDate(selectedPatient.registeredAt) }}</strong></div>
          </div>
          <div v-for="group in profileGroups" :key="group.title" class="profile-group">
            <h3>{{ group.title }}</h3>
            <div class="profile-fields">
              <div v-for="item in group.fields" :key="item.label" class="profile-field">
                <span>{{ item.label }}</span><strong>{{ displayValue(selectedPatient[item.key]) }}</strong>
              </div>
            </div>
          </div>
          <div class="profile-group clinical-history-group">
            <h3>Historial de evoluciones</h3>
            <div v-if="patientEvolutionHistory.length" class="clinical-history-list">
              <article v-for="evolution in patientEvolutionHistory" :key="evolution.id" class="clinical-history-item">
                <div class="clinical-history-date">{{ formatDate(evolution.date) }}</div>
                <div class="clinical-history-copy">
                  <strong>{{ evolution.reason }} · {{ evolution.dentistName }}</strong>
                  <span>{{ evolution.procedure }}</span>
                  <small>Hallazgos: {{ evolution.findings }}</small>
                </div>
                <q-icon name="verified" class="history-validated" />
              </article>
            </div>
            <div v-else class="clinical-history-empty">Aún no hay evoluciones clínicas registradas.</div>
          </div>
        </q-card-section>
        <q-card-actions class="patient-dialog-actions" align="between"><span class="record-id">REGISTRO · {{
          selectedPatient.cedula }}</span><q-btn unelevated no-caps label="Listo" icon-right="arrow_forward"
            class="dialog-action" v-close-popup />
          <q-btn flat no-caps icon="edit" label="Editar" class="edit-action" @click="editPatient" />
          <q-btn flat no-caps label="Odontograma" class="edit-action" @click="openOdontogram" />
        </q-card-actions>
      </q-card>
    </q-dialog>
    <q-dialog v-model="odontogramDialog" maximized>
      <q-card class="odontogram-dialog">
        <header class="odontogram-header">
          <div class="odontogram-patient">
            <div>
              <div class="eyebrow">Odontograma individual</div>
              <h2>{{ odontogramPatientName }}</h2>
              <span>Cédula: {{ odontogramPatientCedula }}</span>
            </div>
          </div>
          <q-btn round flat icon="close" aria-label="Cerrar odontograma" class="dialog-close" v-close-popup />
        </header>
        <iframe v-if="odontogramPatientCedula" :key="odontogramPatientCedula" :src="odontogramUrl"
          title="Odontograma del paciente" class="odontogram-frame" />
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

const STORAGE_KEY = 'smileos-patients'
const today = () => new Date().toISOString().slice(0, 10)
const makeForm = () => ({
  patientCode: '', cedula: '', firstName: '', lastName: '', birthDate: '', sex: '', nationality: '', maritalStatus: '', occupation: '',
  photo: '', phone: '', phoneSecondary: '', email: '', province: '', district: '', township: '', address: '',
  emergencyName: '', emergencyRelationship: '', emergencyPhone: '', emergencyPhoneAlt: '',
  conditions: [], hasDisease: '', hasAllergies: '', takesMedication: '', hadSurgery: '', hadHospitalization: '', hasOtherCondition: '',
  allergyDescription: '', medications: '', surgeries: '', hospitalizations: '', medicalNotes: '',
  hadDentalTreatment: '', lastDentalVisit: '', hadExtractions: '', usedOrthodontics: '', hasDentalPain: '', hasSensitivity: '', hasGumBleeding: '', hasOralProblem: '', dentalTreatments: '', oralProblems: '', dentalNotes: '',
  dataConsent: false, dentalConsent: false, guardianConsent: false, consentAcceptedAt: '', documents: [],
  registeredAt: today(), status: 'Activo', patientType: 'Nuevo', registeredBy: '', adminNotes: '',
})

const patients = ref([
  { ...makeForm(), firstName: 'María', lastName: 'González', name: 'María González', cedula: '8-123-456', patientCode: '8-123-456', phone: '6000-1234', birthDate: '1990-05-12', registeredAt: '2025-01-15' },
  { ...makeForm(), firstName: 'Carlos', lastName: 'Rodríguez', name: 'Carlos Rodríguez', cedula: '8-234-567', patientCode: '8-234-567', phone: '6000-2345', birthDate: '1985-09-03', registeredAt: '2025-02-02' },
  { ...makeForm(), firstName: 'Ana', lastName: 'Martínez', name: 'Ana Martínez', cedula: '8-345-678', patientCode: '8-345-678', phone: '6000-3456', birthDate: '2000-02-20', registeredAt: '2025-03-11' },
  { ...makeForm(), firstName: 'José', lastName: 'Pérez', name: 'José Pérez', cedula: '8-456-789', patientCode: '8-456-789', phone: '6000-4567', birthDate: '1978-12-05', registeredAt: '2025-04-23' },
  { ...makeForm(), firstName: 'Lucía', lastName: 'Torres', name: 'Lucía Torres', cedula: '8-567-890', patientCode: '8-567-890', phone: '6000-5678', birthDate: '1995-07-17', registeredAt: '2025-05-08' },
  { ...makeForm(), firstName: 'Pedro', lastName: 'Castillo', name: 'Pedro Castillo', cedula: '8-678-901', patientCode: '8-678-901', phone: '6000-6789', birthDate: '1968-03-29', registeredAt: '2025-06-19' },
])
const searchQuery = ref('')
const selectedPatient = ref(null)
const patientEvolutionHistory = ref([])
const detailsDialog = ref(false)
const registrationDialog = ref(false)
const odontogramDialog = ref(false)
const odontogramPatientName = ref('')
const odontogramPatientCedula = ref('')
const editingCedula = ref(null)
const activeTab = ref('personal')
const form = reactive(makeForm())
const photoPreview = ref('')
const odontogramUrl = computed(() => odontogramPatientCedula.value
  ? `/odontograma/odontograma.html?paciente=${encodeURIComponent(odontogramPatientCedula.value)}`
  : '')
const yesNoOptions = ['Sí', 'No']
const conditionOptions = ['Diabetes', 'Hipertensión arterial', 'Enfermedades cardíacas', 'Asma', 'Epilepsia', 'Trastornos de coagulación', 'Enfermedades renales', 'Enfermedades hepáticas', 'Otras']
const provinces = ['Bocas del Toro', 'Coclé', 'Colón', 'Chiriquí', 'Darién', 'Herrera', 'Los Santos', 'Panamá', 'Panamá Oeste', 'Veraguas', 'Comarca Guna Yala', 'Comarca Emberá-Wounaan', 'Comarca Ngäbe-Buglé']
const provinceOptions = ref(provinces)
const tabs = ['personal', 'contact', 'emergency', 'medical', 'dental', 'odontogram', 'consents', 'admin']
const requiredRule = (value) => Boolean(value) || 'Este campo es obligatorio'
const profileGroups = [
  { title: 'Datos personales', fields: [{ label: 'Sexo', key: 'sex' }, { label: 'Nacionalidad', key: 'nationality' }, { label: 'Estado civil', key: 'maritalStatus' }, { label: 'Ocupación', key: 'occupation' }] },
  { title: 'Información de contacto', fields: [{ label: 'Teléfono secundario', key: 'phoneSecondary' }, { label: 'Correo electrónico', key: 'email' }, { label: 'Provincia', key: 'province' }, { label: 'Distrito', key: 'district' }, { label: 'Corregimiento', key: 'township' }, { label: 'Dirección', key: 'address' }] },
  { title: 'Contacto de emergencia', fields: [{ label: 'Nombre', key: 'emergencyName' }, { label: 'Parentesco', key: 'emergencyRelationship' }, { label: 'Teléfono', key: 'emergencyPhone' }, { label: 'Teléfono alternativo', key: 'emergencyPhoneAlt' }] },
  { title: 'Antecedentes médicos', fields: [{ label: 'Condiciones', key: 'conditions' }, { label: 'Enfermedades', key: 'hasDisease' }, { label: 'Alergias', key: 'allergyDescription' }, { label: 'Medicamentos', key: 'medications' }, { label: 'Cirugías', key: 'surgeries' }, { label: 'Hospitalizaciones', key: 'hospitalizations' }, { label: 'Observaciones', key: 'medicalNotes' }] },
  { title: 'Antecedentes odontológicos', fields: [{ label: 'Tratamientos anteriores', key: 'dentalTreatments' }, { label: 'Última visita', key: 'lastDentalVisit' }, { label: 'Extracciones', key: 'hadExtractions' }, { label: 'Ortodoncia', key: 'usedOrthodontics' }, { label: 'Dolor dental', key: 'hasDentalPain' }, { label: 'Sensibilidad', key: 'hasSensitivity' }, { label: 'Sangrado de encías', key: 'hasGumBleeding' }, { label: 'Problemas bucales', key: 'oralProblems' }, { label: 'Observaciones', key: 'dentalNotes' }] },
  { title: 'Consentimientos y documentación', fields: [{ label: 'Tratamiento de datos', key: 'dataConsent' }, { label: 'Consentimiento odontológico', key: 'dentalConsent' }, { label: 'Autorización de tutor', key: 'guardianConsent' }, { label: 'Fecha de aceptación', key: 'consentAcceptedAt' }, { label: 'Documentos', key: 'documents' }] },
  { title: 'Información administrativa', fields: [{ label: 'Tipo de paciente', key: 'patientType' }, { label: 'Registrado por', key: 'registeredBy' }, { label: 'Observaciones generales', key: 'adminNotes' }] },
]

onMounted(() => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try { patients.value = JSON.parse(saved) } catch { localStorage.removeItem(STORAGE_KEY) }
  }
})
watch(patients, (value) => localStorage.setItem(STORAGE_KEY, JSON.stringify(value)), { deep: true })

function normalize(value) {
  return String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').trim()
}
function fullName(patient) { return patient.name || `${patient.firstName || ''} ${patient.lastName || ''}`.trim() || 'Paciente' }
function ageOf(date) {
  if (!date) return null
  const birth = new Date(`${date}T00:00:00`)
  if (Number.isNaN(birth.getTime())) return null
  const now = new Date()
  let age = now.getFullYear() - birth.getFullYear()
  if (now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())) age -= 1
  return age >= 0 ? age : null
}
function formatDate(date) {
  if (!date) return '—'
  const parsed = new Date(`${date}T00:00:00`)
  return Number.isNaN(parsed.getTime()) ? date : new Intl.DateTimeFormat('es-PA', { dateStyle: 'medium' }).format(parsed)
}
function displayValue(value) {
  if (Array.isArray(value)) return value.length ? value.join(', ') : '—'
  if (typeof value === 'boolean') return value ? 'Aceptado' : 'No aceptado'
  return value || '—'
}
const filteredPatients = computed(() => {
  const query = normalize(searchQuery.value)
  if (!query) return []
  return patients.value.filter((patient) => normalize(`${patient.patientCode} ${patient.cedula} ${patient.firstName} ${patient.lastName} ${fullName(patient)} ${patient.phone} ${patient.phoneSecondary}`).includes(query))
})
function showPatientDetails(patient) {
  selectedPatient.value = patient
  try {
    const savedEvolutions = JSON.parse(localStorage.getItem('smileos-evolutions') || '[]')
    patientEvolutionHistory.value = Array.isArray(savedEvolutions)
      ? savedEvolutions
        .filter((evolution) => String(evolution.patientId) === String(patient.cedula)
          || String(evolution.patientCedula) === String(patient.cedula))
        .sort((a, b) => String(b.date).localeCompare(String(a.date)))
      : []
  } catch (error) {
    patientEvolutionHistory.value = []
    console.error('No se pudo cargar el historial clínico del paciente', error)
  }
  detailsDialog.value = true
}
function openOdontogram() {
  if (!selectedPatient.value) return
  odontogramPatientName.value = fullName(selectedPatient.value)
  odontogramPatientCedula.value = selectedPatient.value.cedula
  detailsDialog.value = false
  odontogramDialog.value = true
}
function openRegistrationOdontogram() {
  if (!form.cedula) return
  odontogramPatientName.value = `${form.firstName} ${form.lastName}`.trim() || 'Paciente nuevo'
  odontogramPatientCedula.value = form.cedula
  odontogramDialog.value = true
}
function openRegistration() {
  editingCedula.value = null
  Object.assign(form, makeForm(), { registeredAt: today() })
  photoPreview.value = ''
  activeTab.value = 'personal'
  registrationDialog.value = true
}
function closeRegistration() { registrationDialog.value = false }
function editPatient() {
  if (!selectedPatient.value) return
  editingCedula.value = selectedPatient.value.cedula
  Object.assign(form, makeForm(), JSON.parse(JSON.stringify(selectedPatient.value)))
  form.patientCode = form.cedula
  photoPreview.value = form.photo || ''
  activeTab.value = 'personal'
  detailsDialog.value = false
  registrationDialog.value = true
}
function goNext() { activeTab.value = tabs[Math.min(tabs.indexOf(activeTab.value) + 1, tabs.length - 1)] }
function goPrevious() { activeTab.value = tabs[Math.max(tabs.indexOf(activeTab.value) - 1, 0)] }
function filterProvinces(value, update) {
  update(() => {
    const query = normalize(value)
    provinceOptions.value = query ? provinces.filter((province) => normalize(province).includes(query)) : provinces
  })
}
function onPhotoChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => { form.photo = String(reader.result); photoPreview.value = form.photo }
  reader.readAsDataURL(file)
}
function onDocumentsChange(event) { form.documents = Array.from(event.target.files || []).map((file) => file.name) }
function savePatient() {
  if (!form.cedula || !form.firstName || !form.lastName || !form.birthDate || !form.phone) {
    activeTab.value = !form.cedula || !form.firstName || !form.lastName || !form.birthDate ? 'personal' : 'contact'
    return
  }
  if (patients.value.some((patient) => patient.cedula === form.cedula && patient.cedula !== editingCedula.value)) {
    window.alert('Ya existe un paciente registrado con esa cédula.')
    activeTab.value = 'personal'
    return
  }
  form.patientCode = form.cedula
  const wasEditing = Boolean(editingCedula.value)
  const savedPatient = { ...JSON.parse(JSON.stringify(form)), name: `${form.firstName} ${form.lastName}`.trim() }
  if (wasEditing) {
    const index = patients.value.findIndex((patient) => patient.cedula === editingCedula.value)
    if (index !== -1) patients.value.splice(index, 1, savedPatient)
    selectedPatient.value = savedPatient
    editingCedula.value = null
  } else {
    patients.value.unshift(savedPatient)
  }
  searchQuery.value = form.cedula
  registrationDialog.value = false
  window.alert(wasEditing ? 'Paciente actualizado correctamente.' : 'Paciente registrado correctamente.')
}
</script>

<style scoped>
.patients-page {
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

.page-heading p,
.registration-header p {
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

.primary-action {
  min-height: 42px;
  padding: 0 16px;
  border: 1px solid rgba(34, 211, 238, .45);
  border-radius: 9px;
  background: linear-gradient(120deg, rgba(8, 145, 178, .35), rgba(8, 145, 178, .14));
  color: #a5f3fc;
}

.primary-action:hover {
  background: rgba(8, 145, 178, .38);
}

.patients-panel {
  max-width: 1120px;
  margin: auto;
  padding: 24px;
  border: 1px solid rgba(100, 140, 190, .22);
  border-radius: 18px;
  background: rgba(16, 19, 31, .84);
  box-shadow: 0 0 35px rgba(37, 99, 235, .06);
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

.patient-count {
  border: 1px solid rgba(34, 211, 238, .2);
  border-radius: 20px;
  background: rgba(8, 145, 178, .12);
  color: #67e8f9;
}

.patient-search :deep(.q-field__control) {
  border-radius: 10px;
}

.patient-results {
  margin-top: 20px;
}

.results-caption {
  margin-bottom: 9px;
  color: #94a3b8;
  font-size: 12px;
}

.patient-row {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 14px;
  margin-top: 8px;
  padding: 13px 15px;
  border: 1px solid rgba(100, 140, 190, .16);
  border-radius: 12px;
  background: rgba(23, 36, 59, .62);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color .15s, background .15s;
}

.patient-row:hover,
.patient-row:focus-visible {
  border-color: rgba(34, 211, 238, .5);
  background: rgba(23, 45, 68, .86);
  outline: none;
}

.result-avatar {
  flex: 0 0 auto;
  border: 1px solid rgba(103, 232, 249, .26);
  background: rgba(8, 145, 178, .15);
  color: #67e8f9;
}

.patient-main {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 4px;
}

.patient-main strong {
  overflow: hidden;
  color: #f1f5f9;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.patient-main span {
  color: #94a3b8;
  font-size: 12px;
}

.patient-main i {
  padding: 0 4px;
  color: #475569;
  font-style: normal;
}

.patient-meta {
  display: flex;
  min-width: 90px;
  flex-direction: column;
  gap: 3px;
  color: #cbd5e1;
  font-size: 12px;
}

.patient-meta small {
  color: #64748b;
  font-size: 10px;
}

.status-badge {
  border: 1px solid transparent;
  border-radius: 20px;
  font-size: 10px;
}

.is-active {
  border-color: rgba(34, 197, 94, .2);
  background: rgba(34, 197, 94, .1);
  color: #86efac;
}

.is-inactive {
  border-color: rgba(248, 113, 113, .2);
  background: rgba(248, 113, 113, .1);
  color: #fca5a5;
}

.row-chevron {
  color: #64748b;
}

.empty-state {
  margin-top: 16px;
  padding: 22px;
  border: 1px dashed rgba(148, 163, 184, .23);
  border-radius: 12px;
  color: #94a3b8;
  text-align: center;
  font-size: 13px;
}

.registration-dialog {
  display: flex;
  width: 100%;
  height: 100%;
  flex-direction: column;
  overflow: hidden;
  border-radius: 0;
  background: #0b1120;
  color: #e2e8f0;
}

.registration-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 24px 30px 18px;
  border-bottom: 1px solid rgba(100, 140, 190, .14);
  background: radial-gradient(ellipse at 8% 0%, rgba(8, 145, 178, .14), transparent 55%);
}

.registration-header h2 {
  margin: 5px 0;
  color: #f8fafc;
  font-size: 23px;
  font-weight: 700;
}

.dialog-close {
  color: #94a3b8;
}

.registration-tabs {
  flex: 0 0 auto;
  min-height: 58px;
  padding: 0 18px;
  border-bottom: 1px solid rgba(100, 140, 190, .15);
  background: rgba(15, 23, 42, .72);
}

.registration-tabs :deep(.q-tab) {
  min-height: 58px;
  color: #94a3b8;
  font-size: 11px;
}

.registration-tabs :deep(.q-tab--active) {
  color: #a5f3fc;
}

.registration-tabs :deep(.dental-tab .q-tab__content) {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  text-align: center;
}

.registration-form {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
}

.registration-panels {
  min-height: 0;
  flex: 1;
  background: transparent;
}

.registration-panels :deep(.q-tab-panel) {
  max-width: 1050px;
  margin: auto;
  padding: 28px 32px;
}

.form-section-title {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
}

.form-section-title>span {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid rgba(34, 211, 238, .28);
  border-radius: 12px;
  background: rgba(8, 145, 178, .12);
  color: #67e8f9;
  font-size: 12px;
  font-weight: 700;
}

.form-section-title h3 {
  margin: 0 0 4px;
  color: #f1f5f9;
  font-size: 17px;
  font-weight: 650;
}

.form-section-title p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.form-grid :deep(.q-field__control) {
  border-radius: 9px;
}

.full-width {
  grid-column: 1 / -1;
}

.yes-no-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.photo-field,
.attachment-field {
  display: flex;
  flex-direction: column;
  gap: 9px;
  color: #94a3b8;
  font-size: 12px;
}

.photo-field input,
.attachment-field input {
  width: 100%;
  padding: 10px;
  border: 1px dashed rgba(148, 163, 184, .26);
  border-radius: 8px;
  color: #94a3b8;
}

.photo-preview {
  width: 78px;
  height: 78px;
  border: 1px solid rgba(34, 211, 238, .3);
  border-radius: 12px;
  object-fit: cover;
}

.consent-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  border: 1px solid rgba(100, 140, 190, .16);
  border-radius: 12px;
  background: rgba(15, 23, 42, .55);
}

.consent-date-row {
  display: grid;
  grid-template-columns: minmax(220px, .7fr) 1.3fr;
  align-items: center;
  gap: 18px;
  margin: 18px 0;
}

.consent-date-row p {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.5;
}

.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.file-list span {
  padding: 5px 9px;
  border: 1px solid rgba(34, 211, 238, .18);
  border-radius: 20px;
  color: #a5f3fc;
}

.odontogram-notice {
  border: 1px solid rgba(34, 211, 238, .2);
  border-radius: 10px;
  background: rgba(8, 145, 178, .1);
  color: #a5f3fc;
}

.odontogram-launch-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px;
  border: 1px solid rgba(34, 211, 238, .2);
  border-radius: 12px;
  background: rgba(15, 38, 58, .55);
}

.odontogram-launch-card p {
  margin: 0;
  color: #cbd5e1;
  font-size: 13px;
  line-height: 1.5;
}

.registration-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 30px;
  border-top: 1px solid rgba(100, 140, 190, .15);
  background: rgba(2, 6, 23, .46);
}

.footer-hint {
  color: #64748b;
  font-size: 11px;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cancel-action,
.secondary-action {
  color: #94a3b8;
}

.patient-dialog {
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  width: 100%;
  max-width: 760px;
  max-height: 90vh;
  border: 1px solid rgba(34, 211, 238, .32);
  border-radius: 18px;
  background: radial-gradient(ellipse at 10% 0%, rgba(8, 145, 178, .19), transparent 48%), #0b1120;
  color: #e2e8f0;
  box-shadow: 0 24px 80px rgba(0, 0, 0, .6), 0 0 38px rgba(6, 182, 212, .12);
}

.patient-dialog-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex: 0 0 auto;
  padding: 24px 24px 20px;
}

.patient-dialog-header>div:first-child {
  min-width: 0;
  flex: 1 1 auto;
}

.patient-dialog-avatar {
  flex: 0 0 52px;
  overflow: hidden;
  border: 1px solid rgba(103, 232, 249, .38);
  background: rgba(8, 145, 178, .17);
  color: #67e8f9;
}

.patient-dialog-kicker {
  color: #67e8f9;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .18em;
  text-transform: uppercase;
}

.patient-dialog-name {
  overflow-wrap: anywhere;
  margin: 5px 0 0;
  color: #f8fafc;
  font-size: 20px;
  font-weight: 650;
  line-height: 1.25;
}

.profile-content {
  min-height: 0;
  flex: 1 1 auto;
  max-height: none;
  overflow: auto;
  padding: 0 24px 20px;
}

.profile-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.profile-summary>div,
.profile-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
  padding: 12px;
  border: 1px solid rgba(34, 211, 238, .13);
  border-radius: 10px;
  background: rgba(15, 38, 58, .55);
}

.profile-summary span,
.profile-field span {
  color: #64748b;
  font-size: 10px;
  letter-spacing: .05em;
}

.profile-summary strong,
.profile-field strong {
  overflow-wrap: anywhere;
  color: #dbeafe;
  font-size: 12px;
  font-weight: 550;
}

.profile-group {
  margin-top: 18px;
}

.profile-group h3 {
  margin: 0 0 9px;
  color: #67e8f9;
  font-size: 11px;
  letter-spacing: .12em;
  text-transform: uppercase;
}

.profile-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.clinical-history-list { display: flex; flex-direction: column; gap: 8px; }
.clinical-history-item { display: flex; align-items: flex-start; gap: 12px; padding: 12px; border: 1px solid rgba(34, 211, 238, .14); border-radius: 10px; background: rgba(15, 38, 58, .48); }
.clinical-history-date { flex: 0 0 92px; color: #67e8f9; font-size: 10px; }
.clinical-history-copy { display: flex; min-width: 0; flex: 1; flex-direction: column; gap: 4px; }
.clinical-history-copy strong { color: #e2e8f0; font-size: 11px; font-weight: 550; }
.clinical-history-copy span,.clinical-history-copy small { color: #94a3b8; font-size: 10px; line-height: 1.45; }
.history-validated { color: #4ade80; font-size: 17px; }
.clinical-history-empty { padding: 14px; border: 1px dashed rgba(100, 140, 190, .2); border-radius: 9px; color: #718096; font-size: 11px; }

.patient-dialog-actions {
  display: flex;
  flex-wrap: wrap;
  flex: 0 0 auto;
  min-height: 62px;
  padding: 12px 24px;
  border-top: 1px solid rgba(100, 140, 190, .14);
  background: rgba(2, 6, 23, .35);
}

.patient-dialog-actions :deep(.q-btn) {
  margin-left: 8px;
}

.edit-action {
  margin-right: 8px;
  border: 1px solid rgba(148, 163, 184, .2);
  border-radius: 8px;
  color: #cbd5e1;
}

.edit-action:hover {
  border-color: rgba(34, 211, 238, .35);
  background: rgba(8, 145, 178, .12);
  color: #a5f3fc;
}

.record-id {
  color: #64748b;
  font-size: 9px;
  letter-spacing: .12em;
}

.dialog-action {
  border: 1px solid rgba(34, 211, 238, .42);
  border-radius: 8px;
  background: rgba(8, 145, 178, .18);
  color: #a5f3fc;
}

.odontogram-dialog {
  display: flex;
  width: 100%;
  height: 100%;
  flex-direction: column;
  overflow: hidden;
  background: #0b1120;
  color: #e2e8f0;
}

.odontogram-header {
  display: flex;
  min-height: 84px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 24px;
  border-bottom: 1px solid rgba(100, 140, 190, .17);
  background: rgba(15, 23, 42, .95);
}

.odontogram-patient {
  display: flex;
  min-width: 0;
  flex: 1 1 auto;
  align-items: center;
  gap: 14px;
  color: #67e8f9;
}

.odontogram-patient>.q-icon {
  position: static;
  flex: 0 0 24px;
}

.odontogram-patient>div {
  min-width: 0;
}

.odontogram-patient h2 {
  overflow-wrap: anywhere;
  margin: 3px 0;
  color: #f8fafc;
  font-size: 16px;
  line-height: 1.3;
}

.odontogram-patient span {
  color: #94a3b8;
  font-size: 11px;
}

.odontogram-frame {
  width: 100%;
  min-height: 0;
  flex: 1;
  border: 0;
  background: #fff;
}

@media (max-width: 700px) {
  .page-heading {
    align-items: flex-start;
  }

  .page-heading .primary-action {
    flex: 0 0 auto;
    font-size: 11px;
  }

  .patients-panel {
    padding: 17px;
  }

  .patient-row {
    gap: 10px;
    padding: 11px;
  }

  .patient-meta {
    display: none;
  }

  .registration-header {
    padding: 18px;
  }

  .registration-panels :deep(.q-tab-panel) {
    padding: 22px 18px;
  }

  .form-grid,
  .yes-no-grid {
    grid-template-columns: 1fr;
  }

  .full-width {
    grid-column: auto;
  }

  .consent-date-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .odontogram-launch-card {
    align-items: stretch;
    flex-direction: column;
  }

  .registration-footer {
    align-items: flex-start;
    flex-direction: column;
    padding: 12px 18px;
  }

  .footer-actions {
    width: 100%;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .profile-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .odontogram-header {
    padding: 12px 16px;
  }
}

@media (max-width: 430px) {
  .page-heading {
    flex-direction: column;
  }

  .patient-row .status-badge {
    display: none;
  }

  .profile-fields {
    grid-template-columns: 1fr;
  }
}
</style>
