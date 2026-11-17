<template>
  <q-page class="futuristic-bg">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-[#e3bc50] tracking-wide">Documentos Clínicos</h1>
          <p class="tx-subtle text-sm">Plantillas preformateadas para la consulta</p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div v-for="tpl in plantillas" :key="tpl.id" @click="seleccionarPlantilla(tpl)"
          class="bg-card border border-theme rounded-xl p-6 cursor-pointer hover:border-[#e3bc50]/30 hover:bg-card/80 transition-all group">
          <q-icon :name="tpl.icono" size="32px"
            class="text-[#e3bc50] mb-3 group-hover:scale-110 transition-transform" />
          <div class="tx-body text-sm font-bold">{{ tpl.nombre }}</div>
          <div class="tx-muted text-[11px] mt-1">{{ tpl.descripcion }}</div>
        </div>
      </div>

      <q-card v-if="plantillaActiva" class="bg-card border border-theme-accent" flat>
        <q-card-section>
          <div class="flex justify-between items-center mb-4">
            <div class="text-[#e3bc50] font-bold text-sm tracking-wide">{{ plantillaActiva.nombre }}</div>
            <div class="flex gap-2">
              <q-btn flat dense color="white" icon="close" label="Cerrar" @click="plantillaActiva = null" size="sm"
                class="tx-subtle" no-caps />
            </div>
          </div>

          <div class="bg-main rounded-lg p-6 border border-theme">
            <div class="grid grid-cols-2 gap-4 mb-6 text-sm">
              <div><span class="tx-muted">Paciente:</span> <span class="tx-body font-medium ml-2" contenteditable>{{
                pacienteEjemplo.nombre }}</span></div>
              <div><span class="tx-muted">Identificación:</span> <span class="tx-body ml-2">{{
                pacienteEjemplo.identificacion }}</span></div>
              <div><span class="tx-muted">Fecha:</span> <span class="tx-body ml-2">{{ fechaActual }}</span></div>
              <div><span class="tx-muted">Doctor:</span> <span class="tx-body font-medium ml-2" contenteditable>Dr.
                  García</span></div>
            </div>

            <q-separator class="bg-gray-800 q-mb-md" />

            <div class="text-sm tx-body leading-relaxed whitespace-pre-line" contenteditable>
              {{ plantillaActiva.contenido }}
            </div>
          </div>

          <div class="flex justify-end gap-3 mt-4">
            <q-btn flat color="white" icon="print" label="Imprimir" class="tx-body" no-caps />
            <q-btn color="primary" icon="save" label="Guardar" class="bg-[#e3bc50] text-black font-bold" no-caps />
          </div>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { pacientes } from 'src/data/dummy.js'

const plantillaActiva = ref(null)

const fechaActual = new Date().toLocaleDateString('es-PA', { year: 'numeric', month: 'long', day: 'numeric' })
const pacienteEjemplo = pacientes[0]

const plantillas = [
  {
    id: 'receta',
    nombre: 'Receta Médica',
    icono: 'medication',
    descripcion: 'Receta odontológica con indicaciones',
    contenido: `Receta Médica

Indicaciones:
[Indicaciones del medicamento]

Dosis:
[Dosis y frecuencia]

Duración del tratamiento:
[Duración]

Observaciones:
[Observaciones adicionales]

_________________________
Firma del Profesional`,
  },
  {
    id: 'incapacidad',
    nombre: 'Incapacidad',
    icono: 'event_busy',
    descripcion: 'Certificado de incapacidad temporal',
    contenido: `CERTIFICADO DE INCAPACIDAD

Por medio de la presente, certifico que el paciente arriba identificado se encuentra incapacitado para realizar sus labores habituales por un período de [cantidad] días, a partir del [fecha de inicio].

Motivo: [Motivo de la incapacidad]

Recomendaciones:
[Recomendaciones médicas]

_________________________
Firma del Profesional`,
  },
  {
    id: 'referencia',
    nombre: 'Referencia',
    icono: 'forward',
    descripcion: 'Referencia a especialista',
    contenido: `REFERENCIA MÉDICA

Estimado colega,

Por medio de la presente, refiero al paciente arriba identificado para evaluación y tratamiento por las siguientes razones:

Diagnóstico:
[Diagnóstico del paciente]

Hallazgos relevantes:
[Hallazgos clínicos relevantes]

Exámenes realizados:
[Exámenes realizados]

Especialidad solicitada:
[Especialidad]

_________________________
Doctor Referente`,
  },
  {
    id: 'consentimiento',
    nombre: 'Consentimiento Informado',
    icono: 'gavel',
    descripcion: 'Consentimiento para procedimientos',
    contenido: `CONSENTIMIENTO INFORMADO

Yo, [Nombre del paciente], identificado con cédula [Identificación], declaro que he sido informado(a) de manera clara y comprensible sobre el procedimiento de [nombre del procedimiento].

Entiendo los riesgos, beneficios y alternativas del tratamiento propuesto.

Procedimiento a realizar:
[Descripción del procedimiento]

Riesgos:
[Posibles riesgos]

Alternativas:
[Alternativas al tratamiento]

Autorizo al Dr./Dra. [Nombre del profesional] a realizar el procedimiento descrito.

_________________________          _________________________
Firma del Paciente                  Fecha`,
  },
]

const seleccionarPlantilla = (tpl) => {
  plantillaActiva.value = tpl
}
</script>
