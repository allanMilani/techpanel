<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppGithubAutocomplete from '../components/inputs/AppGithubAutocomplete.vue'
import AppTextField from '../components/inputs/AppTextField.vue'
import { ApiError, apiJson } from '../composables/useApi'
import { useToast } from '../composables/useToast'

interface Project {
  id: string
  name: string
  repo_github: string
  tech_stack: string
}

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.name === 'projects-edit')

const name = ref('')
const repoGithub = ref('')
const techStack = ref('')
const { showToast } = useToast()

onMounted(async () => {
  if (!isEdit.value) return
  const id = route.params.id as string
  const p = await apiJson<Project>(`/api/projects/${id}`)
  name.value = p.name
  repoGithub.value = p.repo_github
  techStack.value = p.tech_stack
})

async function save() {
  const body = {
    name: name.value,
    repo_github: repoGithub.value,
    tech_stack: techStack.value,
  }
  try {
    if (isEdit.value) {
      const id = route.params.id as string
      await apiJson(`/api/projects/${id}`, {
        method: 'PUT',
        body: JSON.stringify(body),
      })
    } else {
      await apiJson('/api/projects/', { method: 'POST', body: JSON.stringify(body) })
    }
    showToast(isEdit.value ? 'Projeto atualizado.' : 'Projeto criado.', 'success')
    await router.push('/projects')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Erro ao salvar o projeto.'
    showToast(msg, 'error')
  }
}
</script>

<template>
  <div>
    <RouterLink to="/projects" class="mb-4 inline-flex items-center gap-1 text-sm text-sky-600 hover:underline">
      <font-awesome-icon :icon="['fas', 'arrow-left']" />
      Voltar
    </RouterLink>
    <h1 class="mb-6 text-2xl font-semibold text-slate-800">
      {{ isEdit ? 'Editar projeto' : 'Novo projeto' }}
    </h1>
    <form class="w-full rounded-lg border border-slate-200 bg-white p-6 shadow-sm" @submit.prevent="save">
      <AppTextField id="name" v-model="name" label="Nome" required />
      <AppGithubAutocomplete
        id="repo"
        v-model="repoGithub"
        mode="repo"
        label="Repositório GitHub"
        hint="Formato owner/repo. Pesquisa com o PAT configurado em Perfil."
        required
        doc-href="/ajuda#github-repo"
        doc-aria-label="Documentação sobre repositório GitHub"
      />
      <AppTextField id="stack" v-model="techStack" label="Tech stack" required />
      <button type="submit" class="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700">
        Salvar
      </button>
    </form>
  </div>
</template>
