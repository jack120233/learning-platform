<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchTeacherOptions, submitFeedback, uploadFeedbackImage } from '@/api/learning'
import type { TeacherOption } from '@/api/learning'
import type { UploadFile } from 'element-plus'

// Props
interface Props {
  /** 嵌入模式：inline（内联） | dialog（弹窗） */
  mode?: 'inline' | 'dialog'
  /** 预设反馈类型 */
  defaultType?: 'system' | 'course'
  /** 是否锁定反馈类型 */
  typeLocked?: boolean
  /** 关联课程 ID */
  courseId?: number
  /** 关联课程名称 */
  courseName?: string
  /** 当前课程老师 ID */
  courseTeacherId?: number
  /** 当前课程老师名称 */
  courseTeacherName?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'inline',
  defaultType: 'system',
  typeLocked: false,
})

// Emits
const emit = defineEmits<{
  (e: 'success'): void
  (e: 'cancel'): void
}>()

// 表单数据
const form = reactive({
  feedback_type: props.defaultType as 'system' | 'course',
  target_user_id: props.courseTeacherId,
  content: '',
  images: [] as string[],
})

// 表单引用
const formRef = ref()

// 提交状态
const submitting = ref(false)

// 上传文件列表
const uploadFiles = ref<UploadFile[]>([])

// 上传中数量
const uploadingCount = ref(0)

// 是否显示课程选择
const showCourseSelect = computed(() => form.feedback_type === 'course')

const teacherOptions = ref<TeacherOption[]>([])
const loadingTeachers = ref(false)

const normalizedTeacherOptions = computed(() => {
  const options = [...teacherOptions.value]
  if (
    props.courseTeacherId
    && !options.some((teacher) => teacher.teacher_id === props.courseTeacherId)
  ) {
    options.unshift({
      teacher_id: props.courseTeacherId,
      username: props.courseTeacherName || `老师 ${props.courseTeacherId}`,
      nickname: props.courseTeacherName || null,
      avatar: null,
    })
  }
  return options
})

// 反馈类型选项
const feedbackTypes = [
  { label: '系统问题', value: 'system' },
  { label: '课程问题', value: 'course' },
]

const currentFeedbackTypeLabel = computed(() =>
  feedbackTypes.find((type) => type.value === form.feedback_type)?.label ?? form.feedback_type
)

// 表单校验规则
const rules = {
  feedback_type: [
    { required: true, message: '请选择反馈类型', trigger: 'change' },
  ],
  target_user_id: [
    { required: true, message: '请选择反馈老师', trigger: 'change' },
  ],
  content: [
    { required: true, message: '请输入反馈内容', trigger: 'blur' },
    { min: 10, message: '反馈内容至少 10 个字符', trigger: 'blur' },
    { max: 500, message: '反馈内容最多 500 个字符', trigger: 'blur' },
  ],
}

async function loadTeacherOptions() {
  if (!showCourseSelect.value) return
  loadingTeachers.value = true
  try {
    teacherOptions.value = await fetchTeacherOptions()
    if (!form.target_user_id && props.courseTeacherId) {
      form.target_user_id = props.courseTeacherId
    }
  } catch (error) {
    ElMessage.error('老师列表加载失败')
  } finally {
    loadingTeachers.value = false
  }
}

watch(() => props.courseTeacherId, (teacherId) => {
  if (showCourseSelect.value && teacherId && !form.target_user_id) {
    form.target_user_id = teacherId
  }
}, { immediate: true })

watch(showCourseSelect, (visible) => {
  if (visible) {
    void loadTeacherOptions()
  } else {
    form.target_user_id = undefined
  }
}, { immediate: true })

// 图片上传前校验
function beforeUpload(file: File): boolean {
  // 校验文件类型
  const validTypes = ['image/jpeg', 'image/png']
  if (!validTypes.includes(file.type)) {
    ElMessage.warning('仅支持 JPG/PNG 格式')
    return false
  }

  // 校验文件大小（最大 5MB）
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('单张图片最大 5MB')
    return false
  }

  // 校验数量
  if (form.images.length >= 8) {
    ElMessage.warning('最多上传 8 张截图')
    return false
  }

  return true
}

// 自定义上传
async function handleUpload(options: { file: File }) {
  if (!beforeUpload(options.file)) return

  uploadingCount.value++
  try {
    const result = await uploadFeedbackImage(options.file)
    form.images.push(result.file_url)
  } catch (error) {
    // 错误已处理
  } finally {
    uploadingCount.value--
  }
}

// 移除图片
function handleRemove(file: UploadFile) {
  const index = uploadFiles.value.findIndex((f) => f.uid === file.uid)
  if (index > -1) {
    uploadFiles.value.splice(index, 1)
    form.images.splice(index, 1)
  }
}

// 提交反馈
async function handleSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    await submitFeedback({
      feedback_type: form.feedback_type,
      course_id: showCourseSelect.value ? props.courseId : undefined,
      target_user_id: showCourseSelect.value ? form.target_user_id : undefined,
      content: form.content,
      images: form.images.length > 0 ? form.images : undefined,
    })

    ElMessage.success('反馈已提交，感谢您的反馈')

    // 重置表单
    resetForm()

    // 触发成功事件
    emit('success')
  } catch (error) {
    // 错误已处理
  } finally {
    submitting.value = false
  }
}

// 重置表单
function resetForm() {
  form.feedback_type = props.defaultType
  form.target_user_id = props.defaultType === 'course' ? props.courseTeacherId : undefined
  form.content = ''
  form.images = []
  uploadFiles.value = []
  formRef.value?.resetFields()
}

// 取消
function handleCancel() {
  emit('cancel')
}
</script>

<template>
  <div class="feedback-form" :class="mode">
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
    >
      <!-- 反馈类型 -->
      <el-form-item label="反馈类型" prop="feedback_type">
        <div v-if="typeLocked" class="readonly-type-field">
          <span class="readonly-type-label">{{ currentFeedbackTypeLabel }}</span>
        </div>
        <el-select
          v-else
          v-model="form.feedback_type"
          placeholder="请选择反馈类型"
          style="width: 100%"
        >
          <el-option
            v-for="type in feedbackTypes"
            :key="type.value"
            :label="type.label"
            :value="type.value"
          />
        </el-select>
      </el-form-item>

      <!-- 关联课程（课程问题时显示） -->
      <el-form-item v-if="showCourseSelect && courseName" label="关联课程">
        <el-input :model-value="courseName" readonly>
          <template #prepend>
            <el-icon><Link /></el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item v-if="showCourseSelect" label="反馈给老师" prop="target_user_id">
        <el-select
          v-model="form.target_user_id"
          placeholder="请选择要反馈的老师"
          :loading="loadingTeachers"
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="teacher in normalizedTeacherOptions"
            :key="teacher.teacher_id"
            :label="teacher.nickname || teacher.username"
            :value="teacher.teacher_id"
          >
            <span>{{ teacher.nickname || teacher.username }}</span>
            <span v-if="teacher.teacher_id === courseTeacherId" class="teacher-option-tag">当前课程老师</span>
          </el-option>
        </el-select>
      </el-form-item>

      <!-- 反馈内容 -->
      <el-form-item label="反馈内容" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="5"
          :maxlength="500"
          show-word-limit
          placeholder="请详细描述您遇到的问题（10-500 字符）"
        />
      </el-form-item>

      <!-- 截图上传 -->
      <el-form-item label="截图上传（可选）">
        <el-upload
          v-model:file-list="uploadFiles"
          list-type="picture-card"
          :limit="8"
          accept=".jpg,.jpeg,.png"
          :http-request="handleUpload"
          :on-remove="handleRemove"
        >
          <el-icon><Plus /></el-icon>
          <template #tip>
            <div class="upload-tip">
              支持 JPG/PNG，单张最大 5MB，最多 8 张
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <!-- 操作按钮 -->
      <el-form-item class="form-actions">
        <div class="soft-action-surface feedback-action-surface">
          <el-button
            class="soft-action-btn soft-action-btn--primary"
            type="primary"
            :loading="submitting || uploadingCount > 0"
            @click="handleSubmit"
          >
            提交反馈
          </el-button>
          <el-button
            v-if="mode === 'dialog'"
            class="soft-action-btn soft-action-btn--secondary"
            @click="handleCancel"
          >
            取消
          </el-button>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<style lang="scss" scoped>
.feedback-form {
  &.dialog {
    padding: 0;
  }

  &.inline {
    padding: 20px;
    background: #fafafa;
    border-radius: 8px;
  }
}

.readonly-type-field {
  display: flex;
  align-items: center;
  width: 100%;
  min-height: 44px;
  padding: 10px 14px;
  background: #f4f7fb;
  border: 1px solid #dbe5f0;
  border-radius: 10px;
}

.readonly-type-label {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  background: #e8f1ff;
  color: #1d4ed8;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
}

.teacher-option-tag {
  float: right;
  color: #409eff;
  font-size: 12px;
}

.upload-tip {
  font-size: 12px;
  color: #999;
  line-height: 1.4;
}

.form-actions {
  margin-bottom: 0;
  margin-top: 8px;
}

.feedback-action-surface {
  width: fit-content;
}

@media (max-width: 768px) {
  .feedback-action-surface {
    width: 100%;
  }
}
</style>
