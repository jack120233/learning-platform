import { onUnmounted, ref } from 'vue'
import {
  saveLearningSession,
  type LearningSessionEndReason,
  type LearningSessionRequest,
} from '@/api/learning'

export interface LearningSessionResourceContext {
  resourceId: number
  resourceType: 'video' | 'audio' | 'document' | 'image'
  currentTime?: number
  totalTime?: number
  isCompleted?: boolean
}

interface QueuedSessionItem {
  payload: LearningSessionRequest
  queued_at: string
}

const QUEUE_KEY = 'learning_session_retry_queue'
const QUEUE_TTL_MS = 7 * 24 * 60 * 60 * 1000
const DOCUMENT_IDLE_MS = 5 * 60 * 1000
const DOCUMENT_CAP_SECONDS = 20 * 60
const IMAGE_CAP_SECONDS = 5 * 60

function createSessionId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function isStorageAvailable(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

function isQueuedSessionItem(value: unknown): value is QueuedSessionItem {
  if (!value || typeof value !== 'object') return false
  const item = value as Partial<QueuedSessionItem>
  return !!item.payload && typeof item.payload === 'object' && typeof item.queued_at === 'string'
}

function loadQueue(): QueuedSessionItem[] {
  if (!isStorageAvailable()) return []

  try {
    const raw = window.localStorage.getItem(QUEUE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    const cutoff = Date.now() - QUEUE_TTL_MS
    const retained = parsed.filter((item): item is QueuedSessionItem => (
      isQueuedSessionItem(item) && new Date(item.queued_at).getTime() >= cutoff
    ))
    if (retained.length !== parsed.length) {
      window.localStorage.setItem(QUEUE_KEY, JSON.stringify(retained))
    }
    return retained
  } catch {
    return []
  }
}

function saveQueue(items: QueuedSessionItem[]): void {
  if (!isStorageAvailable()) return

  try {
    window.localStorage.setItem(QUEUE_KEY, JSON.stringify(items))
  } catch {
    // Storage quota/private-mode failures must not block learning.
  }
}

export function useLearningSession() {
  const isSubmitting = ref(false)
  const queue = ref<QueuedSessionItem[]>(loadQueue())

  let sessionId: string | null = null
  let activeResource: LearningSessionResourceContext | null = null
  let startedAt: Date | null = null
  let startPositionSeconds: number | null = null
  let effectiveDurationSeconds = 0
  let lastMediaTickAt: number | null = null
  let lastActivityAt = Date.now()
  let finalized = false
  let idleTimer: ReturnType<typeof window.setInterval> | null = null
  let documentIdleFinalized = false

  function stopIdleTimer(): void {
    if (idleTimer) {
      window.clearInterval(idleTimer)
      idleTimer = null
    }
    documentIdleFinalized = false
  }

  function startIdleTimer(): void {
    stopIdleTimer()
    idleTimer = window.setInterval(() => {
      if (!activeResource || activeResource.resourceType !== 'document' || documentIdleFinalized) return
      if (Date.now() - lastActivityAt >= DOCUMENT_IDLE_MS) {
        documentIdleFinalized = true
        finishSession('timeout')
      }
    }, 30000)
  }

  function persistQueue() {
    queue.value = loadQueue()
    saveQueue(queue.value)
  }

  function enqueue(payload: LearningSessionRequest) {
    persistQueue()
    queue.value.push({ payload, queued_at: new Date().toISOString() })
    saveQueue(queue.value)
  }

  function startSession(context: LearningSessionResourceContext): void {
    stopIdleTimer()
    sessionId = createSessionId()
    activeResource = { ...context }
    startedAt = new Date()
    startPositionSeconds = Math.floor(context.currentTime ?? 0)
    effectiveDurationSeconds = 0
    lastMediaTickAt = null
    lastActivityAt = Date.now()
    finalized = false
    if (context.resourceType === 'document') {
      startIdleTimer()
    }
  }

  function updateSessionContext(context: Partial<LearningSessionResourceContext>): void {
    if (!activeResource) return
    activeResource = { ...activeResource, ...context }
  }

  function recordMediaPlay(): void {
    lastMediaTickAt = Date.now()
  }

  function recordMediaPause(): void {
    lastMediaTickAt = null
  }

  function recordMediaPlayingDelta(): void {
    if (!activeResource || !['video', 'audio'].includes(activeResource.resourceType)) return
    const now = Date.now()
    if (lastMediaTickAt != null) {
      const delta = Math.max(0, (now - lastMediaTickAt) / 1000)
      effectiveDurationSeconds += Math.min(delta, 5)
    }
    lastMediaTickAt = now
  }

  function recordActivity(): void {
    lastActivityAt = Date.now()
  }

  function accumulatePassiveDuration(): void {
    if (!activeResource || !startedAt) return
    const wallClockSeconds = (Date.now() - startedAt.getTime()) / 1000
    if (activeResource.resourceType === 'document') {
      const idleSeconds = (Date.now() - lastActivityAt) / 1000
      effectiveDurationSeconds = Math.min(Math.max(0, wallClockSeconds - Math.max(0, idleSeconds - DOCUMENT_IDLE_MS / 1000)), DOCUMENT_CAP_SECONDS)
    } else if (activeResource.resourceType === 'image') {
      effectiveDurationSeconds = Math.min(wallClockSeconds, IMAGE_CAP_SECONDS)
    }
  }

  function buildPayload(endReason: LearningSessionEndReason): LearningSessionRequest | null {
    if (!sessionId || !activeResource || !startedAt || finalized) return null
    if (['video', 'audio'].includes(activeResource.resourceType)) {
      recordMediaPlayingDelta()
    }
    accumulatePassiveDuration()

    const currentTime = Math.floor(activeResource.currentTime ?? 0)
    const totalTime = Math.floor(activeResource.totalTime ?? 0)
    const progressPercent = totalTime > 0 ? Math.min((currentTime / totalTime) * 100, 100) : null

    return {
      session_id: sessionId,
      resource_id: activeResource.resourceId,
      started_at: startedAt.toISOString(),
      ended_at: new Date().toISOString(),
      effective_duration_seconds: Math.floor(effectiveDurationSeconds),
      start_position_seconds: ['video', 'audio'].includes(activeResource.resourceType) ? startPositionSeconds : null,
      end_position_seconds: ['video', 'audio'].includes(activeResource.resourceType) ? currentTime : null,
      progress_percent_at_end: activeResource.isCompleted ? 100 : progressPercent,
      is_completed_at_end: activeResource.isCompleted ?? false,
      end_reason: endReason,
    }
  }

  async function submitPayload(payload: LearningSessionRequest): Promise<boolean> {
    try {
      isSubmitting.value = true
      await saveLearningSession(payload)
      return true
    } catch (error) {
      console.warn('[LearningSession] 会话上报失败，将加入重试队列', error)
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  async function finishSession(endReason: LearningSessionEndReason): Promise<void> {
    const payload = buildPayload(endReason)
    finalized = true
    stopIdleTimer()
    sessionId = null
    activeResource = null
    startedAt = null
    startPositionSeconds = null
    lastMediaTickAt = null
    if (!payload) return

    const submitted = navigator.onLine ? await submitPayload(payload) : false
    if (!submitted) {
      enqueue(payload)
    }
  }

  function onBeforeUnloadSession(): void {
    const payload = buildPayload('beacon')
    finalized = true
    stopIdleTimer()
    sessionId = null
    activeResource = null
    startedAt = null
    startPositionSeconds = null
    lastMediaTickAt = null
    if (payload) {
      enqueue(payload)
    }
  }

  async function flushSessionQueue(): Promise<void> {
    persistQueue()
    const retained: QueuedSessionItem[] = []
    for (const item of queue.value) {
      const ok = await submitPayload(item.payload)
      if (!ok) {
        retained.push(item)
      }
    }
    queue.value = retained
    saveQueue(queue.value)
  }

  onUnmounted(() => {
    stopIdleTimer()
  })

  return {
    isSubmitting,
    queue,
    startSession,
    updateSessionContext,
    recordMediaPlay,
    recordMediaPause,
    recordMediaPlayingDelta,
    recordActivity,
    finishSession,
    flushSessionQueue,
    onBeforeUnloadSession,
  }
}
