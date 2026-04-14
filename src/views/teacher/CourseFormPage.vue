<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Upload, Delete, Back } from '@element-plus/icons-vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'
import {
  fetchCourseDetail,
  fetchChapters,
  fetchSections,
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
  type TagItem,
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

// 裁切状态
const cropVisible = ref(false)
const currentCropImage = ref('')
const currentCropFileName = ref('')
const imageRef = ref<HTMLImageElement>()
let cropper: Cropper | null = null

// 表单数据
const form = ref({
  title: '',
  cover_url: '',
  summary: '',
  description: '',
  category_id: null as number | null,
  author: '',
  tags: [] as number[], // 改为存储 tag_id
})

// 表单引用
const formRef = ref()

// 分类列表
const categories = ref<CategoryItem[]>([])

// 标签库列表
const tags = ref<TagItem[]>([])

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
    { min: 2, max: 30, message: '标题长度在 2-30 个字符', trigger: 'blur' },
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
  tags: [
    { type: 'array', required: true, message: '请至少添加一个课程标签', trigger: 'change' }
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
    // 兼容后端不同字段名
    detail.course_id = detail.course_id || (detail as any).id
    courseDetail.value = detail

    // 填充表单
    form.value.title = detail.title
    form.value.cover_url = detail.cover_url
    form.value.summary = detail.summary || ''
    form.value.description = detail.description || ''
    form.value.category_id = detail.category_id
    form.value.author = detail.author || ''
    
    // 加载标签回显
    const loadedTags = detail.tags || []
    form.value.tags = loadedTags.map((t: any) => typeof t === 'number' ? t : (t.id || t.tag_id))

    if (detail.chapters && detail.chapters.length > 0) {
      chapters.value = detail.chapters
    } else {
      // 如果详情接口没返回章节，主动获取
      const chapterList = await fetchChapters(courseId.value)
      
      // 遍历获取每个章节下的小节
      const chaptersWithSections = await Promise.all((chapterList || []).map(async (ch: any) => {
        try {
          const sections = await fetchSections(courseId.value, ch.chapter_id || ch.id)
          return {
            ...ch,
            chapter_id: ch.chapter_id || ch.id,
            sections: sections || []
          }
        } catch (e) {
          return {
            ...ch,
            chapter_id: ch.chapter_id || ch.id,
            sections: []
          }
        }
      }))
      
      chapters.value = chaptersWithSections
    }
    
    materials.value = detail.materials || []
  } catch (error) {
    ElMessage.error('加载课程详情失败')
    router.push('/teacher/courses')
  } finally {
    isLoading.value = false
  }
}

// 封面图片加载
function handleCoverChange(uploadFile: any) {
  const file = uploadFile.raw
  if (!file) return

  const validTypes = ['image/jpeg', 'image/png']
  if (!validTypes.includes(file.type)) {
    ElMessage.warning('仅支持 JPG/PNG 格式')
    return
  }

  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片最大 10MB')
    return
  }

  currentCropFileName.value = file.name || 'cover.jpg'
  currentCropImage.value = URL.createObjectURL(file)
  cropVisible.value = true
}

function initCropper() {
  if (imageRef.value) {
    cropper = new Cropper(imageRef.value, {
      aspectRatio: 16 / 9,
      viewMode: 1,
      dragMode: 'move',
      background: false,
    })
  }
}

function destroyCropper() {
  if (cropper) {
    cropper.destroy()
    cropper = null
  }
  if (currentCropImage.value) {
    URL.revokeObjectURL(currentCropImage.value)
    currentCropImage.value = ''
  }
}

function confirmCrop() {
  if (!cropper) return
  isUploading.value = true
  cropper.getCroppedCanvas({
    width: 1280,
    height: 720,
    fillColor: '#fff',
  }).toBlob(async (blob: Blob | null) => {
    if (!blob) {
      ElMessage.error('裁切失败')
      isUploading.value = false
      return
    }
    const file = new File([blob], currentCropFileName.value, { type: 'image/jpeg' })
    try {
      const result = await uploadFile(file)
      form.value.cover_url = result.file_url
      ElMessage.success('封面上传成功')
      cropVisible.value = false
    } catch (error) {
      ElMessage.error('封面上传失败')
    } finally {
      isUploading.value = false
    }
  }, 'image/jpeg', 0.9)
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

  let tag = tags.value.find(t => t.name === tagName)
  
  if (!tag) {
    try {
      const result = await createTag({ name: tagName })
      tag = result
      tags.value.push(result)
    } catch (error) {
      await loadTags()
      tag = tags.value.find(t => t.name === tagName)
    }
  }

  if (tag) {
    if (form.value.tags.includes(tag.id)) {
      ElMessage.warning('标签已添加')
    } else {
      form.value.tags.push(tag.id)
    }
  }
  
  newTagInput.value = ''
}

function handleRemoveTag(index: number) {
  form.value.tags.splice(index, 1)
}

function toggleAvailableTag(tag: TagItem) {
  const index = form.value.tags.indexOf(tag.id)
  if (index > -1) {
    form.value.tags.splice(index, 1)
  } else {
    if (form.value.tags.length >= 5) {
      ElMessage.warning('最多添加 5 个标签')
      return
    }
    form.value.tags.push(tag.id)
  }
}

function getTagName(tagId: number) {
  return tags.value.find(t => t.id === tagId)?.name || `Tag-${tagId}`
}

async function handleMaterialUpload(options: { file: File }) {
  if (!courseId.value) {
    ElMessage.warning('请先保存课程后再上传资料')
    return
  }
  const file = options.file
  const validTypes = [
    'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv',
    'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/markdown', 'text/plain', 'application/zip', 'application/x-zip-compressed',
  ]
  if (!validTypes.includes(file.type) && !file.name.endsWith('.md') && !file.name.endsWith('.csv')) {
    ElMessage.warning('仅支持 PDF、Word、PPT、Excel、Markdown、ZIP 等格式')
    return
  }
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

function formatFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function validateCourseForm() {
  try {
    await formRef.value.validate()
    return true
  } catch {
    ElMessage.warning('请完善必填信息')
    return false
  }
}

function checkPublishReady() {
  const missing: string[] = []
  if (!form.value.title) missing.push('课程标题')
  if (!form.value.cover_url) missing.push('课程封面')
  if (!form.value.summary) missing.push('课程简介')
  if (!form.value.category_id) missing.push('课程分类')
  if (chapters.value.length === 0) missing.push('至少 1 个章节')
  const hasResources = chapters.value.some(ch =>
    (ch.resources && ch.resources.length > 0) ||
    (ch.sections && ch.sections.some(s => s.resources && s.resources.length > 0))
  )
  if (!hasResources) missing.push('至少 1 个学习资源')
  return {
    canPublish: missing.length === 0,
    missingItems: missing,
  }
}

async function handleSaveDraft() {
  const isValid = await validateCourseForm()
  if (!isValid) return false
  isSaving.value = true
  try {
    const data = {
      title: form.value.title,
      cover_url: form.value.cover_url,
      summary: form.value.summary,
      description: form.value.description || undefined,
      category_id: form.value.category_id!,
      author: form.value.author || undefined,
      tag_ids: form.value.tags.length > 0 ? form.value.tags : undefined,
    }
    let result: TeacherCourseDetail
    if (isEdit.value && courseId.value) {
      result = await updateCourse(courseId.value, data)
    } else {
      result = await createCourse(data)
      const resolvedCourseId = result.course_id || (result as any).id
      if (resolvedCourseId) {
        router.replace(`/teacher/courses/${resolvedCourseId}/edit`)
      }
    }
    courseDetail.value = {
      ...result,
      course_id: result.course_id || (result as any).id
    }
    ElMessage.success('保存成功')
    return true
  } catch (error) {
    ElMessage.error('保存失败')
    return false
  } finally {
    isSaving.value = false
  }
}

async function handleSaveAndPublish() {
  const isValid = await validateCourseForm()
  if (!isValid) return
  const check = checkPublishReady()
  if (!check.canPublish) {
    ElMessage.warning(`以下内容缺失，无法发布：${check.missingItems.join('、')}`)
    return
  }
  const saveSuccess = await handleSaveDraft()
  if (!saveSuccess) return
  const finalId = courseDetail.value?.course_id || (courseDetail.value as any)?.id || courseId.value
  if (!finalId) {
    ElMessage.error('请先保存课程')
    return
  }
  try {
    await publishCourse(finalId)
    ElMessage.success('课程已发布')
    router.push('/teacher/courses')
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

function handleBack() {
  router.push('/teacher/courses')
}

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
    <div class="page-header">
      <el-button text :icon="Back" @click="handleBack">返回列表</el-button>
      <h2 class="page-title">{{ pageTitle }}</h2>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      class="course-form"
    >
      <el-form-item label="课程标题" prop="title">
        <el-input
          v-model="form.title"
          placeholder="请输入课程标题"
          maxlength="30"
          show-word-limit
          style="width: 240px"
        />
      </el-form-item>

      <el-form-item label="课程封面" prop="cover_url">
        <div class="cover-uploader">
          <el-upload
            class="cover-upload"
            :show-file-list="false"
            :auto-upload="false"
            :on-change="handleCoverChange"
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

      <el-form-item label="课程分类" prop="category_id">
        <el-select v-model="form.category_id" placeholder="请选择分类" style="width: 240px">
          <el-option
            v-for="category in categories"
            :key="category.category_id"
            :label="category.name"
            :value="category.category_id"
          />
        </el-select>
      </el-form-item>

      <!-- 讲师信息 -->
      <el-form-item label="讲师" prop="author">
        <el-input
          v-model="form.author"
          placeholder="请输入讲师名称（可选）"
          maxlength="20"
          show-word-limit
          style="width: 240px"
        />
      </el-form-item>

      <el-form-item label="课程标签" prop="tags">
        <div class="tag-input-area">
          <div class="tag-list" v-if="form.tags.length > 0">
            <el-tag
              v-for="(tagId, index) in form.tags"
              :key="index"
              closable
              round
              type="primary"
              size="large"
              @close="handleRemoveTag(index)"
            >
              {{ getTagName(tagId) }}
            </el-tag>
          </div>
          <div class="tag-add" v-if="form.tags.length < 5">
            <el-input
              v-model="newTagInput"
              placeholder="输入标签后按回车添加"
              style="width: 220px"
              @keyup.enter="handleAddTag"
            />
            <el-button type="primary" :icon="Plus" plain @click="handleAddTag">添加标签</el-button>
          </div>
          <div class="tag-tip" v-if="form.tags.length >= 5">
            温馨提示：已达到 5 个标签上限，可以点击标签上的 'x' 删除后再添加。
          </div>
          
          <div class="available-tags-box" v-if="tags.length > 0">
            <div class="available-title">可选标签池（点击即可快速添加或移除）</div>
            <div class="available-tags-list">
              <el-tag
                v-for="tag in tags"
                :key="tag.id"
                :type="form.tags.includes(tag.id) ? 'primary' : 'info'"
                :effect="form.tags.includes(tag.id) ? 'dark' : 'plain'"
                round
                class="available-tag-item"
                :class="{ 'is-selected': form.tags.includes(tag.id) }"
                @click="toggleAvailableTag(tag)"
              >
                {{ tag.name }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-form-item>

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

      <el-form-item label="课程描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="6"
          placeholder="请输入课程详细描述（可选）"
        />
      </el-form-item>

      <el-divider content-position="left">课程全局资料区</el-divider>

      <el-form-item label="配套资料" v-if="isEdit && courseId">
        <el-upload
          class="material-upload"
          :show-file-list="false"
          :http-request="handleMaterialUpload"
          accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.csv,.md,.txt,.zip"
        >
          <el-button type="primary" plain :icon="Upload">上传资料</el-button>
        </el-upload>
        <div class="material-tip">上传课程大纲或全局参考资料（支持 PDF、PPT、Word、Excel、Markdown、ZIP 等），单个文件最大 50MB，最多 10 个</div>

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

      <el-form-item class="form-actions">
        <el-button @click="handleBack">返回列表</el-button>
        <el-button type="primary" plain :loading="isSaving" @click="handleSaveDraft()">
          保存草稿
        </el-button>
        <el-button v-if="isEdit" type="primary" :loading="isSaving" @click="handleSaveAndPublish">
          保存并发布
        </el-button>
      </el-form-item>
    </el-form>

    <el-dialog
      v-model="cropVisible"
      title="裁切封面"
      width="800px"
      append-to-body
      destroy-on-close
      @opened="initCropper"
      @closed="destroyCropper"
    >
      <div class="cropper-container">
        <img ref="imageRef" :src="currentCropImage" alt="crop" style="max-width: 100%; display: block;" />
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cropVisible = false">取消</el-button>
          <el-button type="primary" :loading="isUploading" @click="confirmCrop">确认裁切并上传</el-button>
        </div>
      </template>
    </el-dialog>
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
    width: 240px;
    height: 135px;
    border: 1px dashed $border-color;
    border-radius: $radius-md;
    overflow: hidden;
    cursor: pointer;
    transition: border-color 0.2s;

    :deep(.el-upload) {
      width: 100%;
      height: 100%;
      position: relative;
      display: block;
    }

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
  width: 100%;

  .tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 16px;
    
    .el-tag {
      padding: 0 14px;
      font-size: 14px;
      height: 34px;
    }
  }

  .tag-add {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .tag-tip {
    display: block;
    font-size: 13px;
    color: #e6a23c;
    margin-top: 10px;
    background-color: #fff8e6;
    padding: 6px 12px;
    border-radius: 6px;
    width: fit-content;
  }

  .available-tags-box {
    margin-top: 24px;
    padding: 16px 20px;
    background-color: #f8f9fc;
    border-radius: 8px;
    border: 1px dashed #dcdfe6;

    .available-title {
      font-size: 14px;
      font-weight: 500;
      color: #606266;
      margin-bottom: 16px;
      position: relative;
      padding-left: 10px;
      
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 14px;
        background-color: var(--el-color-primary);
        border-radius: 2px;
      }
    }

    .available-tags-list {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      max-height: 140px;
      overflow-y: auto;
      padding-right: 4px;

      &::-webkit-scrollbar {
        width: 6px;
      }
      &::-webkit-scrollbar-thumb {
        background-color: #c0c4cc;
        border-radius: 3px;
      }
      &::-webkit-scrollbar-track {
        background: transparent;
      }

      .available-tag-item {
        cursor: pointer;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        user-select: none;
        padding: 0 14px;
        height: 30px;
        line-height: 28px;
        font-size: 13px;
        border-radius: 15px;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
          &:not(.is-selected) {
            color: var(--el-color-primary);
            border-color: var(--el-color-primary-light-5);
            background-color: var(--el-color-primary-light-9);
          }
        }

        &.is-selected {
          font-weight: 500;
          transform: scale(1.02);
          box-shadow: 0 2px 6px rgba(var(--el-color-primary-rgb), 0.3);
        }
      }
    }
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

.cropper-container {
  width: 100%;
  height: 400px;
  background-color: #f0f2f5;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.form-actions {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid $border-color-light;
}
</style>
