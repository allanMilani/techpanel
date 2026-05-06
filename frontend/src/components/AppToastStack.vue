<script setup lang="ts">
import { computed } from 'vue'

import { useToast } from '../composables/useToast'

const { removeToast, toasts } = useToast()

const toastClassByType = computed<Record<string, string>>(() => ({
  info: 'border-sky-200 bg-sky-50 text-sky-900',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  error: 'border-rose-200 bg-rose-50 text-rose-900',
}))
</script>

<template>
  <div class="pointer-events-none fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-2">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="pointer-events-auto rounded-md border px-4 py-3 text-sm shadow-md"
      :class="toastClassByType[toast.type]"
    >
      <div class="flex items-start justify-between gap-3">
        <p>{{ toast.message }}</p>
        <button
          type="button"
          class="text-xs font-medium opacity-75 hover:opacity-100"
          aria-label="Fechar notificação"
          title="Fechar notificação"
          @click="removeToast(toast.id)"
        >
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
      </div>
    </div>
  </div>
</template>
