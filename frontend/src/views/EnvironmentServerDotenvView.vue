<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import AppTextarea from '../components/inputs/AppTextarea.vue'
import { ApiError, apiJson } from '../composables/useApi'
import { useToast } from '../composables/useToast'

interface DotenvGet {
  content: string
  exists: boolean
  path: string
}

const route = useRoute()
const projectId = computed(() => route.params.projectId as string)
const environmentId = computed(() => route.params.environmentId as string)

const content = ref('')
const remotePath = ref('')
const fileExists = ref<boolean | null>(null)
const loading = ref(true)
const saving = ref(false)
const { showToast } = useToast()

const apiBase = computed(
  () => `/api/projects/${projectId.value}/environments/${environmentId.value}/server-dotenv`,
)

onMounted(async () => {
  loading.value = true
  try {
    const data = await apiJson<DotenvGet>(apiBase.value)
    content.value = data.content
    remotePath.value = data.path
    fileExists.value = data.exists
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível ler o .env remoto.'
    showToast(msg, 'error')
  } finally {
    loading.value = false
  }
})

async function save() {
  saving.value = true
  try {
    const res = await apiJson<{ path: string }>(apiBase.value, {
      method: 'PUT',
      body: JSON.stringify({ content: content.value }),
    })
    remotePath.value = res.path
    fileExists.value = true
    showToast('Alterações gravadas no servidor.', 'success')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Erro ao gravar no servidor.'
    showToast(msg, 'error')
  } finally {
    saving.value = false
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
      Ambientes
    </RouterLink>

    <h1 class="mb-2 text-2xl font-semibold text-slate-800">.env no servidor</h1>
    <p class="mb-4 text-sm text-slate-600">
      Caminho remoto: <code v-if="remotePath" class="rounded bg-slate-100 px-1 text-xs">{{ remotePath }}</code>
      <span v-else class="text-slate-400">—</span>
    </p>

    <div
      class="mb-4 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950"
      role="alert"
    >
      <strong>Atenção:</strong> o conteúdo inclui segredos em texto claro. Use apenas em redes confiáveis (HTTPS em
      produção). Não partilhe capturas de ecrã desta página.
    </div>

    <p v-if="fileExists === false" class="mb-2 text-sm text-slate-600">
      O ficheiro ainda não existe no servidor; ao salvar será criado se o diretório raiz do projeto existir.
    </p>

    <div v-if="loading" class="text-sm text-slate-500">A carregar…</div>
    <form v-else class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm" @submit.prevent="save">
      <AppTextarea id="dotenv" v-model="content" label="Conteúdo do .env" :rows="18" hint="UTF-8. Máximo 256 KiB." />
      <button
        type="submit"
        class="mt-3 rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
        :disabled="saving"
      >
        {{ saving ? 'A gravar…' : 'Gravar no servidor' }}
      </button>
    </form>
  </div>
</template>
