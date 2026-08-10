<template>
  <main class="home">
    <h1>Flatnotes</h1>
    <p v-if="workspace">Workspace: {{ workspace }}</p>
    <p v-else>No workspace selected.</p>
    <button type="button" @click="$emit('select-workspace')">Select workspace</button>
    <button type="button" @click="$emit('open-markdown')">Open Markdown</button>
    <form @submit.prevent="submitSearch">
      <input v-model="term" placeholder="Search notes" />
      <button type="submit">Search</button>
    </form>
    <ul>
      <li v-for="result in results" :key="result.path">{{ result.title }}</li>
    </ul>
  </main>
</template>

<script setup>
import { ref } from "vue";
import { searchWorkspace } from "../api/desktop.js";

defineProps({ workspace: { type: String, default: null } });
defineEmits(["select-workspace"]);
const term = ref("");
const results = ref([]);

async function submitSearch() {
  if (term.value.trim()) results.value = await searchWorkspace(term.value.trim());
}
</script>
