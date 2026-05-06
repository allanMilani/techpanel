<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import AppPaginationBar from '../components/AppPaginationBar.vue'
import AppSelect from '../components/inputs/AppSelect.vue'
import AppTextField from '../components/inputs/AppTextField.vue'
import AppTextarea from '../components/inputs/AppTextarea.vue'
import { ON_FAILURE_POLICIES, STEP_TYPES } from '../constants/formOptions'
import { ApiError, apiJson, apiJsonNoBody, fetchAllPaged, type Paged, withPagination } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import { useConfirm } from '../composables/useConfirm'
import { useToast } from '../composables/useToast'

interface PipelineSummary {
  id: string
  environment_id: string
  name: string
  description: string | null
  project_id: string | null
}

interface Step {
  id: string
  order: number
  name: string
  step_type: string
  command: string
  on_failure: string
  timeout_seconds: number
  working_directory: string | null
  is_active: boolean
}

interface ExecutionRow {
  id: string
  pipeline_id: string
  branch_or_tag: string
  status: string
  created_at: string
}

const route = useRoute()
const pipelineId = computed(() => route.params.pipelineId as string)

const summary = ref<PipelineSummary | null>(null)
const steps = ref<Step[]>([])
const history = ref<ExecutionRow[]>([])
const historyPage = ref(1)
const historyTotalPages = ref(1)
const historyTotal = ref(0)

const sName = ref('')
const stepType = ref('ssh_command')
const command = ref('')
const onFailure = ref('stop')
const timeoutSeconds = ref('300')
const workingDir = ref('')

const dragStepId = ref<string | null>(null)
const cancellingHistoryExecutionId = ref<string | null>(null)

const { isAdmin } = useAuth()
const { requestConfirm } = useConfirm()
const { showToast } = useToast()

const stepTypeOptions = STEP_TYPES.map((t) => ({ value: t, label: t }))
const onFailOptions = ON_FAILURE_POLICIES.map((t) => ({ value: t, label: t }))

const projectId = computed(() => summary.value?.project_id ?? '')

function formatExecutionDateTime(iso: string): string {
  const d = new Date(iso)
  if (d.toString() === 'Invalid Date') return iso
  return d.toLocaleString('pt-BR', { hour12: false })
}

const commandFieldLabel = computed(() => {
  if (stepType.value === 'ssh_command') return 'Comando SSH'
  if (stepType.value === 'http_healthcheck') return 'URL do health check'
  if (stepType.value === 'notify_webhook') return 'URL do webhook'
  return 'Comando'
})

const commandFieldHint = computed(() => {
  if (stepType.value === 'ssh_command') {
    return 'executado no servidor do ambiente; ex.: cd /var/www/app && git pull'
  }
  if (stepType.value === 'http_healthcheck') return 'ex.: https://api.exemplo.com/health'
  if (stepType.value === 'notify_webhook') return 'POST será enviado para esta URL'
  return undefined
})

async function loadStepsAll() {
  const id = pipelineId.value
  steps.value = await fetchAllPaged<Step>(`/api/pipelines/${id}`)
}

async function loadHistoryPage() {
  const id = pipelineId.value
  const data = await apiJson<Paged<ExecutionRow>>(
    withPagination(`/api/pipelines/${id}/history`, historyPage.value),
  )
  history.value = data.items
  historyTotalPages.value = data.total_pages
  historyTotal.value = data.total
}

async function load() {
  const id = pipelineId.value
  summary.value = await apiJson<PipelineSummary>(`/api/pipelines/${id}/summary`)
  await loadStepsAll()
  historyPage.value = 1
  await loadHistoryPage()
}

function onHistoryPageChange(p: number) {
  historyPage.value = p
  loadHistoryPage()
}

function scrollToRouteHash(): void {
  const raw = (route.hash || '').replace(/^#/, '')
  if (raw !== 'comandos') return
  nextTick(() => {
    document.getElementById('pipeline-comandos')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

onMounted(async () => {
  await load()
  scrollToRouteHash()
})

watch(
  () => route.params.pipelineId as string,
  async (newId, oldId) => {
    if (newId === oldId || oldId === undefined) return
    await load()
    scrollToRouteHash()
  },
)

watch(
  () => route.hash,
  () => {
    if (summary.value) scrollToRouteHash()
  },
)

async function addStep() {
  try {
    await apiJson(`/api/pipelines/${pipelineId.value}/steps`, {
      method: 'POST',
      body: JSON.stringify({
        name: sName.value,
        step_type: stepType.value,
        command: command.value,
        on_failure: onFailure.value,
        timeout_seconds: Number.parseInt(timeoutSeconds.value, 10),
        working_directory: workingDir.value.trim() || null,
      }),
    })
    sName.value = ''
    command.value = ''
    await load()
    showToast('Passo adicionado.', 'success')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível adicionar o passo.'
    showToast(msg, 'error')
  }
}

function onStepDragStart(e: DragEvent, stepId: string) {
  dragStepId.value = stepId
  e.dataTransfer?.setData('text/plain', stepId)
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
  }
}

function onStepDragEnd() {
  dragStepId.value = null
}

function onStepRowDragOver(e: DragEvent) {
  if (!isAdmin.value) return
  e.preventDefault()
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move'
  }
}

async function onStepRowDrop(e: DragEvent, targetId: string) {
  e.preventDefault()
  if (!isAdmin.value) return
  const fromId = dragStepId.value
  if (!fromId || fromId === targetId) return
  const idxFrom = steps.value.findIndex((s) => s.id === fromId)
  const idxTo = steps.value.findIndex((s) => s.id === targetId)
  if (idxFrom < 0 || idxTo < 0) return
  const next = [...steps.value]
  const [moved] = next.splice(idxFrom, 1)
  next.splice(idxTo, 0, moved)
  const orderedIds = next.map((s) => s.id)
  try {
    await apiJson(`/api/pipelines/${pipelineId.value}/steps/reorder`, {
      method: 'POST',
      body: JSON.stringify({ ordered_step_ids: orderedIds }),
    })
    await load()
    showToast('Ordem dos passos atualizada.', 'success')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível reordenar.'
    showToast(msg, 'error')
    await load()
  }
}

async function deleteStep(stepId: string) {
  const ok = await requestConfirm('Remover este passo?')
  if (!ok) return
  try {
    await apiJsonNoBody(`/api/pipelines/${pipelineId.value}/steps/${stepId}`, { method: 'DELETE' })
    await load()
    showToast('Passo removido.', 'success')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível remover o passo.'
    showToast(msg, 'error')
  }
}

function canCancelExecutionFromHistory(status: string): boolean {
  return status === 'pending' || status === 'running' || status === 'blocked'
}

async function cancelExecutionFromHistory(executionId: string) {
  const ok = await requestConfirm(
    'Cancelar esta execução? Passos pendentes ou em andamento serão ignorados e será possível disparar outra execução no projeto.',
  )
  if (!ok) return
  cancellingHistoryExecutionId.value = executionId
  try {
    await apiJsonNoBody(`/api/executions/${executionId}/cancel`, { method: 'POST' })
    showToast('Execução cancelada.', 'success')
    await load()
  } catch (e) {
    const msg = e instanceof ApiError ? (e.detail ?? e.message) : 'Não foi possível cancelar a execução.'
    showToast(msg, 'error')
  } finally {
    cancellingHistoryExecutionId.value = null
  }
}
</script>

<template>
  <div v-if="summary">
    <nav class="mb-4 text-sm text-slate-600">
      <RouterLink to="/projects" class="text-sky-600 hover:underline">Projetos</RouterLink>
      <span class="mx-2">/</span>
      <RouterLink
        v-if="projectId"
        :to="`/projects/${projectId}/environments`"
        class="text-sky-600 hover:underline"
      >
        Ambientes
      </RouterLink>
      <span class="mx-2">/</span>
      <RouterLink
        :to="`/environments/${summary.environment_id}/pipelines`"
        class="text-sky-600 hover:underline"
      >
        Pipelines
      </RouterLink>
      <span class="mx-2">/</span>
      <span class="text-slate-800">{{ summary.name }}</span>
    </nav>

    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold text-slate-800">{{ summary.name }}</h1>
        <p v-if="summary.description" class="mt-1 text-sm text-slate-600">{{ summary.description }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <RouterLink
          :to="`/pipelines/${pipelineId}/run`"
          class="inline-flex items-center gap-2 rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          <font-awesome-icon :icon="['fas', 'play']" />
          Executar
        </RouterLink>
      </div>
    </div>

    <div id="pipeline-comandos" class="scroll-mt-24 space-y-6">
      <div v-if="isAdmin" class="w-full rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-4 text-lg font-medium text-slate-800">Adicionar passo</h2>
        <form class="space-y-3 text-sm" @submit.prevent="addStep">
          <AppTextField id="sn" v-model="sName" label="Nome" required />
          <AppSelect id="st" v-model="stepType" label="Tipo" :options="stepTypeOptions" required />
          <AppTextarea
            id="cmd"
            v-model="command"
            :label="commandFieldLabel"
            :hint="commandFieldHint"
            :rows="stepType === 'ssh_command' ? 4 : 3"
            required
          />
          <div class="grid gap-3 sm:grid-cols-2">
            <AppSelect id="of" v-model="onFailure" label="Em falha" :options="onFailOptions" required />
            <AppTextField id="to" v-model="timeoutSeconds" label="Timeout (s)" type="number" required />
          </div>
          <AppTextField id="wd" v-model="workingDir" label="Working dir (opcional)" />
          <button type="submit" class="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700">
            Adicionar passo
          </button>
        </form>
      </div>

      <div class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div class="border-b border-slate-100 px-4 py-2 text-sm font-medium text-slate-800">
          Passos
          <span v-if="isAdmin" class="ml-2 font-normal text-slate-500">Arraste pelo ícone para reordenar.</span>
        </div>
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-50">
            <tr>
              <th v-if="isAdmin" class="w-10 px-2 py-2 text-left" scope="col" aria-label="Reordenar"></th>
              <th class="px-3 py-2 text-left">#</th>
              <th class="px-3 py-2 text-left">Nome</th>
              <th class="px-3 py-2 text-left">Tipo</th>
              <th class="px-3 py-2 text-left">Ativo</th>
              <th class="px-3 py-2 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="st in steps"
              :key="st.id"
              :class="{ 'opacity-60': dragStepId === st.id }"
              @dragover="onStepRowDragOver($event)"
              @drop="onStepRowDrop($event, st.id)"
            >
              <td v-if="isAdmin" class="w-10 px-2 py-2 align-middle">
                <span
                  class="inline-flex cursor-grab touch-none text-slate-400 hover:text-slate-600 active:cursor-grabbing"
                  draggable="true"
                  aria-label="Arrastar para reordenar"
                  @dragstart="onStepDragStart($event, st.id)"
                  @dragend="onStepDragEnd"
                >
                  <font-awesome-icon :icon="['fas', 'grip-vertical']" />
                </span>
              </td>
              <td class="px-3 py-2">{{ st.order }}</td>
              <td class="px-3 py-2">{{ st.name }}</td>
              <td class="px-3 py-2 font-mono text-xs">{{ st.step_type }}</td>
              <td class="px-3 py-2">{{ st.is_active ? 'Sim' : 'Não' }}</td>
              <td class="px-3 py-2 text-right">
                <div v-if="isAdmin" class="flex items-center justify-end gap-1">
                  <RouterLink
                    :to="`/pipelines/${pipelineId}/steps/${st.id}/edit`"
                    class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                    title="Editar passo"
                    aria-label="Editar passo"
                  >
                    <font-awesome-icon :icon="['fas', 'pen-to-square']" />
                  </RouterLink>
                  <button
                    type="button"
                    class="inline-flex rounded p-2 text-red-600 hover:bg-red-50"
                    title="Excluir passo"
                    aria-label="Excluir passo"
                    @click="deleteStep(st.id)"
                  >
                    <font-awesome-icon :icon="['fas', 'trash']" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!steps.length">
              <td :colspan="isAdmin ? 6 : 5" class="px-3 py-8 text-center text-slate-500">
                Nenhum passo cadastrado.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="mt-8 rounded-lg border border-slate-200 bg-white shadow-sm">
      <div class="border-b border-slate-100 px-4 py-2 text-sm font-medium">Histórico de execuções</div>
      <div class="overflow-x-auto p-4">
        <table class="min-w-full text-sm">
          <thead>
            <tr class="text-left text-slate-600">
              <th class="py-2 pr-4">Data e hora</th>
              <th class="py-2 pr-4">Branch</th>
              <th class="py-2 pr-4">Status</th>
              <th v-if="isAdmin" class="py-2 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in history" :key="h.id" class="border-t border-slate-100">
              <td class="py-2 pr-4">
                <div class="text-slate-800">{{ formatExecutionDateTime(h.created_at) }}</div>
                <div class="mt-0.5 font-mono text-xs text-slate-500">{{ h.id }}</div>
              </td>
              <td class="py-2 pr-4">{{ h.branch_or_tag }}</td>
              <td class="py-2 pr-4">
                <span
                  class="rounded px-2 py-0.5 text-xs font-medium"
                  :class="{
                    'bg-red-100 text-red-800': h.status === 'failed',
                    'bg-emerald-100 text-emerald-800': h.status === 'success',
                    'bg-amber-100 text-amber-900': h.status === 'cancelled',
                    'bg-slate-100 text-slate-700':
                      h.status !== 'failed' &&
                      h.status !== 'success' &&
                      h.status !== 'cancelled',
                  }"
                >
                  {{ h.status }}
                </span>
              </td>
              <td v-if="isAdmin" class="py-2 text-right">
                <div class="flex items-center justify-end gap-1">
                  <RouterLink
                    :to="`/executions/${h.id}/monitor`"
                    class="inline-flex rounded p-2 text-sky-600 hover:bg-sky-50"
                    title="Abrir monitor"
                    aria-label="Abrir monitor da execução"
                  >
                    <font-awesome-icon :icon="['fas', 'terminal']" />
                  </RouterLink>
                  <button
                    v-if="canCancelExecutionFromHistory(h.status)"
                    type="button"
                    class="inline-flex rounded p-2 text-red-600 hover:bg-red-50 disabled:opacity-40"
                    title="Cancelar execução"
                    aria-label="Cancelar execução"
                    :disabled="cancellingHistoryExecutionId === h.id"
                    @click="cancelExecutionFromHistory(h.id)"
                  >
                    <font-awesome-icon :icon="['fas', 'xmark']" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!history.length">
              <td :colspan="isAdmin ? 4 : 3" class="py-6 text-center text-slate-500">Nenhuma execução.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <AppPaginationBar
        :page="historyPage"
        :total-pages="historyTotalPages"
        :total="historyTotal"
        @update:page="onHistoryPageChange"
      />
    </div>
  </div>
</template>
