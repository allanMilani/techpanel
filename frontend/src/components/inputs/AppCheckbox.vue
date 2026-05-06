<script setup lang="ts">
defineProps<{
  id: string
  label: string
  modelValue: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()
</script>

<template>
  <div class="mb-4 flex items-center gap-2">
    <input
      :id="id"
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      class="h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
      @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    />
    <label :for="id" class="text-sm text-slate-700">{{ label }}</label>
  </div>
</template>
