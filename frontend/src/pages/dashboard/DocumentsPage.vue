<template>
  <q-page class="q-pa-md tx-body">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">Documentos Administrativos</h1>
          <p class="tx-subtle text-sm">Historial de documentos y archivos administrativos</p>
        </div>
      </div>

      <q-card class="bg-card border border-theme-accent" flat>
        <q-table :rows="documentos" :columns="columns" row-key="id" dark
          :pagination="{ rowsPerPage: 10 }"
          class="bg-transparent tx-body"
          table-header-class="text-[#e3bc50] font-bold">
          <template v-slot:body-cell-tipo="props">
            <td>
              <q-badge :color="colorTipo(props.row.tipo)" class="text-[10px] capitalize">
                {{ props.row.tipo }}
              </q-badge>
            </td>
          </template>
          <template v-slot:body-cell-pacienteId="props">
            <td class="tx-body text-sm">{{ nombrePaciente(props.row.pacienteId) }}</td>
          </template>
        </q-table>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { documentos, pacientes } from 'src/data/dummy.js'

const columns = [
  { name: 'titulo', label: 'Título', field: 'titulo', align: 'left', sortable: true },
  { name: 'tipo', label: 'Tipo', field: 'tipo', align: 'center' },
  { name: 'pacienteId', label: 'Paciente', field: 'pacienteId', align: 'left' },
  { name: 'fecha', label: 'Fecha', field: 'fecha', align: 'center', sortable: true },
  { name: 'autor', label: 'Autor', field: 'autor', align: 'center' },
]

const colorTipo = (tipo) => {
  const map = { receta: 'positive', consentimiento: 'info', referencia: 'warning', incapacidad: 'negative' }
  return map[tipo] || 'grey'
}

const nombrePaciente = (id) => {
  const p = pacientes.find(p => p.id === id)
  return p ? p.nombre : '—'
}
</script>
