<script setup lang="ts">
const props = defineProps<{
  page: number
  totalPages: number
  total: number
}>()

const emit = defineEmits<{ (e: 'update:page', value: number): void }>()

function go(p: number) {
  if (p < 1 || p > props.totalPages) return
  emit('update:page', p)
}
</script>

<template>
  <div
    v-if="totalPages > 1"
    class="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 bg-slate-50/80 px-4 py-2 text-sm text-slate-600"
  >
    <span>{{ total }} registro(s) · página {{ page }} de {{ totalPages }}</span>
    <div class="flex gap-2">
      <button
        type="button"
        class="rounded border border-slate-200 bg-white px-3 py-1 text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        :disabled="page <= 1"
        @click="go(page - 1)"
      >
        Anterior
      </button>
      <button
        type="button"
        class="rounded border border-slate-200 bg-white px-3 py-1 text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        :disabled="page >= totalPages"
        @click="go(page + 1)"
      >
        Próxima
      </button>
    </div>
  </div>
</template>
