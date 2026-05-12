<script setup lang="ts">
import InputFieldLabel from './InputFieldLabel.vue'

defineProps<{
  id: string
  label: string
  modelValue: string
  rows?: number
  required?: boolean
  hint?: string
  disabled?: boolean
  docHref?: string
  docAriaLabel?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="mb-4">
    <InputFieldLabel
      :for-id="id"
      :label="label"
      :hint="hint"
      :doc-href="docHref"
      :doc-aria-label="docAriaLabel"
    />
    <textarea
      :id="id"
      :value="modelValue"
      :rows="rows ?? 3"
      :required="required"
      :disabled="disabled"
      spellcheck="false"
      autocomplete="off"
      class="block w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm shadow-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-100"
      @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
  </div>
</template>
