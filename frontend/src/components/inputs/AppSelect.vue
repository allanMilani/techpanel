<script setup lang="ts">
import InputFieldLabel from './InputFieldLabel.vue'

export interface SelectOption {
  value: string
  label: string
}

defineProps<{
  id: string
  label: string
  modelValue: string
  options: readonly SelectOption[] | SelectOption[]
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
    <select
      :id="id"
      :value="modelValue"
      :required="required"
      :disabled="disabled"
      class="block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-100"
      @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="o in options" :key="o.value" :value="o.value">
        {{ o.label }}
      </option>
    </select>
  </div>
</template>
