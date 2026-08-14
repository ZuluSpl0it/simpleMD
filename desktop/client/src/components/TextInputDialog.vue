<template>
  <div class="modal-backdrop" role="presentation">
    <div class="text-input-dialog" role="dialog" aria-modal="true" aria-labelledby="text-input-dialog-title">
      <h2 id="text-input-dialog-title">{{ title }}</h2>
      <form @submit.prevent="submit">
        <label for="text-input-dialog-value">{{ label }}</label>
        <input id="text-input-dialog-value" ref="input" v-model="draft" type="text" autocomplete="off" @keydown.escape="cancel" />
        <div class="text-input-dialog-actions">
          <button type="submit">{{ confirmLabel }}</button>
          <button type="button" @click="cancel">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";

const props = defineProps({
  title: { type: String, required: true },
  label: { type: String, required: true },
  value: { type: String, default: "" },
  confirmLabel: { type: String, default: "Save" },
});
const emit = defineEmits(["submit", "cancel"]);
const input = ref();
const draft = ref(props.value);
function submit() {
  const value = draft.value.trim();
  if (value) emit("submit", value);
}
function cancel() { emit("cancel"); }
onMounted(() => nextTick(() => input.value?.focus()));
</script>
