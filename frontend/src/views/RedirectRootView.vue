<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { refreshMe, isAuthenticated } = useAuth()

onMounted(async () => {
  await refreshMe()
  await router.replace(isAuthenticated.value ? '/dashboard' : '/login')
})
</script>

<template>
  <div class="p-8 text-center text-slate-500">Carregando…</div>
</template>
