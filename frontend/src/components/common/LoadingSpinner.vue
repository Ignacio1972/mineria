<script setup lang="ts">
defineProps<{
  size?: 'xs' | 'sm' | 'md' | 'lg';
  text?: string;
}>();
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-2">
    <span
      class="loading loading-spinner"
      :class="{
        'loading-xs': size === 'xs',
        'loading-sm': size === 'sm',
        'loading-md': size === 'md' || !size,
        'loading-lg': size === 'lg',
      }"
    ></span>
    <span v-if="text" class="text-sm opacity-60">{{ text }}</span>
  </div>
</template>
