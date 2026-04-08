import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CourseChapter, ContinueLearningInfo } from '@/api/learning'

// ==================== 类型定义 ====================

/** 资源加载状态 */
export type ResourceLoadState = 'idle' | 'loading' | 'ready' | 'error'

/** 媒体播放状态 */
export type MediaPlayState = 'stopped' | 'playing' | 'paused' | 'completed'

/** 当前活动资源的完整状态 */
export interface ActiveResourceState {
  resourceId: number | null
  resourceType: 'video' | 'audio' | 'document' | 'image' | null
  sectionId: number | null
  chapterId: number | null

  // 加载状态
  loadState: ResourceLoadState

  // 播放状态（视频/音频专用）
  playState: MediaPlayState
  currentTime: number
  totalTime: number
  playbackRate: number
  volume: number
  isMuted: boolean

  // 进度
  progressPercent: number
  isCompleted: boolean

  // 播放地址
  fileUrl: string
  errorMessage: string
}

/** 进度缓存项 */
interface ProgressCacheItem {
  currentTime: number
  totalTime: number
  isCompleted: boolean
  lastSyncedAt: number
}

function getSectionId(section: CourseChapter['sections'][number]): number {
  return section.section_id ?? 0
}

// ==================== Store 定义 ====================

export const useLearnStore = defineStore('learn', () => {
  // ---- 课程上下文 ----
  const currentCourseId = ref<number | null>(null)
  const currentCourseTitle = ref<string>('')
  const currentCourseCover = ref<string>('')
  const currentCourseChapters = ref<CourseChapter[]>([])
  const courseStatus = ref<'published' | 'archived' | 'draft' | null>(null)

  // ---- 当前活动资源 ----
  const activeResource = ref<ActiveResourceState>({
    resourceId: null,
    resourceType: null,
    sectionId: null,
    chapterId: null,
    loadState: 'idle',
    playState: 'stopped',
    currentTime: 0,
    totalTime: 0,
    playbackRate: 1,
    volume: 1,
    isMuted: false,
    progressPercent: 0,
    isCompleted: false,
    fileUrl: '',
    errorMessage: '',
  })

  // ---- 继续学习信息 ----
  const continueInfo = ref<ContinueLearningInfo | null>(null)
  const hasLearningRecord = ref<boolean>(false)

  // ---- 进度缓存 ----
  const progressCache = ref<Map<number, ProgressCacheItem>>(new Map())

  // ---- 计算属性 ----
  const hasActiveResource = computed(() => activeResource.value.resourceId !== null)

  // ---- Actions ----

  /**
   * 初始化课程上下文
   */
  function initCourseContext(courseId: number, title: string, cover: string, chapters: CourseChapter[], status: 'published' | 'archived' | 'draft' = 'published') {
    currentCourseId.value = courseId
    currentCourseTitle.value = title
    currentCourseCover.value = cover
    currentCourseChapters.value = chapters
    courseStatus.value = status
  }

  /**
   * 设置继续学习信息
   */
  function setContinueInfo(info: ContinueLearningInfo | null) {
    continueInfo.value = info
    hasLearningRecord.value = info !== null
  }

  /**
   * 切换到指定资源
   */
  function setActiveResource(data: {
    resourceId: number
    resourceType: 'video' | 'audio' | 'document' | 'image'
    sectionId: number
    chapterId: number
    fileUrl: string
    totalTime?: number
  }) {
    activeResource.value = {
      resourceId: data.resourceId,
      resourceType: data.resourceType,
      sectionId: data.sectionId,
      chapterId: data.chapterId,
      loadState: 'ready',
      playState: 'stopped',
      currentTime: 0,
      totalTime: data.totalTime || 0,
      playbackRate: activeResource.value.playbackRate,
      volume: activeResource.value.volume,
      isMuted: activeResource.value.isMuted,
      progressPercent: 0,
      isCompleted: false,
      fileUrl: data.fileUrl,
      errorMessage: '',
    }
  }

  /**
   * 设置资源加载状态
   */
  function setResourceLoadState(state: ResourceLoadState, errorMessage?: string) {
    activeResource.value.loadState = state
    if (errorMessage) {
      activeResource.value.errorMessage = errorMessage
    }
  }

  /**
   * 更新播放进度
   */
  function updatePlayProgress(currentTime: number, totalTime?: number) {
    activeResource.value.currentTime = currentTime
    if (totalTime !== undefined) {
      activeResource.value.totalTime = totalTime
    }
    if (activeResource.value.totalTime > 0) {
      activeResource.value.progressPercent = Math.round((currentTime / activeResource.value.totalTime) * 100)
    }
  }

  /**
   * 设置播放状态
   */
  function setPlayState(state: MediaPlayState) {
    activeResource.value.playState = state
  }

  /**
   * 恢复历史进度
   */
  function restoreProgress(currentTime: number, isCompleted: boolean) {
    activeResource.value.currentTime = currentTime
    activeResource.value.isCompleted = isCompleted
    if (activeResource.value.totalTime > 0) {
      activeResource.value.progressPercent = Math.round((currentTime / activeResource.value.totalTime) * 100)
    }
  }

  /**
   * 标记资源完成
   */
  function markResourceCompleted() {
    activeResource.value.isCompleted = true
    activeResource.value.progressPercent = 100
    activeResource.value.playState = 'completed'
    if (activeResource.value.resourceId) {
      progressCache.value.set(activeResource.value.resourceId, {
        currentTime: activeResource.value.currentTime,
        totalTime: activeResource.value.totalTime,
        isCompleted: true,
        lastSyncedAt: Date.now(),
      })
    }
  }

  /**
   * 更新进度缓存
   */
  function updateProgressCache(resourceId: number, data: Partial<ProgressCacheItem>) {
    const existing = progressCache.value.get(resourceId) || {
      currentTime: 0,
      totalTime: 0,
      isCompleted: false,
      lastSyncedAt: 0,
    }
    progressCache.value.set(resourceId, {
      ...existing,
      ...data,
      lastSyncedAt: Date.now(),
    })
  }

  /**
   * 获取下一个资源
   */
  function getNextResource(): { sectionId: number; resourceId: number } | null {
    const chapters = currentCourseChapters.value
    const current = activeResource.value
    if (!current.resourceId) return null

    let found = false

    for (const chapter of chapters) {
      for (const section of chapter.sections) {
        for (const resource of section.resources ?? []) {
          if (found) {
            return { sectionId: getSectionId(section), resourceId: resource.resource_id }
          }
          if (resource.resource_id === current.resourceId) {
            found = true
          }
        }
      }
    }

    return null
  }

  /**
   * 获取上一个资源
   */
  function getPrevResource(): { sectionId: number; resourceId: number } | null {
    const chapters = currentCourseChapters.value
    const current = activeResource.value
    if (!current.resourceId) return null

    let prev: { sectionId: number; resourceId: number } | null = null

    for (const chapter of chapters) {
      for (const section of chapter.sections) {
        for (const resource of section.resources ?? []) {
          if (resource.resource_id === current.resourceId) {
            return prev
          }
          prev = { sectionId: getSectionId(section), resourceId: resource.resource_id }
        }
      }
    }

    return null
  }

  /**
   * 清理学习状态
   */
  function cleanup() {
    currentCourseId.value = null
    currentCourseTitle.value = ''
    currentCourseCover.value = ''
    currentCourseChapters.value = []
    courseStatus.value = null
    activeResource.value = {
      resourceId: null,
      resourceType: null,
      sectionId: null,
      chapterId: null,
      loadState: 'idle',
      playState: 'stopped',
      currentTime: 0,
      totalTime: 0,
      playbackRate: 1,
      volume: 1,
      isMuted: false,
      progressPercent: 0,
      isCompleted: false,
      fileUrl: '',
      errorMessage: '',
    }
    continueInfo.value = null
    hasLearningRecord.value = false
    progressCache.value.clear()
  }

  return {
    // 状态
    currentCourseId,
    currentCourseTitle,
    currentCourseCover,
    currentCourseChapters,
    courseStatus,
    activeResource,
    continueInfo,
    hasLearningRecord,
    progressCache,

    // 计算属性
    hasActiveResource,

    // Actions
    initCourseContext,
    setContinueInfo,
    setActiveResource,
    setResourceLoadState,
    updatePlayProgress,
    setPlayState,
    restoreProgress,
    markResourceCompleted,
    updateProgressCache,
    getNextResource,
    getPrevResource,
    cleanup,
  }
})
