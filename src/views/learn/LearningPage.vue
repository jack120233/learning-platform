<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
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
} from '@/api/learning'
import { useProgressSync } from '@/composables/useProgressSync'
import { formatDuration } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const learnStore = useLearnStore()

// 进度同步
const progressSync = useProgressSync({
  intervalMs: 30000,
  minDeltaSeconds: 5,
})

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

// 计算属性
const courseId = computed(() => Number(route.params.courseId))
const targetSectionId = computed(() => route.query.sectionId ? Number(route.query.sectionId) : null)
const targetResourceId = computed(() => route.query.resourceId ? Number(route.query.resourceId) : null)

const activeResource = computed(() => learnStore.activeResource)
const hasActiveResource = computed(() => learnStore.hasActiveResource)
const courseChapters = computed(() => learnStore.currentCourseChapters)

// 资源类型图标映射
const resourceIconMap: Record<string, typeof VideoPlay> = {
  video: VideoPlay,
  audio: Headset,
  document: Document,
  image: Picture,
}

// 构建目录树（带 UI 状态）
interface SectionTreeNode {
  section_id: number
  title: string
  resources: { resource_id: number; resource_type: string; file_name: string; duration?: number }[]
  isActive: boolean
}

interface ChapterTreeNode {
  chapter_id: number
  title: string
  isExpanded: boolean
  sections: SectionTreeNode[]
}

const chapterTree = computed<ChapterTreeNode[]>(() => {
  return courseChapters.value.map(chapter => ({
    chapter_id: chapter.chapter_id,
    title: chapter.title,
    isExpanded: chapterExpandMap.value[chapter.chapter_id] ?? false,
    sections: chapter.sections.map(section => ({
      section_id: section.section_id,
      title: section.title,
      resources: section.resources,
      isActive: activeResource.value.sectionId === section.section_id,
    })),
  }))
})

// 当前小节的资源列表（用于"当前任务"Tab）
const currentSectionResources = computed(() => {
  if (!activeResource.value.sectionId) return []

  for (const chapter of courseChapters.value) {
    const section = chapter.sections.find(s => s.section_id === activeResource.value.sectionId)
    if (section) {
      return section.resources.map(r => {
        const cache = learnStore.progressCache.get(r.resource_id)
        const progressPercent = cache && cache.totalTime > 0
          ? Math.round((cache.currentTime / cache.totalTime) * 100)
          : 0
        return {
          ...r,
          isActive: r.resource_id === activeResource.value.resourceId,
          isCompleted: cache?.isCompleted ?? false,
          progressPercent,
        }
      })
    }
  }
  return []
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
      data.course_id,
      data.title,
      data.cover_url,
      data.chapters,
      data.status
    )

    // 初始化章节展开状态
    if (data.chapters.length > 0) {
      chapterExpandMap.value = { [data.chapters[0].chapter_id]: true }
    }
  } catch {
    ElMessage.error('课程加载失败')
    router.push('/')
  }
}

// 确定初始资源
async function determineInitialResource(): Promise<{ sectionId: number; resourceId: number } | null> {
  // 优先级 1：路由 query 参数
  if (targetSectionId.value && targetResourceId.value) {
    return { sectionId: targetSectionId.value, resourceId: targetResourceId.value }
  }

  // 优先级 2：继续学习信息
  try {
    const info = await fetchContinueInfo(courseId.value)
    learnStore.setContinueInfo(info)
    return { sectionId: info.last_section_id, resourceId: info.last_resource_id }
  } catch {
    learnStore.setContinueInfo(null)
  }

  // 优先级 3：课程第一个资源
  const chapters = learnStore.currentCourseChapters
  if (chapters.length > 0 && chapters[0].sections.length > 0 && chapters[0].sections[0].resources.length > 0) {
    return {
      sectionId: chapters[0].sections[0].section_id,
      resourceId: chapters[0].sections[0].resources[0].resource_id,
    }
  }

  return null
}

// 切换资源
let switchAbortController: AbortController | null = null
let currentSwitchId = 0

async function switchResource(sectionId: number, resourceId: number): Promise<void> {
  // 取消上一次未完成的切换
  if (switchAbortController) {
    switchAbortController.abort()
  }
  switchAbortController = new AbortController()
  const thisSwitchId = ++currentSwitchId

  // 保存当前资源进度
  await progressSync.immediateSync()

  // 重置状态
  learnStore.setResourceLoadState('loading')

  // 找到章节 ID
  let chapterId = 0
  for (const chapter of courseChapters.value) {
    const section = chapter.sections.find(s => s.section_id === sectionId)
    if (section) {
      chapterId = chapter.chapter_id
      break
    }
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
  if (!videoRef.value) return
  progressSync.onTimeUpdate(videoRef.value.currentTime, videoRef.value.duration)
}

function handleVideoPause() {
  learnStore.setPlayState('paused')
  progressSync.immediateSync()
}

function handleVideoPlay() {
  learnStore.setPlayState('playing')
}

function handleVideoEnded() {
  learnStore.markResourceCompleted()
  progressSync.immediateSync()
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
      switchResource(next.sectionId, next.resourceId)
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

function toggleChapter(chapterId: number) {
  chapterExpandMap.value[chapterId] = !chapterExpandMap.value[chapterId]
}

function handleResourceClick(sectionId: number, resourceId: number) {
  switchResource(sectionId, resourceId)
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
  }
}

// 网络状态处理
function handleOnline() {
  ElMessage.success('网络已恢复')
  progressSync.handleOnline()
}

function handleOffline() {
  ElMessage.warning('网络已断开，请检查网络连接')
  progressSync.handleOffline()
}

// 页面离开处理
onBeforeRouteLeave(async (_to, _from, next) => {
  await progressSync.immediateSync()
  progressSync.stopPeriodicSync()
  learnStore.cleanup()
  window.removeEventListener('beforeunload', progressSync.onBeforeUnload)
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
  document.removeEventListener('keydown', handleKeydown)
  next()
})

// 初始化
onMounted(async () => {
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

  // 注册事件监听
  window.addEventListener('beforeunload', progressSync.onBeforeUnload)
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  document.addEventListener('keydown', handleKeydown)

  // 监听全屏变化
  document.addEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement
  })
})

// 清理
onUnmounted(() => {
  progressSync.stopPeriodicSync()
  window.removeEventListener('beforeunload', progressSync.onBeforeUnload)
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
  document.removeEventListener('keydown', handleKeydown)
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
                v-for="resource in currentSectionResources"
                :key="resource.resource_id"
                class="task-item"
                :class="{ active: resource.isActive }"
                @click="handleResourceClick(activeResource.sectionId!, resource.resource_id)"
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
                  <span v-else class="progress">{{ Math.round((activeResource.currentTime / activeResource.totalTime) * 100) }}%</span>
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
                    v-for="section in chapter.sections"
                    :key="section.section_id"
                    class="section-node"
                    :class="{ active: section.isActive }"
                  >
                    <div class="section-title">{{ section.title }}</div>
                    <div class="resource-mini-list">
                      <div
                        v-for="resource in section.resources"
                        :key="resource.resource_id"
                        class="resource-mini-item"
                        :class="{ active: activeResource.resourceId === resource.resource_id }"
                        @click="handleResourceClick(section.section_id, resource.resource_id)"
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
              <el-button type="primary" @click="switchResource(activeResource.sectionId!, activeResource.resourceId!)">
                重试
              </el-button>
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
          <iframe :src="activeResource.fileUrl" class="document-viewer" />
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
        <el-button size="small" @click="cancelAutoNext">取消</el-button>
      </div>
    </el-notification>
  </div>
</template>

<style lang="scss" scoped>

.learn-page {
  position: fixed;
  top: 0;
  left: 0;
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
  transition: width 0.3s ease;
  overflow: hidden;
  flex-shrink: 0;

  &.collapsed {
    width: 0;
  }
}

.sidebar-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;

  :deep(.el-tabs__header) {
    margin: 0;
    background: #333;
  }

  :deep(.el-tabs__nav) {
    width: 100%;
  }

  :deep(.el-tabs__item) {
    color: #888;
    width: 50%;

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
}

.document-viewer {
  flex: 1;
  width: 100%;
  border: none;
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