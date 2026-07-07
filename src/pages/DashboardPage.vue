<template>
  <div class="q-pa-md text-white min-h-screen" style="background-color: #1d1d1d;">

    <div class="max-w-7xl mx-auto bg-[#1c1a18] rounded-xl shadow-2xl border border-[#e3bc50]/20 p-6">


      <div class="flex flex-col sm:flex-row justify-between items-center gap-4 mb-6 border-b border-gray-700 pb-4">
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">DASHBOARD</h1>

        </div>


        <div class="bg-[#1d1d1d] p-1 rounded-lg border border-gray-700">
          <q-btn-toggle v-model="vistaActual" toggle-color="primary" text-color="primary" toggle-text-color="#FFFFFF"
            flat unelevated class="border border-slate-700 bg-[#1d1d1d]" :options="[
              { label: 'Diario', value: 'diario', attrs: { class: vistaActual === 'diario' ? 'text-neutral-950 font-bold bg-[#e3bc50]' : '' } },
              { label: 'Semanal', value: 'semanal', attrs: { class: vistaActual === 'semanal' ? 'text-neutral-950 font-bold bg-[#e3bc50]' : '' } },
              { label: 'Quincenal', value: 'quincenal', attrs: { class: vistaActual === 'quincenal' ? 'text-neutral-950 font-bold bg-[#e3bc50]' : '' } },
              { label: 'Mensual', value: 'mensual', attrs: { class: vistaActual === 'mensual' ? 'text-neutral-950 font-bold bg-[#e3bc50]' : '' } }
            ]" />
        </div>
        <div class="mb-8 flex justify-start">
          <q-tabs dense no-caps inline-label
            class="rounded-2xl border p-1.5 transition-all duration-300 shadow-md max-w-lg w-full sm:w-auto" :class="esModoOscuro
              ? 'bg-[#1c1a18] border-[#e3bc50]/15 text-gray-400'
              : 'bg-white border-gray-200 text-slate-500 shadow-sm'" active-color="primary"
            :active-bg-color="esModoOscuro ? 'white/5' : 'gray-100'" indicator-color="transparent">
            <q-route-tab to="/dashboard/citas" icon="calendar_today" label="Citas"
              class="px-6 py-2.5 rounded-xl font-bold tracking-wide transition-all duration-200 mx-0.5" :class="pestanaActiva('/dashboard/citas')
                ? (esModoOscuro ? 'text-[#e3bc50] bg-[#1d1d1d] border border-[#e3bc50]/30 shadow-[0_0_15px_rgba(227,188,80,0.1)]' : 'text-slate-900 bg-amber-500/10 border border-amber-500/20')
                : 'hover:text-[#e3bc50]/80'" />

            <q-route-tab to="/dashboard/pacientes" icon="people" label="Pacientes"
              class="px-6 py-2.5 rounded-xl font-bold tracking-wide transition-all duration-200 mx-0.5" :class="pestanaActiva('/dashboard/pacientes')
                ? (esModoOscuro ? 'text-[#e3bc50] bg-[#1d1d1d] border border-[#e3bc50]/30 shadow-[0_0_15px_rgba(227,188,80,0.1)]' : 'text-slate-900 bg-amber-500/10 border border-amber-500/20')
                : 'hover:text-[#e3bc50]/80'" />

            <q-route-tab to="/dashboard/reportes" icon="bar_chart" label="Reportes"
              class="px-6 py-2.5 rounded-xl font-bold tracking-wide transition-all duration-200 mx-0.5" :class="pestanaActiva('/dashboard/reportes')
                ? (esModoOscuro ? 'text-[#e3bc50] bg-[#1d1d1d] border border-[#e3bc50]/30 shadow-[0_0_15px_rgba(227,188,80,0.1)]' : 'text-slate-900 bg-amber-500/10 border border-amber-500/20')
                : 'hover:text-[#e3bc50]/80'" />
          </q-tabs>
        </div>
      </div>


      <div class="flex flex-wrap gap-4 mb-6 bg-[#1d1d1d] p-3 rounded-lg border border-gray-800 text-xs sm:text-sm">
        <span class="text-gray-400 font-medium">Estados:</span>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-[#7dc091]"></span>
          <span>Confirmada</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-[#e3bc50]"></span>
          <span>Pendiente</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-[#c10015]"></span>
          <span>Cancelada</span>
        </div>
      </div>


      <div v-if="vistaActual === 'diario' || vistaActual === 'semanal'" class="overflow-x-auto">
        <div class="min-w-[600px]">


          <div
            class="grid grid-cols-8 gap-2 bg-[#1d1d1d] p-3 rounded-t-lg border-b border-gray-700 text-center font-bold text-[#e3bc50]">
            <div class="text-left text-gray-400 font-normal">Hora</div>
            <template v-if="vistaActual === 'diario'">
              <div class="col-span-7">Hoy (Lunes 6 de Julio)</div>
            </template>
            <template v-else>
              <div>Lun</div>
              <div>Mar</div>
              <div>Mié</div>
              <div>Jue</div>
              <div>Vie</div>
              <div>Sáb</div>
              <div>Dom</div>
            </template>
          </div>


          <div class="divide-y divide-gray-800 bg-[#151413]">
            <div v-for="hora in horasLaborales" :key="hora"
              class="grid grid-cols-8 gap-2 items-center p-2 min-h-[65px] hover:bg-gray-800/30 transition-colors">
              <!-- Columna de la Hora -->
              <div class="text-gray-400 font-medium text-xs sm:text-sm">
                {{ hora }}
              </div>


              <template v-if="vistaActual === 'diario'">
                <div class="col-span-7 h-full flex items-center">
                  <!-- Renderizador de Cita Ejemplo si coincide con la hora -->
                  <div v-if="obtenerCita('diario', hora)" :class="[
                    'w-full p-2 rounded-lg text-black font-semibold shadow-md border-l-4 transform hover:scale-[1.01] transition-transform cursor-pointer',
                    colorEstado(obtenerCita('diario', hora).estado)
                  ]">
                    <div class="text-xs sm:text-sm font-bold">{{ obtenerCita('diario', hora).paciente }}</div>
                    <div class="text-[11px] opacity-80">{{ obtenerCita('diario', hora).tratamiento }}</div>
                  </div>
                  <div v-else class="text-gray-600 text-xs italic pl-2">Disponible</div>
                </div>
              </template>


              <template v-else>
                <div v-for="dia in 7" :key="dia" class="h-full flex items-center">
                  <div v-if="obtenerCita('semanal', hora, dia)" :class="[
                    'w-full p-1.5 rounded-md text-black font-semibold text-center shadow-sm text-xs border-l-2 truncate cursor-pointer',
                    colorEstado(obtenerCita('semanal', hora, dia).estado)
                  ]"
                    :title="`${obtenerCita('semanal', hora, dia).paciente} - ${obtenerCita('semanal', hora, dia).tratamiento}`">
                    <span class="font-bold block truncate">{{ obtenerCita('semanal', hora, dia).paciente }}</span>
                  </div>
                </div>
              </template>

            </div>
          </div>

        </div>
      </div>

      <!-- Marcador de posición amigable para Quincenal y Mensual (Próximo paso) -->
      <div v-else
        class="flex flex-col items-center justify-center p-12 bg-[#1d1d1d] rounded-lg border border-dashed border-gray-700">
        <q-icon name="calendar_month" size="4rem" class="text-[#e3bc50] mb-3" />
        <div class="text-lg font-medium text-gray-300">Vista {{ vistaActual.toUpperCase() }}</div>
        <p class="text-gray-500 text-sm text-center max-w-sm mt-1">
          La maquetación en grilla extendida para este formato está lista para configurarse tras definir los detalles
          base de
          las citas.
        </p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'

// Estado de la vista seleccionada
const vistaActual = ref('diario')

// Definición estricta del horario clínico (8:00 AM a 5:00 PM)
const horasLaborales = [
  '08:00 AM', '09:00 AM', '10:00 AM', '11:00 AM',
  '12:00 PM', '01:00 PM', '02:00 PM', '03:00 PM',
  '04:00 PM', '05:00 PM'
]

// Datos simulados de citas para verificar los colores de tu paleta
const citasDummy = ref([
  { hora: '08:00 AM', dia: 1, paciente: 'Carlos Mendoza', tratamiento: 'Limpieza General', estado: 'confirmada' },
  { hora: '10:00 AM', dia: 1, paciente: 'Ana Sofia (Adolescente)', tratamiento: 'Ajuste de Brackets', estado: 'pendiente' },
  { hora: '01:00 PM', dia: 1, paciente: 'Roberto Gómez (Adulto Mayor)', tratamiento: 'Revisión de Prótesis', estado: 'cancelada' },
  { hora: '03:00 AM', dia: 3, paciente: 'Luis Torres', tratamiento: 'Extracción', estado: 'confirmada' }
])
const esModoOscuro = ref(true)
const route = useRoute()

// Función auxiliar para verificar la pestaña activa
const pestanaActiva = (path) => {
  return route.path === path
}
// Retorna las clases CSS correctas usando exactamente tus variables de color
const colorEstado = (estado) => {
  switch (estado) {
    case 'confirmada':
      return 'bg-[#7dc091] border-green-800 text-neutral-900' // $positive
    case 'pendiente':
      return 'bg-[#e3bc50] border-yellow-700 text-neutral-900' // $primary
    case 'cancelada':
      return 'bg-[#c10015] border-red-950 text-white' // $negative
    default:
      return 'bg-gray-500 border-gray-700 text-white'
  }
}

// Lógica de filtrado simple para renderizar en la cuadrícula
const obtenerCita = (tipo, hora, dia = 1) => {
  if (tipo === 'diario') {
    return citasDummy.value.find(c => c.hora === hora && c.dia === 1)
  }
  return citasDummy.value.find(c => c.hora === hora && c.dia === dia)
}
</script>

<style scoped>
::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}

::-webkit-scrollbar-thumb {
  background: #e3bc50;
  border-radius: 4px;
}
</style>
