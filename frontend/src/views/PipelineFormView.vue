<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppCheckbox from '../components/inputs/AppCheckbox.vue'
import AppTextarea from '../components/inputs/AppTextarea.vue'
import AppTextField from '../components/inputs/AppTextField.vue'
import { ApiError, apiJson } from '../composables/useApi'
import { useToast } from '../composables/useToast'

interface PipelineSummary {
  id: string
  environment_id: string
  name: string
  description: string | null
  run_git_workspace_sync?: boolean
}

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => route.name === 'pipelines-edit')

const name = ref('')
const description = ref('')
const runGitWorkspaceSync = ref(false)
const { showToast } = useToast()

const environmentId = computed(() => route.params.environmentId as string | undefined)
const pipelineIdParam = computed(() => route.params.pipelineId as string | undefined)

const backTo = computed(() => {
  if (isEdit.value && pipelineIdParam.value) {
    return `/pipelines/${pipelineIdParam.value}`
  }
  const eid = environmentId.value
  return eid ? `/environments/${eid}/pipelines` : '/projects'
})

onMounted(async () => {
  if (!isEdit.value) return
  const id = route.params.pipelineId as string
  try {
    const s = await apiJson<PipelineSummary>(`/api/pipelines/${id}/summary`)
    name.value = s.name
    description.value = s.description ?? ''
    runGitWorkspaceSync.value = Boolean(s.run_git_workspace_sync)
  } catch {
    showToast('Pipeline não encontrada.', 'error')
  }
})

async function save() {
  try {
    if (isEdit.value) {
      const id = route.params.pipelineId as string
      await apiJson(`/api/pipelines/${id}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: name.value,
          description: description.value.trim() || null,
          run_git_workspace_sync: runGitWorkspaceSync.value,
        }),
      })
      showToast('Pipeline atualizada.', 'success')
      await router.push(`/pipelines/${id}`)
      return
    }
    const eid = route.params.environmentId as string
    const created = await apiJson<PipelineSummary>(`/api/environments/${eid}/pipelines`, {
      method: 'POST',
      body: JSON.stringify({
        name: name.value,
        description: description.value.trim() || null,
        run_git_workspace_sync: runGitWorkspaceSync.value,
      }),
    })
    showToast('Pipeline criada.', 'success')
    await router.push(`/pipelines/${created.id}`)
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível salvar a pipeline.'
    showToast(msg, 'error')
  }
}
</script>

<template>
  <div>
    <RouterLink
      :to="backTo"
      class="mb-4 inline-flex items-center gap-1 text-sm text-sky-600 hover:underline"
    >
      <font-awesome-icon :icon="['fas', 'arrow-left']" />
      Voltar
    </RouterLink>
    <h1 class="mb-6 text-2xl font-semibold text-slate-800">
      {{ isEdit ? 'Editar pipeline' : 'Nova pipeline' }}
    </h1>
    <form class="w-full rounded-lg border border-slate-200 bg-white p-6 shadow-sm" @submit.prevent="save">
      <AppTextField id="pname" v-model="name" label="Nome" required />
      <AppTextarea
        id="pdesc"
        v-model="description"
        label="Descrição"
        hint="Opcional."
        :rows="3"
      />
      <AppCheckbox
        id="run_git"
        v-model="runGitWorkspaceSync"
        label="Sincronizar repositório Git antes dos passos (reset/clean, checkout da branch/tag, pull em branches)"
      />
      <p class="-mt-1 mb-4 text-xs text-slate-500">
        Requer diretório do projeto no servidor ou diretório de trabalho no ambiente, e uma branch/tag válida na
        execução. Operação destrutiva no working tree remoto (<code class="text-xs">git reset --hard</code>,
        <code class="text-xs">git clean -fd</code>).
      </p>
      <button type="submit" class="mt-2 rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700">
        {{ isEdit ? 'Salvar' : 'Criar pipeline' }}
      </button>
    </form>
  </div>
</template>
