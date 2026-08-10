<template>
  <TabBar :tabs="tabs" @new-tab="newTab" />
  <HomeView v-if="!tabs.active" :workspace="workspace" @select-workspace="selectWorkspace" @open-markdown="openMarkdown" />
  <MarkdownEditor v-else :content="tabs.active.content" @change="(content) => tabs.setContent(tabs.activeId, content)" />
</template>

<script setup>
import { ref } from "vue";
import HomeView from "./views/HomeView.vue";
import { openMarkdown as chooseMarkdown, selectWorkspace as chooseWorkspace } from "./api/desktop.js";
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
async function selectWorkspace() {
  const selected = await chooseWorkspace();
  if (selected?.workspace) workspace.value = selected.workspace;
}
</script>
