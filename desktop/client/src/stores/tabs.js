import { computed, reactive, ref } from "vue";

export function createTabs() {
  const items = reactive([]);
  const activeId = ref(null);
  const byId = (id) => items.find((item) => item.id === id);
  function open(document) {
    const id = `${Date.now()}-${items.length}`;
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
      mode: document.mode || "markdown",
      editing: document.editing ?? false,
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
  function requestClose(id) {
    const tab = byId(id);
    if (tab?.dirty) return { requiresConflict: true };
    items.splice(items.indexOf(tab), 1);
    activeId.value = items.at(-1)?.id || null;
    return { requiresConflict: false };
  }
  return { items, activeId, byId, open, setContent, requestClose, active: computed(() => byId(activeId.value)) };
}
