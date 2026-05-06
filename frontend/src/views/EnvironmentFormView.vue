<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppCheckbox from '../components/inputs/AppCheckbox.vue'
import AppSelect from '../components/inputs/AppSelect.vue'
import AppTextField from '../components/inputs/AppTextField.vue'
import { ENVIRONMENT_TYPES } from '../constants/formOptions'
import { ApiError, apiJson, fetchAllPaged } from '../composables/useApi'
import { useToast } from '../composables/useToast'

interface Environment {
  id: string
  name: string
  environment_type: string
  server_id: string
  working_directory: string
  is_active: boolean
}

interface Server {
  id: string
  name: string
}

const route = useRoute()
const router = useRouter()
const projectId = computed(() => route.params.projectId as string)
const environmentId = computed(() => route.params.environmentId as string)

const name = ref('')
const envType = ref('staging')
const serverId = ref('')
const workDir = ref('')
const isActive = ref(true)
const servers = ref<Server[]>([])
const { showToast } = useToast()

const envTypeOptions = ENVIRONMENT_TYPES.map((t) => ({ value: t, label: t }))
const serverOptions = computed(() =>
  servers.value.map((s) => ({ value: s.id, label: s.name })),
)

onMounted(async () => {
  servers.value = await fetchAllPaged<Server>('/api/servers/')
  const list = await fetchAllPaged<Environment>(`/api/projects/${projectId.value}/environments`)
  const e = list.find((x) => x.id === environmentId.value)
  if (!e) {
    showToast('Ambiente não encontrado.', 'error')
    return
  }
  name.value = e.name
  envType.value = e.environment_type
  serverId.value = e.server_id
  workDir.value = e.working_directory
  isActive.value = e.is_active
})

async function save() {
  try {
    await apiJson(
      `/api/projects/${projectId.value}/environments/${environmentId.value}`,
      {
        method: 'PUT',
        body: JSON.stringify({
          name: name.value,
          environment_type: envType.value,
          server_id: serverId.value,
          working_directory: workDir.value,
          is_active: isActive.value,
        }),
      },
    )
    showToast('Ambiente atualizado.', 'success')
    await router.push(`/projects/${projectId.value}/environments`)
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Erro ao salvar o ambiente.'
    showToast(msg, 'error')
  }
}
</script>

<template>
  <div>
    <RouterLink
      :to="`/projects/${projectId}/environments`"
      class="mb-4 inline-flex items-center gap-1 text-sm text-sky-600 hover:underline"
    >
      <font-awesome-icon :icon="['fas', 'arrow-left']" />
      Voltar
    </RouterLink>
    <h1 class="mb-6 text-2xl font-semibold text-slate-800">Editar ambiente</h1>
    <form class="w-full rounded-lg border border-slate-200 bg-white p-6 shadow-sm" @submit.prevent="save">
      <AppTextField id="n" v-model="name" label="Nome" required />
      <AppSelect id="t" v-model="envType" label="Tipo" :options="envTypeOptions" required />
      <AppSelect id="s" v-model="serverId" label="Servidor" :options="serverOptions" required />
      <AppTextField id="w" v-model="workDir" label="Diretório de trabalho" required />
      <AppCheckbox id="a" v-model="isActive" label="Ativo" />
      <button type="submit" class="mt-2 rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700">
        Salvar
      </button>
    </form>
  </div>
</template>
