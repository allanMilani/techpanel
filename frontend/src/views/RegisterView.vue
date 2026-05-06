<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import AppTextField from '../components/inputs/AppTextField.vue'
import { ApiError } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import { useToast } from '../composables/useToast'

const name = ref('')
const email = ref('')
const password = ref('')
const passwordConfirmation = ref('')
const loading = ref(false)

const router = useRouter()
const { register } = useAuth()
const { showToast } = useToast()

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

function validateForm(): boolean {
  if (!name.value.trim()) {
    showToast('Informe o nome.', 'error')
    return false
  }
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
  if (password.value.length < 6) {
    showToast('A senha deve ter pelo menos 6 caracteres.', 'error')
    return false
  }
  if (!passwordConfirmation.value) {
    showToast('Confirme a senha.', 'error')
    return false
  }
  if (password.value !== passwordConfirmation.value) {
    showToast('As senhas não coincidem.', 'error')
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
    await register(name.value.trim(), email.value.trim(), password.value)
    showToast('Cadastro realizado com sucesso. Faça login para continuar.', 'success')
    await router.replace('/login')
  } catch (e) {
    const fallbackMessage = 'Não foi possível concluir o cadastro.'
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
      <h1 class="mb-2 text-center text-2xl font-semibold text-slate-800">Cadastro</h1>
      <p class="mb-6 text-center text-sm text-slate-600">Crie sua conta no TechPanel</p>
      <form novalidate @submit.prevent="onSubmit">
        <AppTextField id="name" v-model="name" label="Nome" />
        <AppTextField id="email" v-model="email" label="E-mail" type="email" />
        <AppTextField id="password" v-model="password" label="Senha" type="password" />
        <AppTextField
          id="passwordConfirmation"
          v-model="passwordConfirmation"
          label="Confirmar senha"
          type="password"
        />
        <button
          type="submit"
          class="mt-2 flex w-full items-center justify-center rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-60"
          aria-label="Cadastrar"
          title="Cadastrar"
          :disabled="loading"
        >
          <span v-if="!loading">Enviar</span>
          <span v-else>Enviando…</span>
        </button>
      </form>
      <p class="mt-6 text-center text-sm text-slate-600">
        <router-link
          to="/login"
          class="inline-flex items-center text-sky-600 hover:underline"
          aria-label="Ir para login"
          title="Ir para login"
        >
          Já tem uma conta? Faça login
        </router-link>
      </p>
    </div>
  </div>
</template>
