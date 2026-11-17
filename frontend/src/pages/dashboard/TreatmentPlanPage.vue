<template>
  <q-page class="q-pa-md tx-body">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">Plan de Tratamiento</h1>
          <p class="tx-subtle text-sm">Gestión de planes por fases</p>
        </div>
        <q-select v-model="filtroPaciente" :options="opcionesPacientes" label="Filtrar por paciente" dense
          class="bg-main rounded-lg border border-theme min-w-[200px]" dark standout
          option-label="nombre" option-value="id" clearable emit-value map-options />
      </div>

      <div v-if="!filtroPaciente" class="flex flex-col items-center justify-center p-16 bg-card rounded-xl border border-dashed border-theme">
        <q-icon name="assignment" size="4rem" class="tx-muted mb-3" />
        <p class="tx-subtle text-lg font-medium">Selecciona un paciente</p>
        <p class="tx-muted text-sm mt-1">Para ver su plan de tratamiento</p>
      </div>

      <template v-else>
        <div class="mb-6">
          <div class="tx-body text-lg font-bold mb-1">{{ nombrePaciente(filtroPaciente) }}</div>
          <div class="flex gap-4 text-xs tx-muted">
            <span>Total fases: {{ planPaciente.length }}</span>
            <span>Completadas: {{ planPaciente.filter(p => p.estado === 'completado').length }}</span>
            <span>En progreso: {{ planPaciente.filter(p => p.estado === 'en_proceso').length }}</span>
          </div>
        </div>

        <div class="space-y-3">
          <div v-for="(fase, index) in planPaciente" :key="fase.id"
            class="bg-card border border-theme rounded-xl overflow-hidden hover:border-theme-accent transition-all">
            <div class="flex items-center gap-4 p-4">
              <div class="flex-shrink-0 w-8 h-8 rounded-full bg-[#e3bc50]/20 flex items-center justify-center">
                <span class="text-[#e3bc50] text-xs font-bold">{{ index + 1 }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="tx-body text-sm font-bold">{{ fase.fase }}</div>
                <div class="tx-subtle text-xs mt-0.5">{{ fase.descripcion }}</div>
              </div>
              <q-badge :color="colorEstado(fase.estado)" class="text-[10px] capitalize px-3 py-1">
                {{ textoEstado(fase.estado) }}
              </q-badge>
            </div>
            <div v-if="fase.fechaInicio || fase.fechaFin" class="px-4 pb-3 flex gap-4 text-[10px] tx-muted font-mono">
              <span v-if="fase.fechaInicio">Inicio: {{ fase.fechaInicio }}</span>
              <span v-if="fase.fechaFin">Fin: {{ fase.fechaFin }}</span>
            </div>
          </div>
        </div>

        <div v-if="!planPaciente.length" class="flex flex-col items-center justify-center p-12 bg-main rounded-lg border border-dashed border-theme mt-4">
          <p class="tx-muted text-sm">Este paciente no tiene plan de tratamiento</p>
        </div>
      </template>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed } from 'vue'
import { planesTratamiento, pacientes } from 'src/data/dummy.js'

const filtroPaciente = ref(null)

const opcionesPacientes = pacientes
const nombrePaciente = (id) => {
  const p = pacientes.find(p => p.id === id)
  return p ? p.nombre : '—'
}

const planPaciente = computed(() => {
  if (!filtroPaciente.value) return []
  return planesTratamiento.filter(p => p.pacienteId === filtroPaciente.value)
})

const colorEstado = (estado) => {
  const map = { pendiente: 'warning', en_proceso: 'info', completado: 'positive', pospuesto: 'grey' }
  return map[estado] || 'grey'
}

const textoEstado = (estado) => {
  const map = { pendiente: 'Pendiente', en_proceso: 'En Proceso', completado: 'Completado', pospuesto: 'Pospuesto' }
  return map[estado] || estado
}
</script>
