export const pacientes = [
  {
    id: 1,
    nombre: 'Carlos Mendoza',
    identificacion: '8-123-456',
    edad: 45,
    telefono: '6000-1234',
    email: 'carlos@email.com',
    direccion: 'Calle Principal, Panamá',
    contactoEmergencia: 'Maria Mendoza - 6000-5678',
    aseguradora: 'ASSA Compañía de Seguros',
    alergias: 'Penicilina',
    notas: 'Paciente regular, viene cada 6 meses',
    ultimaVisita: '2026-05-15',
  },
  {
    id: 2,
    nombre: 'Ana Sofia Rodríguez',
    identificacion: '8-234-567',
    edad: 16,
    telefono: '6000-2345',
    email: 'anasofia@email.com',
    direccion: 'Avenida Central, Panamá',
    contactoEmergencia: 'Laura Rodríguez - 6000-6789',
    aseguradora: 'Palig insurance',
    alergias: 'Ninguna',
    notas: 'Paciente adolescente, tratamiento de ortodoncia',
    ultimaVisita: '2026-06-20',
  },
  {
    id: 3,
    nombre: 'Roberto Gómez',
    identificacion: '8-345-678',
    edad: 68,
    telefono: '6000-3456',
    email: 'rgomez@email.com',
    direccion: 'Calle 50, Panamá',
    contactoEmergencia: 'Elena Gómez - 6000-7890',
    aseguradora: 'Seguros Suramericana',
    alergias: 'Sulfa',
    notas: 'Adulto mayor, prótesis dental parcial',
    ultimaVisita: '2026-07-01',
  },
  {
    id: 4,
    nombre: 'Luis Torres',
    identificacion: '8-456-789',
    edad: 32,
    telefono: '6000-4567',
    email: 'ltorres@email.com',
    direccion: 'Vía España, Panamá',
    contactoEmergencia: 'Carla Torres - 6000-8901',
    aseguradora: 'Blue Cross Panama',
    alergias: 'Ninguna',
    notas: 'Tratamiento de conducto pendiente',
    ultimaVisita: '2026-06-10',
  },
  {
    id: 5,
    nombre: 'María Castillo',
    identificacion: '8-567-890',
    edad: 28,
    telefono: '6000-5678',
    email: 'mcastillo@email.com',
    direccion: 'Calle 60, Panamá',
    contactoEmergencia: 'Pedro Castillo - 6000-9012',
    aseguradora: 'Sin seguro',
    alergias: 'Látex',
    notas: 'Blanqueamiento dental programado',
    ultimaVisita: '2026-07-05',
  },
]

export const citas = [
  { id: 1, pacienteId: 1, hora: '08:00 AM', fecha: '2026-07-09', paciente: 'Carlos Mendoza', tratamiento: 'Limpieza General', estado: 'confirmada', profesional: 'Dr. García' },
  { id: 2, pacienteId: 2, hora: '10:00 AM', fecha: '2026-07-09', paciente: 'Ana Sofia Rodríguez', tratamiento: 'Ajuste de Brackets', estado: 'pendiente', profesional: 'Dr. García' },
  { id: 3, pacienteId: 3, hora: '01:00 PM', fecha: '2026-07-09', paciente: 'Roberto Gómez', tratamiento: 'Revisión de Prótesis', estado: 'cancelada', profesional: 'Dr. García' },
  { id: 4, pacienteId: 4, hora: '09:00 AM', fecha: '2026-07-10', paciente: 'Luis Torres', tratamiento: 'Extracción', estado: 'confirmada', profesional: 'Dr. Pérez' },
  { id: 5, pacienteId: 5, hora: '11:00 AM', fecha: '2026-07-10', paciente: 'María Castillo', tratamiento: 'Blanqueamiento', estado: 'pendiente', profesional: 'Dr. García' },
  { id: 6, pacienteId: 1, hora: '03:00 PM', fecha: '2026-07-11', paciente: 'Carlos Mendoza', tratamiento: 'Revisión General', estado: 'confirmada', profesional: 'Dr. Pérez' },
]

export const evoluciones = [
  { id: 1, pacienteId: 1, fecha: '2026-05-15', profesional: 'Dr. García', descripcion: 'Limpieza profunda realizada. Se aplicó flúor. Paciente sin molestias.', tipo: 'limpieza' },
  { id: 2, pacienteId: 1, fecha: '2026-06-20', profesional: 'Dr. García', descripcion: 'Revisión de rutina. Se detectó caries incipiente en diente 26. Pendiente de restaurar.', tipo: 'revision' },
  { id: 3, pacienteId: 2, fecha: '2026-06-01', profesional: 'Dr. García', descripcion: 'Colocación de brackets superior e inferior. Se explicó higiene con ortodoncia.', tipo: 'ortodoncia' },
  { id: 4, pacienteId: 2, fecha: '2026-06-20', profesional: 'Dr. García', descripcion: 'Ajuste mensual de brackets. Se cambiaron ligas. Progreso satisfactorio.', tipo: 'ortodoncia' },
  { id: 5, pacienteId: 4, fecha: '2026-06-10', profesional: 'Dr. Pérez', descripcion: 'Diagnóstico de caries profunda en diente 36. Se recomienda tratamiento de conducto.', tipo: 'diagnostico' },
  { id: 6, pacienteId: 5, fecha: '2026-07-05', profesional: 'Dr. García', descripcion: 'Evaluación pre-blanqueamiento. Se tomó muestra de color. Encías saludables.', tipo: 'estetica' },
]

export const planesTratamiento = [
  { id: 1, pacienteId: 1, fase: 'Fase 1: Urgencia', descripcion: 'Restauración caries diente 26', estado: 'pendiente', fechaInicio: null, fechaFin: null },
  { id: 2, pacienteId: 1, fase: 'Fase 2: Mantenimiento', descripcion: 'Limpieza profunda y aplicación de flúor', estado: 'completado', fechaInicio: '2026-05-15', fechaFin: '2026-05-15' },
  { id: 3, pacienteId: 1, fase: 'Fase 3: Seguimiento', descripcion: 'Revisión a los 6 meses', estado: 'pendiente', fechaInicio: null, fechaFin: null },
  { id: 4, pacienteId: 2, fase: 'Fase 1: Ortodoncia Inicial', descripcion: 'Colocación de brackets completos', estado: 'completado', fechaInicio: '2026-06-01', fechaFin: '2026-06-01' },
  { id: 5, pacienteId: 2, fase: 'Fase 2: Ajustes Mensuales', descripcion: 'Ajustes periódicos cada 4 semanas', estado: 'en_proceso', fechaInicio: '2026-06-20', fechaFin: null },
  { id: 6, pacienteId: 2, fase: 'Fase 3: Retenedores', descripcion: 'Colocación de retenedores post-tratamiento', estado: 'pendiente', fechaInicio: null, fechaFin: null },
  { id: 7, pacienteId: 4, fase: 'Fase 1: Diagnóstico', descripcion: 'Evaluación y radiografías', estado: 'completado', fechaInicio: '2026-06-10', fechaFin: '2026-06-10' },
  { id: 8, pacienteId: 4, fase: 'Fase 2: Tratamiento de Conducto', descripcion: 'Endodoncia diente 36', estado: 'pendiente', fechaInicio: null, fechaFin: null },
]

export const documentos = [
  { id: 1, pacienteId: 1, tipo: 'consentimiento', titulo: 'Consentimiento Informado - Limpieza', fecha: '2026-05-15', autor: 'Dr. García', url: '#' },
  { id: 2, pacienteId: 1, tipo: 'receta', titulo: 'Receta - Amoxicilina 500mg', fecha: '2026-05-15', autor: 'Dr. García', url: '#' },
  { id: 3, pacienteId: 2, tipo: 'referencia', titulo: 'Referencia a Ortodoncia', fecha: '2026-05-20', autor: 'Dr. Pérez', url: '#' },
  { id: 4, pacienteId: 3, tipo: 'consentimiento', titulo: 'Consentimiento - Prótesis Parcial', fecha: '2026-07-01', autor: 'Dr. García', url: '#' },
  { id: 5, pacienteId: 4, tipo: 'receta', titulo: 'Receta - Ibuprofeno 600mg', fecha: '2026-06-10', autor: 'Dr. Pérez', url: '#' },
  { id: 6, pacienteId: 5, tipo: 'incapacidad', titulo: 'Incapacidad - Post Blanqueamiento', fecha: '2026-07-05', autor: 'Dr. García', url: '#' },
]

export const archivos = [
  { id: 1, pacienteId: 1, tipo: 'radiografia', nombre: 'Panorámica - Carlos Mendoza', fecha: '2026-05-15', autor: 'Dr. García', miniatura: null },
  { id: 2, pacienteId: 1, tipo: 'foto', nombre: 'Foto intraoral frontal', fecha: '2026-05-15', autor: 'Dr. García', miniatura: null },
  { id: 3, pacienteId: 2, tipo: 'radiografia', nombre: 'Cefalométrica lateral', fecha: '2026-05-20', autor: 'Dr. García', miniatura: null },
  { id: 4, pacienteId: 2, tipo: 'foto', nombre: 'Fotos pre-ortodoncia', fecha: '2026-05-20', autor: 'Dr. García', miniatura: null },
  { id: 5, pacienteId: 3, tipo: 'pdf', nombre: 'Factura Laboratorio Prótesis', fecha: '2026-07-01', autor: 'Recepción', miniatura: null },
  { id: 6, pacienteId: 4, tipo: 'radiografia', nombre: 'Periapical diente 36', fecha: '2026-06-10', autor: 'Dr. Pérez', miniatura: null },
  { id: 7, pacienteId: 1, tipo: 'factura', nombre: 'Factura - Limpieza General', fecha: '2026-05-15', autor: 'Recepción', miniatura: null },
]

export const profesionales = [
  { id: 1, nombre: 'Dr. García', especialidad: 'Odontología General', color: '#4f8ef7' },
  { id: 2, nombre: 'Dr. Pérez', especialidad: 'Endodoncia', color: '#e3bc50' },
]

export const horasLaborales = [
  '08:00 AM', '09:00 AM', '10:00 AM', '11:00 AM',
  '12:00 PM', '01:00 PM', '02:00 PM', '03:00 PM',
  '04:00 PM', '05:00 PM',
]

export const coloresEstado = {
  confirmada: 'bg-[#7dc091] border-green-800 text-neutral-900',
  pendiente: 'bg-[#e3bc50] border-yellow-700 text-neutral-900',
  cancelada: 'bg-[#c10015] border-red-950 text-white',
  cumplida: 'bg-[#4f8ef7] border-blue-800 text-white',
}

export const estadoCitaTexto = {
  confirmada: 'Confirmada',
  pendiente: 'Pendiente',
  cancelada: 'Cancelada',
  cumplida: 'Cumplida',
}
