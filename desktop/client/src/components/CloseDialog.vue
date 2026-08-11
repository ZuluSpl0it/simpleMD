<template>
  <div class="modal-backdrop" role="presentation">
    <div class="close-dialog" role="dialog" aria-modal="true" aria-labelledby="close-dialog-title">
      <p id="close-dialog-title">Save changes to {{ tab.title }}?</p>
      <div>
        <button type="button" @click="$emit('resolve', 'save')">Save</button>
        <button type="button" @click="$emit('resolve', 'discard')">Discard</button>
        <button type="button" @click="$emit('resolve', 'cancel')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ tab: { type: Object, required: true } });
defineEmits(["resolve"]);
</script>
