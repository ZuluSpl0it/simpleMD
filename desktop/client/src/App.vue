<template>
  <TabBar :tabs="tabs" @new-tab="newTab" @close-tab="closeTab" />
  <div v-if="tabs.active.value" class="actions">
    <button type="button" @click="saveActive">Save</button>
    <button type="button" @click="saveActiveAs">Save As</button>
  </div>
  <HomeView v-if="!tabs.active.value" :workspace="workspace" @select-workspace="selectWorkspace" @open-markdown="openMarkdown" />
  <MarkdownEditor v-else :content="tabs.active.value.content" @change="(content) => tabs.setContent(tabs.activeId.value, content)" />
  <ConflictDialog v-if="conflictTab" :visible="true" :tab="conflictTab" @resolve="resolveConflict" />
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import HomeView from "./views/HomeView.vue";
import { checkFile, getWorkspace, openDroppedPath, openMarkdown as chooseMarkdown, saveAs, saveTab, selectWorkspace as chooseWorkspace } from "./api/desktop.js";
import TabBar from "./components/TabBar.vue";
import MarkdownEditor from "./components/MarkdownEditor.vue";
import ConflictDialog from "./components/ConflictDialog.vue";
import { createTabs } from "./stores/tabs.js";

const workspace = ref(null);
const tabs = createTabs();
const conflictTab = ref(null);
let pollTimer;
function newTab() { tabs.open({ kind: "workspace", title: "Untitled", content: "" }); }
async function openMarkdown() {
  const document = await chooseMarkdown();
  if (document) tabs.open(document);
}
async function saveActive() {
  const tab = tabs.active.value;
  if (!tab?.path) return saveActiveAs();
  const saved = await saveTab(tab);
  Object.assign(tab, { content: saved.content, savedContent: saved.content, dirty: false, fingerprint: saved.content_hash, content_hash: saved.content_hash, modified_ns: saved.modified_ns });
}
async function saveActiveAs() {
  const tab = tabs.active.value;
  if (!tab) return;
  const saved = await saveAs(tab);
  if (saved) Object.assign(tab, { kind: "external", path: saved.path, content: saved.content, savedContent: saved.content, dirty: false, fingerprint: saved.content_hash, content_hash: saved.content_hash, modified_ns: saved.modified_ns, title: saved.path.split(/[\\/]/).pop() });
}
async function closeTab(id) {
  const tab = tabs.byId(id);
  if (!tab) return;
  if (tab.dirty) {
    const choice = window.confirm(`Save changes to ${tab.title}?`);
    if (choice) {
      const previous = tabs.activeId.value;
      tabs.activeId.value = id;
      await saveActive();
      tabs.activeId.value = previous;
    }
  }
  if (!tab.dirty) tabs.requestClose(id);
}
async function pollActiveFile() {
  const tab = tabs.active.value;
  if (!tab?.path || tab.externalState) return;
  const status = await checkFile(tab);
  if (status.state !== "clean") { tab.externalState = status.state; conflictTab.value = tab; }
}
async function resolveConflict(action) {
  const tab = conflictTab.value;
  if (!tab) return;
  if (action === "reload") {
    const document = await openDroppedPath(tab.path);
    Object.assign(tab, { content: document.content, savedContent: document.content, modified_ns: document.modified_ns, content_hash: document.content_hash, dirty: false, externalState: null });
  } else if (action === "overwrite") {
    await saveTab(tab); tab.dirty = false; tab.externalState = null;
  } else { await saveActiveAs(); tab.externalState = null; }
  conflictTab.value = null;
}
async function selectWorkspace() {
  const selected = await chooseWorkspace();
  if (selected?.workspace) workspace.value = selected.workspace;
}
function handleDrop(event) {
  const document = event.detail;
  if (document?.kind === "external") tabs.open(document);
}
onMounted(async () => {
  workspace.value = await getWorkspace();
  window.addEventListener("flatnotes-drop", handleDrop);
  pollTimer = window.setInterval(pollActiveFile, 1000);
});
onUnmounted(() => { window.clearInterval(pollTimer); window.removeEventListener("flatnotes-drop", handleDrop); });
</script>
