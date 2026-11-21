<template>
  <q-drawer v-model="drawerOpen" side="left" :mini="miniState" :width="280" :breakpoint="768" bordered
    :show-if-above="true" class="bg-sidebar custom-drawer transition-all">
    <q-scroll-area class="fit tx-body">
      <q-list padding class="q-px-sm">

        <!-- Header / Logo -->
        <q-item class="q-mb-md q-mt-sm rounded-xl logo-section" style="padding: 12px;">
          <q-item-section avatar>
            <div class="logo-container">
              <img src="/src/assets/LOGOSMILEOS.png" class="w-10 h-10 rounded-lg shadow-md" />
            </div>
          </q-item-section>

          <q-item-section class="q-mini-drawer-hide">
            <div class="text-[#e3bc50] text-lg font-extrabold tracking-wider drop-shadow-sm">SMILEOS</div>
            <div class="text-[10px] text-gray-500 font-mono tracking-widest opacity-90">DENTAL SYSTEM</div>
          </q-item-section>
        </q-item>

        <!-- Botón para expandir cuando está en modo mini -->
        <div v-if="miniState" class="flex justify-center q-mb-md">
          <q-btn dense flat round icon="chevron_right" @click="miniState = false"
            class="text-gray-400 hover:text-[#e3bc50] transition-colors" size="sm" />
        </div>

        <q-separator class="q-mb-md opacity-30 mx-4" />

        <!-- Sección Administrativo -->
        <div class="q-mini-drawer-hide section-title q-px-md q-pt-sm q-pb-xs">
          Administrativo
        </div>

        <q-item v-for="item in adminItems" :key="item.label" :to="item.to" clickable active-class="sidebar-active"
          class="sidebar-item">
          <q-item-section avatar>
            <q-icon :name="item.icon" size="22px" class="item-icon" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-sm font-semibold">{{ item.label }}</q-item-label>
          </q-item-section>
          <q-tooltip v-if="miniState" anchor="center right" self="center left"
            class="bg-[#e3bc50] text-black font-bold shadow-lg">
            {{ item.label }}
          </q-tooltip>
        </q-item>

        <q-separator class="q-my-md opacity-30 mx-4" />

        <!-- Sección Clínico -->
        <div class="q-mini-drawer-hide section-title q-px-md q-pt-sm q-pb-xs">
          Clínico
        </div>
        <q-item v-for="item in clinicoItems" :key="item.label" :to="item.to" clickable active-class="sidebar-active"
          class="sidebar-item">
          <q-item-section avatar>
            <q-icon :name="item.icon" size="22px" class="item-icon" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-sm font-semibold">{{ item.label }}</q-item-label>
          </q-item-section>
          <q-tooltip v-if="miniState" anchor="center right" self="center left"
            class="bg-[#e3bc50] text-black font-bold shadow-lg">
            {{ item.label }}
          </q-tooltip>
        </q-item>

        <q-separator class="q-my-md opacity-30 mx-4" />

        <!-- Reportes -->
        <q-item to="/dashboard/reportes" clickable active-class="sidebar-active" class="sidebar-item">
          <q-item-section avatar>
            <q-icon name="bar_chart" size="22px" class="item-icon" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-sm font-semibold">Reportes</q-item-label>
          </q-item-section>
          <q-tooltip v-if="miniState" anchor="center right" self="center left"
            class="bg-[#e3bc50] text-black font-bold shadow-lg">
            Reportes
          </q-tooltip>
        </q-item>

        <!-- Cerrar Sesión -->
        <q-item @click="logout" clickable class="sidebar-item logout-item">
          <q-item-section avatar>
            <q-icon name="logout" size="22px" class="item-icon" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-sm font-bold">Cerrar Sesión</q-item-label>
          </q-item-section>
          <q-tooltip v-if="miniState" anchor="center right" self="center left"
            class="bg-red-600 text-white font-bold shadow-lg">
            Cerrar Sesión
          </q-tooltip>
        </q-item>

      </q-list>
    </q-scroll-area>
  </q-drawer>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const drawerOpen = ref(true)
const miniState = ref(false)

const adminItems = [
  { label: 'Citas', icon: 'calendar_today', to: '/dashboard/citas' },
  { label: 'Pacientes', icon: 'people', to: '/dashboard/pacientes' },
  { label: 'Inventario', icon: 'inventory_2', to: '/dashboard/inventario' },
]

const clinicoItems = [
  { label: 'Historial Clínico', icon: 'medical_information', to: '/dashboard/historial-clinico' },
  { label: 'Evoluciones', icon: 'timeline', to: '/dashboard/evoluciones' },
  { label: 'Plan de Tratamiento', icon: 'assignment', to: '/dashboard/plan-tratamiento' },
]

const logout = () => {
  router.push('/login')
}
</script>

<style scoped>
/* Ajustes generales del drawer */
.custom-drawer {
  box-shadow: 2px 0 15px rgba(0, 0, 0, 0.03);
}

.section-title {
  color: #94a3b8;
  /* Slate-400 */
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  display: flex;
  align-items: center;
}

.section-title::after {
  content: "";
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(227, 188, 80, 0.4), transparent);
  margin-left: 12px;
}

/* Estilo base de los ítems: Diseño tipo pastilla (Pill) */
.sidebar-item {
  border-radius: 12px;
  margin: 6px 12px;
  padding: 10px 14px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  color: #718096;
  /* Color gris suave moderno */
  background: transparent;
}

.item-icon {
  transition: all 0.3s ease;
}

/* Efecto Hover moderno */
.sidebar-item:hover {
  background: rgba(227, 188, 80, 0.06);
  color: #c9a341;
  transform: translateX(6px);
}

.sidebar-item:hover .item-icon {
  transform: scale(1.1);
  color: #e3bc50;
}

/* Estado Activo: Resaltado principal */
.sidebar-active {
  background: linear-gradient(90deg, rgba(227, 188, 80, 0.15) 0%, rgba(227, 188, 80, 0.02) 100%) !important;
  color: #e3bc50 !important;
  box-shadow: inset 4px 0 0 0 #e3bc50, 0 4px 10px rgba(227, 188, 80, 0.08);
}

.sidebar-active .item-icon {
  filter: drop-shadow(0 0 6px rgba(227, 188, 80, 0.6));
  transform: scale(1.15);
  color: #e3bc50;
}

/* Botón de Logout Especial */
.logout-item {
  color: #f87171;
  /* Red 400 */
}

.logout-item:hover {
  background: rgba(239, 68, 68, 0.1) !important;
  color: #ef4444 !important;
  /* Red 500 */
  box-shadow: inset 4px 0 0 0 #ef4444;
}

.logout-item:hover .item-icon {
  color: #ef4444 !important;
  filter: drop-shadow(0 0 6px rgba(239, 68, 68, 0.4));
}
</style>
