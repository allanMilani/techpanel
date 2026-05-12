<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppCheckbox from '../components/inputs/AppCheckbox.vue'
import AppSelect from '../components/inputs/AppSelect.vue'
import AppTextField from '../components/inputs/AppTextField.vue'
import AppTextarea from '../components/inputs/AppTextarea.vue'
import { ON_FAILURE_POLICIES, STEP_TYPES } from '../constants/formOptions'
import { ApiError, apiJson, fetchAllPaged } from '../composables/useApi'
import { useToast } from '../composables/useToast'

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

const route = useRoute()
const router = useRouter()
const pipelineId = route.params.pipelineId as string
const stepId = route.params.stepId as string | undefined
const isCreate = computed(() => route.name === 'pipeline-step-new')

const name = ref('')
const stepType = ref('ssh_command')
const command = ref('')
const onFailure = ref('stop')
const timeoutSeconds = ref('300')
const workingDir = ref('')
const isActive = ref(true)
const { showToast } = useToast()

const stepTypeOptions = STEP_TYPES.map((t) => ({ value: t, label: t }))
const onFailOptions = ON_FAILURE_POLICIES.map((t) => ({ value: t, label: t }))

const commandFieldLabel = computed(() => {
  if (stepType.value === 'ssh_command') return 'Comando SSH'
  if (stepType.value === 'http_healthcheck') return 'URL do health check'
  if (stepType.value === 'notify_webhook') return 'URL do webhook'
  return 'Comando'
})

const commandFieldHint = computed(() => {
  if (stepType.value === 'ssh_command') {
    return 'Numa execução, os passos SSH partilham a mesma sessão shell (remoto via SSH ou Docker local via um único `sh` no container): um cd num passo mantém o directório nos seguintes. Working dir igual ao do ambiente é omitido (evita repetir cd); use Working dir só para outro caminho absoluto ou cd no comando.'
  }
  if (stepType.value === 'http_healthcheck') return 'ex.: https://api.exemplo.com/health'
  if (stepType.value === 'notify_webhook') return 'POST será enviado para esta URL'
  return undefined
})

const workingDirHint = computed(() =>
  stepType.value === 'ssh_command'
    ? 'Opcional. Caminho absoluto: o passo corre como cd aqui && comando (ou posiciona a sessão persistente). Se for igual ao directório do ambiente, é omitido na mesma execução (o ambiente já posiciona o shell uma vez). Para voltar a essa pasta depois de outro cd, use cd no próprio comando. Deixe vazio para continuar onde o shell ficou.'
    : undefined,
)

onMounted(async () => {
  if (isCreate.value) return
  const id = stepId
  if (!id) {
    showToast('Passo não encontrado.', 'error')
    return
  }
  const steps = await fetchAllPaged<Step>(`/api/pipelines/${pipelineId}`)
  const st = steps.find((s) => s.id === id)
  if (!st) {
    showToast('Passo não encontrado.', 'error')
    return
  }
  name.value = st.name
  stepType.value = st.step_type
  command.value = st.command
  onFailure.value = st.on_failure
  timeoutSeconds.value = String(st.timeout_seconds)
  workingDir.value = st.working_directory ?? ''
  isActive.value = st.is_active
})

async function save() {
  try {
    if (isCreate.value) {
      await apiJson<Step>(`/api/pipelines/${pipelineId}/steps`, {
        method: 'POST',
        body: JSON.stringify({
          name: name.value,
          step_type: stepType.value,
          command: command.value,
          on_failure: onFailure.value,
          timeout_seconds: Number.parseInt(timeoutSeconds.value, 10),
          working_directory: workingDir.value.trim() || null,
        }),
      })
      showToast('Passo criado.', 'success')
      await router.push(`/pipelines/${pipelineId}#comandos`)
      return
    }
    const id = stepId
    if (!id) return
    await apiJson(`/api/pipelines/${pipelineId}/steps/${id}`, {
      method: 'PUT',
      body: JSON.stringify({
        name: name.value,
        step_type: stepType.value,
        command: command.value,
        on_failure: onFailure.value,
        timeout_seconds: Number.parseInt(timeoutSeconds.value, 10),
        working_directory: workingDir.value.trim() || null,
        is_active: isActive.value,
      }),
    })
    showToast('Passo atualizado.', 'success')
    await router.push(`/pipelines/${pipelineId}`)
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível salvar o passo.'
    showToast(msg, 'error')
  }
}
</script>

<template>
  <div>
    <RouterLink
      :to="`/pipelines/${pipelineId}`"
      class="mb-4 inline-flex items-center gap-1 text-sm text-sky-600 hover:underline"
    >
      <font-awesome-icon :icon="['fas', 'arrow-left']" />
      Pipeline
    </RouterLink>
    <h1 class="mb-6 text-2xl font-semibold text-slate-800">
      {{ isCreate ? 'Novo passo' : 'Editar passo' }}
    </h1>
    <form class="w-full space-y-3 rounded-lg border border-slate-200 bg-white p-6 text-sm shadow-sm" @submit.prevent="save">
      <AppTextField id="n" v-model="name" label="Nome" required />
      <AppSelect id="t" v-model="stepType" label="Tipo" :options="stepTypeOptions" required />
      <AppTextarea
        id="c"
        v-model="command"
        :label="commandFieldLabel"
        :hint="commandFieldHint"
        :rows="stepType === 'ssh_command' ? 4 : 3"
        required
        doc-href="/ajuda#pipeline-passos-ssh"
        doc-aria-label="Ajuda sobre comandos SSH e directório por passo"
      />
      <div class="grid gap-3 sm:grid-cols-2">
        <AppSelect id="o" v-model="onFailure" label="Em falha" :options="onFailOptions" required />
        <AppTextField id="to" v-model="timeoutSeconds" label="Timeout (s)" type="number" required />
      </div>
      <AppTextField
        id="w"
        v-model="workingDir"
        label="Working dir (opcional)"
        :hint="workingDirHint"
        doc-href="/ajuda#pipeline-passos-ssh"
        doc-aria-label="Ajuda sobre working directory e sessões SSH"
      />
      <AppCheckbox v-if="!isCreate" id="a" v-model="isActive" label="Ativo" />
      <button type="submit" class="mt-2 rounded-md bg-sky-600 px-4 py-2 text-sm text-white hover:bg-sky-700">
        Salvar
      </button>
    </form>
  </div>
</template>
