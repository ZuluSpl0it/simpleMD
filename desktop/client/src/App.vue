<template>
  <TabBar :tabs="tabs" :active="tabs.active.value" :theme="theme" @new-tab="newTab" @home="goHome" @toggle-theme="toggleTheme" @close-tab="closeTab" @toggle-edit="toggleEdit" @save="saveActive" @save-as="saveActiveAs" @rename="renameActive" @delete="deleteActive" />
  <FindBar v-if="findOpen && tabs.active.value" :query="findQuery" :replacement="replacementQuery" :editing="tabs.active.value.editing" :match-count="findCount" :active-match="findIndex" @update:query="setFindQuery" @update:replacement="replacementQuery = $event" @previous="moveFind(-1)" @next="moveFind(1)" @replace="replaceActive" @replace-all="replaceAllActive" @close="closeFind" />
  <HomeView v-if="!tabs.active.value" :workspace="workspace" :index-busy="indexBusy" :index-message="indexMessage" :index-error="indexError" @select-workspace="selectWorkspace" @rebuild-index="rebuildSearchIndex" @open-markdown="openMarkdown" @open-result="openResult" />
  <MarkdownEditor v-else :key="`${tabs.active.value.id}-${tabs.active.value.mode}-${tabs.active.value.editing}-${tabs.active.value.editorRevision}-${theme}`" :content="tabs.active.value.content" :mode="tabs.active.value.mode" :editing="tabs.active.value.editing" :theme="theme" :find-query="findQuery" :find-index="findIndex" :initial-scroll-position="tabs.active.value.scrollPosition" :scroll-key="tabs.active.value.id" @change="(content) => tabs.setContent(tabs.activeId.value, content)" @find-count="setFindCount" @scroll-position="(id, position) => tabs.setScrollPosition(id, position)" />
  <ConflictDialog v-if="conflictTab" :visible="true" :tab="conflictTab" @resolve="resolveConflict" />
  <CloseDialog v-if="pendingCloseTab" :tab="pendingCloseTab" @resolve="resolveClose" />
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import HomeView from "./views/HomeView.vue";
import FindBar from "./components/FindBar.vue";
import { checkFile, createWorkspaceNote, deleteWorkspaceNote, getFontSettings, getHeadingColors, getIndexStatus, getTheme, getWorkspace, openDroppedPath, openMarkdown as chooseMarkdown, rebuildIndex, renameWorkspaceNote, saveAs, saveTab, selectWorkspace as chooseWorkspace, setTheme, startupEvent } from "./api/desktop.js";
import TabBar from "./components/TabBar.vue";
import MarkdownEditor from "./components/MarkdownEditor.vue";
import ConflictDialog from "./components/ConflictDialog.vue";
import CloseDialog from "./components/CloseDialog.vue";
import { createTabs } from "./stores/tabs.js";
import { classifyDocument } from "./documents.js";
import { replaceAllMatches, replaceMatch } from "./find.js";
import {
  applyHeadingColors,
  DEFAULT_HEADING_COLORS,
} from "./headingColors.js";
import { applyFontSettings, DEFAULT_FONT_SIZES } from "./fontSettings.js";

const workspace = ref(null);
const tabs = createTabs();
const conflictTab = ref(null);
const pendingCloseTab = ref(null);
const findOpen = ref(false);
const findQuery = ref("");
const replacementQuery = ref("");
const findIndex = ref(0);
const findCount = ref(0);
const theme = ref("dark");
const headingColors = ref(DEFAULT_HEADING_COLORS);
const indexBusy = ref(false);
const indexMessage = ref("");
const indexError = ref(false);
let wasIndexing = false;
let pollTimer;
function newTab() { tabs.open({ kind: "workspace", title: "Untitled", content: "", editing: true }); }
function toggleEdit() {
  const tab = tabs.active.value;
  if (tab) tab.editing = !tab.editing;
}
function goHome() {
  closeFind();
  tabs.showHome();
}
function openFind() {
  if (!tabs.active.value) return;
  findOpen.value = true;
}
function closeFind() {
  findOpen.value = false;
  findQuery.value = "";
  replacementQuery.value = "";
  findIndex.value = 0;
  findCount.value = 0;
}
function setFindQuery(query) {
  findQuery.value = query;
  findIndex.value = 0;
}
function setFindCount(count) {
  findCount.value = count;
  if (!count) findIndex.value = 0;
  else if (findIndex.value >= count) findIndex.value = count - 1;
}
function moveFind(delta) {
  if (!findCount.value) return;
  findIndex.value = (findIndex.value + delta + findCount.value) % findCount.value;
}
function replaceActive() {
  const tab = tabs.active.value;
  if (!tab?.editing || !findQuery.value.trim()) return;
  const nextContent = replaceMatch(tab.content, findQuery.value, replacementQuery.value, findIndex.value);
  if (nextContent !== tab.content) tabs.setContent(tab.id, nextContent);
}
function replaceAllActive() {
  const tab = tabs.active.value;
  if (!tab?.editing || !findQuery.value.trim()) return;
  const nextContent = replaceAllMatches(tab.content, findQuery.value, replacementQuery.value);
  if (nextContent !== tab.content) tabs.setContent(tab.id, nextContent);
}
function handleShortcut(event) {
  if ((event.ctrlKey || event.metaKey) && event.code === "KeyF" && tabs.active.value) {
    event.preventDefault();
    event.stopPropagation();
    openFind();
  } else if ((event.ctrlKey || event.metaKey) && event.code === "KeyH" && tabs.active.value) {
    event.preventDefault();
    event.stopPropagation();
    goHome();
  } else if (event.key === "Escape" && findOpen.value) {
    closeFind();
  }
}
async function toggleTheme() {
  theme.value = await setTheme(theme.value === "dark" ? "light" : "dark");
  document.documentElement.dataset.theme = theme.value;
  applyHeadingColors(
    document.documentElement,
    headingColors.value,
    theme.value,
  );
}
async function openMarkdown() {
  const document = await chooseMarkdown();
  if (document) tabs.open(classifyDocument(document, workspace.value));
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
  tab.renaming = true;
  try {
    const renamed = await renameWorkspaceNote(tab.title, title);
    Object.assign(tab, {
      title: renamed.title,
      path: renamed.path,
      modified_ns: renamed.modified_ns,
      content_hash: renamed.content_hash,
      externalState: null,
    });
  } finally {
    tab.renaming = false;
  }
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
  if (!tab?.path || tab.externalState || tab.renaming) return;
  const pathBeingChecked = tab.path;
  const status = await checkFile(tab);
  if (tab.renaming || tab.path !== pathBeingChecked || tabs.active.value !== tab) return;
  if (status.state !== "clean") { tab.externalState = status.state; conflictTab.value = tab; }
}
async function resolveConflict(action) {
  const tab = conflictTab.value;
  if (!tab) return;
  if (action === "cancel") {
    conflictTab.value = null;
    return;
  }
  if (action === "reload") {
    const document = await openDroppedPath(tab.path);
    tabs.replace(tab.id, document);
  } else if (action === "overwrite") {
    await saveTab(tab); tab.dirty = false; tab.externalState = null;
  } else { await saveActiveAs(); tab.externalState = null; }
  conflictTab.value = null;
}
async function selectWorkspace() {
  try {
    const selected = await chooseWorkspace();
    if (selected?.workspace) {
      workspace.value = selected.workspace;
      indexBusy.value = true;
      wasIndexing = true;
      indexMessage.value = "Indexing workspace…";
      indexError.value = false;
      await pollIndexStatus();
    }
  } catch (error) { window.alert(`Could not select workspace: ${error.message}`); }
}
async function pollIndexStatus() {
  try {
    const status = await getIndexStatus();
    const normalizeWorkspace = (value) => String(value || "").replaceAll("\\", "/").replace(/\/+$/, "").toLowerCase();
    if (status?.workspace && workspace.value && normalizeWorkspace(status.workspace) !== normalizeWorkspace(workspace.value)) return;
    if (status.indexing) {
      indexBusy.value = true;
      wasIndexing = true;
      indexMessage.value = "Indexing workspace…";
      indexError.value = false;
    } else if (wasIndexing || indexBusy.value) {
      indexBusy.value = false;
      wasIndexing = false;
      indexError.value = Boolean(status.error);
      indexMessage.value = status.error ? `Could not index workspace: ${status.error}` : "Search index ready.";
    }
  } catch (error) {
    indexBusy.value = false;
    wasIndexing = false;
    indexError.value = true;
    indexMessage.value = `Could not check index status: ${error.message}`;
  }
}
async function rebuildSearchIndex() {
  if (indexBusy.value || !workspace.value) return;
  indexBusy.value = true;
  wasIndexing = true;
  indexMessage.value = "";
  indexError.value = false;
  try {
    const result = await rebuildIndex();
    if (result?.error) throw new Error(result.error);
    indexMessage.value = "Search index rebuilt.";
    wasIndexing = false;
  } catch (error) {
    indexError.value = true;
    indexMessage.value = `Could not rebuild search index: ${error.message}`;
  } finally {
    indexBusy.value = false;
  }
}
async function handleDrop(event) {
  const paths = Array.isArray(event.detail?.paths) ? event.detail.paths : [];
  for (const path of paths) {
    try {
      const document = await openDroppedPath(path);
      if (document?.kind === "external") tabs.open(classifyDocument(document, workspace.value));
    } catch (_error) {
      // Continue opening the remaining files in this drop.
    }
  }
  if (!paths.length && event.detail?.kind && event.detail?.path) {
    tabs.open(classifyDocument(event.detail, workspace.value));
  }
}
onMounted(async () => {
  window.addEventListener("keydown", handleShortcut, true);
  await startupEvent("frontend-mounted");
  theme.value = await getTheme();
  document.documentElement.dataset.theme = theme.value;
  headingColors.value = await getHeadingColors().catch(
    () => DEFAULT_HEADING_COLORS,
  );
  applyHeadingColors(
    document.documentElement,
    headingColors.value,
    theme.value,
  );
  const fontSettings = await getFontSettings().catch(() => DEFAULT_FONT_SIZES);
  applyFontSettings(document.documentElement, fontSettings);
  workspace.value = await getWorkspace();
  await pollIndexStatus();
  await startupEvent("frontend-workspace-read");
  window.addEventListener("flatnotes-drop", handleDrop);
  pollTimer = window.setInterval(() => { pollActiveFile(); pollIndexStatus(); }, 1000);
});
onUnmounted(() => { window.clearInterval(pollTimer); window.removeEventListener("flatnotes-drop", handleDrop); window.removeEventListener("keydown", handleShortcut, true); });
</script>
