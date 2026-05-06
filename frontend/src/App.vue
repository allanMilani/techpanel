<template>
  <router-view />
  <AppToastStack />
  <AppConfirmDialog />
</template>

<script setup lang="ts">
import AppConfirmDialog from './components/AppConfirmDialog.vue'
import AppToastStack from './components/AppToastStack.vue'
</script>
