<script setup lang="ts">
import { computed } from 'vue'
import { formatUserIdentity } from '@/utils/format'

interface Props {
  username?: string | null
  userId?: number | string | null
  fallback?: string
  idLabel?: string
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  fallback: '用户',
  idLabel: '',
  compact: false,
})

const displayName = computed(() => {
  const name = props.username?.trim()
  return name || props.fallback
})

const normalizedUserId = computed(() => {
  if (props.userId === null || props.userId === undefined || props.userId === '') {
    return ''
  }
  return String(props.userId)
})

const identityLabel = computed(() => formatUserIdentity(props.username, props.userId, props.fallback))
</script>

<template>
  <span
    class="user-identity"
    :class="{ 'user-identity--compact': compact }"
    :title="identityLabel"
  >
    <span class="user-identity__name">{{ displayName }}</span>
    <span v-if="normalizedUserId" class="user-identity__id">
      {{ idLabel }}#{{ normalizedUserId }}
    </span>
  </span>
</template>

<style lang="scss" scoped>
.user-identity {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  min-width: 0;
  vertical-align: middle;
}

.user-identity__name {
  min-width: 0;
  color: inherit;
  font-weight: inherit;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-identity__id {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  max-width: 100%;
  padding: 1px 6px;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: #f4f8ff;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.45;
}

.user-identity--compact {
  gap: 4px;

  .user-identity__id {
    padding: 0 5px;
    font-size: 11px;
  }
}
</style>
