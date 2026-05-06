<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import AppPaginationBar from '../components/AppPaginationBar.vue'
import { ApiError, apiJson, apiJsonNoBody, type Paged, withPagination } from '../composables/useApi'
import { useConfirm } from '../composables/useConfirm'
import { useToast } from '../composables/useToast'

interface Server {
  id: string
  name: string
  host: string
  port: number
  ssh_user: string
  connection_kind: string
}

const servers = ref<Server[]>([])
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)
const route = useRoute()
const { requestConfirm } = useConfirm()
const { showToast } = useToast()

async function load() {
  const data = await apiJson<Paged<Server>>(withPagination('/api/servers/', page.value))
  servers.value = data.items
  totalPages.value = data.total_pages
  total.value = data.total
}

onMounted(async () => {
  await load()
  const q = route.query.connection_test as string | undefined
  const id = route.query.id as string | undefined
  if (q && id) {
    showToast(
      q === 'ok'
        ? `Teste de conexão OK para o servidor ${id}.`
        : `Teste de conexão falhou para o servidor ${id}.`,
      q === 'ok' ? 'success' : 'error',
    )
  }
})

async function testConn(id: string) {
  try {
    const r = await apiJson<{ ok: boolean }>(`/api/servers/${id}/test`, { method: 'POST' })
    showToast(
      r.ok ? `Conexão OK (${id}).` : `Conexão falhou (${id}).`,
      r.ok ? 'success' : 'error',
    )
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Falha ao testar conexão.'
    showToast(msg, 'error')
  }
}

async function remove(id: string) {
  const ok = await requestConfirm('Excluir este servidor?')
  if (!ok) return
  try {
    await apiJsonNoBody(`/api/servers/${id}`, { method: 'DELETE' })
    page.value = 1
    await load()
    showToast('Servidor excluído.', 'success')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível excluir o servidor.'
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
      <h1 class="text-2xl font-semibold text-slate-800">Servidores</h1>
      <RouterLink
        to="/servers/new"
        class="inline-flex items-center gap-2 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-700"
      >
        <font-awesome-icon :icon="['fas', 'plus']" />
        Novo servidor
      </RouterLink>
    </div>
    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Nome</th>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Host</th>
            <th class="px-4 py-2 text-left font-medium text-slate-700">Tipo</th>
            <th class="px-4 py-2 text-right font-medium text-slate-700">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="s in servers" :key="s.id">
            <td class="px-4 py-2">{{ s.name }}</td>
            <td class="px-4 py-2 font-mono text-xs">{{ s.host }}:{{ s.port }}</td>
            <td class="px-4 py-2">{{ s.connection_kind }}</td>
            <td class="px-4 py-2 text-right text-nowrap">
              <div class="flex items-center justify-end gap-1">
                <button
                  type="button"
                  class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                  title="Testar conexão SSH"
                  aria-label="Testar conexão SSH"
                  @click="testConn(s.id)"
                >
                  <font-awesome-icon :icon="['fas', 'terminal']" />
                </button>
                <RouterLink
                  :to="`/servers/${s.id}/edit`"
                  class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                  title="Editar servidor"
                  aria-label="Editar servidor"
                >
                  <font-awesome-icon :icon="['fas', 'pen-to-square']" />
                </RouterLink>
                <button
                  type="button"
                  class="inline-flex rounded p-2 text-red-600 hover:bg-red-50"
                  title="Excluir servidor"
                  aria-label="Excluir servidor"
                  @click="remove(s.id)"
                >
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!servers.length">
            <td colspan="4" class="px-4 py-8 text-center text-slate-500">Nenhum servidor.</td>
          </tr>
        </tbody>
      </table>
      <AppPaginationBar :page="page" :total-pages="totalPages" :total="total" @update:page="onPageChange" />
    </div>
  </div>
</template>
