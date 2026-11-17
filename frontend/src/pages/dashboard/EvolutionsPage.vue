<template>
  <q-page class="q-pa-md tx-body">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">Evoluciones Clínicas</h1>
          <p class="tx-subtle text-sm">Historial cronológico de atenciones</p>
        </div>
        <q-select v-model="filtroPaciente" :options="opcionesPacientes" label="Filtrar por paciente" dense
          class="bg-main rounded-lg border border-theme min-w-[200px]" dark standout
          option-label="nombre" option-value="id" clearable emit-value map-options />
      </div>

      <div class="relative">
        <div class="absolute left-[17px] top-2 bottom-2 w-0.5 bg-gray-800"></div>

        <div v-for="evo in evolucionesFiltradas" :key="evo.id"
          class="relative flex items-start gap-4 mb-6 p-4 bg-card border border-theme rounded-xl hover:border-theme-accent transition-all">
          <div class="flex-shrink-0 w-9 h-9 rounded-full bg-[#e3bc50]/20 flex items-center justify-center z-10">
            <q-icon :name="iconoTipo(evo.tipo)" size="16px" class="text-[#e3bc50]" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex justify-between items-start gap-2">
              <div>
                <span class="tx-body text-sm font-bold">{{ nombrePaciente(evo.pacienteId) }}</span>
                <span class="tx-muted text-xs ml-2">{{ evo.profesional }}</span>
              </div>
              <span class="tx-muted text-xs font-mono whitespace-nowrap">{{ evo.fecha }}</span>
            </div>
            <p class="tx-body text-sm mt-2 leading-relaxed">{{ evo.descripcion }}</p>
            <q-badge :color="colorTipo(evo.tipo)" class="mt-2 text-[9px] capitalize">{{ evo.tipo }}</q-badge>
          </div>
        </div>
      </div>

      <div v-if="!evolucionesFiltradas.length" class="flex flex-col items-center justify-center p-12 bg-main rounded-lg border border-dashed border-theme">
        <q-icon name="timeline" size="3rem" class="tx-muted mb-3" />
        <p class="tx-muted text-sm">No hay evoluciones para mostrar</p>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed } from 'vue'
import { evoluciones, pacientes } from 'src/data/dummy.js'

const filtroPaciente = ref(null)

const opcionesPacientes = pacientes

const evolucionesFiltradas = computed(() => {
  if (!filtroPaciente.value) return [...evoluciones].reverse()
  return evoluciones.filter(e => e.pacienteId === filtroPaciente.value).reverse()
})

const nombrePaciente = (id) => {
  const p = pacientes.find(p => p.id === id)
  return p ? p.nombre : '—'
}

const iconoTipo = (tipo) => {
  const map = { limpieza: 'cleaning_services', revision: 'visibility', ortodoncia: 'braces', diagnostico: 'biotech', estetica: 'spa' }
  return map[tipo] || 'medical_services'
}

const colorTipo = (tipo) => {
  const map = { limpieza: 'positive', revision: 'info', ortodoncia: 'primary', diagnostico: 'warning', estetica: 'accent' }
  return map[tipo] || 'grey'
}
</script>
