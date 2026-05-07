<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  label: string
  count?: number
  max?: number
  tone?: 'primary' | 'light'
}>(), {
  count: 0,
  max: 99,
  tone: 'primary',
})

const displayCount = computed(() => {
  if (!props.count || props.count <= 0) {
    return ''
  }
  return props.count > props.max ? `${props.max}+` : String(props.count)
})
</script>

<template>
  <span class="unread-label-badge" :class="[`is-${tone}`, { 'has-count': !!displayCount }]">
    <span class="unread-label-badge__text">{{ label }}</span>
    <span v-if="displayCount" class="unread-label-badge__count">{{ displayCount }}</span>
  </span>
</template>

<style lang="scss" scoped>
.unread-label-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  line-height: 1;

  &.has-count {
    padding-right: 0.8em;
  }
}

.unread-label-badge__text {
  display: inline-block;
}

.unread-label-badge__count {
  position: absolute;
  top: -0.75em;
  right: -0.1em;
  min-width: 1.45em;
  height: 1.45em;
  padding: 0 0.36em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 0.68em;
  font-weight: 700;
  letter-spacing: 0;
  box-sizing: border-box;
  box-shadow: 0 6px 14px rgba(245, 34, 45, 0.2);
}

.is-primary .unread-label-badge__count {
  background: linear-gradient(135deg, #ff5a5f 0%, #f5222d 100%);
  color: #fff;
  border: 2px solid #fff;
}

.is-light .unread-label-badge__count {
  background: linear-gradient(135deg, #ff6b6f 0%, #f5222d 100%);
  color: #fff;
  border: 2px solid #f5f7fa;
}
</style>
