<script setup lang="ts">
import { ref, computed, onMounted, watch, defineAsyncComponent } from 'vue'
const VueOfficeDocx = defineAsyncComponent(() => import('@vue-office/docx'))
const VueOfficePdf = defineAsyncComponent(() => import('@vue-office/pdf'))
const VueOfficePptx = defineAsyncComponent(() => import('@vue-office/pptx'))
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  VideoPlay,
  ArrowRight,
  Download,
  Document,
  Headset,
  Picture,
  Plus,
  Delete,
  User,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { useLearnStore } from '@/store/learn'
import {
  fetchCourseDetail,
  fetchContinueInfo,
  startLearning,
  type CourseDetail,
  type CourseMaterial,
  type CourseChapter,
  type CourseResource,
} from '@/api/learning'
import { formatFileSize, formatDuration, formatDate } from '@/utils/format'
import FeedbackForm from '@/components/feedback/FeedbackForm.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const learnStore = useLearnStore()

// 课程数据
const course = ref<CourseDetail | null>(null)
const isLoading = ref(true)
const isError = ref(false)
const errorType = ref<'not_found' | 'archived' | 'network' | 'server' | null>(null)

// 标签页
const activeTab = ref<'outline' | 'intro' | 'materials' | 'feedback'>('outline')

// 章节折叠状态
const chapterExpandMap = ref<Record<number, boolean>>({})

// 继续学习
const isFetchingContinue = ref(false)

// 资料下载
const downloadingMap = ref<Record<number, boolean>>({})

// 预览状态
const previewVisible = ref(false)
const previewUrl = ref('')
const previewType = ref<'pdf' | 'docx' | 'pptx' | 'image' | null>(null)

// 计算属性
const courseId = computed(() => Number(route.params.courseId))
const hasLearningRecord = computed(() => learnStore.hasLearningRecord)
const continueInfo = computed(() => learnStore.continueInfo)

// 动态计算简介行宽：字少则窄，字多则宽，封顶 600px
const summaryMaxWidth = computed(() => {
  const length = course.value?.summary?.length || 0
  if (length === 0) return '100%'
  if (length < 30) return '300px'
  if (length < 80) return '450px'
  return '600px'
})

// 计算课程总小节数
const totalSections = computed(() => {
  if (!course.value?.chapters) return 0
  return course.value.chapters.reduce((total, chapter) => total + (chapter.sections?.length || 0), 0)
})

// 是否显示继续学习按钮
const showContinueBtn = computed(() => userStore.isLoggedIn && hasLearningRecord.value && continueInfo.value)
// 是否显示开始学习按钮
const showStartBtn = computed(() => userStore.isLoggedIn && !showContinueBtn.value)
// 是否显示登录提示按钮
const showLoginPrompt = computed(() => !userStore.isLoggedIn)

// 加载课程详情
async function loadCourseDetail() {
  if (!courseId.value || courseId.value <= 0) {
    errorType.value = 'not_found'
    isError.value = true
    isLoading.value = false
    return
  }

  isLoading.value = true
  isError.value = false
  errorType.value = null

  try {
    const data = await fetchCourseDetail(courseId.value)
    course.value = data

    // 校验课程状态
    if (data.status === 'archived') {
      errorType.value = 'archived'
      isError.value = true
      isLoading.value = false
      return
    }

    // 初始化章节折叠状态（默认第一章展开）
    const chapters = data.chapters || []
    if (chapters.length > 0) {
      const firstChId = chapters[0].chapter_id ?? 0
      chapterExpandMap.value = {
        [firstChId]: true,
      }
    }

    // 写入 LearnStore
    const resolvedCourseId = data.course_id || data.id || 0
    learnStore.initCourseContext(
      resolvedCourseId,
      data.title,
      data.cover_url,
      chapters,
      data.status
    )

    // 设置页面标题
    document.title = `${data.title} - 在线学习平台`

  } catch (error: unknown) {
    const err = error as { response?: { status?: number } }
    if (err.response?.status === 404) {
      errorType.value = 'not_found'
    } else if (err.response?.status === 500) {
      errorType.value = 'server'
    } else {
      errorType.value = 'network'
    }
    isError.value = true
  } finally {
    isLoading.value = false
  }
}

// 加载继续学习信息
async function loadContinueInfo() {
  if (!userStore.isLoggedIn) return

  isFetchingContinue.value = true
  try {
    const info = await fetchContinueInfo(courseId.value)
    learnStore.setContinueInfo(info)
  } catch {
    learnStore.setContinueInfo(null)
  } finally {
    isFetchingContinue.value = false
  }
}

// 开始/继续学习
async function handleStartLearn() {
  if (!userStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

  // 首次学习
  if (!hasLearningRecord.value) {
    try {
      await startLearning(courseId.value)
    } catch {
      ElMessage.error('开始学习失败，请稍后重试')
      return
    }
  }

  // 跳转学习页
  if (continueInfo.value) {
    const query: Record<string, number> = {}
    if (continueInfo.value.last_resource_id != null) {
      query.resourceId = continueInfo.value.last_resource_id
    }
    if (continueInfo.value.last_section_id != null) {
      query.sectionId = continueInfo.value.last_section_id
    } else if (continueInfo.value.chapter_id != null) {
      query.chapterId = continueInfo.value.chapter_id
    }

    router.push({
      path: `/learn/${courseId.value}`,
      query,
    })
  } else {
    router.push(`/learn/${courseId.value}`)
  }
}

// 切换章节折叠
function toggleChapter(chapterId: number) {
  chapterExpandMap.value[chapterId] = !chapterExpandMap.value[chapterId]
}

// 展开全部章节
function expandAllChapters() {
  if (course.value) {
    course.value.chapters?.forEach(ch => {
      const chId = ch.chapter_id ?? 0
      chapterExpandMap.value[chId] = true
    })
  }
}

// 折叠全部章节
function collapseAllChapters() {
  chapterExpandMap.value = {}
}

// 点击小节跳转学习
function handleSectionClick(sectionId: number, resourceId: number) {
  if (!userStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  router.push({
    path: `/learn/${courseId.value}`,
    query: { sectionId, resourceId },
  })
}

// 下载资料
async function handleDownload(material: CourseMaterial) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再下载资料')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

  downloadingMap.value[material.material_id] = true
  try {
    // 使用 fetch + Blob 下载
    const response = await fetch(material.file_url)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = material.file_name
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch {
    ElMessage.error('下载失败，请稍后重试')
  } finally {
    downloadingMap.value[material.material_id] = false
  }
}

// 获取资料类型
function getMaterialType(filename: string): 'pdf' | 'docx' | 'pptx' | 'image' | 'other' {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  if (ext === 'pdf') return 'pdf'
  if (['doc', 'docx'].includes(ext)) return 'docx'
  if (['ppt', 'pptx'].includes(ext)) return 'pptx'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return 'image'
  return 'other'
}

// 处理预览
function handlePreview(material: CourseMaterial) {
  const type = getMaterialType(material.file_name)
  if (type === 'other') {
    handleDownload(material)
    return
  }
  
  previewUrl.value = material.file_url
  previewType.value = type
  previewVisible.value = true
}

// 返回首页
function goHome() {
  router.push('/')
}

// 监听路由参数变化
watch(() => route.params.courseId, () => {
  if (route.params.courseId) {
    loadCourseDetail()
    loadContinueInfo()
  }
}, { immediate: false })

// 初始化
onMounted(async () => {
  await loadCourseDetail()
  if (!isError.value) {
    loadContinueInfo()
  }
})

// 资源类型图标映射
const resourceIconMap: Record<string, typeof VideoPlay> = {
  video: VideoPlay,
  audio: Headset,
  document: Document,
  image: Picture,
}

function getChapterResources(chapter: CourseChapter): CourseResource[] {
  return chapter.resources ?? []
}

function getChapterResourceCount(chapter: CourseChapter): number {
  return getChapterResources(chapter).length
}

function openChapterResource(resource: CourseResource) {
  if (!userStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

  const chapter = course.value?.chapters?.find(item =>
    (item.resources ?? []).some(candidate => candidate.resource_id === resource.resource_id)
  )

  if (!chapter) {
    ElMessage.warning('未找到资源所属章节，暂时无法打开')
    return
  }

  router.push({
    path: `/learn/${courseId.value}`,
    query: {
      chapterId: chapter.chapter_id,
      resourceId: resource.resource_id,
    },
  })
}
</script>

<template>
  <div class="course-detail-page">
    <!-- 加载中 -->
    <div v-if="isLoading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="isError" class="error-container">
      <el-result
        icon="warning"
        :title="errorType === 'not_found' ? '该课程不存在或已下架' : errorType === 'archived' ? '该课程已下架，暂时无法访问' : '课程详情加载失败，请稍后重试'"
      >
        <template #extra>
          <el-button type="primary" @click="errorType === 'network' || errorType === 'server' ? loadCourseDetail : goHome">
            {{ errorType === 'network' || errorType === 'server' ? '重新加载' : '返回首页' }}
          </el-button>
        </template>
      </el-result>
    </div>

    <!-- 正常内容 -->
    <template v-else-if="course">
      <!-- 面包屑 -->
      <div class="breadcrumb-container">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>{{ course.title }}</el-breadcrumb-item>
        </el-breadcrumb>
      </div>

      <!-- 课程封面与基础信息区 -->
      <div class="hero-section">
        <div class="cover-area">
          <el-image
            :src="course.cover_url"
            fit="cover"
            class="cover-image"
          >
            <template #error>
              <div class="cover-placeholder">
                <el-icon :size="48"><Picture /></el-icon>
              </div>
            </template>
          </el-image>
        </div>
        <div class="info-area">
          <h1 class="course-title">{{ course.title }}</h1>

          <!-- 统一元数据行：讲师 | 分类 | 发布时间 -->
          <div class="meta-info-bar">
            <template v-if="course.author">
              <span class="meta-item">
                <el-icon class="meta-icon"><User /></el-icon>
                讲师：{{ course.author }}
              </span>
              <span class="meta-divider"></span>
            </template>

            <span class="meta-item" v-if="course.category_name">
              {{ course.category_name }}
            </span>
            <span class="meta-divider" v-if="course.category_name"></span>

            <span class="meta-item">
              发布于 {{ formatDate(course.published_at) }}
            </span>
          </div>

          <!-- 课程简介 -->
          <div class="course-summary-container">
            <p
              class="course-summary"
              :style="{ maxWidth: summaryMaxWidth }"
            >
              {{ course.summary }}
            </p>
          </div>

          <!-- 操作按钮区 -->
          <div class="action-area">
            <el-button
              v-if="showContinueBtn"
              type="primary"
              size="large"
              :icon="VideoPlay"
              @click="handleStartLearn"
            >
              继续学习 · {{ continueInfo?.last_section_title || '上次位置' }}
            </el-button>
            <el-button
              v-else-if="showStartBtn"
              type="primary"
              size="large"
              :icon="VideoPlay"
              @click="handleStartLearn"
            >
              开始学习
            </el-button>
            <el-button
              v-else-if="showLoginPrompt"
              type="primary"
              size="large"
              @click="handleStartLearn"
            >
              登录后开始学习
            </el-button>
          </div>
        </div>
      </div>

      <!-- 标签页区域 -->
      <div class="tabs-section">
        <el-tabs v-model="activeTab">
          <!-- 课程目录 -->
          <el-tab-pane label="课程目录" name="outline">
            <div class="outline-header">
              <span class="outline-count">共 {{ course.chapters?.length || 0 }} 章 / {{ totalSections }} 小节</span>
              <div class="header-actions">
                <el-button-group>
                  <el-button 
                    plain 
                    size="small" 
                    :icon="Plus" 
                    @click="expandAllChapters"
                  >
                    全部展开
                  </el-button>
                  <el-button 
                    plain 
                    size="small" 
                    :icon="Delete" 
                    @click="collapseAllChapters"
                  >
                    全部折叠
                  </el-button>
                </el-button-group>
              </div>
            </div>
            <div class="chapter-list">
              <div
                v-for="chapter in course.chapters"
                :key="chapter.chapter_id"
                class="chapter-item"
              >
                <div 
                  class="chapter-header" 
                  :class="{ active: chapterExpandMap[chapter.chapter_id!] }"
                  @click="toggleChapter(chapter.chapter_id!)"
                >
                  <el-icon class="expand-icon" :class="{ expanded: chapterExpandMap[chapter.chapter_id!] }">
                    <ArrowRight />
                  </el-icon>
                  <span class="chapter-title">{{ chapter.title }}</span>
                  <span class="section-count">
                    {{ chapter.sections.length }} 小节
                    <template v-if="getChapterResourceCount(chapter) > 0">
                      / {{ getChapterResourceCount(chapter) }} 章节资源
                    </template>
                  </span>
                </div>
                <div v-show="chapterExpandMap[chapter.chapter_id!]" class="section-list">
                  <div v-if="getChapterResourceCount(chapter) > 0" class="chapter-resource-group">
                    <div class="chapter-resource-title">章节资源</div>
                    <div
                      v-for="resource in getChapterResources(chapter)"
                      :key="resource.resource_id"
                      class="resource-item chapter-resource-item"
                      @click="openChapterResource(resource)"
                    >
                      <el-icon class="resource-icon" :class="resource.resource_type">
                        <component :is="resourceIconMap[resource.resource_type]" />
                      </el-icon>
                      <span class="resource-name">{{ resource.file_name }}</span>
                      <span v-if="resource.duration" class="resource-duration">
                        {{ formatDuration(resource.duration) }}
                      </span>
                    </div>
                  </div>
                  <div
                    v-for="section in chapter.sections"
                    :key="section.section_id"
                    class="section-item"
                    @click="handleSectionClick(section.section_id!, section.resources?.[0]?.resource_id ?? 0)"
                  >
                    <div class="section-info">
                      <span class="section-title">{{ section.title }}</span>
                      <span class="resource-count">{{ section.resource_count ?? section.resources?.length ?? 0 }} 个资源</span>
                    </div>
                    <div class="resource-list" v-if="section.resources?.length">
                      <div
                        v-for="resource in section.resources"
                        :key="resource.resource_id"
                        class="resource-item"
                        @click.stop="handleSectionClick(section.section_id!, resource.resource_id)"
                      >
                        <el-icon class="resource-icon" :class="resource.resource_type">
                          <component :is="resourceIconMap[resource.resource_type]" />
                        </el-icon>
                        <span class="resource-name">{{ resource.file_name }}</span>
                        <span v-if="resource.duration" class="resource-duration">
                          {{ formatDuration(resource.duration) }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 课程简介 -->
          <el-tab-pane label="课程简介" name="intro">
            <div class="summary-content">{{ course.summary || '暂无课程简介' }}</div>
          </el-tab-pane>

          <!-- 配套资料 -->
          <el-tab-pane label="配套资料" name="materials">
            <div v-if="(course.materials?.length ?? 0) > 0" class="material-list">
              <div
                v-for="material in course.materials"
                :key="material.material_id"
                class="material-item"
              >
                <el-icon class="file-icon"><Document /></el-icon>
                <div class="file-info">
                  <span class="file-name">{{ material.file_name }}</span>
                  <span class="file-meta">
                    {{ formatFileSize(material.file_size) }} · {{ material.download_count }} 次下载
                  </span>
                </div>
                <el-button
                  type="primary"
                  :icon="Download"
                  :loading="downloadingMap[material.material_id]"
                  @click="handleDownload(material)"
                >
                  下载
                </el-button>
                <el-button
                  v-if="getMaterialType(material.file_name) !== 'other'"
                  type="primary"
                  plain
                  @click="handlePreview(material)"
                >
                  预览
                </el-button>
              </div>
            </div>
            <el-empty v-else description="暂无配套资料" />
          </el-tab-pane>

          <!-- 反馈 -->
          <el-tab-pane label="反馈" name="feedback">
            <div class="course-feedback-panel">
              <FeedbackForm
                class="course-feedback-form"
                mode="inline"
                default-type="course"
                :type-locked="true"
                :course-id="courseId"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>

    <!-- 资料预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      :title="course?.materials?.find(m => m.file_url === previewUrl)?.file_name || '资料预览'"
      width="90%"
      class="preview-dialog"
      destroy-on-close
      append-to-body
    >
      <div class="preview-container" v-loading="!previewUrl">
        <vue-office-pdf
          v-if="previewType === 'pdf'"
          :src="previewUrl"
          class="office-viewer"
        />
        <vue-office-docx
          v-else-if="previewType === 'docx'"
          :src="previewUrl"
          class="office-viewer"
        />
        <vue-office-pptx
          v-else-if="previewType === 'pptx'"
          :src="previewUrl"
          class="office-viewer"
        />
        <div v-else-if="previewType === 'image'" class="image-viewer-box">
          <el-image :src="previewUrl" fit="contain" :preview-src-list="[previewUrl]" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
@use 'sass:color';

/* 预览弹窗样式 */
:deep(.preview-dialog) {
  .el-dialog__body {
    padding: 0;
    background: #f5f7fa;
  }
}

.preview-container {
  height: calc(100vh - 200px);
  overflow-y: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  
  .office-viewer {
    width: 100%;
    height: 100%;
  }
  
  .image-viewer-box {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    
    .el-image {
      max-width: 100%;
      max-height: 100%;
    }
  }
}

.course-detail-page {
  padding: 24px 0 40px;
  min-height: calc(100vh - 64px - 200px);
}

.page-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
}

.loading-container,
.error-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 40px 24px;
}

// 面包屑
.breadcrumb-container {
  max-width: 1440px;
  margin: 0 auto 16px;
  padding: 0 24px;
}

// Hero Section
.hero-section {
  display: flex;
  gap: 32px;
  max-width: 1440px;
  margin: 0 auto 32px;
  padding: 0 24px;

  @media (max-width: $breakpoint-lg) {
    flex-direction: column;
    gap: 24px;
  }
}

.cover-area {
  flex-shrink: 0;
  width: 400px;

  @media (max-width: $breakpoint-lg) {
    width: 100%;
    max-width: 400px;
  }
}

.cover-image {
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: $radius-lg;
  overflow: hidden;
}

.course-title {
  font-size: 32px;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 20px;
  line-height: 1.25;
  letter-spacing: -0.5px;
}

.meta-info-bar {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 16px;
  font-size: $font-size-sm;
  color: $text-secondary;

  .meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .meta-icon {
    font-size: 14px;
    color: $text-tertiary;
  }

  .meta-divider {
    display: inline-block;
    width: 1px;
    height: 12px;
    background-color: $border-color;
    margin: 0 12px;
  }
}

.course-summary-container {
  margin-bottom: 24px;
  
  .course-summary {
    font-size: $font-size-base;
    color: $text-secondary;
    line-height: 1.8;
    margin: 0;
    text-align: justify;
  }
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-color;
  color: $text-tertiary;
}

.info-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.course-title {
  font-size: 28px;
  font-weight: 600;
  color: $text-primary;
  margin: 0;
  line-height: 1.3;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;

  .teacher-info {
    display: flex;
    align-items: center;
    gap: 4px;
    color: $text-secondary;
    
    .lecturer-icon {
      font-size: 14px;
      color: $text-tertiary;
    }
    
    .teacher-name {
      font-size: $font-size-sm;
      color: $text-secondary;
    }
  }

  .el-divider--vertical {
    margin: 0 4px;
    border-color: $border-color-light;
  }

  .tag-item {
    background-color: transparent;
    border-color: $border-color;
    color: $text-secondary;
  }
}

.course-summary {
  font-size: $font-size-base;
  color: $text-secondary;
  line-height: 1.6;
  margin: 0;
}

.publish-time {
  font-size: $font-size-sm;
  color: $text-tertiary;
}

.action-area {
  margin-top: 8px;
}

// Tabs Section
.tabs-section {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
  background: $bg-white;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;

  :deep(.el-tabs__item) {
    font-size: 15px;
    height: 54px;
    line-height: 54px;
    transition: all 0.3s;

    &.is-active {
      font-weight: 600;
      color: $primary-color;
    }

    &:hover {
      color: $primary-color;
    }
  }

  :deep(.el-tabs__active-bar) {
    height: 3px;
    border-radius: 3px;
  }

  :deep(.el-tabs__nav-wrap::after) {
    height: 1px;
    background-color: $border-color-light;
  }
}

// 章节目录
.outline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 8px 0;
  border-bottom: 1px dashed $border-color-light;

  .outline-count {
    font-size: 14px;
    color: $text-secondary;
    font-weight: 500;
  }

  .header-actions {
    display: flex;
    gap: 8px;

    :deep(.el-button) {
      font-weight: 500;
      color: $text-secondary;
      transition: all 0.2s ease;
      
      &:hover {
        color: $primary-color;
        border-color: $primary-color;
        background-color: color.adjust($primary-color, $lightness: 46%);
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
      }

      &:active {
        transform: translateY(0);
      }
    }
  }
}

.chapter-list {
  .chapter-item {
    border: 1px solid $border-color;
    border-radius: $radius-md;
    margin-bottom: 12px;
    overflow: hidden;
  }

  .chapter-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    background: color.adjust($bg-color, $lightness: 2%);
    cursor: pointer;
    user-select: none;
    transition: all 0.3s ease;
    position: relative;
    border-left: 3px solid transparent;

    &:hover {
      background: color.adjust($bg-color, $lightness: -1%);
      padding-left: 20px;
    }

    &.active {
      background: color.adjust($primary-color, $lightness: 46%);
      border-left-color: $primary-color;

      .chapter-title {
        color: $primary-color;
        font-weight: 600;
      }

      .expand-icon {
        color: $primary-color;
      }
    }

    .expand-icon {
      transition: all 0.3s ease;

      &.expanded {
        transform: rotate(90deg);
      }
    }

    .chapter-title {
      flex: 1;
      font-weight: 500;
      color: $text-primary;
    }

    .section-count {
      font-size: $font-size-sm;
      color: $text-tertiary;
    }
  }

  .section-list {
    padding: 8px 12px 12px;
    background: #fff;
  }

  .chapter-resource-group {
    padding: 4px 0 12px;
  }

  .chapter-resource-title {
    padding: 0 12px 8px;
    font-size: $font-size-xs;
    font-weight: 600;
    color: $text-tertiary;
    letter-spacing: 0.04em;
  }

  .section-item {
    padding: 10px 12px;
    border-radius: $radius-md;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: color.adjust($bg-color, $lightness: 1%);
      transform: translateX(4px);
    }

    &:not(:last-child) {
      margin-bottom: 4px;
    }
  }

  .section-info {
    display: flex;
    align-items: center;
    gap: 8px;

    .section-title {
      font-weight: 500;
      color: $text-primary;
      font-size: 15px;
    }

    .resource-count {
      font-size: $font-size-xs;
      color: $text-tertiary;
    }
  }

  .resource-list {
    padding-left: 16px;
    margin-top: 8px;
    border-left: 2px solid $border-color-light;
  }

  .resource-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: $radius-sm;

    &:hover {
      background: rgba($primary-color, 0.05);
    }

    .resource-icon {
      font-size: 16px;

      &.video { color: #52c41a; }
      &.audio { color: #1890ff; }
      &.document { color: #faad14; }
      &.image { color: #f5222d; }
    }

    .resource-name {
      flex: 1;
      font-size: $font-size-sm;
      color: $text-secondary;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .resource-duration {
      font-size: $font-size-xs;
      color: $text-tertiary;
    }
  }

  .chapter-resource-item {
    margin-bottom: 4px;
    cursor: pointer;
    border: 1px dashed $border-color-light;

    &:hover {
      background: rgba($primary-color, 0.05);
      border-color: rgba($primary-color, 0.3);
    }
  }
}

// 课程简介
.summary-content {
  line-height: 1.8;
  color: $text-secondary;
  white-space: pre-wrap;
}

// 课程描述
.description-content {
  line-height: 1.8;
  color: $text-secondary;

  :deep(img) {
    max-width: 100%;
    border-radius: $radius-md;
  }

  :deep(h1), :deep(h2), :deep(h3) {
    color: $text-primary;
    margin: 24px 0 12px;
  }

  :deep(p) {
    margin: 12px 0;
  }
}

// 配套资料
.material-list {
  .material-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    border-bottom: 1px solid $border-color-light;

    &:last-child {
      border-bottom: none;
    }
  }

  .file-icon {
    font-size: 32px;
    color: $primary-color;
  }

  .file-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .file-name {
    font-weight: 500;
    color: $text-primary;
  }

  .file-meta {
    font-size: $font-size-sm;
    color: $text-tertiary;
  }
}

// 反馈区
.course-feedback-panel {
  max-width: 720px;
  padding: 24px 0;
}

.course-feedback-form {
  :deep(.feedback-form.inline) {
    padding: 0;
    background: #fff;
  }
}

// 移动端适配
@media (max-width: $breakpoint-sm) {
  .breadcrumb-section {
    padding: 0 16px;
  }

  .hero-section {
    padding: 0 16px;
    margin-bottom: 24px;
  }

  .course-title {
    font-size: 22px;
  }

  .teacher-info {
    flex-wrap: wrap;
  }

  .tabs-section {
    padding: 0 16px;
    border-radius: 0;
    margin: 0 -16px;
    width: calc(100% + 32px);

    :deep(.el-tabs__header) {
      margin: 0 16px;
    }

    :deep(.el-tabs__nav-wrap) {
      &::after {
        display: none;
      }
    }

    :deep(.el-tabs__nav-scroll) {
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;

      &::-webkit-scrollbar {
        display: none;
      }
    }

    :deep(.el-tabs__nav) {
      display: flex;
      flex-wrap: nowrap;
    }

    :deep(.el-tabs__item) {
      padding: 0 16px;
      white-space: nowrap;
    }

    :deep(.el-tabs__content) {
      padding: 16px;
    }
  }

  .outline-header {
    justify-content: space-between;

    .el-button {
      font-size: 13px;
    }
  }

  .chapter-list {
    .chapter-header {
      padding: 12px;
    }

    .chapter-title {
      font-size: 14px;
    }

    .section-list {
      padding: 0 12px 12px;
    }

    .section-item {
      padding: 10px;
    }

    .section-info .section-title {
      font-size: 14px;
    }

    .resource-item {
      padding: 6px 10px;

      .resource-name {
        font-size: 13px;
      }
    }
  }

  .material-list .material-item {
    padding: 12px;
    gap: 12px;

    .file-icon {
      font-size: 24px;
    }
  }

  .course-feedback-panel {
    padding: 16px 0;
  }

  .action-area {
    :deep(.el-button) {
      width: 100%;
    }
  }
}
</style>
