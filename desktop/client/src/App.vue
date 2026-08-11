<template>
  <TabBar :tabs="tabs" :active="tabs.active.value" @new-tab="newTab" @close-tab="closeTab" @toggle-edit="toggleEdit" @save="saveActive" @save-as="saveActiveAs" @rename="renameActive" @delete="deleteActive" />
  <HomeView v-if="!tabs.active.value" :workspace="workspace" @select-workspace="selectWorkspace" @open-markdown="openMarkdown" @open-result="openResult" />
  <MarkdownEditor v-else :key="`${tabs.active.value.id}-${tabs.active.value.mode}-${tabs.active.value.editing}`" :content="tabs.active.value.content" :mode="tabs.active.value.mode" :editing="tabs.active.value.editing" @change="(content) => tabs.setContent(tabs.activeId.value, content)" />
  <ConflictDialog v-if="conflictTab" :visible="true" :tab="conflictTab" @resolve="resolveConflict" />
  <CloseDialog v-if="pendingCloseTab" :tab="pendingCloseTab" @resolve="resolveClose" />
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import HomeView from "./views/HomeView.vue";
import { checkFile, createWorkspaceNote, deleteWorkspaceNote, getWorkspace, openDroppedPath, openMarkdown as chooseMarkdown, renameWorkspaceNote, saveAs, saveTab, selectWorkspace as chooseWorkspace, startupEvent } from "./api/desktop.js";
import TabBar from "./components/TabBar.vue";
import MarkdownEditor from "./components/MarkdownEditor.vue";
import ConflictDialog from "./components/ConflictDialog.vue";
import CloseDialog from "./components/CloseDialog.vue";
import { createTabs } from "./stores/tabs.js";

const workspace = ref(null);
const tabs = createTabs();
const conflictTab = ref(null);
const pendingCloseTab = ref(null);
let pollTimer;
function newTab() { tabs.open({ kind: "workspace", title: "Untitled", content: "", editing: true }); }
function toggleEdit() {
  const tab = tabs.active.value;
  if (tab) tab.editing = !tab.editing;
}
async function openMarkdown() {
  const document = await chooseMarkdown();
  if (document) tabs.open(document);
}
async function openResult(result) {
  const document = await openDroppedPath(result.path);
  if (document?.kind === "external") tabs.open({ ...document, kind: "workspace", title: result.title });
}
async function saveActive() {
  const tab = tabs.active.value;
  if (!tab?.path) {
    if (tab?.kind === "workspace") {
      const title = window.prompt("Note title", tab.title === "Untitled" ? "" : tab.title);
      if (!title) return;
      const created = await createWorkspaceNote(title, tab.content);
      Object.assign(tab, { path: created.path, title: created.title, content: created.content, savedContent: created.content, dirty: false, modified_ns: created.modified_ns, content_hash: created.content_hash });
      return;
    }
    return saveActiveAs();
  }
  const saved = await saveTab(tab);
  Object.assign(tab, { content: saved.content, savedContent: saved.content, dirty: false, fingerprint: saved.content_hash, content_hash: saved.content_hash, modified_ns: saved.modified_ns });
}
async function saveActiveAs() {
  const tab = tabs.active.value;
  if (!tab) return;
  const saved = await saveAs(tab);
  if (saved) Object.assign(tab, { kind: "external", path: saved.path, content: saved.content, savedContent: saved.content, dirty: false, fingerprint: saved.content_hash, content_hash: saved.content_hash, modified_ns: saved.modified_ns, title: saved.path.split(/[\\/]/).pop() });
}
async function renameActive() {
  const tab = tabs.active.value;
  const title = window.prompt("New note title", tab.title);
  if (!title || title === tab.title) return;
  const renamed = await renameWorkspaceNote(tab.title, title);
  Object.assign(tab, { title: renamed.title, path: renamed.path, modified_ns: renamed.modified_ns, content_hash: renamed.content_hash });
}
async function deleteActive() {
  const tab = tabs.active.value;
  if (!window.confirm(`Delete ${tab.title}?`)) return;
  await deleteWorkspaceNote(tab.title);
  tabs.requestClose(tab.id);
}
async function closeTab(id) {
  const tab = tabs.byId(id);
  if (!tab) return;
  if (tab.dirty) { pendingCloseTab.value = tab; return; }
  tabs.requestClose(id);
}
async function resolveClose(action) {
  const tab = pendingCloseTab.value;
  if (!tab || action === "cancel") { pendingCloseTab.value = null; return; }
  if (action === "discard") {
    tab.dirty = false;
    tabs.requestClose(tab.id);
    pendingCloseTab.value = null;
    return;
  }
  const previous = tabs.activeId.value;
  tabs.activeId.value = tab.id;
  await saveActive();
  if (!tab.dirty) tabs.requestClose(tab.id);
  else tabs.activeId.value = previous;
  pendingCloseTab.value = null;
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
  try {
    const selected = await chooseWorkspace();
    if (selected?.workspace) workspace.value = selected.workspace;
  } catch (error) { window.alert(`Could not select workspace: ${error.message}`); }
}
function handleDrop(event) {
  const document = event.detail;
  if (document?.kind === "external") tabs.open(document);
}
onMounted(async () => {
  await startupEvent("frontend-mounted");
  workspace.value = await getWorkspace();
  await startupEvent("frontend-workspace-read");
  window.addEventListener("flatnotes-drop", handleDrop);
  pollTimer = window.setInterval(pollActiveFile, 1000);
});
onUnmounted(() => { window.clearInterval(pollTimer); window.removeEventListener("flatnotes-drop", handleDrop); });
</script>
