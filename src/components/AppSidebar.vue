<template>
  <q-drawer v-model="drawerOpen" side="left" :mini="miniState" :width="260" :breakpoint="768"
    bordered :show-if-above="true">
    <q-scroll-area class="fit bg-sidebar tx-body">
      <q-list padding>

        <q-item class="q-mb-md" style="padding: 16px 12px;">
          <q-item-section avatar v-if="!miniState">
            <img src="/src/assets/LOGOSMILEOS.png" class="w-8 h-8 rounded" />
          </q-item-section>
          <q-item-section>
            <div class="text-[#e3bc50] text-sm font-bold tracking-wider">SMILEOS</div>
            <div v-if="!miniState" class="text-[10px] tx-muted font-mono tracking-widest">DENTAL SYSTEM</div>
          </q-item-section>
        </q-item>

        <q-separator class="q-mb-sm" />

        <div v-if="!miniState" class="text-[10px] tx-muted font-mono tracking-widest q-px-md q-py-sm uppercase">
          Administrativo
        </div>

        <q-item v-for="item in adminItems" :key="item.label" :to="item.to" clickable
          :class="activeClass" class="sidebar-item">
          <q-item-section avatar>
            <q-icon :name="item.icon" size="20px" />
          </q-item-section>
          <q-item-section v-if="!miniState">
            <q-item-label class="text-sm">{{ item.label }}</q-item-label>
          </q-item-section>
        </q-item>

        <q-separator class="q-my-sm" />

        <div v-if="!miniState" class="text-[10px] tx-muted font-mono tracking-widest q-px-md q-py-sm uppercase">
          Clínico
        </div>

        <q-item v-for="item in clinicoItems" :key="item.label" :to="item.to" clickable
          :class="activeClass" class="sidebar-item">
          <q-item-section avatar>
            <q-icon :name="item.icon" size="20px" />
          </q-item-section>
          <q-item-section v-if="!miniState">
            <q-item-label class="text-sm">{{ item.label }}</q-item-label>
          </q-item-section>
        </q-item>

        <q-separator class="q-my-sm" />

        <q-item to="/dashboard/reportes" clickable :class="activeClass" class="sidebar-item">
          <q-item-section avatar>
            <q-icon name="bar_chart" size="20px" />
          </q-item-section>
          <q-item-section v-if="!miniState">
            <q-item-label class="text-sm">Reportes</q-item-label>
          </q-item-section>
        </q-item>

        <q-separator class="q-my-sm" />

        <q-item clickable @click="toggleDark" class="sidebar-item">
          <q-item-section avatar>
            <q-icon :name="isDark ? 'light_mode' : 'dark_mode'" size="20px" />
          </q-item-section>
          <q-item-section v-if="!miniState">
            <q-item-label class="text-sm">{{ isDark ? 'Modo Claro' : 'Modo Oscuro' }}</q-item-label>
          </q-item-section>
        </q-item>

        <q-item @click="logout" clickable class="sidebar-item tx-muted hover:text-red-400">
          <q-item-section avatar>
            <q-icon name="logout" size="20px" />
          </q-item-section>
          <q-item-section v-if="!miniState">
            <q-item-label class="text-sm">Cerrar Sesión</q-item-label>
          </q-item-section>
        </q-item>

      </q-list>
    </q-scroll-area>

    <div class="absolute top-2 right-2 tx-muted" v-if="!miniState">
      <q-btn dense flat round icon="chevron_left" @click="miniState = true" class="tx-muted" size="sm" />
    </div>
    <div class="absolute top-2 right-2 tx-muted" v-else>
      <q-btn dense flat round icon="chevron_right" @click="miniState = false" class="tx-muted" size="sm" />
    </div>
  </q-drawer>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'src/composables/useTheme.js'

const router = useRouter()
const { isDark, toggleDark } = useTheme()
const drawerOpen = ref(true)
const miniState = ref(false)

const activeClass = 'text-[#e3bc50]'

const adminItems = [
  { label: 'Citas', icon: 'calendar_today', to: '/dashboard/citas' },
  { label: 'Pacientes', icon: 'people', to: '/dashboard/pacientes' },
  { label: 'Galería', icon: 'photo_library', to: '/dashboard/galeria' },
  { label: 'Documentos', icon: 'description', to: '/dashboard/documentos' },
]

const clinicoItems = [
  { label: 'Evoluciones', icon: 'timeline', to: '/dashboard/evoluciones' },
  { label: 'Plan de Tratamiento', icon: 'assignment', to: '/dashboard/plan-tratamiento' },
  { label: 'Documentos Clínicos', icon: 'note_alt', to: '/dashboard/documentos-clinicos' },
  { label: 'Periodontograma', icon: 'grid_view', to: '/dashboard/periodontograma' },
]

const logout = () => {
  router.push('/login')
}
</script>

<style scoped>
.sidebar-item {
  border-radius: 0 20px 20px 0;
  margin: 2px 8px 2px 0;
  padding: 8px 12px;
  transition: all 0.2s;
}

.sidebar-item:hover {
  background: var(--bg-hover);
}

.sidebar-active {
  background: var(--bg-active) !important;
  border-right: 3px solid var(--accent);
}
</style>
