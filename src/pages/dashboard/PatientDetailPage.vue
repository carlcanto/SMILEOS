<template>
  <q-page class="q-pa-md tx-body">
    <div class="max-w-7xl mx-auto">
      <div class="flex items-center gap-3 mb-6">
        <q-btn flat round icon="arrow_back" color="white" @click="$router.push('/dashboard/pacientes')" />
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">{{ paciente.nombre }}</h1>
          <p class="tx-subtle text-sm">{{ paciente.identificacion }} · {{ paciente.edad }} años</p>
        </div>
      </div>

      <q-tabs v-model="tab" dense no-caps inline-label class="rounded-2xl border border-theme-accent bg-card q-mb-md"
        active-color="primary" indicator-color="transparent">
        <q-tab name="admin" label="Administrativo" class="sidebar-item" />
        <q-tab name="clinico" label="Clínico" class="sidebar-item" />
      </q-tabs>

      <q-tab-panels v-model="tab" animated class="bg-transparent">
        <q-tab-panel name="admin" class="q-pa-none">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <q-card class="bg-card border border-theme-accent" flat>
              <q-card-section>
                <div class="text-[#e3bc50] font-bold mb-4 text-sm tracking-wide">DATOS GENERALES</div>
                <div class="space-y-3">
                  <div v-for="field in camposAdmin" :key="field.key" class="flex border-b border-theme pb-2">
                    <span class="tx-muted text-xs w-36 font-medium">{{ field.label }}</span>
                    <span class="tx-body text-sm">{{ paciente[field.key] || '-' }}</span>
                  </div>
                </div>
              </q-card-section>
            </q-card>

            <q-card class="bg-card border border-theme-accent" flat>
              <q-card-section>
                <div class="text-[#e3bc50] font-bold mb-4 text-sm tracking-wide">PRÓXIMAS CITAS</div>
                <div v-if="citasPaciente.length" class="space-y-2">
                  <div v-for="cita in citasPaciente" :key="cita.id"
                    class="flex justify-between items-center p-3 bg-main rounded-lg border border-theme">
                    <div>
                      <div class="tx-body text-sm font-medium">{{ cita.hora }}</div>
                      <div class="tx-subtle text-xs">{{ cita.tratamiento }}</div>
                    </div>
                    <q-badge :color="cita.estado === 'confirmada' ? 'positive' : cita.estado === 'pendiente' ? 'warning' : 'negative'">
                      {{ cita.estado }}
                    </q-badge>
                  </div>
                </div>
                <div v-else class="tx-muted text-sm italic">Sin citas programadas</div>
              </q-card-section>
            </q-card>
          </div>
        </q-tab-panel>

        <q-tab-panel name="clinico" class="q-pa-none">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <q-card class="bg-card border border-theme-accent" flat>
              <q-card-section>
                <div class="text-[#e3bc50] font-bold mb-4 text-sm tracking-wide">ÚLTIMAS EVOLUCIONES</div>
                <div v-if="evolucionesPaciente.length">
                  <div v-for="evo in evolucionesPaciente.slice(0, 3)" :key="evo.id"
                    class="flex items-start gap-3 p-3 border-l-2 border-[#e3bc50] mb-3 bg-main rounded-r-lg">
                    <div class="text-xs tx-muted w-20 font-mono">{{ evo.fecha }}</div>
                    <div>
                      <div class="tx-body text-xs font-medium">{{ evo.profesional }}</div>
                      <div class="tx-subtle text-xs mt-1">{{ evo.descripcion }}</div>
                    </div>
                  </div>
                </div>
                <div v-else class="tx-muted text-sm italic">Sin evoluciones registradas</div>
              </q-card-section>
            </q-card>

            <q-card class="bg-card border border-theme-accent" flat>
              <q-card-section>
                <div class="text-[#e3bc50] font-bold mb-4 text-sm tracking-wide">PLAN DE TRATAMIENTO</div>
                <div v-if="planPaciente.length">
                  <div v-for="fase in planPaciente" :key="fase.id"
                    class="flex items-center gap-3 p-3 mb-2 bg-main rounded-lg border border-theme">
                    <q-icon :name="iconoEstado(fase.estado)" :color="colorEstadoBadge(fase.estado)" size="18px" />
                    <div class="flex-1">
                      <div class="tx-body text-xs font-medium">{{ fase.fase }}</div>
                      <div class="tx-subtle text-xs">{{ fase.descripcion }}</div>
                    </div>
                    <q-badge :color="colorEstadoBadge(fase.estado)" class="text-[10px]">
                      {{ textoEstado(fase.estado) }}
                    </q-badge>
                  </div>
                </div>
                <div v-else class="tx-muted text-sm italic">Sin plan de tratamiento</div>
              </q-card-section>
            </q-card>
          </div>
        </q-tab-panel>
      </q-tab-panels>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { pacientes, citas, evoluciones, planesTratamiento } from 'src/data/dummy.js'

const route = useRoute()
const tab = ref('admin')

const pacienteId = computed(() => Number(route.params.id))
const paciente = computed(() => pacientes.find(p => p.id === pacienteId.value) || pacientes[0])

const citasPaciente = computed(() => citas.filter(c => c.pacienteId === pacienteId.value))
const evolucionesPaciente = computed(() => evoluciones.filter(e => e.pacienteId === pacienteId.value))
const planPaciente = computed(() => planesTratamiento.filter(p => p.pacienteId === pacienteId.value))

const camposAdmin = [
  { key: 'telefono', label: 'Teléfono' },
  { key: 'email', label: 'Email' },
  { key: 'direccion', label: 'Dirección' },
  { key: 'contactoEmergencia', label: 'Contacto Emergencia' },
  { key: 'aseguradora', label: 'Aseguradora' },
  { key: 'alergias', label: 'Alergias' },
  { key: 'notas', label: 'Notas' },
]

const iconoEstado = (estado) => {
  const map = { pendiente: 'hourglass_empty', en_proceso: 'sync', completado: 'check_circle', pospuesto: 'schedule' }
  return map[estado] || 'radio_button_unchecked'
}

const colorEstadoBadge = (estado) => {
  const map = { pendiente: 'warning', en_proceso: 'info', completado: 'positive', pospuesto: 'grey' }
  return map[estado] || 'grey'
}

const textoEstado = (estado) => {
  const map = { pendiente: 'Pendiente', en_proceso: 'En Proceso', completado: 'Completado', pospuesto: 'Pospuesto' }
  return map[estado] || estado
}
</script>

<style scoped>
.sidebar-item {
  padding: 8px 20px;
  border-radius: 10px;
  transition: all 0.2s;
  font-weight: 600;
}
</style>
