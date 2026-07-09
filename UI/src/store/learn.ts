import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CourseChapter, ContinueLearningInfo, CourseResource } from '@/api/learning'
import { resolveCourseCoverUrl } from '@/utils/course'

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

interface ResourceLocator {
  chapterId: number
  sectionId: number | null
  resource: CourseResource
}

function getSectionId(section: CourseChapter['sections'][number]): number {
  return section.section_id ?? 0
}

function hasContinueProgress(info: ContinueLearningInfo | null): info is ContinueLearningInfo {
  if (!info) return false

  // 后端在没有学习进度时也会返回一个字段齐全的空对象，这里收窄为“存在真实上次位置/进度”。
  return (
    info.last_resource_id !== null ||
    info.resource_id !== null ||
    info.last_section_id !== null ||
    info.section_id !== null ||
    info.chapter_id !== null ||
    info.position > 0 ||
    info.current_time > 0 ||
    info.last_learn_at !== null
  )
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
    currentCourseCover.value = resolveCourseCoverUrl(cover)
    currentCourseChapters.value = chapters
    courseStatus.value = status
  }

  /**
   * 设置继续学习信息
   */
  function setContinueInfo(info: ContinueLearningInfo | null) {
    const normalizedInfo = hasContinueProgress(info) ? info : null
    continueInfo.value = normalizedInfo
    hasLearningRecord.value = normalizedInfo !== null
  }

  /**
   * 切换到指定资源
   */
  function setActiveResource(data: {
    resourceId: number
    resourceType: 'video' | 'audio' | 'document' | 'image'
    sectionId: number | null
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
  function getNextResource(): { sectionId: number | null; chapterId: number; resourceId: number } | null {
    const orderedResources = flattenCourseResources()
    const currentIndex = orderedResources.findIndex(item => item.resource.resource_id === activeResource.value.resourceId)
    if (currentIndex < 0 || currentIndex + 1 >= orderedResources.length) return null

    const next = orderedResources[currentIndex + 1]
    return {
      sectionId: next.sectionId,
      chapterId: next.chapterId,
      resourceId: next.resource.resource_id,
    }
  }

  /**
   * 获取上一个资源
   */
  function getPrevResource(): { sectionId: number | null; chapterId: number; resourceId: number } | null {
    const orderedResources = flattenCourseResources()
    const currentIndex = orderedResources.findIndex(item => item.resource.resource_id === activeResource.value.resourceId)
    if (currentIndex <= 0) return null

    const prev = orderedResources[currentIndex - 1]
    return {
      sectionId: prev.sectionId,
      chapterId: prev.chapterId,
      resourceId: prev.resource.resource_id,
    }
  }

  function flattenCourseResources(): ResourceLocator[] {
    const resources: ResourceLocator[] = []
    for (const chapter of currentCourseChapters.value) {
      const chapterId = chapter.chapter_id ?? 0
      for (const resource of chapter.resources ?? []) {
        resources.push({
          chapterId,
          sectionId: null,
          resource,
        })
      }
      for (const section of chapter.sections) {
        const sectionId = getSectionId(section)
        for (const resource of section.resources ?? []) {
          resources.push({
            chapterId,
            sectionId,
            resource,
          })
        }
      }
    }
    return resources
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
    flattenCourseResources,
    getNextResource,
    getPrevResource,
    cleanup,
  }
})
