<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, defineAsyncComponent, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import '@vue-office/docx/lib/index.css'
import {
  ArrowLeft,
  FullScreen,
  Aim,
  Fold,
  Expand,
  VideoPlay,
  Headset,
  Document,
  Picture,
  CircleCheckFilled,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { useLearnStore } from '@/store/learn'
import {
  fetchCourseDetail,
  fetchContinueInfo,
  startLearning,
  getResourcePlayUrl,
  getProgress,
  type CourseChapter,
  type CourseResource,
  type CourseSection,
  type SectionResource,
} from '@/api/learning'
import { BREAKPOINT_VALUES, useBreakpoint } from '@/composables/useBreakpoint'
import { useLearningSession } from '@/composables/useLearningSession'
import { useProgressSync } from '@/composables/useProgressSync'
import { formatDuration } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const learnStore = useLearnStore()
const { width } = useBreakpoint()
const VueOfficeDocx = defineAsyncComponent(() => import('@vue-office/docx'))
const VueOfficePdf = defineAsyncComponent(() => import('@vue-office/pdf'))
const VueOfficePptx = defineAsyncComponent(() => import('@vue-office/pptx'))

// 进度同步
const progressSync = useProgressSync({
  intervalMs: 30000,
  minDeltaSeconds: 5,
})
const learningSession = useLearningSession()

// 侧边栏
const sidebarTab = ref<'current-task' | 'directory'>('current-task')
const isSidebarCollapsed = ref(false)
const chapterExpandMap = ref<Record<number, boolean>>({})

// 全屏
const isFullscreen = ref(false)

// 自动跳转
const showAutoNextNotice = ref(false)
const autoNextCountdown = ref(3)
let autoNextTimer: ReturnType<typeof setInterval> | null = null

// 视频播放器引用
const videoRef = ref<HTMLVideoElement | null>(null)
const audioRef = ref<HTMLAudioElement | null>(null)
const documentTextContent = ref('')
const documentRenderMode = ref<'text' | 'docx' | 'pdf' | 'pptx' | 'download'>('download')

// 计算属性
const courseId = computed(() => Number(route.params.courseId))
const targetSectionId = computed(() => route.query.sectionId ? Number(route.query.sectionId) : null)
const targetChapterId = computed(() => route.query.chapterId ? Number(route.query.chapterId) : null)
const targetResourceId = computed(() => route.query.resourceId ? Number(route.query.resourceId) : null)

const activeResource = computed(() => learnStore.activeResource)
const hasActiveResource = computed(() => learnStore.hasActiveResource)
const courseChapters = computed(() => learnStore.currentCourseChapters)
const activeDocumentExtension = computed(() => getDocumentExtension(activeResource.value.fileUrl))
const activeDocumentFileName = computed(() => getActiveResourceFileName())
const isOverlaySidebar = computed(() => width.value <= BREAKPOINT_VALUES.lg)

// 资源类型图标映射
const resourceIconMap: Record<string, typeof VideoPlay> = {
  video: VideoPlay,
  audio: Headset,
  document: Document,
  image: Picture,
}

// 构建目录树（带 UI 状态）
interface SectionTreeNode {
  chapter_id: number
  section_id: number
  title: string
  resources: CourseResource[]
  isActive: boolean
}

interface ChapterTreeNode {
  chapter_id: number
  title: string
  isExpanded: boolean
  resources: CourseResource[]
  hasActiveChapterResource: boolean
  sections: SectionTreeNode[]
}

function getChapterId(chapter: CourseChapter): number {
  return chapter.chapter_id ?? 0
}

function getSectionId(section: CourseSection): number {
  return section.section_id ?? 0
}

function getSectionResources(section: CourseSection): SectionResource[] {
  return section.resources ?? []
}

function getChapterResources(chapter: CourseChapter): CourseResource[] {
  return chapter.resources ?? []
}

function getTaskResources(): CourseResource[] {
  if (activeResource.value.sectionId != null) {
    for (const chapter of courseChapters.value) {
      const section = chapter.sections.find(s => getSectionId(s) === activeResource.value.sectionId)
      if (section) {
        return getSectionResources(section)
      }
    }
    return []
  }

  if (activeResource.value.chapterId != null) {
    const chapter = courseChapters.value.find(item => getChapterId(item) === activeResource.value.chapterId)
    return chapter ? getChapterResources(chapter) : []
  }

  return []
}

function findResourceLocation(resourceId: number): { chapterId: number; sectionId: number | null; resource: CourseResource } | null {
  for (const chapter of courseChapters.value) {
    const chapterId = getChapterId(chapter)
    const chapterResource = getChapterResources(chapter).find(item => item.resource_id === resourceId)
    if (chapterResource) {
      return { chapterId, sectionId: null, resource: chapterResource }
    }

    for (const section of chapter.sections) {
      const sectionResource = getSectionResources(section).find(item => item.resource_id === resourceId)
      if (sectionResource) {
        return { chapterId, sectionId: getSectionId(section), resource: sectionResource }
      }
    }
  }
  return null
}

function getDocumentExtension(fileUrl: string): string {
  if (!fileUrl) return ''

  try {
    const pathname = new URL(fileUrl, window.location.origin).pathname
    const fileName = pathname.split('/').pop() || ''
    const ext = fileName.includes('.') ? fileName.split('.').pop() : ''
    return (ext || '').toLowerCase()
  } catch {
    const sanitized = fileUrl.split('?')[0]
    const ext = sanitized.includes('.') ? sanitized.split('.').pop() : ''
    return (ext || '').toLowerCase()
  }
}

function getActiveResourceFileName(): string {
  const resourceId = activeResource.value.resourceId
  if (!resourceId) return ''

  for (const chapter of courseChapters.value) {
    const chapterResource = getChapterResources(chapter).find(item => item.resource_id === resourceId)
    if (chapterResource) {
      return chapterResource.file_name
    }
    for (const section of chapter.sections) {
      const resource = getSectionResources(section).find(item => item.resource_id === resourceId)
      if (resource) {
        return resource.file_name
      }
    }
  }

  try {
    const pathname = new URL(activeResource.value.fileUrl, window.location.origin).pathname
    return decodeURIComponent(pathname.split('/').pop() || '')
  } catch {
    return activeResource.value.fileUrl.split('/').pop() || ''
  }
}

function handleDocumentDownload() {
  if (!activeResource.value.fileUrl) return

  const link = document.createElement('a')
  link.href = activeResource.value.fileUrl
  link.download = activeDocumentFileName.value || `resource.${activeDocumentExtension.value || 'file'}`
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const chapterTree = computed<ChapterTreeNode[]>(() => {
  return courseChapters.value.map(chapter => ({
    chapter_id: getChapterId(chapter),
    title: chapter.title,
    isExpanded: chapterExpandMap.value[getChapterId(chapter)] ?? false,
    resources: getChapterResources(chapter),
    hasActiveChapterResource:
      activeResource.value.chapterId === getChapterId(chapter) && activeResource.value.sectionId == null,
    sections: chapter.sections.map(section => ({
      chapter_id: getChapterId(chapter),
      section_id: getSectionId(section),
      title: section.title,
      resources: getSectionResources(section),
      isActive: activeResource.value.sectionId === getSectionId(section),
    })),
  }))
})

// 当前小节的资源列表（用于"当前任务"Tab）
const currentTaskResources = computed(() => {
  return getTaskResources().map(r => {
    const cache = learnStore.progressCache.get(r.resource_id)
    const isActive = r.resource_id === activeResource.value.resourceId
    const liveProgressPercent = activeResource.value.totalTime > 0
      ? Math.round((activeResource.value.currentTime / activeResource.value.totalTime) * 100)
      : 0
    const progressPercent = isActive
      ? liveProgressPercent
      : cache && cache.totalTime > 0
        ? Math.round((cache.currentTime / cache.totalTime) * 100)
        : 0
    return {
      ...r,
      isActive,
      isCompleted: cache?.isCompleted ?? false,
      progressPercent,
    }
  })
})

// 初始化课程
async function initCourse() {
  // 如果 Store 中已有数据且匹配当前课程 ID，直接使用
  if (learnStore.currentCourseId === courseId.value && courseChapters.value.length > 0) {
    return
  }

  try {
    const data = await fetchCourseDetail(courseId.value)

    if (data.status !== 'published') {
      ElMessage.error('该课程已下架或删除，无法继续学习')
      router.push('/')
      return
    }

    learnStore.initCourseContext(
      data.course_id || data.id || courseId.value,
      data.title,
      data.cover_url,
      data.chapters || [],
      data.status
    )

    // 初始化章节展开状态
    const chapters = data.chapters || []
    if (chapters.length > 0) {
      chapterExpandMap.value = { [getChapterId(chapters[0])]: true }
    }
  } catch {
    ElMessage.error('课程加载失败')
    router.push('/')
  }
}

// 确定初始资源
async function determineInitialResource(): Promise<{ sectionId: number | null; chapterId: number; resourceId: number } | null> {
  // 优先级 1：路由 query 参数
  if (targetResourceId.value) {
    const located = findResourceLocation(targetResourceId.value)
    if (located) {
      return {
        sectionId: located.sectionId,
        chapterId: targetChapterId.value ?? located.chapterId,
        resourceId: targetResourceId.value,
      }
    }
    if (targetChapterId.value) {
      return { sectionId: null, chapterId: targetChapterId.value, resourceId: targetResourceId.value }
    }
    if (targetSectionId.value) {
      return { sectionId: targetSectionId.value, chapterId: 0, resourceId: targetResourceId.value }
    }
  }

  // 优先级 2：继续学习信息
  try {
    const info = await fetchContinueInfo(courseId.value)
    learnStore.setContinueInfo(info)
    if (info.last_resource_id != null) {
      const located = findResourceLocation(info.last_resource_id)
      return {
        sectionId: located?.sectionId ?? info.last_section_id ?? info.section_id ?? null,
        chapterId: located?.chapterId ?? info.chapter_id ?? 0,
        resourceId: info.last_resource_id,
      }
    }
  } catch {
    learnStore.setContinueInfo(null)
  }

  // 优先级 3：课程第一个资源，优先小节资源，其次章节资源
  const chapters = learnStore.currentCourseChapters
  const firstChapter = chapters[0]
  const firstChapterResource = firstChapter ? getChapterResources(firstChapter)[0] : null
  const firstSection = firstChapter?.sections[0]
  const firstResource = firstSection ? getSectionResources(firstSection)[0] : null

  if (firstChapter && firstSection && firstResource) {
    return {
      sectionId: getSectionId(firstSection),
      chapterId: getChapterId(firstChapter),
      resourceId: firstResource.resource_id,
    }
  }

  if (firstChapter && firstChapterResource) {
    return {
      sectionId: null,
      chapterId: getChapterId(firstChapter),
      resourceId: firstChapterResource.resource_id,
    }
  }

  return null
}

// 切换资源
let switchAbortController: AbortController | null = null
let currentSwitchId = 0

async function switchResource(sectionId: number | null, resourceId: number, chapterIdArg?: number): Promise<void> {
  // 取消上一次未完成的切换
  if (switchAbortController) {
    switchAbortController.abort()
  }
  switchAbortController = new AbortController()
  const thisSwitchId = ++currentSwitchId

  // 保存当前资源进度和学习会话
  await progressSync.immediateSync()
  await learningSession.finishSession('switch_resource')

  // 重置状态
  learnStore.setResourceLoadState('loading')
  documentTextContent.value = ''
  documentRenderMode.value = 'download'

  // 找到章节 ID
  let chapterId = chapterIdArg ?? 0
  if (!chapterId) {
    const located = findResourceLocation(resourceId)
    chapterId = located?.chapterId ?? 0
  }

  try {
    // 并行加载
    const [playInfoRes, progressRes] = await Promise.allSettled([
      getResourcePlayUrl(resourceId),
      getProgress(sectionId, resourceId),
    ])

    // 竞态校验
    if (currentSwitchId !== thisSwitchId) {
      return
    }

    // 处理播放地址
    if (playInfoRes.status === 'fulfilled') {
      const playInfo = playInfoRes.value
      learnStore.setActiveResource({
        resourceId: playInfo.resource_id,
        resourceType: playInfo.resource_type,
        sectionId,
        chapterId,
        fileUrl: playInfo.file_url,
        totalTime: playInfo.duration,
      })
    } else {
      learnStore.setResourceLoadState('error', '资源加载失败')
      return
    }

    // 恢复进度
    if (progressRes.status === 'fulfilled' && progressRes.value) {
      learnStore.restoreProgress(progressRes.value.current_time, progressRes.value.is_completed)
    }

    if (learnStore.activeResource.resourceType) {
      learningSession.startSession({
        resourceId: learnStore.activeResource.resourceId!,
        resourceType: learnStore.activeResource.resourceType,
        currentTime: learnStore.activeResource.currentTime,
        totalTime: learnStore.activeResource.totalTime,
        isCompleted: learnStore.activeResource.isCompleted,
      })
    }

    if (learnStore.activeResource.resourceType === 'document') {
      const extension = getDocumentExtension(learnStore.activeResource.fileUrl)

      if (['md', 'markdown', 'txt', 'json'].includes(extension)) {
        try {
          const response = await fetch(learnStore.activeResource.fileUrl)
          documentTextContent.value = await response.text()
          documentRenderMode.value = 'text'
        } catch {
          learnStore.setResourceLoadState('error', '文档加载失败，请稍后重试')
          return
        }
      } else if (extension === 'pdf') {
        documentRenderMode.value = 'pdf'
      } else if (extension === 'docx') {
        documentRenderMode.value = 'docx'
      } else if (extension === 'pptx') {
        documentRenderMode.value = 'pptx'
      } else {
        documentRenderMode.value = 'download'
      }
    }

    // 自动标记非音视频资源为已完成
    if (learnStore.activeResource.resourceType && ['document', 'image'].includes(learnStore.activeResource.resourceType)) {
      learnStore.markResourceCompleted()
      learningSession.updateSessionContext({ isCompleted: true })
      progressSync.immediateSync()
    }

    // 自动播放视频/音频
    if (learnStore.activeResource.resourceType === 'video' || learnStore.activeResource.resourceType === 'audio') {
      await nextTick()
      const mediaRef = learnStore.activeResource.resourceType === 'video' ? videoRef.value : audioRef.value
      if (mediaRef) {
        mediaRef.currentTime = learnStore.activeResource.currentTime
        mediaRef.play().catch(() => {
          // 自动播放被阻止，需要用户手动点击
        })
        learnStore.setPlayState('playing')
      }
    }

  } catch (error) {
    if ((error as Error).name === 'AbortError') return
    learnStore.setResourceLoadState('error', '网络异常，请检查网络后重试')
  }
}

// 播放器事件处理
function handleVideoTimeUpdate() {
  const mediaRef = videoRef.value || audioRef.value
  if (!mediaRef) return
  learningSession.recordMediaPlayingDelta()
  progressSync.onTimeUpdate(mediaRef.currentTime, mediaRef.duration)
  learningSession.updateSessionContext({
    currentTime: mediaRef.currentTime,
    totalTime: mediaRef.duration,
    isCompleted: learnStore.activeResource.isCompleted,
  })
}

function handleVideoPause() {
  learnStore.setPlayState('paused')
  learningSession.recordMediaPause()
  progressSync.immediateSync()
}

function handleVideoPlay() {
  learnStore.setPlayState('playing')
  learningSession.recordMediaPlay()
}

async function handleVideoEnded() {
  const mediaRef = videoRef.value || audioRef.value
  if (mediaRef) {
    progressSync.onTimeUpdate(mediaRef.currentTime, mediaRef.duration)
  }
  learnStore.markResourceCompleted()
  learningSession.updateSessionContext({
    currentTime: mediaRef?.currentTime ?? learnStore.activeResource.currentTime,
    totalTime: mediaRef?.duration ?? learnStore.activeResource.totalTime,
    isCompleted: true,
  })
  await progressSync.immediateSync()
  await learningSession.finishSession('completed')
  handleAutoNext()
}

function handleVideoError() {
  learnStore.setResourceLoadState('error', '视频加载失败，请检查网络或稍后重试')
}

function handleVideoLoadedMetadata() {
  if (!videoRef.value) return
  // 恢复历史进度
  if (learnStore.activeResource.currentTime > 0) {
    videoRef.value.currentTime = learnStore.activeResource.currentTime
  }
}

// 自动跳转下一资源
function handleAutoNext() {
  const next = learnStore.getNextResource()
  if (!next) {
    ElMessage.success('恭喜您已完成全部课程内容')
    return
  }

  showAutoNextNotice.value = true
  autoNextCountdown.value = 3

  autoNextTimer = setInterval(() => {
    autoNextCountdown.value--
    if (autoNextCountdown.value <= 0) {
      cancelAutoNext()
      switchResource(next.sectionId, next.resourceId, next.chapterId)
    }
  }, 1000)
}

function cancelAutoNext() {
  if (autoNextTimer) {
    clearInterval(autoNextTimer)
    autoNextTimer = null
  }
  showAutoNextNotice.value = false
}

// 侧边栏交互
function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

function closeSidebar() {
  isSidebarCollapsed.value = true
}

function toggleChapter(chapterId: number) {
  chapterExpandMap.value[chapterId] = !chapterExpandMap.value[chapterId]
}

function handleResourceClick(sectionId: number | null, resourceId: number, chapterId?: number) {
  switchResource(sectionId, resourceId, chapterId)
  if (isOverlaySidebar.value) {
    closeSidebar()
  }
}

function handleSectionClick(section: any) {
  if (section.resources && section.resources.length > 0) {
    switchResource(section.section_id, section.resources[0].resource_id, section.chapter_id)
    if (isOverlaySidebar.value) {
      closeSidebar()
    }
  }
}

function handleChapterResourceClick(chapterId: number, resourceId: number) {
  switchResource(null, resourceId, chapterId)
  if (isOverlaySidebar.value) {
    closeSidebar()
  }
}

// 全屏切换
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

// 返回课程详情
function goBack() {
  router.push(`/courses/${courseId.value}`)
}

// 键盘快捷键
function handleKeydown(e: KeyboardEvent) {
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) return

  const mediaRef = videoRef.value || audioRef.value

  learningSession.recordActivity()

  switch (e.code) {
    case 'Space':
      e.preventDefault()
      if (mediaRef) {
        mediaRef.paused ? mediaRef.play() : mediaRef.pause()
      }
      break
    case 'ArrowLeft':
      e.preventDefault()
      if (mediaRef) {
        mediaRef.currentTime = Math.max(0, mediaRef.currentTime - 5)
      }
      break
    case 'ArrowRight':
      e.preventDefault()
      if (mediaRef) {
        mediaRef.currentTime = Math.min(mediaRef.duration, mediaRef.currentTime + 5)
      }
      break
    case 'KeyF':
      e.preventDefault()
      toggleFullscreen()
      break
    case 'KeyM':
      e.preventDefault()
      if (mediaRef) {
        mediaRef.muted = !mediaRef.muted
      }
      break
    case 'Escape':
      if (isOverlaySidebar.value && !isSidebarCollapsed.value) {
        e.preventDefault()
        closeSidebar()
      }
      break
  }
}

// 网络状态处理
function handleOnline() {
  ElMessage.success('网络已恢复')
  progressSync.handleOnline()
  learningSession.flushSessionQueue()
}

function handleOffline() {
  ElMessage.warning('网络已断开，请检查网络连接')
  progressSync.handleOffline()
}

// 页面离开处理
onBeforeRouteLeave(async (_to, _from, next) => {
  await progressSync.immediateSync()
  await learningSession.finishSession('leave_page')
  progressSync.stopPeriodicSync()
  learnStore.cleanup()
  window.removeEventListener('beforeunload', progressSync.onBeforeUnload)
  window.removeEventListener('beforeunload', learningSession.onBeforeUnloadSession)
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('mousemove', learningSession.recordActivity)
  document.removeEventListener('scroll', learningSession.recordActivity, true)
  document.removeEventListener('touchstart', learningSession.recordActivity)
  next()
})

watch(isOverlaySidebar, (overlay, previous) => {
  if (overlay && !previous) {
    isSidebarCollapsed.value = true
  }
})

// 初始化
onMounted(async () => {
  if (isOverlaySidebar.value) {
    isSidebarCollapsed.value = true
  }

  // 检查登录状态
  if (!userStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

  // 加载课程数据
  await initCourse()

  // 确定初始资源
  const initial = await determineInitialResource()
  if (!initial) {
    ElMessage.error('该课程暂无学习内容')
    router.push('/')
    return
  }

  // 首次学习需要调用开始学习接口
  if (!learnStore.hasLearningRecord) {
    try {
      await startLearning(courseId.value)
    } catch {
      // 忽略错误，继续
    }
  }

  // 加载初始资源
  await switchResource(initial.sectionId, initial.resourceId)

  // 启动进度上报定时器
  progressSync.startPeriodicSync()
  learningSession.flushSessionQueue()

  // 注册事件监听
  window.addEventListener('beforeunload', progressSync.onBeforeUnload)
  window.addEventListener('beforeunload', learningSession.onBeforeUnloadSession)
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('mousemove', learningSession.recordActivity)
  document.addEventListener('scroll', learningSession.recordActivity, true)
  document.addEventListener('touchstart', learningSession.recordActivity)

  // 监听全屏变化
  document.addEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement
  })
})

// 清理
onUnmounted(() => {
  learningSession.finishSession('leave_page')
  progressSync.stopPeriodicSync()
  window.removeEventListener('beforeunload', progressSync.onBeforeUnload)
  window.removeEventListener('beforeunload', learningSession.onBeforeUnloadSession)
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('mousemove', learningSession.recordActivity)
  document.removeEventListener('scroll', learningSession.recordActivity, true)
  document.removeEventListener('touchstart', learningSession.recordActivity)
  cancelAutoNext()
})
</script>

<template>
  <div class="learn-page" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- 顶部工具栏 -->
    <div class="learn-topbar">
      <div class="topbar-left">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回课程详情
        </el-button>
      </div>
      <div class="topbar-center">
        <span class="course-title">{{ learnStore.currentCourseTitle }}</span>
      </div>
      <div class="topbar-right">
        <el-button text @click="toggleFullscreen">
          <el-icon><component :is="isFullscreen ? Aim : FullScreen" /></el-icon>
        </el-button>
        <el-button text @click="toggleSidebar">
          <el-icon><component :is="isSidebarCollapsed ? Expand : Fold" /></el-icon>
        </el-button>
      </div>
    </div>

    <div class="learn-body">
      <!-- 左侧侧边栏 -->
      <div class="learn-sidebar" :class="{ collapsed: isSidebarCollapsed }">
        <el-tabs v-model="sidebarTab" stretch class="sidebar-tabs">
          <!-- 当前任务 Tab -->
          <el-tab-pane label="当前任务" name="current-task">
            <div class="task-list">
              <div
                v-for="resource in currentTaskResources"
                :key="resource.resource_id"
                class="task-item"
                :class="{ active: resource.isActive }"
                @click="handleResourceClick(activeResource.sectionId, resource.resource_id, activeResource.chapterId ?? undefined)"
              >
                <el-icon class="resource-icon" :class="resource.resource_type">
                  <component :is="resourceIconMap[resource.resource_type]" />
                </el-icon>
                <div class="task-info">
                  <span class="task-name">{{ resource.file_name }}</span>
                  <span v-if="resource.duration" class="task-duration">
                    {{ formatDuration(resource.duration) }}
                  </span>
                </div>
                <div class="task-status">
                  <el-icon v-if="resource.isCompleted" class="completed"><CircleCheckFilled /></el-icon>
                  <span v-else class="progress">{{ resource.progressPercent }}%</span>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 目录 Tab -->
          <el-tab-pane label="目录" name="directory">
            <div class="directory-list">
              <div
                v-for="chapter in chapterTree"
                :key="chapter.chapter_id"
                class="chapter-node"
              >
                <div class="chapter-header" @click="toggleChapter(chapter.chapter_id)">
                  <el-icon class="expand-icon" :class="{ expanded: chapter.isExpanded }">
                    <ArrowLeft />
                  </el-icon>
                  <span class="chapter-title">{{ chapter.title }}</span>
                </div>
                <div v-show="chapter.isExpanded" class="section-list">
                  <div
                    v-for="resource in chapter.resources"
                    :key="`chapter-${chapter.chapter_id}-${resource.resource_id}`"
                    class="chapter-resource-node"
                    :class="{ active: chapter.hasActiveChapterResource && activeResource.resourceId === resource.resource_id }"
                    @click="handleChapterResourceClick(chapter.chapter_id, resource.resource_id)"
                  >
                    <div class="section-title">{{ resource.file_name }}</div>
                    <div class="resource-mini-list">
                      <div
                        class="resource-mini-item"
                        :class="{ active: activeResource.resourceId === resource.resource_id }"
                      >
                        <el-icon class="mini-icon" :class="resource.resource_type">
                          <component :is="resourceIconMap[resource.resource_type]" />
                        </el-icon>
                      </div>
                    </div>
                  </div>
                  <div
                    v-for="section in chapter.sections"
                    :key="section.section_id"
                    class="section-node"
                    :class="{ active: section.isActive }"
                    @click="handleSectionClick(section)"
                  >
                    <div class="section-title">{{ section.title }}</div>
                    <div class="resource-mini-list">
                      <div
                        v-for="resource in section.resources"
                        :key="resource.resource_id"
                        class="resource-mini-item"
                        :class="{ active: activeResource.resourceId === resource.resource_id }"
                        @click.stop="handleResourceClick(section.section_id, resource.resource_id)"
                      >
                        <el-icon class="mini-icon" :class="resource.resource_type">
                          <component :is="resourceIconMap[resource.resource_type]" />
                        </el-icon>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <div
        v-if="isOverlaySidebar && !isSidebarCollapsed"
        class="sidebar-overlay"
        @click="closeSidebar"
      />

      <!-- 右侧主内容区 -->
      <div class="learn-content">
        <!-- 加载中 -->
        <div v-if="activeResource.loadState === 'loading'" class="content-skeleton">
          <el-skeleton :rows="10" animated />
        </div>

        <!-- 错误状态 -->
        <div v-else-if="activeResource.loadState === 'error'" class="content-error">
          <el-result icon="warning" :title="activeResource.errorMessage || '资源加载失败'">
            <template #extra>
              <div class="content-action-surface soft-action-surface">
                <el-button class="soft-action-btn soft-action-btn--primary" type="primary" @click="switchResource(activeResource.sectionId, activeResource.resourceId!, activeResource.chapterId ?? undefined)">
                  重试
                </el-button>
              </div>
            </template>
          </el-result>
        </div>

        <!-- 空状态 -->
        <div v-else-if="!hasActiveResource" class="content-empty">
          <el-empty description="暂无课件，请在左侧目录中选择学习内容" />
        </div>

        <!-- 视频播放器 -->
        <div v-else-if="activeResource.resourceType === 'video'" class="video-container">
          <video
            ref="videoRef"
            class="video-player"
            controls
            :src="activeResource.fileUrl"
            @timeupdate="handleVideoTimeUpdate"
            @pause="handleVideoPause"
            @play="handleVideoPlay"
            @ended="handleVideoEnded"
            @error="handleVideoError"
            @loadedmetadata="handleVideoLoadedMetadata"
          />
        </div>

        <!-- 音频播放器 -->
        <div v-else-if="activeResource.resourceType === 'audio'" class="audio-container">
          <div class="audio-cover">
            <img :src="learnStore.currentCourseCover || '/placeholder-audio.png'" alt="audio cover" />
          </div>
          <div class="audio-info">
            <h3>{{ activeResource.fileUrl?.split('/').pop() || '音频' }}</h3>
          </div>
          <audio
            ref="audioRef"
            class="audio-player"
            controls
            :src="activeResource.fileUrl"
            @timeupdate="handleVideoTimeUpdate"
            @pause="handleVideoPause"
            @play="handleVideoPlay"
            @ended="handleVideoEnded"
            @error="handleVideoError"
            @loadedmetadata="handleVideoLoadedMetadata"
          />
        </div>

        <!-- 文档查看器 -->
        <div v-else-if="activeResource.resourceType === 'document'" class="document-container">
          <div v-if="documentRenderMode === 'text'" class="document-text-viewer">
            <pre>{{ documentTextContent || '文档内容为空' }}</pre>
          </div>
          <vue-office-pdf
            v-else-if="documentRenderMode === 'pdf'"
            :src="activeResource.fileUrl"
            class="document-office-viewer"
          />
          <vue-office-docx
            v-else-if="documentRenderMode === 'docx'"
            :src="activeResource.fileUrl"
            class="document-office-viewer document-docx-viewer"
          />
          <vue-office-pptx
            v-else-if="documentRenderMode === 'pptx'"
            :src="activeResource.fileUrl"
            class="document-office-viewer"
          />
          <div v-else class="document-download-viewer">
            <el-result
              icon="info"
              :title="`当前文件暂不支持在线预览`"
              :sub-title="`${activeDocumentFileName || '该文档'} 请下载后查看`"
            >
              <template #extra>
                <div class="content-action-surface soft-action-surface">
                  <el-button class="soft-action-btn soft-action-btn--primary" type="primary" @click="handleDocumentDownload">下载文档</el-button>
                </div>
              </template>
            </el-result>
          </div>
        </div>

        <!-- 图片查看器 -->
        <div v-else-if="activeResource.resourceType === 'image'" class="image-container">
          <el-image
            :src="activeResource.fileUrl"
            fit="contain"
            class="image-viewer"
            :preview-src-list="[activeResource.fileUrl]"
          />
        </div>
      </div>
    </div>

    <!-- 自动跳转提示 -->
    <el-notification
      v-if="showAutoNextNotice"
      title="即将自动播放下一个资源"
      :duration="0"
      type="info"
    >
      <div class="auto-next-content">
        <p>{{ autoNextCountdown }} 秒后自动跳转...</p>
        <div class="auto-next-action soft-action-surface">
          <el-button class="soft-action-btn soft-action-btn--secondary soft-action-btn--small" size="small" @click="cancelAutoNext">取消</el-button>
        </div>
      </div>
    </el-notification>
  </div>
</template>

<style lang="scss" scoped>

.learn-page {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1001;
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
  color: #fff;
}

// 顶部工具栏
.learn-topbar {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #2b2b2b;
  border-bottom: 1px solid #3a3a3a;
  flex-shrink: 0;
}

.topbar-left,
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topbar-center {
  flex: 1;
  text-align: center;
}

.course-title {
  font-size: 16px;
  font-weight: 500;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

:deep(.el-button) {
  color: #aaa;

  &:hover {
    color: #fff;
  }
}

.content-action-surface,
.auto-next-action {
  width: fit-content;
}

.content-action-surface :deep(.soft-action-btn),
.auto-next-action :deep(.soft-action-btn) {
  color: #fff;
}

.auto-next-action :deep(.soft-action-btn--secondary) {
  color: #2563eb;

  &:hover,
  &:focus {
    color: #1d4ed8;
  }
}

// 主体区域
.learn-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

// 侧边栏
.learn-sidebar {
  width: 320px;
  background: #2b2b2b;
  border-right: 1px solid #3a3a3a;
  transition: width 0.3s ease, transform 0.3s ease;
  overflow: hidden;
  flex-shrink: 0;

  &.collapsed {
    width: 0;
  }
}

.sidebar-overlay {
  display: none;
}

.sidebar-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;

  :deep(.el-tabs__header) {
    margin: 0;
    padding: 4px 0;
    background: #333;
    border-bottom: 1px solid #3a3a3a;
  }

  :deep(.el-tabs__nav) {
    width: 100%;
  }

  :deep(.el-tabs__item) {
    color: #888;
    width: 50%;
    height: 48px;
    line-height: 48px;
    font-size: 14px;

    &.is-active {
      color: #fff;
    }
  }

  :deep(.el-tabs__content) {
    flex: 1;
    overflow: hidden;
  }

  :deep(.el-tab-pane) {
    height: 100%;
    overflow-y: auto;
  }
}

// 任务列表
.task-list {
  padding: 8px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #3a3a3a;
  }

  &.active {
    background: rgba(24, 144, 255, 0.15);
    border-left: 3px solid #1890ff;
  }
}

.resource-icon {
  font-size: 20px;

  &.video { color: #52c41a; }
  &.audio { color: #1890ff; }
  &.document { color: #faad14; }
  &.image { color: #f5222d; }
}

.task-info {
  flex: 1;
  overflow: hidden;
}

.task-name {
  display: block;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-duration {
  font-size: 12px;
  color: #888;
}

.task-status {
  .completed {
    color: #52c41a;
  }

  .progress {
    font-size: 12px;
    color: #888;
  }
}

// 目录列表
.directory-list {
  padding: 8px;
}

.chapter-node {
  margin-bottom: 8px;
}

.chapter-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #333;
  border-radius: 8px;
  cursor: pointer;

  .expand-icon {
    transition: transform 0.2s;

    &.expanded {
      transform: rotate(-90deg);
    }
  }

  .chapter-title {
    flex: 1;
    font-size: 14px;
    font-weight: 500;
  }
}

.section-list {
  padding: 8px 0 0 16px;
}

.section-node {
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 4px;
  cursor: pointer;

  &:hover {
    background: #3a3a3a;
  }

  &.active {
    background: rgba(24, 144, 255, 0.1);
  }
}

.chapter-resource-node {
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 4px;
  cursor: pointer;
  border: 1px dashed rgba(255, 255, 255, 0.12);

  &:hover {
    background: #3a3a3a;
  }

  &.active {
    background: rgba(24, 144, 255, 0.1);
    border-color: rgba(24, 144, 255, 0.4);
  }
}

.section-title {
  font-size: 13px;
  margin-bottom: 6px;
}

.resource-mini-list {
  display: flex;
  gap: 4px;
}

.resource-mini-item {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3a3a3a;
  border-radius: 4px;

  &.active {
    background: #1890ff;
  }

  .mini-icon {
    font-size: 14px;
  }
}

// 主内容区
.learn-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-skeleton,
.content-error,
.content-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

// 视频播放器
.video-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.video-player {
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
}

// 音频播放器
.audio-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.audio-cover {
  width: 200px;
  height: 200px;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.audio-info {
  text-align: center;
  margin-bottom: 24px;

  h3 {
    font-size: 18px;
    font-weight: 500;
    margin: 0;
  }
}

.audio-player {
  width: 100%;
  max-width: 400px;
}

// 文档查看器
.document-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.document-office-viewer {
  flex: 1;
  width: 100%;
  min-height: 0;
}

.document-text-viewer {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: #111827;
  color: #f3f4f6;

  pre {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: Consolas, 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.7;
  }
}

.document-download-viewer {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

:deep(.document-docx-viewer .vue-office-docx) {
  height: 100%;
  overflow: auto;
}

// 图片查看器
.image-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a1a;
}

.image-viewer {
  max-width: 100%;
  max-height: 100%;
}

// 自动跳转提示
.auto-next-content {
  display: flex;
  align-items: center;
  gap: 12px;

  p {
    margin: 0;
  }
}

// 响应式
@media (max-width: $breakpoint-lg) {
  .sidebar-overlay {
    display: block;
    position: fixed;
    top: 48px;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 90;
    background: rgba(0, 0, 0, 0.45);
  }

  .learn-sidebar {
    position: fixed;
    top: 48px;
    left: 0;
    bottom: 0;
    z-index: 100;
    width: 280px !important;

    &.collapsed {
      transform: translateX(-100%);
    }
  }

  .learn-content {
    width: 100% !important;
  }

  // 移动端工具栏调整
  .learn-toolbar {
    padding: 8px 12px;
    gap: 8px;

    .toolbar-left {
      gap: 8px;
    }

    .resource-title {
      font-size: 14px;
      max-width: 150px;
    }
  }

  // 视频播放器移动端优化
  .video-container {
    min-height: 56.25vw; // 16:9 比例
  }

  // 音频播放器移动端优化
  .audio-container {
    padding: 24px;
  }

  .audio-cover {
    width: 150px;
    height: 150px;
    margin-bottom: 16px;
  }

  // 资源导航栏移动端优化
  .resource-nav {
    padding: 8px 12px;

    .nav-info {
      font-size: 13px;
    }
  }

  .content-action-surface,
  .auto-next-action {
    width: 100%;
  }
}

// 小屏幕手机适配
@media (max-width: $breakpoint-sm) {
  .learn-toolbar {
    padding: 8px;
    height: auto;
    flex-wrap: wrap;

    .toolbar-left {
      width: 100%;
      justify-content: space-between;
    }

    .toolbar-right {
      width: 100%;
      justify-content: flex-end;
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
  }

  .video-container {
    min-height: 56.25vw;
  }

  .resource-nav {
    flex-wrap: wrap;
    gap: 8px;

    .nav-actions {
      width: 100%;
      justify-content: space-between;
    }
  }
}
</style>
