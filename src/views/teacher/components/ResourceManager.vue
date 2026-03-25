<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, VideoPlay, Headset, Document, Picture, Delete } from '@element-plus/icons-vue'
import {
  uploadResource,
  deleteResource,
  uploadFile,
  initChunkUpload,
  uploadChunk,
  completeChunkUpload,
  type ResourceItem,
} from '@/api/teacher'

// Props
interface Props {
  courseId: number
  sectionId: number
  resources: ResourceItem[]
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  (e: 'update', sectionId: number, resources: ResourceItem[]): void
}>()

// 本地资源列表
const localResources = ref<ResourceItem[]>([...props.resources])

// 上传中状态
const uploading = ref(false)

// 上传进度
const uploadProgress = ref<Record<string, number>>({})

// 资源类型映射
const resourceTypeMap: Record<string, { icon: typeof VideoPlay; color: string; text: string }> = {
  video: { icon: VideoPlay, color: '#52c41a', text: '视频' },
  audio: { icon: Headset, color: '#1890ff', text: '音频' },
  document: { icon: Document, color: '#faad14', text: '文档' },
  image: { icon: Picture, color: '#f5222d', text: '图片' },
}

// 格式化文件大小
function formatFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

// 格式化时长
function formatDuration(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 获取资源类型
function getResourceType(file: File): 'video' | 'audio' | 'document' | 'image' {
  const type = file.type
  if (type.startsWith('video/')) return 'video'
  if (type.startsWith('audio/')) return 'audio'
  if (type.startsWith('image/')) return 'image'
  return 'document'
}

// 处理文件上传
async function handleUpload(options: { file: File }) {
  const file = options.file
  const fileId = Date.now() + '-' + Math.random().toString(36).slice(2)

  // 校验文件类型
  const validTypes = [
    'video/mp4', 'video/webm', 'video/ogg',
    'audio/mpeg', 'audio/wav', 'audio/ogg',
    'application/pdf',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'image/jpeg', 'image/png', 'image/gif',
  ]
  if (!validTypes.includes(file.type)) {
    ElMessage.warning('不支持的文件格式')
    return
  }

  // 校验文件大小（最大 500MB）
  if (file.size > 500 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过 500MB')
    return
  }

  uploading.value = true
  uploadProgress.value[fileId] = 0

  try {
    let fileUrl: string

    // 大于 100MB 使用分片上传
    if (file.size > 100 * 1024 * 1024) {
      fileUrl = await handleChunkUpload(file, fileId)
    } else {
      // 普通上传
      const result = await uploadFile(file)
      fileUrl = result.file_url
      uploadProgress.value[fileId] = 100
    }

    // 创建资源记录
    const resourceType = getResourceType(file)
    const newResource = await uploadResource(props.courseId, props.sectionId, {
      resource_type: resourceType,
      file_name: file.name,
      file_url: fileUrl,
      file_size: file.size,
    })

    localResources.value.push(newResource)
    emit('update', props.sectionId, [...localResources.value])
    ElMessage.success('资源上传成功')

  } catch (error) {
    ElMessage.error('资源上传失败')
  } finally {
    uploading.value = false
    delete uploadProgress.value[fileId]
  }
}

// 分片上传
async function handleChunkUpload(file: File, fileId: string): Promise<string> {
  const chunkSize = 10 * 1024 * 1024 // 10MB
  const totalChunks = Math.ceil(file.size / chunkSize)

  // 初始化分片上传
  const initResult = await initChunkUpload({
    file_name: file.name,
    file_size: file.size,
    chunk_size: chunkSize,
  })

  const uploadId = initResult.upload_id

  // 上传分片（并发 3 个）
  const uploadedChunks: number[] = []
  const uploadQueue: Promise<void>[] = []
  let activeUploads = 0

  const uploadOneChunk = async (chunkIndex: number) => {
    const start = chunkIndex * chunkSize
    const end = Math.min(start + chunkSize, file.size)
    const chunk = file.slice(start, end)

    await uploadChunk(uploadId, chunkIndex, chunk)
    uploadedChunks.push(chunkIndex)
    uploadProgress.value[fileId] = Math.round((uploadedChunks.length / totalChunks) * 100)
    activeUploads--
  }

  for (let i = 0; i < totalChunks; i++) {
    while (activeUploads >= 3) {
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    activeUploads++
    uploadQueue.push(uploadOneChunk(i))
  }

  await Promise.all(uploadQueue)

  // 完成上传
  const result = await completeChunkUpload({
    upload_id: uploadId,
    file_name: file.name,
    total_chunks: totalChunks,
  })

  return result.file_url
}

// 删除资源
async function handleDelete(resource: ResourceItem) {
  try {
    await deleteResource(props.courseId, props.sectionId, resource.resource_id)

    localResources.value = localResources.value.filter(r => r.resource_id !== resource.resource_id)
    emit('update', props.sectionId, [...localResources.value])
    ElMessage.success('资源已删除')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}
</script>

<template>
  <div class="resource-manager">
    <!-- 上传区域 -->
    <el-upload
      class="upload-area"
      drag
      multiple
      :auto-upload="true"
      :http-request="handleUpload"
      :show-file-list="false"
      accept=".mp4,.webm,.mp3,.wav,.pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png,.gif"
    >
      <el-icon class="upload-icon"><Upload /></el-icon>
      <div class="upload-text">
        拖拽或<em>点击上传</em>学习资源
      </div>
      <template #tip>
        <div class="upload-tip">
          支持视频、音频、文档、图片格式，单个文件最大 500MB
        </div>
      </template>
    </el-upload>

    <!-- 资源列表 -->
    <div v-if="localResources.length > 0" class="resource-list">
      <div
        v-for="resource in localResources"
        :key="resource.resource_id"
        class="resource-item"
      >
        <!-- 类型图标 -->
        <el-icon class="type-icon" :style="{ color: resourceTypeMap[resource.resource_type]?.color }">
          <component :is="resourceTypeMap[resource.resource_type]?.icon || Document" />
        </el-icon>

        <!-- 文件信息 -->
        <div class="file-info">
          <span class="file-name">{{ resource.file_name }}</span>
          <div class="file-meta">
            <span>{{ resourceTypeMap[resource.resource_type]?.text || '文件' }}</span>
            <span>{{ formatFileSize(resource.file_size) }}</span>
            <span v-if="resource.duration">{{ formatDuration(resource.duration) }}</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <el-button text size="small" type="danger" :icon="Delete" @click="handleDelete(resource)">
          删除
        </el-button>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无学习资源" :image-size="60" />
  </div>
</template>

<style lang="scss" scoped>
@import '@/assets/styles/variables.scss';

.resource-manager {
  .upload-area {
    margin-bottom: 20px;

    :deep(.el-upload-dragger) {
      padding: 30px;
      border: 2px dashed $border-color;
      border-radius: $radius-md;

      &:hover {
        border-color: $primary-color;
      }
    }

    .upload-icon {
      font-size: 48px;
      color: $text-tertiary;
    }

    .upload-text {
      margin-top: 8px;
      color: $text-secondary;

      em {
        color: $primary-color;
        font-style: normal;
      }
    }

    .upload-tip {
      margin-top: 8px;
      font-size: $font-size-xs;
      color: $text-tertiary;
    }
  }
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resource-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: $bg-color;
  border-radius: $radius-sm;

  .type-icon {
    font-size: 24px;
  }

  .file-info {
    flex: 1;
    min-width: 0;

    .file-name {
      display: block;
      font-weight: 500;
      color: $text-primary;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .file-meta {
      display: flex;
      gap: 12px;
      font-size: $font-size-xs;
      color: $text-tertiary;
      margin-top: 4px;
    }
  }
}
</style>