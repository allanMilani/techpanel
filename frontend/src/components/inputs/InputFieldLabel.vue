<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps<{
  forId: string
  label: string
  hint?: string
  docHref?: string
  docAriaLabel?: string
}>()

const isExternal = computed(() => /^https?:\/\//i.test(props.docHref ?? ''))

const aria = computed(
  () => props.docAriaLabel ?? `Documentação: ${props.label}`,
)
</script>

<template>
  <label :for="forId" class="mb-1 flex flex-wrap items-center gap-1.5 text-sm font-medium text-slate-700">
    <span>
      {{ label }}
      <span v-if="hint" class="font-normal text-slate-500">({{ hint }})</span>
    </span>
    <a
      v-if="docHref && isExternal"
      :href="docHref"
      class="inline-flex shrink-0 text-sky-600 hover:text-sky-800"
      target="_blank"
      rel="noopener noreferrer"
      :aria-label="aria"
      :title="aria"
      @click.stop
    >
      <font-awesome-icon :icon="['fas', 'circle-info']" class="text-base" />
    </a>
    <RouterLink
      v-else-if="docHref"
      :to="docHref"
      class="inline-flex shrink-0 text-sky-600 hover:text-sky-800"
      :aria-label="aria"
      :title="aria"
      @click.stop
    >
      <font-awesome-icon :icon="['fas', 'circle-info']" class="text-base" />
    </RouterLink>
  </label>
</template>
