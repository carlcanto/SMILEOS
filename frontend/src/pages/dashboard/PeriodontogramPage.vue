<template>
  <q-page class="q-pa-md tx-body">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">Periodontograma</h1>
          <p class="tx-subtle text-sm">Registro de profundidades de bolsa periodontal</p>
        </div>
        <q-select v-model="filtroPaciente" :options="opcionesPacientes" label="Seleccionar paciente" dense
          class="bg-main rounded-lg border border-theme min-w-[200px]" dark standout
          option-label="nombre" option-value="id" clearable emit-value map-options />
      </div>

      <div v-if="!filtroPaciente" class="flex flex-col items-center justify-center p-16 bg-card rounded-xl border border-dashed border-theme">
        <q-icon name="grid_view" size="4rem" class="tx-muted mb-3" />
        <p class="tx-subtle text-lg font-medium">Selecciona un paciente</p>
        <p class="tx-muted text-sm mt-1">Para registrar el periodontograma</p>
      </div>

      <template v-else>
        <div class="overflow-x-auto">
          <div class="min-w-[700px]">
            <q-card class="bg-card border border-theme" flat>
              <q-card-section class="text-center">
                <div class="tx-subtle text-[10px] font-mono tracking-widest mb-2">CUADRANTES SUPERIORES</div>
                <div class="flex justify-center items-end gap-1">
                  <div v-for="diente in dientesSuperiores" :key="diente.numero"
                    class="flex flex-col items-center">
                    <div class="w-10 h-10 bg-main border border-theme rounded flex items-center justify-center">
                      <span class="text-[10px] tx-subtle font-mono">{{ diente.numero }}</span>
                    </div>
                    <div class="flex gap-0.5 mt-0.5">
                      <input type="text" maxlength="4" :value="diente.profundidad"
                        class="w-10 h-5 bg-darker border border-theme rounded text-[9px] text-center tx-body font-mono focus:border-[#e3bc50] focus:outline-none"
                        :class="colorProfundidad(diente.profundidad)" placeholder="mm" />
                    </div>
                    <div class="flex gap-0.5 mt-0.5">
                      <span class="w-4 h-1.5 rounded-sm" :class="diente.sangrado ? 'bg-red-500' : 'bg-gray-700'"></span>
                    </div>
                  </div>
                </div>
              </q-card-section>
            </q-card>

            <q-card class="bg-card border border-theme q-mt-md" flat>
              <q-card-section class="text-center">
                <div class="tx-subtle text-[10px] font-mono tracking-widest mb-2">CUADRANTES INFERIORES</div>
                <div class="flex justify-center items-start gap-1">
                  <div v-for="diente in dientesInferiores" :key="diente.numero"
                    class="flex flex-col items-center">
                    <div class="flex gap-0.5 mb-0.5">
                      <span class="w-4 h-1.5 rounded-sm" :class="diente.sangrado ? 'bg-red-500' : 'bg-gray-700'"></span>
                    </div>
                    <div class="flex gap-0.5 mb-0.5">
                      <input type="text" maxlength="4" :value="diente.profundidad"
                        class="w-10 h-5 bg-darker border border-theme rounded text-[9px] text-center tx-body font-mono focus:border-[#e3bc50] focus:outline-none"
                        :class="colorProfundidad(diente.profundidad)" placeholder="mm" />
                    </div>
                    <div class="w-10 h-10 bg-main border border-theme rounded flex items-center justify-center">
                      <span class="text-[10px] tx-subtle font-mono">{{ diente.numero }}</span>
                    </div>
                  </div>
                </div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <div class="flex justify-between mt-6 p-4 bg-card rounded-lg border border-theme">
          <div class="space-y-2 text-xs tx-subtle">
            <div class="font-bold text-[#e3bc50] mb-2">Leyenda</div>
            <div class="flex items-center gap-2"><span class="w-4 h-1.5 bg-red-500 rounded-sm"></span> Sangrado presente</div>
            <div class="flex items-center gap-2"><span class="w-4 h-1.5 bg-gray-700 rounded-sm"></span> Sin sangrado</div>
            <div class="flex items-center gap-2"><span class="w-3 h-3 rounded bg-yellow-600 inline-block"></span> 4-5mm (alerta)</div>
            <div class="flex items-center gap-2"><span class="w-3 h-3 rounded bg-red-700 inline-block"></span> 6mm+ (crítico)</div>
          </div>
          <div class="flex items-end gap-2">
            <q-btn color="primary" icon="save" label="Guardar" class="bg-[#e3bc50] text-black font-bold" no-caps />
          </div>
        </div>
      </template>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { pacientes } from 'src/data/dummy.js'

const filtroPaciente = ref(null)
const opcionesPacientes = pacientes

const dientesSuperiores = Array.from({ length: 16 }, (_, i) => {
  const nums = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
  return { numero: nums[i], profundidad: i % 3 === 0 ? (Math.random() * 3 + 1).toFixed(1) : '', sangrado: Math.random() > 0.8 }
})

const dientesInferiores = Array.from({ length: 16 }, (_, i) => {
  const nums = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]
  return { numero: nums[i], profundidad: i % 4 === 0 ? (Math.random() * 4 + 1).toFixed(1) : '', sangrado: Math.random() > 0.85 }
})

const colorProfundidad = (val) => {
  if (!val) return ''
  const n = parseFloat(val)
  if (n >= 6) return 'bg-red-900/30 text-red-300'
  if (n >= 4) return 'bg-yellow-900/30 text-yellow-300'
  return ''
}
</script>
