<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppGithubAutocomplete from '../components/inputs/AppGithubAutocomplete.vue'
import AppTextField from '../components/inputs/AppTextField.vue'
import { ApiError, apiJson, apiJsonNoBody, fetchAllPaged } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import { useToast } from '../composables/useToast'

interface PipelineSummary {
  id: string
  environment_id: string
  name: string
  description: string | null
  project_id: string | null
  repo_github: string | null
  refs_repository_full_name?: string | null
  run_git_workspace_sync: boolean
}

interface Environment {
  id: string
  environment_type: string
  name: string
}

/** Valor gravado em `branch_or_tag` quando não há sync Git; o backend não usa na preparação do workspace. */
const BRANCH_OR_TAG_WHEN_GIT_SYNC_OFF = 'sem-git-sync'

const route = useRoute()
const router = useRouter()
const pipelineId = route.params.pipelineId as string

const summary = ref<PipelineSummary | null>(null)
const env = ref<Environment | null>(null)
const branch = ref('main')
const { showToast } = useToast()
const showConfirm = ref(false)
const showProdConfirm = ref(false)
const prodAck = ref(false)
const blockingExecutionId = ref<string | null>(null)
const autoStarting = ref(false)

const { isAdmin } = useAuth()

const isProduction = computed(() => env.value?.environment_type === 'production')

const gitSyncEnabled = computed(() => Boolean(summary.value?.run_git_workspace_sync))

const repoForRefs = computed(() => {
  const fromWorkspace = summary.value?.refs_repository_full_name?.trim()
  if (fromWorkspace) {
    return fromWorkspace
  }
  const raw = summary.value?.repo_github?.trim() ?? ''
  if (!raw) return null
  try {
    const u = new URL(raw.startsWith('http') ? raw : `https://github.com/${raw}`)
    const parts = u.pathname.replace(/^\/+|\/+$/g, '').split('/')
    if (parts.length >= 2) {
      return `${parts[0]}/${parts[1]}`
    }
  } catch {
    /* ignore */
  }
  if (raw.includes('/') && !raw.includes('://')) {
    return raw.split('/').filter(Boolean).slice(0, 2).join('/') || null
  }
  return null
})

function branchOrTagForStart(): string {
  if (!gitSyncEnabled.value) {
    return BRANCH_OR_TAG_WHEN_GIT_SYNC_OFF
  }
  return branch.value.trim() || 'main'
}

onMounted(async () => {
  const base = `/api/pipelines/${pipelineId}/summary`
  summary.value = await apiJson<PipelineSummary>(base)
  if (summary.value.project_id) {
    const envs = await fetchAllPaged<Environment>(
      `/api/projects/${summary.value.project_id}/environments`,
    )
    env.value = envs.find((e) => e.id === summary.value!.environment_id) ?? null
  }

  if (gitSyncEnabled.value) {
    summary.value = await apiJson<PipelineSummary>(`${base}?resolve_workspace_github_repo=1`)
  }

  if (!gitSyncEnabled.value && isAdmin.value && !isProduction.value) {
    autoStarting.value = true
    try {
      await doStart()
    } finally {
      autoStarting.value = false
    }
  }
})

async function doStart() {
  showConfirm.value = false
  showProdConfirm.value = false
  prodAck.value = false
  blockingExecutionId.value = null
  const tag = branchOrTagForStart()
  try {
    const out = await apiJson<{ id: string }>('/api/executions/start', {
      method: 'POST',
      body: JSON.stringify({
        pipeline_id: pipelineId,
        branch_or_tag: tag,
      }),
    })
    await router.push(`/executions/${out.id}/monitor`)
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      const raw = e.body?.blocking_execution_id
      const bid = typeof raw === 'string' ? raw : null
      if (bid) {
        blockingExecutionId.value = bid
      }
      showToast(e.message, 'error', 10000)
      return
    }
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível iniciar a execução.'
    showToast(msg, 'error')
  }
}

async function cancelBlockingExecution() {
  const bid = blockingExecutionId.value
  if (!bid) return
  try {
    await apiJsonNoBody(`/api/executions/${bid}/cancel`, { method: 'POST' })
    blockingExecutionId.value = null
    showToast('Execução anterior cancelada. Você pode disparar de novo.', 'success')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível cancelar.'
    showToast(msg, 'error')
  }
}

function requestRun() {
  if (isProduction.value) {
    showProdConfirm.value = true
  } else {
    showConfirm.value = true
  }
}
</script>

<template>
  <div v-if="summary">
    <nav class="mb-4 text-sm text-slate-600">
      <RouterLink :to="`/pipelines/${pipelineId}`" class="text-sky-600 hover:underline">
        {{ summary.name }}
      </RouterLink>
      <span class="mx-2">/</span>
      <span>Executar</span>
    </nav>

    <div
      v-if="autoStarting"
      class="rounded-lg border border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-700"
    >
      A iniciar execução…
    </div>

    <template v-else>
      <h1 class="mb-2 text-2xl font-semibold">Executar pipeline</h1>
      <p class="mb-6 text-slate-600">
        {{ summary.name }}
        <template v-if="env"> — ambiente <strong>{{ env.name }}</strong> ({{ env.environment_type }})</template>
      </p>

      <form v-if="gitSyncEnabled" class="w-full space-y-4" @submit.prevent>
        <AppGithubAutocomplete
          v-if="repoForRefs"
          id="branch"
          v-model="branch"
          mode="refs"
          :repository-full-name="repoForRefs"
          label="Branch ou tag"
          hint="Refs do repositório GitHub do clone no servidor (origin no diretório do projeto), ou do repositório configurado no projeto. Pode escrever um valor à mão."
          required
          doc-href="/ajuda#github-repo"
          doc-aria-label="Documentação sobre branch, tag e GitHub"
        />
        <AppTextField
          v-else
          id="branch"
          v-model="branch"
          label="Branch ou tag"
          hint="ex.: main, develop ou v1.2.0 (sem repo no projeto — introdução manual)"
          required
          doc-href="/ajuda#github-repo"
          doc-aria-label="Documentação sobre branch, tag e GitHub"
        />
      </form>
      <p v-else class="mb-6 text-sm text-slate-600">
        A sincronização Git antes dos passos está desligada para esta pipeline. Não é necessário escolher branch ou
        tag; a execução usa apenas os comandos configurados no servidor.
      </p>

      <div
        v-if="blockingExecutionId && isAdmin"
        class="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950"
      >
        <p class="mb-3 font-medium">Há uma execução anterior ainda ativa neste projeto (conflito 409).</p>
        <div class="flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="rounded-md border border-amber-700 bg-white px-3 py-1.5 text-sm font-medium text-amber-950 hover:bg-amber-100"
            @click="cancelBlockingExecution"
          >
            Cancelar execução anterior
          </button>
          <RouterLink
            :to="`/executions/${blockingExecutionId}/monitor`"
            class="text-sm font-medium text-sky-700 underline hover:text-sky-900"
          >
            Abrir monitor da execução bloqueante
          </RouterLink>
        </div>
      </div>

      <div v-if="isAdmin" class="mt-6">
        <button
          v-if="!isProduction"
          type="button"
          class="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700"
          @click="requestRun"
        >
          Solicitar execução
        </button>
        <button
          v-else
          type="button"
          class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          @click="requestRun"
        >
          Solicitar execução (produção)
        </button>
      </div>
      <p v-else class="mt-4 text-slate-500">Apenas administradores podem disparar execuções.</p>

      <RouterLink
        :to="`/pipelines/${pipelineId}`"
        class="mt-8 inline-block text-sm text-sky-600 hover:underline"
      >
        Voltar
      </RouterLink>

      <!-- Modal simples -->
      <div
        v-if="showConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        role="dialog"
        aria-modal="true"
      >
        <div class="max-w-md rounded-lg bg-white p-6 shadow-xl">
          <h2 class="mb-2 text-lg font-semibold">Confirmar execução</h2>
          <p v-if="gitSyncEnabled" class="mb-4 text-sm text-slate-600">
            Deseja iniciar a execução com branch/tag <strong>{{ branch }}</strong>?
          </p>
          <p v-else class="mb-4 text-sm text-slate-600">
            Deseja iniciar a execução? (Sem sincronização Git — não há escolha de branch.)
          </p>
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded border px-3 py-1 text-sm" @click="showConfirm = false">
              Cancelar
            </button>
            <button type="button" class="rounded bg-sky-600 px-3 py-1 text-sm text-white" @click="doStart">
              Confirmar
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="showProdConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        role="dialog"
        aria-modal="true"
      >
        <div class="max-w-md rounded-lg bg-white p-6 shadow-xl">
          <h2 class="mb-2 text-lg font-semibold text-red-700">Produção</h2>
          <p v-if="gitSyncEnabled" class="mb-4 text-sm text-slate-600">
            Ambiente de produção. Confirme que deseja prosseguir com <strong>{{ branch }}</strong>.
          </p>
          <p v-else class="mb-4 text-sm text-slate-600">
            Ambiente de produção. A sincronização Git está desligada; não há escolha de branch. Confirme que deseja
            prosseguir.
          </p>
          <label class="mb-4 flex items-center gap-2 text-sm">
            <input v-model="prodAck" type="checkbox" class="rounded" />
            Entendo que esta ação afeta produção.
          </label>
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded border px-3 py-1 text-sm" @click="showProdConfirm = false">
              Cancelar
            </button>
            <button
              type="button"
              class="rounded bg-red-600 px-3 py-1 text-sm text-white disabled:opacity-40"
              :disabled="!prodAck"
              @click="doStart"
            >
              Confirmar execução
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
