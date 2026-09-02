<template>
  <q-page class="q-pa-md tx-body">
    <div class="max-w-7xl mx-auto">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">Citas</h1>
          <p class="tx-subtle text-sm">Gestión de agenda diaria</p>
        </div>
        <div class="bg-main p-1 rounded-lg border border-theme">
          <q-btn-toggle v-model="vistaActual" toggle-color="primary" text-color="primary" toggle-text-color="#FFFFFF"
            flat unelevated class="border border-slate-700 bg-main" :options="[
              { label: 'Diario', value: 'diario' },
              { label: 'Semanal', value: 'semanal' },
              { label: 'Quincenal', value: 'quincenal' },
              { label: 'Mensual', value: 'mensual' }
            ]" />
        </div>
      </div>

      <div class="flex flex-wrap gap-4 mb-6 bg-main p-3 rounded-lg border border-theme text-xs sm:text-sm">
        <span class="tx-subtle font-medium">Estados:</span>
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
          <div class="grid grid-cols-8 gap-2 bg-main p-3 rounded-t-lg border-b border-theme text-center font-bold text-[#e3bc50]">
            <div class="text-left tx-subtle font-normal">Hora</div>
            <template v-if="vistaActual === 'diario'">
              <div class="col-span-7">Hoy (Lunes 6 de Julio)</div>
            </template>
            <template v-else>
              <div v-for="dia in diasSemana" :key="dia">{{ dia }}</div>
            </template>
          </div>

          <div class="divide-y divide-gray-800 bg-darker">
            <div v-for="hora in horasLaborales" :key="hora" class="grid grid-cols-8 gap-2 items-center p-2 min-h-[65px] hover:bg-gray-800/30 transition-colors">
              <div class="tx-subtle font-medium text-xs sm:text-sm">{{ hora }}</div>

              <template v-if="vistaActual === 'diario'">
                <div class="col-span-7 h-full flex items-center">
                  <div v-if="citaDiaria(hora)" :class="['w-full p-2 rounded-lg text-black font-semibold shadow-md border-l-4 transform hover:scale-[1.01] transition-transform cursor-pointer', colorEstado(citaDiaria(hora).estado)]">
                    <div class="text-xs sm:text-sm font-bold">{{ citaDiaria(hora).paciente }}</div>
                    <div class="text-[11px] opacity-80">{{ citaDiaria(hora).tratamiento }}</div>
                  </div>
                  <div v-else class="tx-muted text-xs italic pl-2">Disponible</div>
                </div>
              </template>

              <template v-else>
                <div v-for="dia in 7" :key="dia" class="h-full flex items-center">
                  <div v-if="citaSemanal(hora, dia)" :class="['w-full p-1.5 rounded-md text-black font-semibold text-center shadow-sm text-xs border-l-2 truncate cursor-pointer', colorEstado(citaSemanal(hora, dia).estado)]"
                    :title="`${citaSemanal(hora, dia).paciente} - ${citaSemanal(hora, dia).tratamiento}`">
                    <span class="font-bold block truncate">{{ citaSemanal(hora, dia).paciente }}</span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="flex flex-col items-center justify-center p-12 bg-main rounded-lg border border-dashed border-theme">
        <q-icon name="calendar_month" size="4rem" class="text-[#e3bc50] mb-3" />
        <div class="text-lg font-medium tx-body">Vista {{ vistaActual.toUpperCase() }}</div>
        <p class="tx-muted text-sm text-center max-w-sm mt-1">Vista en desarrollo para este formato.</p>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { citas, horasLaborales, coloresEstado } from 'src/data/dummy.js'

const vistaActual = ref('diario')
const diasSemana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

const citaDiaria = (hora) => citas.find(c => c.hora === hora)

const citaSemanal = (hora, dia) => citas.find(c => c.hora === hora && c.dia === dia)

const colorEstado = (estado) => coloresEstado[estado] || 'bg-gray-500 border-theme tx-body'
</script>
