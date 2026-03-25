<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  VideoPlay,
  ArrowRight,
  Download,
  Document,
  Headset,
  Picture,
  Upload,
  Plus,
  Delete,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { useLearnStore } from '@/store/learn'
import {
  fetchCourseDetail,
  fetchContinueInfo,
  startLearning,
  submitFeedback,
  uploadFile as uploadFileApi,
  type CourseDetail,
  type CourseMaterial,
} from '@/api/learning'
import { formatFileSize, formatDuration, formatDate } from '@/utils/format'

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
const activeTab = ref<'outline' | 'intro' | 'exam' | 'materials' | 'feedback'>('outline')

// 章节折叠状态
const chapterExpandMap = ref<Record<number, boolean>>({})

// 继续学习
const isFetchingContinue = ref(false)

// 资料下载
const downloadingMap = ref<Record<number, boolean>>({})

// 反馈表单
const feedbackForm = ref({
  content: '',
  images: [] as string[],
  uploading: false,
  submitting: false,
})

// 计算属性
const courseId = computed(() => Number(route.params.courseId))
const hasLearningRecord = computed(() => learnStore.hasLearningRecord)
const continueInfo = computed(() => learnStore.continueInfo)

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
    if (data.chapters.length > 0) {
      chapterExpandMap.value = {
        [data.chapters[0].chapter_id]: true,
      }
    }

    // 写入 LearnStore
    learnStore.initCourseContext(
      data.course_id,
      data.title,
      data.cover_url,
      data.chapters,
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
    router.push({
      path: `/learn/${courseId.value}`,
      query: {
        sectionId: continueInfo.value.last_section_id,
        resourceId: continueInfo.value.last_resource_id,
      },
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
    course.value.chapters.forEach(ch => {
      chapterExpandMap.value[ch.chapter_id] = true
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

// 处理图片上传
async function handleImageUpload(uploadFile: { raw?: File }) {
  const file = uploadFile.raw
  if (!file) return

  // 校验文件类型
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    ElMessage.warning('仅支持 JPG/PNG 格式')
    return
  }

  // 校验文件大小
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('单张图片最大 5MB')
    return
  }

  // 校验数量
  if (feedbackForm.value.images.length >= 8) {
    ElMessage.warning('最多上传 8 张图片')
    return
  }

  feedbackForm.value.uploading = true
  try {
    const result = await uploadFileApi(file)
    feedbackForm.value.images.push(result.file_url)
  } catch {
    ElMessage.error('图片上传失败')
  } finally {
    feedbackForm.value.uploading = false
  }
}

// 删除已上传图片
function handleRemoveImage(index: number) {
  feedbackForm.value.images.splice(index, 1)
}

// 提交反馈
async function handleSubmitFeedback() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再提交反馈')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

  // 校验内容
  if (feedbackForm.value.content.length < 10) {
    ElMessage.warning('反馈内容至少 10 个字符')
    return
  }
  if (feedbackForm.value.content.length > 500) {
    ElMessage.warning('反馈内容最多 500 个字符')
    return
  }

  feedbackForm.value.submitting = true
  try {
    await submitFeedback({
      feedback_type: 'course',
      course_id: courseId.value,
      content: feedbackForm.value.content,
      images: feedbackForm.value.images.length > 0 ? feedbackForm.value.images : undefined,
    })
    ElMessage.success('反馈已提交，感谢您的反馈')
    feedbackForm.value.content = ''
    feedbackForm.value.images = []
  } catch (error: unknown) {
    const err = error as { response?: { status?: number } }
    if (err.response?.status === 429) {
      ElMessage.warning('提交过于频繁，请稍后再试')
    } else {
      ElMessage.error('反馈提交失败，请稍后重试')
    }
  } finally {
    feedbackForm.value.submitting = false
  }
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

          <!-- 讲师信息 -->
          <div class="teacher-info">
            <el-avatar :size="32" :src="course.teacher_avatar">
              {{ course.teacher_name?.charAt(0) }}
            </el-avatar>
            <span class="teacher-name">{{ course.teacher_name }}</span>
          </div>

          <!-- 元数据行 -->
          <div class="meta-row">
            <el-tag type="info" size="small">{{ course.category_name }}</el-tag>
            <el-tag
              v-for="tag in course.tags?.slice(0, 5)"
              :key="tag"
              size="small"
              class="tag-item"
            >
              {{ tag }}
            </el-tag>
            <span class="view-count">
              <el-icon><VideoPlay /></el-icon>
              {{ course.view_count }} 次学习
            </span>
          </div>

          <!-- 课程简介 -->
          <p class="course-summary">{{ course.summary }}</p>

          <!-- 发布时间 -->
          <div class="publish-time">
            发布于 {{ formatDate(course.published_at) }}
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
              <el-button text size="small" @click="expandAllChapters">展开全部</el-button>
              <el-button text size="small" @click="collapseAllChapters">折叠全部</el-button>
            </div>
            <div class="chapter-list">
              <div
                v-for="chapter in course.chapters"
                :key="chapter.chapter_id"
                class="chapter-item"
              >
                <div class="chapter-header" @click="toggleChapter(chapter.chapter_id)">
                  <el-icon class="expand-icon" :class="{ expanded: chapterExpandMap[chapter.chapter_id] }">
                    <ArrowRight />
                  </el-icon>
                  <span class="chapter-title">{{ chapter.title }}</span>
                  <span class="section-count">{{ chapter.sections.length }} 小节</span>
                </div>
                <div v-show="chapterExpandMap[chapter.chapter_id]" class="section-list">
                  <div
                    v-for="section in chapter.sections"
                    :key="section.section_id"
                    class="section-item"
                    @click="handleSectionClick(section.section_id, section.resources[0]?.resource_id)"
                  >
                    <div class="section-info">
                      <span class="section-title">{{ section.title }}</span>
                      <span class="resource-count">{{ section.resources.length }} 个资源</span>
                    </div>
                    <div class="resource-list">
                      <div
                        v-for="resource in section.resources"
                        :key="resource.resource_id"
                        class="resource-item"
                        @click.stop="handleSectionClick(section.section_id, resource.resource_id)"
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
            <div class="description-content" v-html="course.description"></div>
          </el-tab-pane>

          <!-- 考试入口 -->
          <el-tab-pane label="考试入口" name="exam">
            <el-empty description="考试功能即将上线，敬请期待" />
          </el-tab-pane>

          <!-- 配套资料 -->
          <el-tab-pane label="配套资料" name="materials">
            <div v-if="course.materials?.length > 0" class="material-list">
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
              </div>
            </div>
            <el-empty v-else description="暂无配套资料" />
          </el-tab-pane>

          <!-- 反馈 -->
          <el-tab-pane label="反馈" name="feedback">
            <div class="feedback-form">
              <el-form label-position="top">
                <el-form-item label="反馈类型">
                  <el-select value="课程问题" disabled>
                    <el-option label="课程问题" value="course" />
                  </el-select>
                </el-form-item>
                <el-form-item label="反馈内容">
                  <el-input
                    v-model="feedbackForm.content"
                    type="textarea"
                    :rows="5"
                    :maxlength="500"
                    show-word-limit
                    placeholder="请描述您遇到的问题或建议..."
                  />
                </el-form-item>
                <el-form-item label="截图（可选，最多8张）">
                  <el-upload
                    ref="uploadRef"
                    action="#"
                    list-type="picture-card"
                    :auto-upload="false"
                    :on-change="handleImageUpload"
                    :show-file-list="false"
                    accept="image/jpeg,image/png"
                  >
                    <el-icon v-if="feedbackForm.uploading" class="is-loading"><Upload /></el-icon>
                    <el-icon v-else><Plus /></el-icon>
                  </el-upload>
                  <div v-if="feedbackForm.images.length > 0" class="image-preview-list">
                    <div
                      v-for="(img, index) in feedbackForm.images"
                      :key="index"
                      class="image-preview-item"
                    >
                      <el-image :src="img" fit="cover" />
                      <div class="remove-btn" @click="handleRemoveImage(index)">
                        <el-icon><Delete /></el-icon>
                      </div>
                    </div>
                  </div>
                </el-form-item>
                <el-form-item>
                  <el-button
                    type="primary"
                    :loading="feedbackForm.submitting"
                    :disabled="feedbackForm.content.length < 10"
                    @click="handleSubmitFeedback"
                  >
                    提交反馈
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
@import '@/assets/styles/variables.scss';

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

.teacher-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.teacher-name {
  font-size: $font-size-base;
  color: $text-secondary;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.tag-item {
  margin-left: 0;
}

.view-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: $font-size-sm;
  color: $text-tertiary;
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
}

// 章节目录
.outline-header {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 16px;
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
    gap: 8px;
    padding: 16px;
    background: $bg-color;
    cursor: pointer;
    user-select: none;

    &:hover {
      background: darken($bg-color, 3%);
    }

    .expand-icon {
      transition: transform 0.2s ease;

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
    padding: 0 16px 16px;
  }

  .section-item {
    padding: 12px;
    border-radius: $radius-sm;
    cursor: pointer;

    &:hover {
      background: $bg-color;
    }
  }

  .section-info {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;

    .section-title {
      font-weight: 500;
      color: $text-primary;
    }

    .resource-count {
      font-size: $font-size-xs;
      color: $text-tertiary;
    }
  }

  .resource-list {
    padding-left: 16px;
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
}

// 课程简介
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

// 反馈表单
.feedback-form {
  max-width: 600px;
  padding: 24px 0;
}

.image-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.image-preview-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: $radius-sm;
  overflow: hidden;

  .el-image {
    width: 100%;
    height: 100%;
  }

  .remove-btn {
    position: absolute;
    top: 4px;
    right: 4px;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.5);
    border-radius: 50%;
    color: white;
    cursor: pointer;

    &:hover {
      background: rgba(0, 0, 0, 0.7);
    }
  }
}
</style>