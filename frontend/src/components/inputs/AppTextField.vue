<script setup lang="ts">
defineProps<{
  id: string
  label: string
  modelValue: string
  type?: string
  hint?: string
  placeholder?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="mb-4">
    <label :for="id" class="mb-1 block text-sm font-medium text-slate-700">
      {{ label }}
      <span v-if="hint" class="font-normal text-slate-500">({{ hint }})</span>
    </label>
    <input
      :id="id"
      :value="modelValue"
      :type="type ?? 'text'"
      :placeholder="placeholder"
      :disabled="disabled"
      class="block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-100"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
  </div>
</template>
