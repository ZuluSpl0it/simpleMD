<template>
  <nav class="tabs" aria-label="Open files">
    <button type="button" title="Home" aria-label="Home" @click.stop.prevent="$emit('home')">⌂</button>
    <button type="button" @click="$emit('new-tab')">+</button>
    <button v-for="tab in tabs.items" :key="tab.id" type="button" :aria-current="tabs.activeId?.value === tab.id" @click="tabs.select(tab.id)">
      {{ tab.title }}<span v-if="tab.dirty"> •</span>
      <span role="button" tabindex="0" @click.stop="$emit('close-tab', tab.id)">×</span>
    </button>
    <div class="tab-actions">
      <template v-if="active">
        <button type="button" class="edit-toggle" :class="{ active: active.editing }" :aria-pressed="active.editing" @click="$emit('toggle-edit')">Edit</button>
        <template v-if="active.editing">
          <button type="button" :disabled="!active.dirty" @click="$emit('save')">Save</button>
          <button type="button" :disabled="!active.dirty" @click="$emit('save-as')">Save As</button>
          <button v-if="active.kind === 'workspace' && active.path" type="button" @click="$emit('rename')">Rename</button>
          <button v-if="active.kind === 'workspace' && active.path" type="button" @click="$emit('delete')">Delete</button>
        </template>
      </template>
      <button type="button" title="Switch theme" :aria-label="`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`" @click="$emit('toggle-theme')">{{ theme === "dark" ? "☼" : "☾" }}</button>
    </div>
  </nav>
</template>

<script setup>
defineProps({ tabs: { type: Object, required: true }, active: { type: Object, default: null }, theme: { type: String, default: "dark" } });
defineEmits(["new-tab", "home", "toggle-theme", "close-tab", "toggle-edit", "save", "save-as", "rename", "delete"]);
</script>
