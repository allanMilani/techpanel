<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'

import { useAuth } from '../composables/useAuth'

const { isAdmin, logout, role, me } = useAuth()

async function onLogout() {
  await logout()
  window.location.href = '/login'
}
</script>

<template>
  <div class="min-h-screen">
    <header class="border-b border-slate-200 bg-slate-900 text-white">
      <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div class="flex items-center gap-6">
          <RouterLink to="/dashboard" class="text-lg font-semibold tracking-tight"> TechPanel </RouterLink>
          <nav class="flex flex-wrap gap-4 text-sm">
            <RouterLink
              to="/dashboard"
              class="rounded px-2 py-1 text-slate-200 hover:bg-slate-800 hover:text-white"
              active-class="!bg-slate-800 !text-white"
            >
              <font-awesome-icon :icon="['fas', 'home']" class="mr-1" />
              Início
            </RouterLink>
            <RouterLink
              v-if="isAdmin"
              to="/servers"
              class="rounded px-2 py-1 text-slate-200 hover:bg-slate-800 hover:text-white"
              active-class="!bg-slate-800 !text-white"
            >
              <font-awesome-icon :icon="['fas', 'server']" class="mr-1" />
              Servidores
            </RouterLink>
            <RouterLink
              to="/projects"
              class="rounded px-2 py-1 text-slate-200 hover:bg-slate-800 hover:text-white"
              active-class="!bg-slate-800 !text-white"
            >
              <font-awesome-icon :icon="['fas', 'project-diagram']" class="mr-1" />
              Projetos
            </RouterLink>
            <RouterLink
              to="/environments"
              class="rounded px-2 py-1 text-slate-200 hover:bg-slate-800 hover:text-white"
              active-class="!bg-slate-800 !text-white"
            >
              <font-awesome-icon :icon="['fas', 'layer-group']" class="mr-1" />
              Ambientes
            </RouterLink>
            <RouterLink
              to="/profile"
              class="rounded px-2 py-1 text-slate-200 hover:bg-slate-800 hover:text-white"
              active-class="!bg-slate-800 !text-white"
            >
              <font-awesome-icon :icon="['fas', 'user']" class="mr-1" />
              Perfil
            </RouterLink>
            <RouterLink
              to="/ajuda"
              class="rounded px-2 py-1 text-slate-200 hover:bg-slate-800 hover:text-white"
              active-class="!bg-slate-800 !text-white"
            >
              <font-awesome-icon :icon="['fas', 'book']" class="mr-1" />
              Ajuda
            </RouterLink>
          </nav>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <span class="max-w-[10rem] truncate text-slate-300" :title="me?.display_name ?? undefined">
            {{ me?.display_name?.trim() || 'Conta' }}
          </span>
          <span class="text-slate-400">Papel: {{ role }}</span>
          <button
            type="button"
            class="inline-flex items-center gap-1 rounded border border-slate-600 px-2 py-1 text-slate-200 hover:bg-slate-800"
            @click="onLogout"
          >
            <font-awesome-icon :icon="['fas', 'sign-out-alt']" />
            Sair
          </button>
        </div>
      </div>
    </header>
    <main class="mx-auto max-w-6xl px-4 py-8">
      <RouterView />
    </main>
  </div>
</template>
