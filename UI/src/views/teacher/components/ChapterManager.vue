<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Rank, Delete, VideoPlay, Document } from '@element-plus/icons-vue'
import {
  createChapter,
  updateChapter,
  deleteChapter,
  updateChapterSort,
  createSection,
  updateSection,
  deleteSection,
  updateSectionSort,
  type ChapterItem,
  type SectionItem,
} from '@/api/teacher'
import ResourceManager from './ResourceManager.vue'
import draggable from 'vuedraggable'

// Props
interface Props {
  courseId: number
  chapters: ChapterItem[]
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  (e: 'update:chapters', chapters: ChapterItem[]): void
}>()

// 本地章节数据
const localChapters = ref<ChapterItem[]>([])

// 正在编辑的项信息
const dialogVisible = ref(false)
const dialogType = ref<'chapter' | 'section'>('chapter')
const dialogMode = ref<'add' | 'edit'>('add')
const dialogForm = ref({
  id: null as number | null,
  parentId: null as number | null, // 章节ID（添加小节时用）
  title: '',
  description: '',
})

// 展开的章节
const expandedChapters = ref<Set<number>>(new Set())

// 当前管理资源的小节或章节
const resourceParent = ref<{ id: number, type: 'chapter' | 'section', defaultTab?: 'video' | 'document' } | null>(null)

// 操作中状态
const operating = ref(false)

// 同步外部数据
watch(() => props.chapters, (newChapters) => {
  localChapters.value = (newChapters || []).map(ch => ({
    ...ch,
    chapter_id: ch.chapter_id || (ch as any).id,
    resources: ch.resources || [],
    sections: (ch.sections || []).map((s: any) => ({
      ...s,
      section_id: s.section_id || s.id,
      resources: s.resources || []
    }))
  }))
  // 默认展开所有章节
  localChapters.value.forEach(ch => {
    if (ch.chapter_id) expandedChapters.value.add(ch.chapter_id)
  })
}, { immediate: true, deep: true })

// 切换章节展开
function toggleChapter(chapterId: number) {
  if (expandedChapters.value.has(chapterId)) {
    expandedChapters.value.delete(chapterId)
  } else {
    expandedChapters.value.add(chapterId)
  }
}

// 打开添加章节对话框
function handleAddChapter() {
  dialogType.value = 'chapter'
  dialogMode.value = 'add'
  dialogForm.value = {
    id: null,
    parentId: null,
    title: '',
    description: '',
  }
  dialogVisible.value = true
}

// 开始编辑章节
function startEditChapter(chapter: ChapterItem) {
  dialogType.value = 'chapter'
  dialogMode.value = 'edit'
  dialogForm.value = {
    id: chapter.chapter_id,
    parentId: null,
    title: chapter.title,
    description: chapter.description || '',
  }
  dialogVisible.value = true
}

// 开始添加小节
function handleAddSection(chapter: ChapterItem) {
  dialogType.value = 'section'
  dialogMode.value = 'add'
  dialogForm.value = {
    id: null,
    parentId: chapter.chapter_id,
    title: '',
    description: '',
  }
  dialogVisible.value = true
}

// 开始编辑小节
function startEditSection(chapterId: number, section: SectionItem) {
  dialogType.value = 'section'
  dialogMode.value = 'edit'
  dialogForm.value = {
    id: section.section_id,
    parentId: chapterId,
    title: section.title,
    description: section.description || '',
  }
  dialogVisible.value = true
}

// 提交对话框
async function handleDialogSubmit() {
  if (!dialogForm.value.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }

  try {
    operating.value = true
    if (dialogType.value === 'chapter') {
      if (dialogMode.value === 'add') {
        const newChapter = await createChapter(props.courseId, {
          title: dialogForm.value.title.trim(),
          description: dialogForm.value.description.trim(),
          sort_order: localChapters.value.length,
        })
        const normalizedChapter: ChapterItem = {
          ...newChapter,
          chapter_id: newChapter.chapter_id || (newChapter as any).id,
          sections: newChapter.sections || [],
        }
        localChapters.value.push(normalizedChapter)
        expandedChapters.value.add(normalizedChapter.chapter_id)
        ElMessage.success('章节添加成功')
      } else {
        await updateChapter(props.courseId, dialogForm.value.id!, {
          title: dialogForm.value.title.trim(),
          description: dialogForm.value.description.trim(),
        })
        const index = localChapters.value.findIndex(ch => ch.chapter_id === dialogForm.value.id)
        if (index > -1) {
          localChapters.value[index].title = dialogForm.value.title.trim()
          localChapters.value[index].description = dialogForm.value.description.trim()
        }
        ElMessage.success('章节更新成功')
      }
    } else {
      // 小节操作
      if (dialogMode.value === 'add') {
        const newSection = await createSection(props.courseId, dialogForm.value.parentId!, {
          title: dialogForm.value.title.trim(),
          description: dialogForm.value.description.trim(),
          sort_order: 0,
        })
        const normalizedSection: SectionItem = {
          ...newSection,
          section_id: newSection.section_id || (newSection as any).id,
          resources: newSection.resources || [],
        }
        const chIndex = localChapters.value.findIndex(ch => ch.chapter_id === dialogForm.value.parentId)
        if (chIndex > -1) {
          if (!localChapters.value[chIndex].sections) localChapters.value[chIndex].sections = []
          localChapters.value[chIndex].sections.push(normalizedSection)
        }
        ElMessage.success('小节添加成功')
      } else {
        await updateSection(props.courseId, dialogForm.value.parentId!, dialogForm.value.id!, {
          title: dialogForm.value.title.trim(),
          description: dialogForm.value.description.trim(),
        })
        const chIndex = localChapters.value.findIndex(ch => ch.chapter_id === dialogForm.value.parentId)
        if (chIndex > -1) {
          const sIndex = localChapters.value[chIndex].sections.findIndex(s => s.section_id === dialogForm.value.id)
          if (sIndex > -1) {
            localChapters.value[chIndex].sections[sIndex].title = dialogForm.value.title.trim()
            localChapters.value[chIndex].sections[sIndex].description = dialogForm.value.description.trim()
          }
        }
        ElMessage.success('小节更新成功')
      }
    }
    emit('update:chapters', [...localChapters.value])
    dialogVisible.value = false
  } catch (error) {
    // 错误已处理
  } finally {
    operating.value = false
  }
}

// 章节排序
async function handleChapterSort() {
  const chapterIds = localChapters.value.map(ch => ch.chapter_id)
  try {
    operating.value = true
    await updateChapterSort(props.courseId, chapterIds)
    emit('update:chapters', [...localChapters.value])
    ElMessage.success('章节排序已更新')
  } catch (error) {
    // 错误处理已集成
  } finally {
    operating.value = false
  }
}

// 小节排序
async function handleSectionSort(chapterId: number) {
  const chapter = localChapters.value.find(ch => ch.chapter_id === chapterId)
  if (!chapter || !chapter.sections) return

  const sectionIds = chapter.sections.map(s => s.section_id)
  try {
    operating.value = true
    await updateSectionSort(props.courseId, chapterId, sectionIds)
    emit('update:chapters', [...localChapters.value])
    ElMessage.success('小节排序已更新')
  } catch (error) {
    // 错误已处理
  } finally {
    operating.value = false
  }
}

// 删除章节
async function handleDeleteChapter(chapter: ChapterItem) {
  try {
    await ElMessageBox.confirm(
      `删除章节「${chapter.title}」后，下属小节和资源将一并删除，是否确认？`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    operating.value = true
    await deleteChapter(props.courseId, chapter.chapter_id)

    localChapters.value = localChapters.value.filter(ch => ch.chapter_id !== chapter.chapter_id)
    emit('update:chapters', [...localChapters.value])
    ElMessage.success('章节已删除')
  } catch (error) {
    // 用户取消
  } finally {
    operating.value = false
  }
}

// 删除小节
async function handleDeleteSection(chapterId: number, section: SectionItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除小节「${section.title}」吗？删除后资源将一并删除。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    operating.value = true
    await deleteSection(props.courseId, chapterId, section.section_id)

    const chapterIndex = localChapters.value.findIndex(ch => ch.chapter_id === chapterId)
    if (chapterIndex > -1) {
      localChapters.value[chapterIndex].sections = localChapters.value[chapterIndex].sections.filter(
        s => s.section_id !== section.section_id
      )
    }
    emit('update:chapters', [...localChapters.value])
    ElMessage.success('小节已删除')
  } catch (error) {
    // 用户取消
  } finally {
    operating.value = false
  }
}

// 管理资源
function handleManageResources(id: number, type: 'chapter' | 'section', defaultTab?: 'video' | 'document') {
  resourceParent.value = { id, type, defaultTab }
}

// 关闭资源管理
function closeResourceManager() {
  resourceParent.value = null
}

// 资源更新
function handleResourcesUpdate(parentId: number, parentType: 'chapter' | 'section', resources: SectionItem['resources']) {
  if (parentType === 'chapter') {
    const chapterIndex = localChapters.value.findIndex(ch => ch.chapter_id === parentId)
    if (chapterIndex > -1) {
      localChapters.value[chapterIndex].resources = resources
    }
  } else {
    for (const chapter of localChapters.value) {
      const sectionIndex = chapter.sections.findIndex(s => s.section_id === parentId)
      if (sectionIndex > -1) {
        chapter.sections[sectionIndex].resources = resources
        break
      }
    }
  }
  emit('update:chapters', [...localChapters.value])
}

// 获取当前编辑资源的对象
const currentResourceParent = computed(() => {
  if (!resourceParent.value) return null
  const { id, type } = resourceParent.value
  
  if (type === 'chapter') {
    const chapter = localChapters.value.find(ch => ch.chapter_id === id)
    return chapter ? { title: chapter.title, resources: chapter.resources, type } : null
  } else {
    for (const chapter of localChapters.value) {
      const section = chapter.sections.find(s => s.section_id === id)
      if (section) return { title: section.title, resources: section.resources, type }
    }
  }
  return null
})
</script>

<template>
  <div class="chapter-manager">
    <div class="manager-header">
      <h3 class="manager-title">章节目录</h3>
      <el-button type="primary" text :icon="Plus" @click="handleAddChapter" :loading="operating">
        添加章节
      </el-button>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="localChapters.length === 0" description="暂无章节，请添加章节" />

    <!-- 章节列表 -->
    <div v-else class="chapter-list">
      <draggable
        v-model="localChapters"
        item-key="chapter_id"
        handle=".expand-icon"
        animation="200"
        @end="handleChapterSort"
      >
        <template #item="{ element: chapter }">
          <div class="chapter-block">
            <!-- 章节头部 -->
            <div class="chapter-header" @click="toggleChapter(chapter.chapter_id)">
              <el-icon class="expand-icon" :class="{ expanded: expandedChapters.has(chapter.chapter_id) }">
                <Rank />
              </el-icon>

              <!-- 章节标题 -->
              <div class="chapter-content">
                <span class="chapter-title" @click.stop="startEditChapter(chapter)">
                  {{ chapter.title }}
                </span>
                <div v-if="chapter.description" class="chapter-description">
                  {{ chapter.description }}
                </div>
              </div>

              <span class="section-count">{{ chapter.sections?.length || 0 }} 小节</span>
              <span class="resource-count" v-if="chapter.resources?.length">{{ chapter.resources.length }} 资源</span>

              <el-button text size="small" type="primary" @click.stop="handleManageResources(chapter.chapter_id, 'chapter')">
                章节直属资源
              </el-button>
              <el-button text size="small" :icon="Plus" @click.stop="handleAddSection(chapter)">
                添加小节
              </el-button>
              <el-button text size="small" type="danger" :icon="Delete" @click.stop="handleDeleteChapter(chapter)">
                删除
              </el-button>
            </div>

            <!-- 小节列表 -->
            <div v-show="expandedChapters.has(chapter.chapter_id)" class="section-list">
              <draggable
                v-model="chapter.sections"
                item-key="section_id"
                handle=".drag-icon"
                animation="200"
                @end="handleSectionSort(chapter.chapter_id)"
              >
                <template #item="{ element: section }">
                  <div class="section-item">
                    <el-icon class="drag-icon"><Rank /></el-icon>

                    <!-- 小节内容 -->
                    <div class="section-content">
                      <span class="section-title" @click="startEditSection(chapter.chapter_id, section)">
                        {{ section.title }}
                      </span>
                      <div v-if="section.description" class="section-description">
                        {{ section.description }}
                      </div>
                    </div>

                    <span class="resource-count">{{ section.resources?.length || 0 }} 资源</span>

                    <el-button text size="small" type="primary" :icon="VideoPlay" @click="handleManageResources(section.section_id, 'section', 'video')">
                      上传视频
                    </el-button>
                    <el-button text size="small" :icon="Document" @click="handleManageResources(section.section_id, 'section', 'document')">
                      课件资源
                    </el-button>
                    <el-button text size="small" type="danger" :icon="Delete" @click="handleDeleteSection(chapter.chapter_id, section)">
                      删除
                    </el-button>
                  </div>
                </template>
              </draggable>

              <!-- 空小节 -->
              <div v-if="!chapter.sections || chapter.sections.length === 0" class="empty-section">
                暂无小节，点击上方"添加小节"按钮添加
              </div>
            </div>
          </div>
        </template>
      </draggable>
    </div>

    <!-- 资源管理弹窗 -->
    <el-dialog
      v-if="currentResourceParent"
      :model-value="!!resourceParent"
      :title="`${currentResourceParent.title} - 资源管理`"
      :width="resourceParent?.defaultTab ? '500px' : '900px'"
      @close="closeResourceManager"
    >
      <ResourceManager
        :course-id="courseId"
        :parent-id="resourceParent!.id"
        :parent-type="resourceParent!.type"
        :resources="currentResourceParent.resources"
        :default-tab="resourceParent!.defaultTab"
        @update="handleResourcesUpdate"
      />
    </el-dialog>

    <!-- 章节/小节编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="`${dialogMode === 'add' ? '添加' : '编辑'}${dialogType === 'chapter' ? '章节' : '小节'}`"
      width="500px"
      append-to-body
    >
      <el-form label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="dialogForm.title" placeholder="请输入标题" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="dialogForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述内容"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="operating" @click="handleDialogSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
@use 'sass:color';

.chapter-manager {
  .manager-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .manager-title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
  }
}

.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chapter-block {
  border: 1px solid $border-color;
  border-radius: $radius-md;
  overflow: hidden;
}

.chapter-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: $bg-color;
  cursor: pointer;

  &:hover {
    background: color.adjust($bg-color, $lightness: -3%);
  }

  .expand-icon {
    transition: transform 0.2s ease;
    color: $text-tertiary;
    cursor: move; // 加强手柄暗示

    &.expanded {
      transform: rotate(90deg);
    }
  }

  .chapter-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
    cursor: text;
  }

  .chapter-title {
    font-weight: 500;
    color: $text-primary;

    &:hover {
      color: $primary-color;
    }
  }

  .chapter-description {
    font-size: $font-size-xs;
    color: $text-tertiary;
    font-weight: normal;
  }

  .section-count, .resource-count {
    font-size: $font-size-xs;
    color: $text-tertiary;
    margin-left: 4px;
  }
}

.section-list {
  padding: 8px 16px 16px 32px;
}

.section-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: $radius-sm;
  background: #fff;
  margin-bottom: 8px;

  &:last-child {
    margin-bottom: 0;
  }

  &:hover {
    background: $bg-color;
  }

  .drag-icon {
    color: $text-tertiary;
    cursor: move;
  }

  .section-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
    cursor: text;
  }

  .section-title {
    color: $text-primary;

    &:hover {
      color: $primary-color;
    }
  }

  .section-description {
    font-size: $font-size-xs;
    color: $text-tertiary;
  }

  .resource-count {
    font-size: $font-size-xs;
    color: $text-tertiary;
  }
}

.empty-section {
  padding: 16px;
  text-align: center;
  color: $text-tertiary;
  font-size: $font-size-sm;
}
</style>
