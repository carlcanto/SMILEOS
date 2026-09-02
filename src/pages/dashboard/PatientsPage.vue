<template>
  <q-page class="q-pa-md tx-body">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">Pacientes</h1>
          <p class="tx-subtle text-sm">Listado de pacientes registrados</p>
        </div>
        <q-btn color="primary" label="+ Nuevo Paciente" class="bg-[#e3bc50] text-black font-bold" no-caps />
      </div>

      <q-card class="bg-card border border-theme-accent" flat>
        <q-table :rows="pacientes" :columns="columns" row-key="id" dark
          :pagination="{ rowsPerPage: 10 }"
          class="bg-transparent tx-body"
          table-header-class="text-[#e3bc50] font-bold"
          :table-style="'background: #1c1a18'"
          :card-style="'background: #1c1a18'">
          <template v-slot:body-cell-nombre="props">
            <td class="tx-body">
              <router-link :to="`/dashboard/pacientes/${props.row.id}`" class="text-[#e3bc50] hover:underline font-medium cursor-pointer">
                {{ props.row.nombre }}
              </router-link>
            </td>
          </template>
          <template v-slot:body-cell-ultimaVisita="props">
            <td class="tx-subtle text-sm">{{ props.row.ultimaVisita }}</td>
          </template>
        </q-table>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { pacientes } from 'src/data/dummy.js'

const columns = [
  { name: 'nombre', label: 'Nombre', field: 'nombre', align: 'left', sortable: true },
  { name: 'identificacion', label: 'Identificación', field: 'identificacion', align: 'left' },
  { name: 'edad', label: 'Edad', field: 'edad', align: 'center', sortable: true },
  { name: 'telefono', label: 'Teléfono', field: 'telefono', align: 'left' },
  { name: 'aseguradora', label: 'Aseguradora', field: 'aseguradora', align: 'left' },
  { name: 'ultimaVisita', label: 'Última Visita', field: 'ultimaVisita', align: 'center', sortable: true },
]
</script>
