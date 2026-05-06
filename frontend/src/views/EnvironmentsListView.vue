<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import AppPaginationBar from '../components/AppPaginationBar.vue'
import AppSelect from '../components/inputs/AppSelect.vue'
import AppTextField from '../components/inputs/AppTextField.vue'
import { ENVIRONMENT_TYPES } from '../constants/formOptions'
import { ApiError, apiJson, fetchAllPaged, type Paged, withPagination } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import { useToast } from '../composables/useToast'

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

interface Server {
  id: string
  name: string
}

const route = useRoute()
const projectId = computed(() => route.params.projectId as string)

const project = ref<Project | null>(null)
const environments = ref<Environment[]>([])
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)
const servers = ref<Server[]>([])
const { isAdmin } = useAuth()

const envName = ref('')
const envType = ref('staging')
const serverId = ref('')
const workDir = ref('')
const { showToast } = useToast()

const envTypeOptions = ENVIRONMENT_TYPES.map((t) => ({ value: t, label: t }))
const serverOptions = computed(() =>
  servers.value.map((s) => ({ value: s.id, label: `${s.name} (${s.id})` })),
)

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
  if (isAdmin.value) {
    servers.value = await fetchAllPaged<Server>('/api/servers/')
    if (servers.value.length && !serverId.value) {
      serverId.value = servers.value[0].id
    }
  }
  page.value = 1
  await loadEnvironments()
})

async function createEnv() {
  try {
    await apiJson(`/api/projects/${projectId.value}/environments`, {
      method: 'POST',
      body: JSON.stringify({
        name: envName.value,
        environment_type: envType.value,
        server_id: serverId.value,
        working_directory: workDir.value,
      }),
    })
    envName.value = ''
    workDir.value = ''
    page.value = 1
    await loadEnvironments()
    showToast('Ambiente criado.', 'success')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Erro ao criar o ambiente.'
    showToast(msg, 'error')
  }
}

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
    <h1 class="mb-2 text-2xl font-semibold text-slate-800">Ambientes</h1>
    <p v-if="project" class="mb-6 text-slate-600">Projeto: <strong>{{ project.name }}</strong></p>

    <div
      v-if="isAdmin"
      class="mb-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
    >
      <h2 class="mb-4 text-lg font-medium">Novo ambiente</h2>
      <form class="grid gap-4 md:grid-cols-2" @submit.prevent="createEnv">
        <AppTextField id="ename" v-model="envName" label="Nome" required />
        <AppSelect
          id="etype"
          v-model="envType"
          label="Tipo"
          :options="envTypeOptions"
          required
        />
        <AppSelect
          v-if="servers.length"
          id="srv"
          v-model="serverId"
          label="Servidor"
          :options="serverOptions"
          required
        />
        <AppTextField id="wd" v-model="workDir" label="Diretório de trabalho" required />
        <div class="md:col-span-2">
          <button
            type="submit"
            class="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700"
          >
            Criar ambiente
          </button>
        </div>
      </form>
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
