import { computed, reactive, ref } from "vue";

export function createTabs() {
  const items = reactive([]);
  const activeId = ref(null);
  const byId = (id) => items.find((item) => item.id === id);
  function open(document) {
    const id = `${Date.now()}-${items.length}`;
    const mode = document.mode || "markdown";
    const editing = document.editing ?? false;
    items.push({
      id,
      kind: document.kind || "workspace",
      path: document.path || null,
      title: document.title || document.path?.split(/[\\/]/).pop() || "Untitled",
      content: document.content || "",
      savedContent: document.content || "",
      dirty: false,
      fingerprint: document.content_hash || null,
      modified_ns: document.modified_ns || 0,
      content_hash: document.content_hash || null,
      mode,
      editing,
      editorRevision: 0,
      scrollPosition: { view: editing ? mode : "viewing", top: 0, ratio: 0 },
    });
    activeId.value = id;
    return id;
  }
  function setContent(id, content) {
    const tab = byId(id);
    if (!tab) return;
    tab.content = content;
    tab.dirty = tab.content !== tab.savedContent;
  }
  function setScrollPosition(id, position) {
    const tab = byId(id);
    if (!tab) return;
    const view = ["viewing", "markdown", "wysiwyg"].includes(position?.view) ? position.view : "viewing";
    const top = Number(position?.top);
    const ratio = Number(position?.ratio);
    tab.scrollPosition = {
      view,
      top: Number.isFinite(top) ? Math.max(0, top) : 0,
      ratio: Number.isFinite(ratio) ? Math.min(1, Math.max(0, ratio)) : 0,
    };
  }
  function replace(id, document) {
    const tab = byId(id);
    if (!tab) return;
    const content = document.content || "";
    Object.assign(tab, {
      content,
      savedContent: content,
      dirty: false,
      fingerprint: document.content_hash || null,
      modified_ns: document.modified_ns || 0,
      content_hash: document.content_hash || null,
      externalState: null,
      editorRevision: tab.editorRevision + 1,
    });
  }
  function showHome() {
    activeId.value = null;
  }
  function select(id) {
    if (byId(id)) activeId.value = id;
  }
  function requestClose(id) {
    const tab = byId(id);
    if (tab?.dirty) return { requiresConflict: true };
    items.splice(items.indexOf(tab), 1);
    activeId.value = items.at(-1)?.id || null;
    return { requiresConflict: false };
  }
  return { items, activeId, byId, open, select, setContent, setScrollPosition, replace, showHome, requestClose, active: computed(() => byId(activeId.value)) };
}
