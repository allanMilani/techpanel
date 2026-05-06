<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { ApiError, apiJson, apiJsonNoBody } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import { useConfirm } from '../composables/useConfirm'
import { useToast } from '../composables/useToast'

interface Execution {
  id: string
  pipeline_id: string
  branch_or_tag: string
  status: string
  created_at?: string
}

interface StepLog {
  id: string
  pipeline_step_id: string
  order: number
  status: string
  log_output: string | null
  exit_code: number | null
  command?: string | null
}

interface Panel {
  error: string | null
  execution: Execution | null
  step_logs: StepLog[]
  step_labels: Record<string, string>
  terminal: boolean
}

const route = useRoute()
const executionId = route.params.executionId as string

const execution = ref<Execution | null>(null)
const panel = ref<Panel | null>(null)
const lastPanelError = ref<string | null>(null)
const terminalBodyRef = ref<HTMLElement | null>(null)
const cancelling = ref(false)
const engineBusy = ref(false)
const { showToast } = useToast()
const { isAdmin } = useAuth()
const { requestConfirm } = useConfirm()
let timer: ReturnType<typeof setInterval> | null = null

const canCancelExecution = computed(() => {
  const st = execution.value?.status
  if (!isAdmin.value || !st) return false
  return st === 'pending' || st === 'running' || st === 'blocked'
})

const sortedStepLogs = computed(() => {
  const logs = panel.value?.step_logs ?? []
  return [...logs].sort((a, b) => a.order - b.order)
})

function stepTitle(log: StepLog): string {
  return panel.value?.step_labels[log.pipeline_step_id] || `passo ${log.order}`
}

function scrollTerminalToBottom() {
  const el = terminalBodyRef.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

async function tick() {
  const ex = await apiJson<Execution>(`/api/executions/${executionId}`)
  execution.value = ex
  const p = await apiJson<Panel>(`/api/executions/${executionId}/panel`)
  panel.value = p
  if (p.terminal && timer) {
    clearInterval(timer)
    timer = null
  }
  if (p.error) {
    if (p.error !== lastPanelError.value) {
      lastPanelError.value = p.error
      showToast(p.error, 'error', 8000)
    }
  } else {
    lastPanelError.value = null
  }
}

/** Dispara um passo do motor no backend (admin). Sem isso a execução fica só em `pending`. */
async function pumpExecutionOnce() {
  if (!isAdmin.value || cancelling.value || engineBusy.value) return
  const ex = execution.value
  const term = panel.value?.terminal
  if (!ex || term) return
  if (!['pending', 'running', 'blocked'].includes(ex.status)) return
  engineBusy.value = true
  try {
    await apiJsonNoBody(`/api/executions/${executionId}/next-step`, { method: 'POST' })
    await tick()
  } catch (e) {
    const msg = e instanceof ApiError ? (e.detail ?? e.message) : 'Falha ao executar o próximo passo.'
    showToast(msg, 'error', 8000)
  } finally {
    engineBusy.value = false
  }
}

async function cancelExecution() {
  const ok = await requestConfirm(
    'Cancelar esta execução? Passos pendentes ou em andamento serão marcados como ignorados; um novo disparo poderá ser feito em seguida.',
  )
  if (!ok) return
  cancelling.value = true
  try {
    await apiJsonNoBody(`/api/executions/${executionId}/cancel`, { method: 'POST' })
    showToast('Execução cancelada.', 'success')
    await tick()
  } catch (e) {
    const msg = e instanceof ApiError ? (e.detail ?? e.message) : 'Não foi possível cancelar.'
    showToast(msg, 'error')
  } finally {
    cancelling.value = false
  }
}

onMounted(async () => {
  await tick()
  await pumpExecutionOnce()
  await nextTick()
  scrollTerminalToBottom()
  if (!panel.value?.terminal) {
    timer = setInterval(() => {
      void (async () => {
        await tick()
        await pumpExecutionOnce()
      })()
    }, 2000)
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

watch(panel, async () => {
  await nextTick()
  scrollTerminalToBottom()
})
</script>

<template>
  <div>
    <nav class="mb-4 text-sm text-slate-600">
      <RouterLink to="/dashboard" class="text-sky-600 hover:underline">Início</RouterLink>
      <span class="mx-2">/</span>
      <span>Execução</span>
    </nav>
    <h1 class="mb-2 text-2xl font-semibold text-slate-800">Acompanhamento da execução</h1>
    <p v-if="execution" class="mb-2 text-sm text-slate-600">
      ID: <code class="rounded bg-slate-100 px-1">{{ executionId }}</code>
      — branch/tag: <strong>{{ execution.branch_or_tag }}</strong>
      — status:
      <span class="rounded bg-slate-200 px-2 py-0.5 text-xs font-medium">{{ execution.status }}</span>
    </p>
    <p class="mb-2 text-xs text-slate-500">
      Atualização a cada ~2s. Com perfil admin, os passos são disparados automaticamente no servidor até a execução
      terminar.
    </p>

    <div v-if="canCancelExecution" class="mb-4">
      <button
        type="button"
        class="rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-800 hover:bg-red-50 disabled:opacity-50"
        :disabled="cancelling"
        @click="cancelExecution"
      >
        Cancelar execução
      </button>
    </div>

    <div v-if="panel" class="overflow-hidden rounded-lg border border-slate-700 shadow-lg">
      <div
        class="flex items-center gap-2 border-b border-slate-700 bg-slate-800 px-3 py-2 text-xs text-slate-300"
        role="banner"
      >
        <span class="inline-flex gap-1.5" aria-hidden="true">
          <span class="size-2.5 rounded-full bg-red-500/90" />
          <span class="size-2.5 rounded-full bg-amber-400/90" />
          <span class="size-2.5 rounded-full bg-emerald-500/90" />
        </span>
        <span class="ml-1 font-medium tracking-tight text-slate-200">techpanel</span>
        <span v-if="execution" class="text-slate-500">— {{ execution.branch_or_tag }}</span>
      </div>
      <div
        ref="terminalBodyRef"
        class="max-h-[min(70vh,42rem)] overflow-y-auto bg-zinc-950 px-4 py-3 font-mono text-[13px] leading-relaxed text-zinc-200"
        role="log"
        aria-live="polite"
        aria-relevant="additions text"
      >
        <template v-if="sortedStepLogs.length">
          <section
            v-for="log in sortedStepLogs"
            :key="log.id"
            class="mb-5 border-b border-zinc-800/80 pb-5 last:mb-0 last:border-b-0 last:pb-0"
          >
            <div class="mb-1 select-none text-emerald-500/95">
              <span class="text-zinc-500">#{{ log.order }}</span>
              {{ stepTitle(log) }}
              <span class="text-zinc-600"> · </span>
              <span
                class="rounded px-1.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide"
                :class="{
                  'bg-emerald-950 text-emerald-400': log.status === 'success',
                  'bg-red-950 text-red-400': log.status === 'failed',
                  'bg-amber-950 text-amber-300': log.status === 'running',
                  'bg-zinc-800 text-zinc-400': log.status === 'pending',
                  'bg-slate-800 text-slate-400': log.status === 'skipped',
                }"
              >
                {{ log.status }}
              </span>
            </div>
            <div class="mb-2 whitespace-pre-wrap break-all text-zinc-100">
              <span class="text-sky-500">$ </span>{{ log.command?.trim() || '—' }}
            </div>
            <pre
              v-if="log.log_output?.trim()"
              class="mb-2 overflow-x-auto whitespace-pre-wrap break-words rounded border border-zinc-800/80 bg-black/40 px-3 py-2 text-zinc-300"
            >{{ log.log_output }}</pre>
            <p v-else-if="log.status === 'pending' || log.status === 'running'" class="mb-2 text-zinc-500 italic">
              aguardando saída…
            </p>
            <p v-else-if="log.status === 'success'" class="mb-2 text-zinc-500">
              Nenhuma saída no stdout/stderr (por exemplo, diretório vazio em <code class="text-zinc-400">ls</code> ou
              comando silencioso).
            </p>
            <p v-else-if="log.status === 'failed'" class="mb-2 text-red-400/90">
              Sem saída capturada no stdout/stderr; exit code {{ log.exit_code ?? '—' }}.
            </p>
            <p v-else-if="log.status === 'skipped'" class="mb-2 text-zinc-500">Passo ignorado.</p>
            <p v-if="log.exit_code !== null && log.exit_code !== undefined" class="text-[11px] text-zinc-500">
              → exit code <span class="font-semibold text-zinc-400">{{ log.exit_code }}</span>
            </p>
          </section>
        </template>
        <p v-else class="text-zinc-500">Sem logs de passos ainda.</p>
      </div>
    </div>

    <RouterLink
      v-if="execution"
      :to="`/pipelines/${execution.pipeline_id}`"
      class="mt-6 inline-block rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50"
    >
      Voltar ao pipeline
    </RouterLink>
  </div>
</template>
