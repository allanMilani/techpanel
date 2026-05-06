<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppTextField from '../components/inputs/AppTextField.vue'
import { ApiError } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import { useToast } from '../composables/useToast'

const email = ref('')
const password = ref('')
const loading = ref(false)

const router = useRouter()
const route = useRoute()
const { login } = useAuth()
const { showToast } = useToast()

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

function validateForm(): boolean {
  if (!email.value.trim()) {
    showToast('Informe o e-mail.', 'error')
    return false
  }
  if (!isValidEmail(email.value.trim())) {
    showToast('Informe um e-mail válido.', 'error')
    return false
  }
  if (!password.value) {
    showToast('Informe a senha.', 'error')
    return false
  }
  return true
}

async function onSubmit() {
  if (!validateForm()) {
    return
  }

  loading.value = true
  try {
    await login(email.value.trim(), password.value)
    const redir = (route.query.redirect as string) || '/dashboard'
    await router.replace(redir)
    showToast('Login realizado com sucesso.', 'success')
  } catch (e) {
    const fallbackMessage = 'E-mail ou senha inválidos.'
    const apiMessage = e instanceof ApiError ? e.detail ?? e.message : null
    showToast(apiMessage || fallbackMessage, 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center px-4">
    <div class="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
      <h1 class="mb-6 text-center text-2xl font-semibold text-slate-800">TechPanel</h1>
      <p class="mb-6 text-center text-sm text-slate-600">Entre com sua conta</p>
      <form novalidate @submit.prevent="onSubmit">
        <AppTextField id="email" v-model="email" label="E-mail" type="email" />
        <AppTextField id="password" v-model="password" label="Senha" type="password" />
        <button
          type="submit"
          class="mt-2 flex w-full items-center justify-center rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-60"
          aria-label="Entrar"
          title="Entrar"
          :disabled="loading"
        >
          <span v-if="!loading">Entrar</span>
          <span v-else>Entrando…</span>
        </button>
      </form>
      <p class="mt-6 text-center text-sm text-slate-600">
        <router-link
          to="/register"
          class="inline-flex items-center text-sky-600 hover:underline"
          aria-label="Criar conta"
          title="Criar conta"
        >
          Não tem uma conta? Cadastre-se
        </router-link>
      </p>
    </div>
  </div>
</template>
