<template>
  <q-page
    class="relative flex flex-col items-center justify-center min-h-screen bg-[#030712] overflow-hidden select-none font-sans">


    <div
      class="absolute inset-0 bg-[linear-gradient(to_right,#1f293710_1px,transparent_1px),linear-gradient(to_bottom,#1f293710_1px,transparent_1px)] bg-[size:4rem_4rem]">
    </div>
    <div
      class="absolute top-1/3 left-1/4 w-[450px] h-[450px] bg-cyan-500/5 rounded-full blur-[120px] pointer-events-none">
    </div>
    <div
      class="absolute bottom-1/3 right-1/4 w-[450px] h-[450px] bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none">
    </div>


    <div
      class="relative z-10 max-w-md w-full mx-4 p-8 rounded-3xl bg-slate-950/40 border border-slate-800/80 backdrop-blur-xl shadow-[0_0_50px_-12px_rgba(6,182,212,0.15)] space-y-6">


      <div class="text-center space-y-2">
        <div class="flex justify-center mb-4">

          <div
            class="relative w-20 h-20 bg-slate-950/80 border border-emerald-500/30 rounded-2xl backdrop-blur-md shadow-[inset_0_0_15px_rgba(16,185,129,0.1)] overflow-hidden">
            <img src="/src/assets/LOGOSMILEOS.png" alt="SmileOS Logo"
              class="w-full h-full object-cover filter drop-shadow-[0_0_10px_rgba(6,182,212,0.3)]" />
          </div>
        </div>
        <h2 class="text-2xl font-black tracking-tight text-white uppercase">
          Acceso a <span
            class="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-400 to-emerald-400 drop-shadow-[0_0_15px_rgba(34,211,238,0.3)]">SmileOS</span>
        </h2>
        <p class="text-xs font-mono tracking-wider text-slate-400">
          AUTENTICACIÓN DE CREDENCIALES
        </p>
      </div>


      <form @submit.prevent="handleLogin" class="space-y-4">


        <div class="space-y-1.5">
          <label class="text-[10px] font-mono tracking-widest text-cyan-500/80 uppercase px-1">Identificador de
            Usuario</label>
          <div class="relative group">
            <span
              class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-500 group-focus-within:text-cyan-400 transition-colors">
              👤
            </span>
            <input v-model="username" type="text" placeholder="Ej. dr.garcia"
              class="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-800 rounded-xl text-slate-200 text-sm placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 focus:bg-slate-900/80 transition-all font-sans"
              required />
          </div>
        </div>


        <div class="relative group">
          <span
            class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-500 group-focus-within:text-cyan-400 transition-colors">
            🔒
          </span>

          <input v-model="password" :type="showPassword ? 'text' : 'password'" placeholder="••••••••••••"
            class="w-full pl-10 pr-12 py-3 bg-slate-900/50 border border-slate-800 rounded-xl text-slate-200 text-sm placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 focus:bg-slate-900/80 transition-all font-sans"
            required />

          <button type="button" @click="showPassword = !showPassword"
            class="absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-500 hover:text-cyan-400 transition-colors focus:outline-none select-none">
            <span class="text-sm">
              {{ showPassword ? '👁️' : '🙈' }}
            </span>
          </button>
        </div>


        <div class="flex items-center justify-between px-1 pt-1">
          <label class="flex items-center text-xs text-slate-400 cursor-pointer select-none">
            <input type="checkbox"
              class="w-4 h-4 rounded border-slate-800 bg-slate-900/50 text-cyan-500 focus:ring-0 focus:ring-offset-0 mr-2 accent-cyan-500" />
            Mantener sesión iniciada
          </label>
        </div>


        <button type="submit"
          class="relative w-full mt-2 py-3 bg-gradient-to-r from-cyan-500 via-teal-500 to-emerald-500 text-slate-950 font-bold tracking-wider text-xs uppercase rounded-xl shadow-lg shadow-cyan-500/10 hover:shadow-cyan-500/20 active:scale-[0.99] transition-all duration-200 overflow-hidden group">
          <!-- Efecto de brillo interior al pasar el cursor -->
          <span
            class="absolute inset-0 w-full h-full bg-white/10 transform -skews-x-12 -translate-x-full group-hover:animate-[shine_0.75s_ease-out]"></span>
          <span class="relative z-10 flex items-center justify-center gap-2">
            Iniciar Sesion
          </span>
        </button>
      </form>

    </div>


    <div class="absolute bottom-6 left-8 font-mono text-[9px] text-slate-600 tracking-widest hidden sm:block">
      SEC_SYS // AUTH_MODE: TOKEN_LOCAL
    </div>
    <div class="absolute bottom-6 right-8 font-mono text-[9px] text-slate-600 tracking-widest hidden sm:block">
      STANDBY // READY_TO_CONNECT
    </div>

  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Variables reactivas para el formulario
const username = ref('')
const password = ref('')

// Control de visibilidad de la contraseña
const showPassword = ref(false)

const handleLogin = () => {
  // Mini backend local de prueba
  if (username.value === 'admin' && password.value === 'admin') {
    console.log('Credenciales válidas. Accediendo al sistema...')
    router.push('/dashboard')
  } else {
    alert('Acceso Denegado: Credenciales de seguridad incorrectas.')
  }
}
</script>

<style>
/* Animación personalizada para el brillo reflectante del botón de login */
@keyframes shine {
  100% {
    transform: translateX(100%);
  }
}
</style>
