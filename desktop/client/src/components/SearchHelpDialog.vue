<template>
  <div class="modal-backdrop" role="presentation" @click.self="close">
    <section
      id="search-help-dialog"
      class="search-help-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="search-help-title"
      @keydown.escape.stop.prevent="close"
    >
      <header>
        <h2 id="search-help-title">Search help</h2>
        <button
          ref="closeButton"
          class="search-help-close"
          type="button"
          aria-label="Close search help"
          @click="close"
        >
          &times;
        </button>
      </header>
      <table>
        <thead>
          <tr><th>Format</th><th>Example</th></tr>
        </thead>
        <tbody>
          <tr><td>All words</td><td><code>terra validator</code></td></tr>
          <tr><td>Exact phrase</td><td><code>&quot;bonding curve&quot;</code></td></tr>
          <tr><td>Prefix</td><td><code>terra*</code></td></tr>
          <tr><td>One wildcard</td><td><code>te?t</code></td></tr>
          <tr><td>Fuzzy, one edit</td><td><code>terrd~</code></td></tr>
          <tr><td>Fuzzy, two edits</td><td><code>terrad~2</code></td></tr>
          <tr><td>Title field</td><td><code>title:curve</code></td></tr>
          <tr><td>Content field</td><td><code>content:node</code></td></tr>
          <tr><td>Tag field</td><td><code>tags:terra</code></td></tr>
          <tr><td>Boolean</td><td><code>terra AND validator</code></td></tr>
        </tbody>
      </table>
      <p class="search-help-note">
        Prefix searches perform best without a leading wildcard. Fuzzy distances
        above two can be slow.
      </p>
    </section>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";

const emit = defineEmits(["close"]);
const closeButton = ref();

function close() { emit("close"); }

onMounted(() => nextTick(() => closeButton.value?.focus()));
</script>
