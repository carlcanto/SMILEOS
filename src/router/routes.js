const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/IndexPage.vue') },
      { path: 'login', component: () => import('pages/LoginPage.vue') },
      {
        path: 'dashboard',
        children: [
          { path: '', redirect: '/dashboard/citas' },
          { path: 'citas', component: () => import('pages/dashboard/AppointmentsPage.vue') },
          { path: 'pacientes', component: () => import('pages/dashboard/PatientsPage.vue') },
          {
            path: 'pacientes/:id',
            component: () => import('pages/dashboard/PatientDetailPage.vue'),
          },
          { path: 'inventario', component: () => import('pages/dashboard/InventoryPage.vue') },
          { path: 'evoluciones', component: () => import('pages/dashboard/EvolutionsPage.vue') },
          { path: 'historial-clinico', component: () => import('pages/dashboard/ClinicalHistoryPage.vue') },
          {
            path: 'plan-tratamiento',
            component: () => import('pages/dashboard/TreatmentPlanPage.vue'),
          },
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
