<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import AppPaginationBar from '../components/AppPaginationBar.vue'
import AppTextField from '../components/inputs/AppTextField.vue'
import { ApiError, apiJson, type Paged, withPagination } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import { useToast } from '../composables/useToast'

interface Pipeline {
  id: string
  environment_id: string
  name: string
  description: string | null
}

const route = useRoute()
const environmentId = route.params.environmentId as string

const pipelines = ref<Pipeline[]>([])
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)
const newName = ref('')
const newDesc = ref('')
const { isAdmin } = useAuth()
const { showToast } = useToast()

async function load() {
  const data = await apiJson<Paged<Pipeline>>(
    withPagination(`/api/environments/${environmentId}/pipelines`, page.value),
  )
  pipelines.value = data.items
  totalPages.value = data.total_pages
  total.value = data.total
}

onMounted(load)

async function createPipeline() {
  try {
    await apiJson(`/api/environments/${environmentId}/pipelines`, {
      method: 'POST',
      body: JSON.stringify({
        name: newName.value,
        description: newDesc.value.trim() || null,
      }),
    })
    newName.value = ''
    newDesc.value = ''
    page.value = 1
    await load()
    showToast('Pipeline criado.', 'success')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível criar o pipeline.'
    showToast(msg, 'error')
  }
}

function onPageChange(p: number) {
  page.value = p
  load()
}
</script>

<template>
  <div>
    <RouterLink to="/projects" class="mb-4 inline-flex text-sm text-sky-600 hover:underline">
      ← Projetos
    </RouterLink>
    <h1 class="mb-6 text-2xl font-semibold text-slate-800">Pipelines do ambiente</h1>

    <div v-if="isAdmin" class="mb-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h2 class="mb-3 text-lg font-medium">Nova pipeline</h2>
      <form class="flex flex-wrap items-end gap-3" @submit.prevent="createPipeline">
        <div class="min-w-[200px] flex-1">
          <AppTextField id="pname" v-model="newName" label="Nome" required />
        </div>
        <div class="min-w-[200px] flex-1">
          <AppTextField id="pdesc" v-model="newDesc" label="Descrição" />
        </div>
        <button
          type="submit"
          class="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700"
        >
          Criar
        </button>
      </form>
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Nome</th>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Descrição</th>
            <th class="px-4 py-2 text-right font-medium text-slate-700">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="p in pipelines" :key="p.id">
            <td class="px-4 py-3 font-medium text-slate-900">{{ p.name }}</td>
            <td class="max-w-md px-4 py-3 text-slate-600">
              <span class="line-clamp-2">{{ p.description || '—' }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              <RouterLink
                :to="`/pipelines/${p.id}#comandos`"
                class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                title="Abrir pipeline"
                aria-label="Abrir pipeline"
              >
                <font-awesome-icon :icon="['fas', 'project-diagram']" />
              </RouterLink>
            </td>
          </tr>
          <tr v-if="!pipelines.length">
            <td colspan="3" class="px-4 py-8 text-center text-slate-500">Nenhum pipeline.</td>
          </tr>
        </tbody>
      </table>
      <AppPaginationBar :page="page" :total-pages="totalPages" :total="total" @update:page="onPageChange" />
    </div>
  </div>
</template>
