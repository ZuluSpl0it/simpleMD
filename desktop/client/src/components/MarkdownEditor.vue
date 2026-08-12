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
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({ content: { type: String, default: "" }, mode: { type: String, default: "markdown" }, editing: { type: Boolean, default: false }, theme: { type: String, default: "dark" }, findQuery: { type: String, default: "" }, findIndex: { type: Number, default: 0 } });
const emit = defineEmits(["change", "find-count"]);
const container = ref();
let editor;
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
onMounted(() => {
  const options = {
    el: container.value,
    height: "100%",
    theme: props.theme,
    initialValue: props.content,
    customHTMLRenderer: {
      // Markdown soft breaks are wrapping hints, not intentional line breaks.
      // Keep hard breaks (two trailing spaces, backslash, or <br>) intact.
      softbreak: () => ({ type: "html", content: " " }),
    },
  };
  editor = props.editing
    ? new Editor({ ...options, initialEditType: props.mode, previewStyle: "tab" })
    : Editor.factory({ ...options, viewer: true });
  if (props.editing) editor.on("change", () => emit("change", editor.getMarkdown()));
  refreshHighlights();
});
watch(() => props.content, (value) => { if (editor && editor.getMarkdown && editor.getMarkdown() !== value) editor.setMarkdown(value); });
watch(() => [props.findQuery, props.findIndex, props.content, props.editing, props.theme], refreshHighlights);
onBeforeUnmount(() => { clearFindHighlights(); editor?.destroy(); });
</script>
