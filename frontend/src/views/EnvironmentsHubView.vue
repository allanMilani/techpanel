<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import AppPaginationBar from '../components/AppPaginationBar.vue'
import { DEFAULT_PAGE_SIZE, fetchAllPaged } from '../composables/useApi'
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

interface Row {
  project: Project
  environment: Environment
}

const rows = ref<Row[]>([])
const projects = ref<Project[]>([])
const page = ref(1)
const { isAdmin } = useAuth()

const perPage = DEFAULT_PAGE_SIZE

/** Primeiro projeto (nome) para o atalho "Novo ambiente"; com vários projetos use Projetos para outro. */
const newEnvironmentTo = computed(() => {
  const list = [...projects.value].sort((a, b) => a.name.localeCompare(b.name, 'pt'))
  if (!list.length) return '/projects'
  return `/projects/${list[0].id}/environments/new`
})

const total = computed(() => rows.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / perPage)))

const pagedRows = computed(() => {
  const start = (page.value - 1) * perPage
  return rows.value.slice(start, start + perPage)
})

function onPageChange(p: number) {
  page.value = p
}

onMounted(async () => {
  const list = await fetchAllPaged<Project>('/api/projects/')
  projects.value = list
  const lists = await Promise.all(
    list.map(async (project) => {
      const envs = await fetchAllPaged<Environment>(`/api/projects/${project.id}/environments`)
      return envs.map((environment) => ({ project, environment }))
    }),
  )
  rows.value = lists.flat()
  page.value = 1
})
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
        <p class="mt-1 text-sm text-slate-600">Todos os ambientes, por projeto.</p>
      </div>
      <RouterLink
        v-if="isAdmin && projects.length"
        :to="newEnvironmentTo"
        class="inline-flex items-center gap-2 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-700"
        :title="
          projects.length > 1
            ? 'Abre o formulário no primeiro projeto (A–Z). Para outro projeto, use Projetos.'
            : 'Abrir formulário de novo ambiente'
        "
      >
        <font-awesome-icon :icon="['fas', 'plus']" />
        Novo ambiente
      </RouterLink>
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Projeto</th>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Ambiente</th>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Tipo</th>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Ativo</th>
            <th class="px-4 py-2 text-right font-medium text-slate-700">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="row in pagedRows" :key="`${row.project.id}-${row.environment.id}`">
            <td class="px-4 py-2 font-medium">{{ row.project.name }}</td>
            <td class="px-4 py-2">{{ row.environment.name }}</td>
            <td class="px-4 py-2">{{ row.environment.environment_type }}</td>
            <td class="px-4 py-2">{{ row.environment.is_active ? 'Sim' : 'Não' }}</td>
            <td class="px-4 py-2 text-right">
              <div class="flex items-center justify-end gap-1">
                <RouterLink
                  :to="`/environments/${row.environment.id}/pipelines`"
                  class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                  title="Pipelines"
                  aria-label="Ver pipelines do ambiente"
                >
                  <font-awesome-icon :icon="['fas', 'project-diagram']" />
                </RouterLink>
                <RouterLink
                  v-if="isAdmin"
                  :to="`/projects/${row.project.id}/environments/${row.environment.id}/edit`"
                  class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                  title="Editar ambiente"
                  aria-label="Editar ambiente"
                >
                  <font-awesome-icon :icon="['fas', 'pen-to-square']" />
                </RouterLink>
              </div>
            </td>
          </tr>
          <tr v-if="!rows.length">
            <td colspan="5" class="px-4 py-8 text-center text-slate-500">Nenhum ambiente.</td>
          </tr>
        </tbody>
      </table>
      <AppPaginationBar
        :page="page"
        :total-pages="totalPages"
        :total="total"
        @update:page="onPageChange"
      />
    </div>
  </div>
</template>
