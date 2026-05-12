<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import AppPaginationBar from '../components/AppPaginationBar.vue'
import { apiJson, type Paged, withPagination } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'

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
const { isAdmin } = useAuth()

async function load() {
  const data = await apiJson<Paged<Pipeline>>(
    withPagination(`/api/environments/${environmentId}/pipelines`, page.value),
  )
  pipelines.value = data.items
  totalPages.value = data.total_pages
  total.value = data.total
}

onMounted(load)

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

    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-2xl font-semibold text-slate-800">Pipelines do ambiente</h1>
      <RouterLink
        v-if="isAdmin"
        :to="`/environments/${environmentId}/pipelines/new`"
        class="inline-flex items-center gap-2 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-700"
      >
        <font-awesome-icon :icon="['fas', 'plus']" />
        Nova pipeline
      </RouterLink>
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
              <div class="flex items-center justify-end gap-1">
                <RouterLink
                  :to="`/pipelines/${p.id}#comandos`"
                  class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                  title="Abrir pipeline"
                  aria-label="Abrir pipeline"
                >
                  <font-awesome-icon :icon="['fas', 'project-diagram']" />
                </RouterLink>
                <RouterLink
                  v-if="isAdmin"
                  :to="`/pipelines/${p.id}/edit`"
                  class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                  title="Editar pipeline"
                  aria-label="Editar pipeline"
                >
                  <font-awesome-icon :icon="['fas', 'pen-to-square']" />
                </RouterLink>
              </div>
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
