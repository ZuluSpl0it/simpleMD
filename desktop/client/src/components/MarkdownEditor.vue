<template>
  <div class="editor-shell" :class="{ editing }">
    <div ref="container" class="editor" :class="{ 'markdown-only': mode === 'markdown', viewing: !editing }" />
  </div>
</template>

<script setup>
import Editor from "@toast-ui/editor";
import "@toast-ui/editor/dist/toastui-editor.css";
import "@toast-ui/editor/dist/theme/toastui-editor-dark.css";
import { clearFindHighlights, highlightMatches } from "../find.js";
import { routeLinkClick } from "../linkRouting.js";
import { configureWysiwygSoftBreaks } from "../softBreaks.js";
import { createScrollPositionListener, preserveModeScroll, readScrollPosition, restoreScrollPosition } from "../editorScroll.js";
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({ content: { type: String, default: "" }, mode: { type: String, default: "markdown" }, editing: { type: Boolean, default: false }, theme: { type: String, default: "dark" }, findQuery: { type: String, default: "" }, findIndex: { type: Number, default: 0 }, initialScrollPosition: { type: Object, default: () => ({ view: "viewing", top: 0, ratio: 0 }) }, scrollKey: { type: String, default: "" }, path: { type: String, default: "" } });
const emit = defineEmits(["change", "find-count", "scroll-position", "link-click"]);
const container = ref();
let editor;
let scrollTargets = [];
let lastScrollPosition = props.initialScrollPosition;
function findRoot() {
  if (!container.value) return null;
  return props.editing
    ? container.value.querySelector(".toastui-editor-md-container > .toastui-editor")
    : container.value.querySelector(".toastui-editor-contents");
}
async function refreshHighlights() {
  await nextTick();
  const count = highlightMatches(findRoot(), props.findQuery, props.findIndex);
  emit("find-count", count);
}
function emitScrollPosition(value) {
  const position = value ?? readScrollPosition(container.value, props.editing ? undefined : "viewing");
  if (position.view === lastScrollPosition?.view && position.top === lastScrollPosition?.top && position.ratio === lastScrollPosition?.ratio) return;
  lastScrollPosition = position;
  emit("scroll-position", props.scrollKey, position);
}
const handleScroll = createScrollPositionListener(emitScrollPosition);
function handleLinkClick(event) {
  routeLinkClick(event, props.path, (route) => emit("link-click", route));
}
function bindScrollListeners() {
  for (const target of scrollTargets) target.removeEventListener("scroll", handleScroll);
  const targets = props.editing
    ? [container.value?.querySelector(".toastui-editor-md-container .ProseMirror"), container.value?.querySelector(".toastui-editor-ww-container .toastui-editor-contents")]
    : [container.value];
  scrollTargets = targets.filter(Boolean);
  for (const target of scrollTargets) target.addEventListener("scroll", handleScroll, { passive: true });
}
function restoreInitialScroll() {
  restoreScrollPosition(container.value, props.editing ? props.mode : "viewing", props.initialScrollPosition);
}
onMounted(() => {
  container.value.addEventListener("click", handleLinkClick);
  const options = {
    el: container.value,
    height: "100%",
    theme: props.theme,
    initialValue: props.editing ? "" : props.content,
    customHTMLRenderer: {
      // Markdown soft breaks are wrapping hints, not intentional line breaks.
      // Keep hard breaks (two trailing spaces, backslash, or <br>) intact.
      softbreak: () => ({ type: "html", content: " " }),
    },
  };
  editor = props.editing
    ? new Editor({ ...options, initialEditType: props.mode, previewStyle: "tab" })
    : Editor.factory({ ...options, viewer: true });
  if (props.editing) {
    configureWysiwygSoftBreaks(editor);
    editor.setMarkdown(props.content, false);
    editor.on("changeMode", (mode) => {
      preserveModeScroll(container.value, mode, lastScrollPosition, undefined, (position) => emitScrollPosition(position));
      bindScrollListeners();
    });
    editor.on("change", () => emit("change", editor.getMarkdown()));
  }
  nextTick(() => {
    bindScrollListeners();
    restoreInitialScroll();
  });
  refreshHighlights();
});
watch(() => props.content, (value) => { if (editor && editor.getMarkdown && editor.getMarkdown() !== value) editor.setMarkdown(value); });
watch(() => [props.findQuery, props.findIndex, props.content, props.editing, props.theme], refreshHighlights);
onBeforeUnmount(() => {
  container.value?.removeEventListener("click", handleLinkClick);
  emitScrollPosition();
  for (const target of scrollTargets) target.removeEventListener("scroll", handleScroll);
  clearFindHighlights();
  editor?.destroy();
});
</script>
