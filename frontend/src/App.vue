<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useTheme } from 'src/composables/useTheme.js'

const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})
</script>
