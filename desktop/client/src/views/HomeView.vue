<template>
  <main class="home">
    <h1>simpleMD</h1>
    <p v-if="workspace">Workspace: {{ workspace }}</p>
    <p v-else>No workspace selected.</p>
    <button type="button" @click="$emit('select-workspace')">Select workspace</button>
    <button class="rebuild-index-button" type="button" :disabled="!workspace || indexBusy" @click="$emit('rebuild-index')">
      {{ indexBusy ? "Rebuilding…" : "Rebuild Index" }}
    </button>
    <button type="button" @click="$emit('open-markdown')">Open Markdown</button>
    <p v-if="indexMessage" class="index-status" :class="{ error: indexError }" role="status" aria-live="polite">{{ indexMessage }}</p>
    <form @submit.prevent="submitSearch">
      <input v-model="term" aria-label="Search notes" :disabled="indexBusy" placeholder="Search notes" />
      <button
        ref="searchHelpButton"
        class="search-help-button"
        type="button"
        aria-label="Search help"
        :aria-expanded="searchHelpOpen"
        aria-controls="search-help-dialog"
        data-tooltip="Search help"
        @click="searchHelpOpen = true"
      >
        ?
      </button>
      <button type="submit" :disabled="indexBusy">Search</button>
    </form>
    <p v-if="searchError" class="search-error" role="alert">{{ searchError }}</p>
    <ul>
      <li v-for="result in results" :key="result.path"><button type="button" @click="$emit('open-result', result)">{{ result.title }}</button></li>
    </ul>
    <SearchHelpDialog v-if="searchHelpOpen" @close="closeSearchHelp" />
  </main>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";
import { searchWorkspace } from "../api/desktop.js";
import SearchHelpDialog from "../components/SearchHelpDialog.vue";

const props = defineProps({
  workspace: { type: String, default: null },
  indexBusy: { type: Boolean, default: false },
  indexMessage: { type: String, default: "" },
  indexError: { type: Boolean, default: false },
});
defineEmits(["select-workspace", "rebuild-index", "open-markdown", "open-result"]);
const term = ref("");
const results = ref([]);
const searchError = ref("");
const searchHelpOpen = ref(false);
const searchHelpButton = ref();
watch(() => props.workspace, () => {
  term.value = "";
  results.value = [];
  searchError.value = "";
  searchHelpOpen.value = false;
});

async function submitSearch() {
  const query = term.value.trim();
  if (props.indexBusy || !query) return;
  searchError.value = "";
  try {
    results.value = await searchWorkspace(query);
  } catch (error) {
    results.value = [];
    searchError.value = `Search failed: ${error?.message || "Unknown error."}`;
  }
}

async function closeSearchHelp() {
  searchHelpOpen.value = false;
  await nextTick();
  searchHelpButton.value?.focus();
}
</script>
