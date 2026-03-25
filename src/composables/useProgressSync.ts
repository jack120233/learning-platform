import { ref, onUnmounted } from 'vue'
import { useLearnStore } from '@/store/learn'
import { saveProgress, type SaveProgressRequest } from '@/api/learning'

interface UseProgressSyncOptions {
  /** 定时上报间隔（毫秒），默认 30000 */
  intervalMs?: number
  /** 最小变化阈值（秒），默认 5 */
  minDeltaSeconds?: number
}

interface OfflineQueueItem extends SaveProgressRequest {}

/**
 * 进度同步 Composable
 * 实现三层防抖架构：
 * Layer 1: 播放器 timeupdate 回调（高频，仅更新内存）
 * Layer 2: 定时上报（30s 一次）
 * Layer 3: 立即保存（暂停、切换、离开等关键时刻）
 */
export function useProgressSync(options: UseProgressSyncOptions = {}) {
  const { intervalMs = 30000, minDeltaSeconds = 5 } = options

  const learnStore = useLearnStore()

  // 定时器
  let syncTimer: ReturnType<typeof setInterval> | null = null

  // 上次上报的播放位置
  const lastReportedTime = ref<number>(0)

  // 是否正在同步
  const isSyncing = ref<boolean>(false)

  // 离线队列
  const offlineQueue = ref<OfflineQueueItem[]>([])

  /**
   * Layer 1: 播放器 timeupdate 回调（高频，仅更新内存）
   */
  function onTimeUpdate(currentTime: number, totalTime: number): void {
    learnStore.updatePlayProgress(currentTime, totalTime)
  }

  /**
   * 执行同步
   */
  async function doSync(force: boolean = false): Promise<void> {
    // 非强制模式下，正在同步则跳过
    if (isSyncing.value && !force) return

    const active = learnStore.activeResource
    if (!active.resourceId) return

    isSyncing.value = true

    try {
      const request: SaveProgressRequest = {
        section_id: active.sectionId!,
        resource_id: active.resourceId,
        current_time: Math.floor(active.currentTime),
        total_time: Math.floor(active.totalTime),
        is_completed: active.isCompleted,
      }

      await saveProgress(request)
      lastReportedTime.value = active.currentTime

      // 更新本地进度缓存
      learnStore.updateProgressCache(active.resourceId, {
        currentTime: active.currentTime,
        totalTime: active.totalTime,
        isCompleted: active.isCompleted,
      })
    } catch (error) {
      // 如果是网络错误，加入离线队列
      if (!navigator.onLine) {
        offlineQueue.value.push({
          section_id: active.sectionId!,
          resource_id: active.resourceId,
          current_time: Math.floor(active.currentTime),
          total_time: Math.floor(active.totalTime),
          is_completed: active.isCompleted,
        })
      }
      console.warn('[ProgressSync] 进度保存失败，将在下次重试', error)
    } finally {
      isSyncing.value = false
    }
  }

  /**
   * Layer 2: 定时上报（30s 一次）
   */
  function startPeriodicSync(): void {
    if (syncTimer) return

    syncTimer = setInterval(async () => {
      const active = learnStore.activeResource
      if (!active.resourceId || active.playState !== 'playing') return

      const delta = Math.abs(active.currentTime - lastReportedTime.value)
      if (delta < minDeltaSeconds) return

      await doSync(false)
    }, intervalMs)
  }

  /**
   * 停止定时上报
   */
  function stopPeriodicSync(): void {
    if (syncTimer) {
      clearInterval(syncTimer)
      syncTimer = null
    }
  }

  /**
   * Layer 3: 立即保存
   */
  async function immediateSync(): Promise<void> {
    await doSync(true)
  }

  /**
   * beforeunload 降级：使用 sendBeacon 确保页面关闭时数据不丢失
   */
  function onBeforeUnload(): void {
    const active = learnStore.activeResource
    if (!active.resourceId) return

    const payload = JSON.stringify({
      section_id: active.sectionId,
      resource_id: active.resourceId,
      current_time: Math.floor(active.currentTime),
      total_time: Math.floor(active.totalTime),
      is_completed: active.isCompleted,
    })

    navigator.sendBeacon(
      '/api/v1/learning/progress',
      new Blob([payload], { type: 'application/json' })
    )
  }

  /**
   * 网络恢复：刷新离线队列
   */
  async function flushOfflineQueue(): Promise<void> {
    while (offlineQueue.value.length > 0) {
      const request = offlineQueue.value.shift()!
      try {
        await saveProgress(request)
      } catch {
        // 失败则放回队列头部
        offlineQueue.value.unshift(request)
        break
      }
    }
  }

  /**
   * 处理网络断开
   */
  function handleOffline(): void {
    stopPeriodicSync()
  }

  /**
   * 处理网络恢复
   */
  async function handleOnline(): Promise<void> {
    await flushOfflineQueue()
    startPeriodicSync()
  }

  // 组件卸载时清理
  onUnmounted(() => {
    stopPeriodicSync()
  })

  return {
    // 状态
    isSyncing,
    offlineQueue,

    // 方法
    onTimeUpdate,
    startPeriodicSync,
    stopPeriodicSync,
    immediateSync,
    onBeforeUnload,
    flushOfflineQueue,
    handleOffline,
    handleOnline,
  }
}