<template>
  <nav class="tabs" aria-label="Open files">
    <button v-for="tab in tabs.items" :key="tab.id" type="button" :aria-current="tabs.activeId === tab.id" @click="tabs.activeId = tab.id">
      {{ tab.title }}<span v-if="tab.dirty"> •</span>
      <span role="button" tabindex="0" @click.stop="$emit('close-tab', tab.id)">×</span>
    </button>
    <button type="button" @click="$emit('new-tab')">+</button>
    <div v-if="active" class="tab-actions">
      <button type="button" class="edit-toggle" :class="{ active: active.editing }" :aria-pressed="active.editing" @click="$emit('toggle-edit')">Edit</button>
      <template v-if="active.editing">
        <button type="button" @click="$emit('save')">Save</button>
        <button type="button" @click="$emit('save-as')">Save As</button>
      </template>
      <button v-if="active.kind === 'workspace' && active.path" type="button" @click="$emit('rename')">Rename</button>
      <button v-if="active.kind === 'workspace' && active.path" type="button" @click="$emit('delete')">Delete</button>
    </div>
  </nav>
</template>

<script setup>
defineProps({ tabs: { type: Object, required: true }, active: { type: Object, default: null } });
defineEmits(["new-tab", "close-tab", "toggle-edit", "save", "save-as", "rename", "delete"]);
</script>
