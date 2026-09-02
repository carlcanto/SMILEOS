<template>
  <q-page class="q-pa-md tx-body">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">Reportes</h1>
          <p class="tx-subtle text-sm">Estadísticas y resúmenes</p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div v-for="stat in stats" :key="stat.label" class="bg-card border border-theme rounded-xl p-5">
          <div class="flex items-center gap-3 mb-3">
            <q-icon :name="stat.icono" size="24px" :color="stat.color" />
            <span class="tx-subtle text-xs font-medium">{{ stat.label }}</span>
          </div>
          <div class="tx-body text-3xl font-bold">{{ stat.valor }}</div>
          <div class="tx-muted text-[10px] mt-1">{{ stat.subtitulo }}</div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-card border border-theme rounded-xl p-5">
          <div class="text-[#e3bc50] font-bold text-sm mb-4 tracking-wide">CITAS POR ESTADO</div>
          <div class="space-y-3">
            <div v-for="item in citasPorEstado" :key="item.estado" class="flex items-center gap-3">
              <div class="flex-1">
                <div class="flex justify-between text-sm mb-1">
                  <span class="tx-body capitalize">{{ item.estado }}</span>
                  <span class="tx-body font-bold">{{ item.cantidad }}</span>
                </div>
                <div class="h-2 bg-main rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500" :class="item.color" :style="{ width: item.porcentaje + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-card border border-theme rounded-xl p-5">
          <div class="text-[#e3bc50] font-bold text-sm mb-4 tracking-wide">PRÓXIMAS CITAS</div>
          <div class="space-y-2">
            <div v-for="cita in proximasCitas" :key="cita.id"
              class="flex items-center gap-3 p-3 bg-main rounded-lg border border-theme">
              <div class="text-center min-w-[40px]">
                <div class="tx-body text-xs font-bold">{{ cita.hora }}</div>
              </div>
              <div class="flex-1 min-w-0">
                <div class="tx-body text-sm font-medium truncate">{{ cita.paciente }}</div>
                <div class="tx-muted text-xs">{{ cita.tratamiento }}</div>
              </div>
              <q-badge :color="colorEstadoBadge(cita.estado)" class="text-[9px] capitalize">
                {{ cita.estado }}
              </q-badge>
            </div>
          </div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { computed } from 'vue'
import { citas, pacientes } from 'src/data/dummy.js'

const stats = [
  { label: 'Total Pacientes', icono: 'people', color: 'primary', valor: pacientes.length, subtitulo: 'Registrados en el sistema' },
  { label: 'Citas Hoy', icono: 'calendar_today', color: 'positive', valor: citas.filter(c => c.fecha === '2026-07-09').length, subtitulo: 'Para hoy' },
  { label: 'Pendientes', icono: 'pending_actions', color: 'warning', valor: citas.filter(c => c.estado === 'pendiente').length, subtitulo: 'Requieren confirmación' },
  { label: 'Completadas', icono: 'check_circle', color: 'positive', valor: citas.filter(c => c.estado === 'confirmada').length, subtitulo: 'Este período' },
]

const citasPorEstado = computed(() => {
  const estados = ['confirmada', 'pendiente', 'cancelada']
  const colores = { confirmada: 'bg-[#7dc091]', pendiente: 'bg-[#e3bc50]', cancelada: 'bg-[#c10015]' }
  const total = citas.length
  return estados.map(e => ({
    estado: e,
    cantidad: citas.filter(c => c.estado === e).length,
    porcentaje: total ? (citas.filter(c => c.estado === e).length / total) * 100 : 0,
    color: colores[e],
  }))
})

const proximasCitas = computed(() => {
  return citas.filter(c => c.estado !== 'cancelada').slice(0, 5)
})

const colorEstadoBadge = (estado) => {
  const map = { confirmada: 'positive', pendiente: 'warning', cancelada: 'negative', cumplida: 'info' }
  return map[estado] || 'grey'
}
</script>
