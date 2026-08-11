<template>
  <div class="editor-shell" :class="{ editing }">
    <div ref="container" class="editor" :class="{ 'markdown-only': mode === 'markdown', viewing: !editing }" />
  </div>
</template>

<script setup>
import Editor from "@toast-ui/editor";
import "@toast-ui/editor/dist/toastui-editor.css";
import "@toast-ui/editor/dist/theme/toastui-editor-dark.css";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({ content: { type: String, default: "" }, mode: { type: String, default: "markdown" }, editing: { type: Boolean, default: false } });
const emit = defineEmits(["change"]);
const container = ref();
let editor;
onMounted(() => {
  const options = { el: container.value, height: "100%", theme: "dark", initialValue: props.content };
  editor = props.editing
    ? new Editor({ ...options, initialEditType: props.mode, previewStyle: "tab" })
    : Editor.factory({ ...options, viewer: true });
  if (props.editing) editor.on("change", () => emit("change", editor.getMarkdown()));
});
watch(() => props.content, (value) => { if (editor && editor.getMarkdown && editor.getMarkdown() !== value) editor.setMarkdown(value); });
onBeforeUnmount(() => editor?.destroy());
</script>
