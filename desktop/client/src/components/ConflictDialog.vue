<template>
  <div v-if="visible" class="conflict" role="dialog">
    <p>{{ tab.externalState === "missing" ? "File no longer exists." : "File changed outside Flatnotes." }}</p>
    <button v-if="actions.includes('reload')" type="button" @click="$emit('resolve', 'reload')">Reload</button>
    <button v-if="actions.includes('overwrite')" type="button" @click="$emit('resolve', 'overwrite')">Overwrite</button>
    <button v-if="actions.includes('saveAs')" type="button" @click="$emit('resolve', 'saveAs')">Save As</button>
    <button type="button" @click="$emit('resolve', 'cancel')">Cancel</button>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { conflictActions } from "./ConflictDialog.js";

const props = defineProps({ visible: Boolean, tab: { type: Object, required: true } });
defineEmits(["resolve"]);
const actions = computed(() => conflictActions(props.tab));
</script>
