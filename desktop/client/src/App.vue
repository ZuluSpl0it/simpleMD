<template>
  <TabBar :tabs="tabs" @new-tab="newTab" />
  <div v-if="tabs.active.value" class="actions">
    <button type="button" @click="saveActive">Save</button>
    <button type="button" @click="saveActiveAs">Save As</button>
  </div>
  <HomeView v-if="!tabs.active.value" :workspace="workspace" @select-workspace="selectWorkspace" @open-markdown="openMarkdown" />
  <MarkdownEditor v-else :content="tabs.active.value.content" @change="(content) => tabs.setContent(tabs.activeId.value, content)" />
</template>

<script setup>
import { ref } from "vue";
import HomeView from "./views/HomeView.vue";
import { openMarkdown as chooseMarkdown, saveAs, saveTab, selectWorkspace as chooseWorkspace } from "./api/desktop.js";
import TabBar from "./components/TabBar.vue";
import MarkdownEditor from "./components/MarkdownEditor.vue";
import { createTabs } from "./stores/tabs.js";

const workspace = ref(null);
const tabs = createTabs();
function newTab() { tabs.open({ kind: "workspace", title: "Untitled", content: "" }); }
async function openMarkdown() {
  const document = await chooseMarkdown();
  if (document) tabs.open(document);
}
async function saveActive() {
  const tab = tabs.active.value;
  if (!tab?.path) return saveActiveAs();
  const saved = await saveTab(tab);
  Object.assign(tab, { content: saved.content, savedContent: saved.content, dirty: false, fingerprint: saved.content_hash });
}
async function saveActiveAs() {
  const tab = tabs.active.value;
  if (!tab) return;
  const saved = await saveAs(tab);
  if (saved) Object.assign(tab, { kind: "external", path: saved.path, content: saved.content, savedContent: saved.content, dirty: false, fingerprint: saved.content_hash, title: saved.path.split(/[\\/]/).pop() });
}
async function selectWorkspace() {
  const selected = await chooseWorkspace();
  if (selected?.workspace) workspace.value = selected.workspace;
}
</script>
