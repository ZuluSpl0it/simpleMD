<template>
  <main class="home">
    <h1>Flatnotes</h1>
    <p v-if="workspace">Workspace: {{ workspace }}</p>
    <p v-else>No workspace selected.</p>
    <button type="button" @click="$emit('select-workspace')">Select workspace</button>
    <button class="rebuild-index-button" type="button" :disabled="!workspace || indexBusy" @click="$emit('rebuild-index')">
      {{ indexBusy ? "Rebuilding…" : "Rebuild Index" }}
    </button>
    <button type="button" @click="$emit('open-markdown')">Open Markdown</button>
    <p v-if="indexMessage" class="index-status" :class="{ error: indexError }" role="status" aria-live="polite">{{ indexMessage }}</p>
    <form @submit.prevent="submitSearch">
      <input v-model="term" :disabled="indexBusy" placeholder="Search notes" />
      <button type="submit" :disabled="indexBusy">Search</button>
    </form>
    <ul>
      <li v-for="result in results" :key="result.path"><button type="button" @click="$emit('open-result', result)">{{ result.title }}</button></li>
    </ul>
  </main>
</template>

<script setup>
import { ref, watch } from "vue";
import { searchWorkspace } from "../api/desktop.js";

const props = defineProps({
  workspace: { type: String, default: null },
  indexBusy: { type: Boolean, default: false },
  indexMessage: { type: String, default: "" },
  indexError: { type: Boolean, default: false },
});
defineEmits(["select-workspace", "rebuild-index", "open-markdown", "open-result"]);
const term = ref("");
const results = ref([]);
watch(() => props.workspace, () => {
  term.value = "";
  results.value = [];
});

async function submitSearch() {
  if (!props.indexBusy && term.value.trim()) results.value = await searchWorkspace(term.value.trim());
}
</script>
