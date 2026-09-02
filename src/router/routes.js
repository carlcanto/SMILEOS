const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/IndexPage.vue') },
      { path: 'login', component: () => import('pages/LoginPage.vue') },
      {
        path: 'dashboard',
        component: () => import('layouts/MainLayout.vue'),
        children: [
          { path: '', redirect: '/dashboard/citas' },
          { path: 'citas', component: () => import('pages/dashboard/AppointmentsPage.vue') },
          { path: 'pacientes', component: () => import('pages/dashboard/PatientsPage.vue') },
          { path: 'pacientes/:id', component: () => import('pages/dashboard/PatientDetailPage.vue') },
          { path: 'galeria', component: () => import('pages/dashboard/GalleryPage.vue') },
          { path: 'documentos', component: () => import('pages/dashboard/DocumentsPage.vue') },
          { path: 'evoluciones', component: () => import('pages/dashboard/EvolutionsPage.vue') },
          { path: 'plan-tratamiento', component: () => import('pages/dashboard/TreatmentPlanPage.vue') },
          { path: 'documentos-clinicos', component: () => import('pages/dashboard/ClinicalDocsPage.vue') },
          { path: 'periodontograma', component: () => import('pages/dashboard/PeriodontogramPage.vue') },
          { path: 'reportes', component: () => import('pages/dashboard/ReportsPage.vue') },
        ],
      },
    ],
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
]

export default routes
