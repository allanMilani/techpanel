<script setup lang="ts">
import { useConfirm } from '../composables/useConfirm'

const { accept, dismiss, message, open } = useConfirm()
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
    >
      <div class="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 id="confirm-dialog-title" class="mb-3 text-lg font-semibold text-slate-800">
          Confirmar
        </h2>
        <p class="mb-6 text-sm text-slate-600">{{ message }}</p>
        <div class="flex flex-wrap justify-end gap-2">
          <button
            type="button"
            class="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            @click="dismiss"
          >
            Cancelar
          </button>
          <button
            type="button"
            class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            @click="accept"
          >
            Confirmar
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
