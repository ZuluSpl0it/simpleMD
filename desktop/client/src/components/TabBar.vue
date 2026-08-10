<template>
  <nav class="tabs" aria-label="Open files">
    <button v-for="tab in tabs.items" :key="tab.id" type="button" :aria-current="tabs.activeId === tab.id" @click="tabs.activeId = tab.id">
      {{ tab.title }}<span v-if="tab.dirty"> •</span>
    </button>
    <button type="button" @click="$emit('new-tab')">+</button>
  </nav>
</template>

<script setup>
defineProps({ tabs: { type: Object, required: true } });
defineEmits(["new-tab"]);
</script>
