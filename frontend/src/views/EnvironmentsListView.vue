<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import AppPaginationBar from '../components/AppPaginationBar.vue'
import { apiJson, type Paged, withPagination } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'

interface Project {
  id: string
  name: string
}

interface Environment {
  id: string
  project_id: string
  name: string
  environment_type: string
  server_id: string
  working_directory: string
  is_active: boolean
}

const route = useRoute()
const projectId = computed(() => route.params.projectId as string)

const project = ref<Project | null>(null)
const environments = ref<Environment[]>([])
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)
const { isAdmin } = useAuth()

async function loadEnvironments() {
  const data = await apiJson<Paged<Environment>>(
    withPagination(`/api/projects/${projectId.value}/environments`, page.value),
  )
  environments.value = data.items
  totalPages.value = data.total_pages
  total.value = data.total
}

onMounted(async () => {
  project.value = await apiJson<Project>(`/api/projects/${projectId.value}`)
  page.value = 1
  await loadEnvironments()
})

function onPageChange(p: number) {
  page.value = p
  loadEnvironments()
}
</script>

<template>
  <div>
    <RouterLink
      to="/projects"
      class="mb-4 inline-flex items-center gap-1 text-sm text-sky-600 hover:underline"
    >
      <font-awesome-icon :icon="['fas', 'arrow-left']" />
      Projetos
    </RouterLink>

    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div class="min-w-0">
        <h1 class="text-2xl font-semibold text-slate-800">Ambientes</h1>
        <p v-if="project" class="mt-1 text-sm text-slate-600">
          Projeto: <strong>{{ project.name }}</strong>
        </p>
      </div>
      <RouterLink
        v-if="isAdmin"
        :to="`/projects/${projectId}/environments/new`"
        class="inline-flex items-center gap-2 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-700"
      >
        <font-awesome-icon :icon="['fas', 'plus']" />
        Novo ambiente
      </RouterLink>
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Nome</th>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Tipo</th>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Ativo</th>
            <th class="px-4 py-2 text-right font-medium text-slate-700">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="e in environments" :key="e.id">
            <td class="px-4 py-2">{{ e.name }}</td>
            <td class="px-4 py-2">{{ e.environment_type }}</td>
            <td class="px-4 py-2">{{ e.is_active ? 'Sim' : 'Não' }}</td>
            <td class="px-4 py-2 text-right">
              <div class="flex items-center justify-end gap-1">
                <RouterLink
                  :to="`/environments/${e.id}/pipelines`"
                  class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                  title="Pipelines"
                  aria-label="Ver pipelines do ambiente"
                >
                  <font-awesome-icon :icon="['fas', 'project-diagram']" />
                </RouterLink>
                <RouterLink
                  v-if="isAdmin"
                  :to="`/projects/${projectId}/environments/${e.id}/server-dotenv`"
                  class="inline-flex rounded p-2 text-amber-700 hover:bg-amber-50"
                  title=".env no servidor"
                  aria-label="Editar ficheiro .env no servidor"
                >
                  <font-awesome-icon :icon="['fas', 'file-lines']" />
                </RouterLink>
                <RouterLink
                  v-if="isAdmin"
                  :to="`/projects/${projectId}/environments/${e.id}/edit`"
                  class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                  title="Editar ambiente"
                  aria-label="Editar ambiente"
                >
                  <font-awesome-icon :icon="['fas', 'pen-to-square']" />
                </RouterLink>
              </div>
            </td>
          </tr>
          <tr v-if="!environments.length">
            <td colspan="4" class="px-4 py-8 text-center text-slate-500">Nenhum ambiente.</td>
          </tr>
        </tbody>
      </table>
      <AppPaginationBar :page="page" :total-pages="totalPages" :total="total" @update:page="onPageChange" />
    </div>
  </div>
</template>
