<template><div ref="container" class="editor" /></template>

<script setup>
import Editor from "@toast-ui/editor";
import "@toast-ui/editor/dist/toastui-editor.css";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({ content: { type: String, default: "" } });
const emit = defineEmits(["change"]);
const container = ref();
let editor;
onMounted(() => {
  editor = new Editor({ el: container.value, height: "calc(100vh - 48px)", initialEditType: "markdown", previewStyle: "vertical", initialValue: props.content });
  editor.on("change", () => emit("change", editor.getMarkdown()));
});
watch(() => props.content, (value) => { if (editor && editor.getMarkdown() !== value) editor.setMarkdown(value); });
onBeforeUnmount(() => editor?.destroy());
</script>
