<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { apiJson, type Paged, withPagination } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'

interface Project {
  id: string
  name: string
  repo_github: string
  tech_stack: string
}

interface Server {
  id: string
  name: string
  host: string
}

const projects = ref<Project[]>([])
const servers = ref<Server[]>([])
const projectTotal = ref(0)
const serverTotal = ref(0)
const { isAdmin } = useAuth()

onMounted(async () => {
  const p = await apiJson<Paged<Project>>(withPagination('/api/projects/', 1))
  projects.value = p.items
  projectTotal.value = p.total
  if (isAdmin.value) {
    try {
      const s = await apiJson<Paged<Server>>(withPagination('/api/servers/', 1))
      servers.value = s.items
      serverTotal.value = s.total
    } catch {
      servers.value = []
      serverTotal.value = 0
    }
  }
})
</script>

<template>
  <div>
    <h1 class="mb-2 text-2xl font-semibold text-slate-800">Início</h1>
    <p class="mb-8 text-slate-600">Atalhos para as áreas principais.</p>

    <div class="grid gap-6 md:grid-cols-2">
      <div class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-4 text-lg font-medium text-slate-800">Projetos</h2>
        <RouterLink
          to="/projects"
          class="inline-flex items-center gap-2 rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700"
        >
          <font-awesome-icon :icon="['fas', 'project-diagram']" />
          Abrir projetos
        </RouterLink>
        <p v-if="projectTotal" class="mt-3 text-sm text-slate-500">
          {{ projectTotal }} projeto(s) cadastrado(s).
        </p>
      </div>

      <div
        v-if="isAdmin"
        class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 class="mb-4 text-lg font-medium text-slate-800">Servidores</h2>
        <RouterLink
          to="/servers"
          class="inline-flex items-center gap-2 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900"
        >
          <font-awesome-icon :icon="['fas', 'server']" />
          Abrir servidores
        </RouterLink>
        <p v-if="serverTotal" class="mt-3 text-sm text-slate-500">
          {{ serverTotal }} servidor(es).
        </p>
      </div>
    </div>
  </div>
</template>
