<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import AppPaginationBar from '../components/AppPaginationBar.vue'
import { ApiError, apiJson, apiJsonNoBody, type Paged, withPagination } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import { useConfirm } from '../composables/useConfirm'
import { useToast } from '../composables/useToast'

interface Project {
  id: string
  name: string
  repo_github: string
  tech_stack: string
}

const projects = ref<Project[]>([])
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)
const { isAdmin } = useAuth()
const { requestConfirm } = useConfirm()
const { showToast } = useToast()

async function load() {
  const data = await apiJson<Paged<Project>>(withPagination('/api/projects/', page.value))
  projects.value = data.items
  totalPages.value = data.total_pages
  total.value = data.total
}

onMounted(load)

async function remove(id: string) {
  const ok = await requestConfirm('Excluir este projeto?')
  if (!ok) return
  try {
    await apiJsonNoBody(`/api/projects/${id}`, { method: 'DELETE' })
    page.value = 1
    await load()
    showToast('Projeto excluído.', 'success')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível excluir o projeto.'
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
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-2xl font-semibold text-slate-800">Projetos</h1>
      <RouterLink
        v-if="isAdmin"
        to="/projects/new"
        class="inline-flex items-center gap-2 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-700"
      >
        <font-awesome-icon :icon="['fas', 'plus']" />
        Novo projeto
      </RouterLink>
    </div>
    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Nome</th>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Repositório</th>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Stack</th>
            <th class="px-4 py-2 text-right font-medium text-slate-700">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="p in projects" :key="p.id">
            <td class="px-4 py-2 font-medium">{{ p.name }}</td>
            <td class="max-w-xs truncate px-4 py-2 font-mono text-xs">{{ p.repo_github }}</td>
            <td class="px-4 py-2">{{ p.tech_stack }}</td>
            <td class="px-4 py-2 text-right">
              <div class="flex items-center justify-end gap-1">
                <RouterLink
                  v-if="isAdmin"
                  :to="`/projects/${p.id}/edit`"
                  class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                  title="Editar projeto"
                  aria-label="Editar projeto"
                >
                  <font-awesome-icon :icon="['fas', 'pen-to-square']" />
                </RouterLink>
                <button
                  v-if="isAdmin"
                  type="button"
                  class="inline-flex rounded p-2 text-red-600 hover:bg-red-50"
                  title="Excluir projeto"
                  aria-label="Excluir projeto"
                  @click="remove(p.id)"
                >
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!projects.length">
            <td colspan="4" class="px-4 py-8 text-center text-slate-500">Nenhum projeto.</td>
          </tr>
        </tbody>
      </table>
      <AppPaginationBar :page="page" :total-pages="totalPages" :total="total" @update:page="onPageChange" />
    </div>
  </div>
</template>
