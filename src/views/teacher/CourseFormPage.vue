<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Upload, Delete, Back } from '@element-plus/icons-vue'
import {
  fetchCourseDetail,
  createCourse,
  updateCourse,
  publishCourse,
  uploadFile,
  uploadMaterial,
  deleteMaterial,
  fetchTags,
  createTag,
  type TeacherCourseDetail,
  type ChapterItem,
  type MaterialItem,
} from '@/api/teacher'
import { fetchCategories, type CategoryItem } from '@/api/category'
import ChapterManager from './components/ChapterManager.vue'

const route = useRoute()
const router = useRouter()

// 是否为编辑模式
const isEdit = computed(() => !!route.params.courseId)
const courseId = computed(() => Number(route.params.courseId))

// 页面标题
const pageTitle = computed(() => isEdit.value ? '编辑课程' : '创建课程')

// 加载状态
const isLoading = ref(false)
const isSaving = ref(false)
const isUploading = ref(false)

// 表单数据
const form = ref({
  title: '',
  cover_url: '',
  summary: '',
  description: '',
  category_id: null as number | null,
  tags: [] as string[],
})

// 表单引用
const formRef = ref()

// 分类列表
const categories = ref<CategoryItem[]>([])

// 标签列表
const tags = ref<string[]>([])

// 新标签输入
const newTagInput = ref('')

// 章节数据
const chapters = ref<ChapterItem[]>([])

// 配套资料
const materials = ref<MaterialItem[]>([])

// 课程详情（编辑模式）
const courseDetail = ref<TeacherCourseDetail | null>(null)

// 表单校验规则
const rules = {
  title: [
    { required: true, message: '请输入课程标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度在 2-100 个字符', trigger: 'blur' },
  ],
  cover_url: [
    { required: true, message: '请上传课程封面', trigger: 'change' },
  ],
  summary: [
    { required: true, message: '请输入课程简介', trigger: 'blur' },
    { min: 10, max: 500, message: '简介长度在 10-500 个字符', trigger: 'blur' },
  ],
  category_id: [
    { required: true, message: '请选择课程分类', trigger: 'change' },
  ],
}

// 加载分类
async function loadCategories() {
  try {
    const result = await fetchCategories()
    categories.value = result
  } catch (error) {
    // 错误已处理
  }
}

// 加载标签
async function loadTags() {
  try {
    const result = await fetchTags()
    tags.value = result
  } catch (error) {
    // 错误已处理
  }
}

// 加载课程详情
async function loadCourseDetail() {
  if (!courseId.value) return

  isLoading.value = true
  try {
    const detail = await fetchCourseDetail(courseId.value)
    courseDetail.value = detail

    // 填充表单
    form.value.title = detail.title
    form.value.cover_url = detail.cover_url
    form.value.summary = detail.summary
    form.value.description = detail.description || ''
    form.value.category_id = detail.category_id
    form.value.tags = detail.tags || []

    chapters.value = detail.chapters || []
    materials.value = detail.materials || []
  } catch (error) {
    ElMessage.error('加载课程详情失败')
    router.push('/teacher/courses')
  } finally {
    isLoading.value = false
  }
}

// 封面上传
async function handleCoverUpload(options: { file: File }) {
  const file = options.file

  // 校验文件类型
  const validTypes = ['image/jpeg', 'image/png']
  if (!validTypes.includes(file.type)) {
    ElMessage.warning('仅支持 JPG/PNG 格式')
    return
  }

  // 校验文件大小
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片最大 10MB')
    return
  }

  isUploading.value = true
  try {
    const result = await uploadFile(file)
    form.value.cover_url = result.file_url
    ElMessage.success('封面上传成功')
  } catch (error) {
    ElMessage.error('封面上传失败')
  } finally {
    isUploading.value = false
  }
}

// 添加标签
async function handleAddTag() {
  const tagName = newTagInput.value.trim()
  if (!tagName) return

  if (form.value.tags.length >= 5) {
    ElMessage.warning('最多添加 5 个标签')
    newTagInput.value = ''
    return
  }

  if (form.value.tags.includes(tagName)) {
    ElMessage.warning('标签已存在')
    return
  }

  // 添加到本地标签列表
  if (!tags.value.includes(tagName)) {
    try {
      await createTag({ name: tagName })
      tags.value.push(tagName)
    } catch (error) {
      // 标签可能已存在，忽略错误
    }
  }

  form.value.tags.push(tagName)
  newTagInput.value = ''
}

// 移除标签
function handleRemoveTag(index: number) {
  form.value.tags.splice(index, 1)
}

// 上传配套资料
async function handleMaterialUpload(options: { file: File }) {
  if (!courseId.value) {
    ElMessage.warning('请先保存课程后再上传资料')
    return
  }

  const file = options.file

  // 校验文件类型
  const validTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/zip',
    'application/x-zip-compressed',
  ]
  if (!validTypes.includes(file.type)) {
    ElMessage.warning('仅支持 PDF、Word、ZIP 格式')
    return
  }

  // 校验文件大小
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.warning('文件最大 50MB')
    return
  }

  try {
    const result = await uploadMaterial(courseId.value, file)
    materials.value.push(result)
    ElMessage.success('资料上传成功')
  } catch (error) {
    ElMessage.error('资料上传失败')
  }
}

// 删除配套资料
async function handleDeleteMaterial(material: MaterialItem) {
  if (!courseId.value) return

  try {
    await deleteMaterial(courseId.value, material.material_id)
    materials.value = materials.value.filter(m => m.material_id !== material.material_id)
    ElMessage.success('资料已删除')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// 格式化文件大小
function formatFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 检查是否可以发布
function checkPublishReady() {
  const missing: string[] = []

  if (!form.value.title) missing.push('课程标题')
  if (!form.value.cover_url) missing.push('课程封面')
  if (!form.value.summary) missing.push('课程简介')
  if (!form.value.category_id) missing.push('课程分类')
  if (chapters.value.length === 0) missing.push('至少 1 个章节')

  const hasSections = chapters.value.some(ch => ch.sections?.length > 0)
  if (!hasSections) missing.push('至少 1 个小节')

  const hasResources = chapters.value.some(ch =>
    ch.sections?.some(s => s.resources?.length > 0)
  )
  if (!hasResources) missing.push('至少 1 个学习资源')

  return {
    canPublish: missing.length === 0,
    missingItems: missing,
  }
}

// 保存草稿
async function handleSaveDraft() {
  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请完善必填信息')
    return
  }

  isSaving.value = true
  try {
    const data = {
      title: form.value.title,
      cover_url: form.value.cover_url,
      summary: form.value.summary,
      description: form.value.description || undefined,
      category_id: form.value.category_id!,
      tags: form.value.tags.length > 0 ? form.value.tags : undefined,
    }

    let result: TeacherCourseDetail
    if (isEdit.value && courseId.value) {
      result = await updateCourse(courseId.value, data)
    } else {
      result = await createCourse(data)
      // 创建成功后跳转到编辑页
      router.replace(`/teacher/courses/${result.course_id}/edit`)
    }

    courseDetail.value = result
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    isSaving.value = false
  }
}

// 保存并发布
async function handleSaveAndPublish() {
  // 先保存
  await handleSaveDraft()

  // 检查是否可以发布
  const check = checkPublishReady()
  if (!check.canPublish) {
    ElMessage.warning(`以下内容缺失，无法发布：${check.missingItems.join('、')}`)
    return
  }

  if (!courseDetail.value?.course_id) {
    ElMessage.error('请先保存课程')
    return
  }

  try {
    await publishCourse(courseDetail.value.course_id)
    ElMessage.success('课程已发布')
    router.push('/teacher/courses')
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

// 返回列表
function handleBack() {
  router.push('/teacher/courses')
}

// 初始化
onMounted(async () => {
  await loadCategories()
  await loadTags()

  if (isEdit.value) {
    await loadCourseDetail()
  }
})
</script>

<template>
  <div class="course-form-page" v-loading="isLoading">
    <!-- 页面标题 -->
    <div class="page-header">
      <el-button text :icon="Back" @click="handleBack">返回列表</el-button>
      <h2 class="page-title">{{ pageTitle }}</h2>
    </div>

    <!-- 表单 -->
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      class="course-form"
    >
      <!-- 课程标题 -->
      <el-form-item label="课程标题" prop="title">
        <el-input
          v-model="form.title"
          placeholder="请输入课程标题"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <!-- 课程封面 -->
      <el-form-item label="课程封面" prop="cover_url">
        <div class="cover-uploader">
          <el-upload
            class="cover-upload"
            :show-file-list="false"
            :before-upload="() => false"
            :http-request="handleCoverUpload"
            accept=".jpg,.jpeg,.png"
          >
            <template v-if="form.cover_url">
              <el-image :src="form.cover_url" fit="cover" class="cover-preview" />
              <div class="cover-actions">
                <el-button size="small" :loading="isUploading">更换封面</el-button>
              </div>
            </template>
            <template v-else>
              <div class="cover-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传封面</span>
              </div>
            </template>
          </el-upload>
          <div class="cover-tip">建议 16:9 比例，JPG/PNG 格式，不超过 10MB</div>
        </div>
      </el-form-item>

      <!-- 课程分类 -->
      <el-form-item label="课程分类" prop="category_id">
        <el-select v-model="form.category_id" placeholder="请选择分类" style="width: 100%">
          <el-option
            v-for="category in categories"
            :key="category.category_id"
            :label="category.name"
            :value="category.category_id"
          />
        </el-select>
      </el-form-item>

      <!-- 课程标签 -->
      <el-form-item label="课程标签">
        <div class="tag-input-area">
          <div class="tag-list">
            <el-tag
              v-for="(tag, index) in form.tags"
              :key="tag"
              closable
              @close="handleRemoveTag(index)"
            >
              {{ tag }}
            </el-tag>
          </div>
          <div class="tag-add" v-if="form.tags.length < 5">
            <el-input
              v-model="newTagInput"
              placeholder="输入标签"
              size="small"
              style="width: 120px"
              @keyup.enter="handleAddTag"
            />
            <el-button size="small" @click="handleAddTag">添加</el-button>
          </div>
          <span class="tag-tip">最多 5 个标签</span>
        </div>
      </el-form-item>

      <!-- 课程简介 -->
      <el-form-item label="课程简介" prop="summary">
        <el-input
          v-model="form.summary"
          type="textarea"
          :rows="3"
          placeholder="请输入课程简介（10-500 字符）"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <!-- 课程描述 -->
      <el-form-item label="课程描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="6"
          placeholder="请输入课程详细描述（可选）"
        />
      </el-form-item>

      <!-- 配套资料 -->
      <el-form-item label="配套资料" v-if="isEdit && courseId">
        <el-upload
          class="material-upload"
          :show-file-list="false"
          :http-request="handleMaterialUpload"
          accept=".pdf,.doc,.docx,.zip"
        >
          <el-button type="primary" text :icon="Upload">上传资料</el-button>
        </el-upload>
        <div class="material-tip">支持 PDF、Word、ZIP 格式，单个文件最大 50MB，最多 10 个</div>

        <div v-if="materials.length > 0" class="material-list">
          <div v-for="material in materials" :key="material.material_id" class="material-item">
            <span class="material-name">{{ material.file_name }}</span>
            <span class="material-size">{{ formatFileSize(material.file_size) }}</span>
            <el-button text size="small" type="danger" :icon="Delete" @click="handleDeleteMaterial(material)">
              删除
            </el-button>
          </div>
        </div>
      </el-form-item>

      <!-- 章节目录管理 -->
      <el-divider content-position="left">课程内容管理</el-divider>

      <el-form-item v-if="isEdit && courseId">
        <ChapterManager
          :course-id="courseId"
          v-model:chapters="chapters"
        />
      </el-form-item>
      <el-form-item v-else>
        <el-alert
          type="info"
          :closable="false"
          show-icon
        >
          <template #title>
            请先保存课程基本信息后，再管理章节目录和学习资源
          </template>
        </el-alert>
      </el-form-item>

      <!-- 操作按钮 -->
      <el-form-item class="form-actions">
        <el-button @click="handleBack">返回列表</el-button>
        <el-button type="primary" plain :loading="isSaving" @click="handleSaveDraft">
          保存草稿
        </el-button>
        <el-button v-if="isEdit" type="primary" :loading="isSaving" @click="handleSaveAndPublish">
          保存并发布
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style lang="scss" scoped>

.course-form-page {
  .page-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid $border-color-light;
  }

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
  }
}

.course-form {
  max-width: 800px;
}

.cover-uploader {
  .cover-upload {
    width: 320px;
    height: 180px;
    border: 1px dashed $border-color;
    border-radius: $radius-md;
    overflow: hidden;
    cursor: pointer;
    transition: border-color 0.2s;

    &:hover {
      border-color: $primary-color;
    }
  }

  .cover-preview {
    width: 100%;
    height: 100%;
  }

  .cover-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: $text-tertiary;

    .el-icon {
      font-size: 32px;
    }
  }

  .cover-actions {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 8px;
    background: rgba(0, 0, 0, 0.5);
    text-align: center;
  }

  .cover-tip {
    margin-top: 8px;
    font-size: $font-size-xs;
    color: $text-tertiary;
  }
}

.tag-input-area {
  .tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
  }

  .tag-add {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .tag-tip {
    display: block;
    font-size: $font-size-xs;
    color: $text-tertiary;
    margin-top: 8px;
  }
}

.material-upload {
  margin-bottom: 8px;
}

.material-tip {
  font-size: $font-size-xs;
  color: $text-tertiary;
  margin-bottom: 12px;
}

.material-list {
  margin-top: 16px;
  border: 1px solid $border-color;
  border-radius: $radius-sm;
  overflow: hidden;

  .material-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid $border-color-light;

    &:last-child {
      border-bottom: none;
    }

    .material-name {
      flex: 1;
      color: $text-primary;
    }

    .material-size {
      font-size: $font-size-sm;
      color: $text-tertiary;
    }
  }
}

.form-actions {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid $border-color-light;
}
</style>