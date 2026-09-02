<template>
  <q-page class="q-pa-md tx-body">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">Galería</h1>
          <p class="tx-subtle text-sm">Imágenes y archivos de pacientes</p>
        </div>
        <div class="flex gap-2">
          <q-btn-toggle v-model="filtroTipo" toggle-color="primary" text-color="primary" toggle-text-color="#FFFFFF"
            flat unelevated class="border border-slate-700 bg-main" :options="[
              { label: 'Todos', value: 'todos' },
              { label: 'Radiografías', value: 'radiografia' },
              { label: 'Fotos', value: 'foto' },
              { label: 'PDFs', value: 'pdf' },
              { label: 'Facturas', value: 'factura' },
            ]" />
        </div>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        <div v-for="archivo in archivosFiltrados" :key="archivo.id"
          class="bg-card border border-theme rounded-xl overflow-hidden hover:border-[#e3bc50]/30 transition-all cursor-pointer group">
          <div class="aspect-square bg-main flex items-center justify-center relative">
            <q-icon :name="iconoTipo(archivo.tipo)" size="48px" class="tx-muted group-hover:text-[#e3bc50]/50 transition-colors" />
            <div class="absolute top-2 right-2">
              <q-badge :color="colorTipo(archivo.tipo)" class="text-[9px]">{{ archivo.tipo }}</q-badge>
            </div>
          </div>
          <div class="p-3">
            <div class="tx-body text-xs font-medium truncate">{{ archivo.nombre }}</div>
            <div class="flex justify-between text-[10px] tx-muted mt-1">
              <span>{{ archivo.fecha }}</span>
              <span>{{ archivo.autor }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!archivosFiltrados.length" class="flex flex-col items-center justify-center p-12 bg-main rounded-lg border border-dashed border-theme mt-4">
        <q-icon name="image_search" size="3rem" class="tx-muted mb-3" />
        <p class="tx-muted text-sm">No hay archivos de este tipo</p>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed } from 'vue'
import { archivos } from 'src/data/dummy.js'

const filtroTipo = ref('todos')

const archivosFiltrados = computed(() => {
  if (filtroTipo.value === 'todos') return archivos
  return archivos.filter(a => a.tipo === filtroTipo.value)
})

const iconoTipo = (tipo) => {
  const map = { radiografia: 'x-ray', foto: 'photo_camera', pdf: 'picture_as_pdf', factura: 'receipt' }
  return map[tipo] || 'insert_drive_file'
}

const colorTipo = (tipo) => {
  const map = { radiografia: 'info', foto: 'positive', pdf: 'negative', factura: 'warning' }
  return map[tipo] || 'grey'
}
</script>
