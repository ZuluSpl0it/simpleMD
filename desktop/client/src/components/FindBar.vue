<template>
  <div class="find-bar" role="search">
    <input
      ref="input"
      :value="query"
      type="search"
      placeholder="Find in document"
      aria-label="Find in document"
      @input="$emit('update:query', $event.target.value)"
      @keydown.enter.prevent="$emit($event.shiftKey ? 'previous' : 'next')"
      @keydown.esc="$emit('close')"
    />
    <span class="find-count" aria-live="polite">
      {{ query ? (matchCount ? `${activeMatch + 1} of ${matchCount}` : "No matches") : "" }}
    </span>
    <button type="button" :disabled="!matchCount" aria-label="Previous match" @click="$emit('previous')">↑</button>
    <button type="button" :disabled="!matchCount" aria-label="Next match" @click="$emit('next')">↓</button>
    <button type="button" aria-label="Close find" @click="$emit('close')">×</button>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";

defineProps({
  query: { type: String, default: "" },
  matchCount: { type: Number, default: 0 },
  activeMatch: { type: Number, default: 0 },
});
defineEmits(["update:query", "previous", "next", "close"]);
const input = ref();
onMounted(() => input.value?.focus());
</script>
