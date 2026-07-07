<template>
  <q-page
    class="relative flex flex-col items-center justify-center min-h-screen bg-[#030712] text-white p-6 overflow-hidden select-none">

    <!-- EFECTOS DE FONDO FUTURISTAS -->
    <!-- Malla tecnológica (Grid) -->
    <div
      class="absolute inset-0 bg-[linear-gradient(to_right,#1f293710_1px,transparent_1px),linear-gradient(to_bottom,#1f293710_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)]">
    </div>

    <!-- Resplandores de Neón Ambientales (Glow Orbs) -->
    <div
      class="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-[120px] pointer-events-none">
    </div>
    <div
      class="absolute bottom-1/4 left-1/2 -translate-x-1/2 w-80 h-80 bg-cyan-500/10 rounded-full blur-[100px] pointer-events-none">
    </div>

    <!-- CONTENEDOR PRINCIPAL -->
    <div
      class="relative z-10 max-w-md w-full text-center space-y-12 backdrop-blur-sm p-8 rounded-3xl border border-slate-800/40 bg-slate-900/20">

      <!-- LOGO CON ESCÁNER CYBERPUNK -->
      <div class="relative inline-flex justify-center group">
        <!-- Círculo de pulso holográfico trasero -->
        <div
          class="absolute inset-0 bg-gradient-to-tr from-emerald-500 to-cyan-500 rounded-full blur-xl opacity-30 group-hover:opacity-50 transition-opacity duration-1000 animate-pulse">
        </div>


        <!-- Contenedor del Logo -->

        <div
          class="relative p-6 bg-slate-950/80 border border-emerald-500/30 rounded-3xl backdrop-blur-md shadow-[inset_0_0_20px_rgba(16,185,129,0.1)]">

          <img src="/src/assets/LOGOSMILEOS.png" alt="SmileOS Logo"
            class="w-28 h-28 object-contain filter drop-shadow-[0_0_15px_rgba(6,182,212,0.3)] animate-[float_4s_ease-in-out_infinite]" />
          <!-- Línea de escaneo láser horizontal -->
          <div
            class="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_10px_#06b6d4] animate-[scan_2.5s_linear_infinite]">
          </div>
        </div>
      </div>

      <!-- TEXTOS HOLOGRÁFICOS -->
      <div class="space-y-3">
        <h1 class="text-4xl font-black tracking-[0.2em] uppercase text-white font-mono">
          <span
            class="text-transparent bg-clip-text bg-gradient-to-r from-slate-100 via-slate-300 to-slate-500">Smile</span>
          <span
            class="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-emerald-400 drop-shadow-[0_0_15px_rgba(6,182,212,0.4)]">OS</span>
        </h1>

        <!-- Subtítulo tipo terminal de comando -->
        <div class="flex items-center justify-center space-x-2 text-xs font-mono tracking-widest text-emerald-400/70">
          <span class="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
          <span>INICIANDO EL SISTEMA...</span>
        </div>
      </div>

      <!-- INTERFAZ DE CARGA HUD (Heads-Up Display) -->
      <div class="space-y-4 max-w-xs mx-auto">
        <!-- Contenedor de la barra -->
        <div class="relative w-full h-2 bg-slate-950 rounded-full p-[2px] border border-slate-800/80 shadow-inner">
          <!-- Progreso de la barra de energía -->
          <div
            class="h-full bg-gradient-to-r from-cyan-500 via-emerald-400 to-emerald-500 rounded-full transition-all ease-out duration-150 shadow-[0_0_12px_#10b981]"
            :style="{ width: progress + '%' }"></div>
        </div>

        <!-- Datos métricos de carga -->
        <div class="flex justify-between items-center text-[10px] font-mono text-slate-500 tracking-wider px-1">
          <div class="flex items-center space-x-1">
            <span class="text-cyan-500/80">SYS_STATUS:</span>
            <span class="text-slate-400">{{ progress < 40 ? 'LOADING_LIBS' : progress < 80 ? 'BOOTING_UI' : 'READY'
            }}</span>
          </div>
          <span class="text-emerald-400 font-bold drop-shadow-[0_0_5px_rgba(16,185,129,0.3)]">{{ Math.round(progress)
          }}%</span>
        </div>
      </div>
    </div>
    <!-- MARCOS Y DETALLES DE ESQUINA TECH -->
    <div
      class="absolute top-6 left-6 font-mono text-[9px] text-slate-600 tracking-widest pointer-events-none hidden sm:block">
      SYS_REV_2026 // THESIS_PROJECT
    </div>
    <div
      class="absolute bottom-6 right-6 font-mono text-[9px] text-slate-600 tracking-widest pointer-events-none hidden sm:block">
      SECURE_CONNECTION_SSL
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const progress = ref(0)

onMounted(() => {
  const duration = 5000 // 5 segundos
  const intervalTime = 50
  const step = (100 / duration) * intervalTime

  const timer = setInterval(() => {
    if (progress.value < 100) {
      progress.value += step
    } else {
      clearInterval(timer)
      router.push('/login')
    }
  }, intervalTime)
})
</script>

<style scoped>
/* ANIMACIONES PERSONALIZADAS VIA CSS */

/* Efecto Flotante para el Logo */
@keyframes float {

  0%,
  100% {
    transform: translateY(0px);
  }

  50% {
    transform: translateY(-8px);
  }
}

/* Láser de Escaneo */
@keyframes scan {
  0% {
    top: 0%;
    opacity: 0;
  }

  10% {
    opacity: 1;
  }

  90% {
    opacity: 1;
  }

  100% {
    top: 100%;
    opacity: 0;
  }
}
</style>
