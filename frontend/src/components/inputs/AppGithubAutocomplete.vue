<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import InputFieldLabel from './InputFieldLabel.vue'
import { ApiError, apiJson, type Paged } from '../../composables/useApi'
import { useToast } from '../../composables/useToast'

const props = withDefaults(
  defineProps<{
    modelValue: string
    id: string
    label: string
    hint?: string
    required?: boolean
    mode: 'repo' | 'refs'
    /** owner/repo — obrigatório quando mode === 'refs' */
    repositoryFullName?: string | null
    docHref?: string
    docAriaLabel?: string
  }>(),
  { required: false, repositoryFullName: null },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { showToast } = useToast()

const internal = ref(props.modelValue)
const open = ref(false)
const suggestions = ref<string[]>([])
const loading = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(
  () => props.modelValue,
  (v) => {
    internal.value = v
  },
)

onBeforeUnmount(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
})

async function runFetch() {
  if (props.mode === 'refs') {
    const repo = (props.repositoryFullName ?? '').trim()
    if (!repo) {
      suggestions.value = []
      return
    }
  }

  loading.value = true
  try {
    if (props.mode === 'repo') {
      const q = encodeURIComponent(internal.value.trim())
      const data = await apiJson<Paged<{ full_name: string }>>(
        `/api/users/me/github/repos?q=${q}&per_page=20`,
      )
      suggestions.value = data.items.map((i) => i.full_name)
    } else {
      const repo = (props.repositoryFullName ?? '').trim()
      const q = encodeURIComponent(internal.value.trim())
      const data = await apiJson<{ branches: string[]; tags: string[] }>(
        `/api/users/me/github/repos/${encodeURIComponent(repo)}/refs?q=${q}&limit=50`,
      )
      suggestions.value = [...new Set([...data.branches, ...data.tags])]
    }
  } catch (e) {
    suggestions.value = []
    if (e instanceof ApiError && e.status === 422) {
      showToast(e.message || 'GitHub: verifique o token em Perfil.', 'error', 6000)
    } else if (e instanceof ApiError) {
      showToast(e.detail ?? e.message, 'error')
    }
  } finally {
    loading.value = false
  }
}

function scheduleFetch() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    debounceTimer = null
    void runFetch()
  }, 300)
}

function onInput() {
  emit('update:modelValue', internal.value)
  scheduleFetch()
}

function onFocus() {
  open.value = true
  void runFetch()
}

function pick(s: string) {
  internal.value = s
  emit('update:modelValue', s)
  open.value = false
}

function onBlur() {
  setTimeout(() => {
    open.value = false
  }, 150)
}
</script>

<template>
  <div class="relative mb-4">
    <InputFieldLabel
      :for-id="id"
      :label="label"
      :hint="hint"
      :doc-href="docHref"
      :doc-aria-label="docAriaLabel"
    />
    <input
      :id="id"
      v-model="internal"
      type="text"
      autocomplete="off"
      class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
      :required="required"
      :aria-expanded="open"
      aria-autocomplete="list"
      @input="onInput"
      @focus="onFocus"
      @blur="onBlur"
    />
    <p class="mt-1 text-xs text-slate-500">
      Token em
      <RouterLink to="/profile" class="text-sky-600 underline hover:text-sky-800">Perfil</RouterLink>
      (escopo <code class="rounded bg-slate-100 px-1">repo</code>).
    </p>
    <div
      v-if="open && (suggestions.length > 0 || loading)"
      class="absolute z-20 mt-1 max-h-48 w-full overflow-auto rounded-md border border-slate-200 bg-white py-1 text-sm shadow-lg"
      role="listbox"
    >
      <div v-if="loading" class="px-3 py-2 text-slate-500">A carregar…</div>
      <button
        v-for="s in suggestions"
        :key="s"
        type="button"
        role="option"
        class="block w-full px-3 py-1.5 text-left font-mono text-xs hover:bg-slate-100"
        @mousedown.prevent="pick(s)"
      >
        {{ s }}
      </button>
    </div>
  </div>
</template>
