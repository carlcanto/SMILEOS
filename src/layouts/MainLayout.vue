<template>
  <q-layout view="hHh Lpr lff" class="bg-main tx-body">
    <AppSidebar v-if="showSidebar" />
    <q-page-container class="bg-main">
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from 'components/AppSidebar.vue'

const route = useRoute()
const showSidebar = computed(() => route.path.startsWith('/dashboard'))
</script>
