<template>
  <HomeView :workspace="workspace" @select-workspace="selectWorkspace" />
</template>

<script setup>
import { ref } from "vue";
import HomeView from "./views/HomeView.vue";
import { selectWorkspace as chooseWorkspace } from "./api/desktop.js";

const workspace = ref(null);
async function selectWorkspace() {
  const selected = await chooseWorkspace();
  if (selected?.workspace) workspace.value = selected.workspace;
}
</script>
