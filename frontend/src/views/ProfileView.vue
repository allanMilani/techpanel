<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import AppTextField from '../components/inputs/AppTextField.vue'
import { ApiError, apiJson } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import { useToast } from '../composables/useToast'

interface ProfileResponse {
  email: string
  display_name: string | null
  has_github_token: boolean
}

const displayName = ref('')
const pat = ref('')
const clearPat = ref(false)
const loading = ref(false)
const { showToast } = useToast()
const { refreshMe } = useAuth()

onMounted(async () => {
  try {
    const p = await apiJson<ProfileResponse>('/api/users/me/profile')
    displayName.value = p.display_name ?? ''
    clearPat.value = false
    pat.value = ''
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível carregar o perfil.'
    showToast(msg, 'error')
  }
})

async function save() {
  loading.value = true
  try {
    const body: Record<string, string | null> = {
      display_name: displayName.value.trim() || null,
    }
    if (clearPat.value) {
      body.github_token = ''
    } else if (pat.value.trim()) {
      body.github_token = pat.value.trim()
    }
    await apiJson('/api/users/me/profile', {
      method: 'PATCH',
      body: JSON.stringify(body),
    })
    showToast('Perfil atualizado.', 'success')
    pat.value = ''
    clearPat.value = false
    await refreshMe()
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Não foi possível guardar.'
    showToast(msg, 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <nav class="mb-4 text-sm text-slate-600">
      <RouterLink to="/dashboard" class="text-sky-600 hover:underline">Início</RouterLink>
      <span class="mx-2">/</span>
      <span>Perfil</span>
    </nav>
    <h1 class="mb-2 text-2xl font-semibold text-slate-800">Perfil</h1>
    <p class="mb-6 text-sm text-slate-600">
      Nome de exibição e token de acesso pessoal (PAT) do GitHub — o PAT é guardado encriptado no servidor e usado para sugerir repositórios e branches nas pipelines.
    </p>
    <form class="max-w-lg space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm" @submit.prevent="save">
      <AppTextField id="displayName" v-model="displayName" label="Nome" />
      <AppTextField
        id="pat"
        v-model="pat"
        label="GitHub PAT (opcional)"
        type="password"
        hint="Classic ou fine-grained com escopo repo. Deixe em branco para manter o token atual."
        doc-href="/ajuda#github-pat"
        doc-aria-label="Documentação sobre GitHub PAT"
      />
      <label class="flex items-center gap-2 text-sm text-slate-700">
        <input v-model="clearPat" type="checkbox" class="rounded border-slate-300" />
        Remover token GitHub guardado
      </label>
      <button
        type="submit"
        class="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-60"
        :disabled="loading"
      >
        {{ loading ? 'A guardar…' : 'Guardar' }}
      </button>
    </form>
  </div>
</template>
