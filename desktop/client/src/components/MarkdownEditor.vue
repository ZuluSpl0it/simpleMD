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
import { linkDestinationAttributes, routeLinkClick } from "../linkRouting.js";
import { isShortcut } from "../shortcuts.js";
import {
  configureWysiwygSoftBreaks,
  decodeEditorLineBreaks,
  insertWysiwygLineBreak,
  lineBreakMarker,
  markdownForWysiwyg,
} from "../softBreaks.js";
import { createScrollPositionListener, preserveModeScroll, readScrollPosition, restoreScrollPosition } from "../editorScroll.js";
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({ content: { type: String, default: "" }, mode: { type: String, default: "markdown" }, editing: { type: Boolean, default: false }, theme: { type: String, default: "dark" }, findQuery: { type: String, default: "" }, findIndex: { type: Number, default: 0 }, initialScrollPosition: { type: Object, default: () => ({ view: "viewing", top: 0, ratio: 0 }) }, scrollKey: { type: String, default: "" }, path: { type: String, default: "" } });
const emit = defineEmits(["change", "find-count", "scroll-position", "link-click", "mode-change"]);
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
function handleEditorKeydown(event) {
  if (!props.editing || !isShortcut(event, "KeyY")) return;
  event.preventDefault();
  event.stopPropagation();
  editor?.exec("redo");
}
function handleModeSwitchClick(event) {
  if (!props.editing || !editor?.isMarkdownMode?.()) return;
  const tab = event.target.closest?.(".toastui-editor-mode-switch .tab-item");
  if (tab?.textContent.trim() !== "WYSIWYG") return;
  const markdown = editor.getMarkdown();
  const encoded = markdownForWysiwyg(editor, markdown);
  if (encoded !== markdown) editor.setMarkdown(encoded, false);
}
function normalizedEditorMarkdown() {
  return decodeEditorLineBreaks(editor.getMarkdown());
}
function setEditorMarkdown(markdown) {
  const value = editor.isWysiwygMode?.() ? markdownForWysiwyg(editor, markdown) : markdown;
  editor.setMarkdown(value, false);
}
function emitEditorChange() {
  emit("change", normalizedEditorMarkdown());
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
  // Capture links before Toast UI or ProseMirror can consume the click.
  container.value.addEventListener("click", handleLinkClick, true);
  container.value.addEventListener("click", handleModeSwitchClick, true);
  container.value.addEventListener("keydown", handleEditorKeydown, true);
  const options = {
    el: container.value,
    height: "100%",
    theme: props.theme,
    initialValue: props.editing ? "" : props.content,
    toolbarItems: [
      ["heading", "bold", "italic", "strike"],
      ["hr", "quote", { name: "lineBreak", className: "line-break toastui-editor-toolbar-icons", tooltip: "Line Break", command: "insertLineBreak" }],
      ["ul", "ol", "task", "indent", "outdent"],
      ["table", "image", "link"],
      ["code", "codeblock"],
      ["scrollSync"],
    ],
    widgetRules: [
      {
        rule: new RegExp(lineBreakMarker),
        toDOM: () => document.createElement("br"),
      },
    ],
    customHTMLRenderer: {
      link: (node, { entering, origin }) => {
        const rendered = origin();
        if (entering) rendered.attributes = { ...rendered.attributes, ...linkDestinationAttributes(node.destination) };
        return rendered;
      },
      // Markdown soft breaks are wrapping hints, not intentional line breaks.
      // Keep hard breaks (two trailing spaces, backslash, or <br>) intact.
      softbreak: () => ({ type: "html", content: " " }),
    },
  };
  editor = props.editing
    ? new Editor({ ...options, initialEditType: props.mode, previewStyle: "tab" })
    : Editor.factory({ ...options, viewer: true });
  if (props.editing) {
    editor.addCommand("markdown", "insertLineBreak", () => {
      editor.insertText("<br>");
      return true;
    });
    editor.addCommand("wysiwyg", "insertLineBreak", insertWysiwygLineBreak);
    configureWysiwygSoftBreaks(editor);
    setEditorMarkdown(props.content);
    editor.on("changeMode", (mode) => {
      preserveModeScroll(container.value, mode, lastScrollPosition, undefined, (position) => emitScrollPosition(position));
      emit("mode-change", mode);
      if (mode === "markdown") {
        const markdown = editor.getMarkdown();
        const decoded = decodeEditorLineBreaks(markdown);
        if (decoded !== markdown) editor.setMarkdown(decoded, false);
      }
      emitEditorChange();
      bindScrollListeners();
    });
    editor.on("change", emitEditorChange);
  }
  nextTick(() => {
    bindScrollListeners();
    restoreInitialScroll();
  });
  refreshHighlights();
});
watch(() => props.content, (value) => {
  if (editor?.getMarkdown && normalizedEditorMarkdown() !== value) setEditorMarkdown(value);
});
watch(() => [props.findQuery, props.findIndex, props.content, props.editing, props.theme], refreshHighlights);
onBeforeUnmount(() => {
  container.value?.removeEventListener("click", handleLinkClick, true);
  container.value?.removeEventListener("click", handleModeSwitchClick, true);
  container.value?.removeEventListener("keydown", handleEditorKeydown, true);
  emitScrollPosition();
  for (const target of scrollTargets) target.removeEventListener("scroll", handleScroll);
  clearFindHighlights();
  editor?.destroy();
});
</script>
