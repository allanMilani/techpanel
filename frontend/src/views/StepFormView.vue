<script setup lang="ts">
import { onMounted, ref } from 'vue'
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
const stepId = route.params.stepId as string

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

onMounted(async () => {
  const steps = await fetchAllPaged<Step>(`/api/pipelines/${pipelineId}`)
  const st = steps.find((s) => s.id === stepId)
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
    await apiJson(`/api/pipelines/${pipelineId}/steps/${stepId}`, {
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
    <h1 class="mb-6 text-2xl font-semibold text-slate-800">Editar passo</h1>
    <form class="w-full rounded-lg border border-slate-200 bg-white p-6 shadow-sm" @submit.prevent="save">
      <AppTextField id="n" v-model="name" label="Nome" required />
      <AppSelect id="t" v-model="stepType" label="Tipo" :options="stepTypeOptions" required />
      <AppTextarea id="c" v-model="command" label="Comando" required />
      <AppSelect id="o" v-model="onFailure" label="Em falha" :options="onFailOptions" required />
      <AppTextField id="to" v-model="timeoutSeconds" label="Timeout (s)" type="number" required />
      <AppTextField id="w" v-model="workingDir" label="Working dir" />
      <AppCheckbox id="a" v-model="isActive" label="Ativo" />
      <button type="submit" class="mt-2 rounded-md bg-sky-600 px-4 py-2 text-sm text-white hover:bg-sky-700">
        Salvar
      </button>
    </form>
  </div>
</template>
