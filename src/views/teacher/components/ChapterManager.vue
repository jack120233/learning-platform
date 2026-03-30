<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Rank, Delete } from '@element-plus/icons-vue'
import {
  createChapter,
  updateChapter,
  deleteChapter,
  createSection,
  updateSection,
  deleteSection,
  type ChapterItem,
  type SectionItem,
} from '@/api/teacher'
import ResourceManager from './ResourceManager.vue'

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

// 正在编辑的章节ID
const editingChapterId = ref<number | null>(null)
const editingChapterTitle = ref('')

// 正在编辑的小节ID
const editingSectionId = ref<number | null>(null)
const editingSectionTitle = ref('')

// 展开的章节
const expandedChapters = ref<Set<number>>(new Set())

// 当前管理资源的小节
const resourceSectionId = ref<number | null>(null)

// 操作中状态
const operating = ref(false)

// 同步外部数据
watch(() => props.chapters, (newChapters) => {
  localChapters.value = JSON.parse(JSON.stringify(newChapters))
  // 默认展开所有章节
  newChapters.forEach(ch => expandedChapters.value.add(ch.chapter_id))
}, { immediate: true, deep: true })

// 切换章节展开
function toggleChapter(chapterId: number) {
  if (expandedChapters.value.has(chapterId)) {
    expandedChapters.value.delete(chapterId)
  } else {
    expandedChapters.value.add(chapterId)
  }
}

// 添加章节
async function handleAddChapter() {
  try {
    const { value: title } = await ElMessageBox.prompt('请输入章节标题', '添加章节', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '2-50 个字符',
      inputValidator: (value) => {
        if (!value || !value.trim()) return '请输入章节标题'
        if (value.length < 2) return '标题至少 2 个字符'
        if (value.length > 50) return '标题最多 50 个字符'
        return true
      },
    })

    if (title) {
      operating.value = true
      const newChapter = await createChapter(props.courseId, {
        title: title.trim(),
        sort_order: localChapters.value.length,
      })

      localChapters.value.push(newChapter)
      expandedChapters.value.add(newChapter.chapter_id)
      emit('update:chapters', [...localChapters.value])
      ElMessage.success('章节添加成功')
    }
  } catch (error) {
    // 用户取消
  } finally {
    operating.value = false
  }
}

// 开始编辑章节
function startEditChapter(chapter: ChapterItem) {
  editingChapterId.value = chapter.chapter_id
  editingChapterTitle.value = chapter.title
  nextTick(() => {
    const input = document.querySelector(`.chapter-input-${chapter.chapter_id}`) as HTMLInputElement
    input?.focus()
  })
}

// 保存章节编辑
async function saveChapterEdit(chapter: ChapterItem) {
  const newTitle = editingChapterTitle.value.trim()

  if (!newTitle) {
    ElMessage.warning('章节标题不能为空')
    return
  }

  if (newTitle === chapter.title) {
    editingChapterId.value = null
    return
  }

  if (newTitle.length < 2 || newTitle.length > 50) {
    ElMessage.warning('标题长度需在 2-50 个字符之间')
    return
  }

  try {
    operating.value = true
    await updateChapter(props.courseId, chapter.chapter_id, { title: newTitle })

    const index = localChapters.value.findIndex(ch => ch.chapter_id === chapter.chapter_id)
    if (index > -1) {
      localChapters.value[index].title = newTitle
    }
    emit('update:chapters', [...localChapters.value])
    editingChapterId.value = null
    ElMessage.success('章节更新成功')
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

// 添加小节
async function handleAddSection(chapter: ChapterItem) {
  try {
    const { value: title } = await ElMessageBox.prompt('请输入小节标题', '添加小节', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '2-50 个字符',
      inputValidator: (value) => {
        if (!value || !value.trim()) return '请输入小节标题'
        if (value.length < 2) return '标题至少 2 个字符'
        if (value.length > 50) return '标题最多 50 个字符'
        return true
      },
    })

    if (title) {
      operating.value = true
      const newSection = await createSection(props.courseId, chapter.chapter_id, {
        title: title.trim(),
        sort_order: chapter.sections.length,
      })

      const index = localChapters.value.findIndex(ch => ch.chapter_id === chapter.chapter_id)
      if (index > -1) {
        localChapters.value[index].sections.push(newSection)
      }
      emit('update:chapters', [...localChapters.value])
      ElMessage.success('小节添加成功')
    }
  } catch (error) {
    // 用户取消
  } finally {
    operating.value = false
  }
}

// 开始编辑小节
function startEditSection(_chapterId: number, section: SectionItem) {
  editingSectionId.value = section.section_id
  editingSectionTitle.value = section.title
  nextTick(() => {
    const input = document.querySelector(`.section-input-${section.section_id}`) as HTMLInputElement
    input?.focus()
  })
}

// 保存小节编辑
async function saveSectionEdit(chapterId: number, section: SectionItem) {
  const newTitle = editingSectionTitle.value.trim()

  if (!newTitle) {
    ElMessage.warning('小节标题不能为空')
    return
  }

  if (newTitle === section.title) {
    editingSectionId.value = null
    return
  }

  if (newTitle.length < 2 || newTitle.length > 50) {
    ElMessage.warning('标题长度需在 2-50 个字符之间')
    return
  }

  try {
    operating.value = true
    await updateSection(props.courseId, chapterId, section.section_id, { title: newTitle })

    const chapterIndex = localChapters.value.findIndex(ch => ch.chapter_id === chapterId)
    if (chapterIndex > -1) {
      const sectionIndex = localChapters.value[chapterIndex].sections.findIndex(
        s => s.section_id === section.section_id
      )
      if (sectionIndex > -1) {
        localChapters.value[chapterIndex].sections[sectionIndex].title = newTitle
      }
    }
    emit('update:chapters', [...localChapters.value])
    editingSectionId.value = null
    ElMessage.success('小节更新成功')
  } catch (error) {
    // 错误已处理
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
function handleManageResources(sectionId: number) {
  resourceSectionId.value = sectionId
}

// 关闭资源管理
function closeResourceManager() {
  resourceSectionId.value = null
}

// 资源更新
function handleResourcesUpdate(sectionId: number, resources: SectionItem['resources']) {
  for (const chapter of localChapters.value) {
    const sectionIndex = chapter.sections.findIndex(s => s.section_id === sectionId)
    if (sectionIndex > -1) {
      chapter.sections[sectionIndex].resources = resources
      break
    }
  }
  emit('update:chapters', [...localChapters.value])
}

// 获取当前编辑资源的小节
const currentResourceSection = computed(() => {
  if (!resourceSectionId.value) return null
  for (const chapter of localChapters.value) {
    const section = chapter.sections.find(s => s.section_id === resourceSectionId.value)
    if (section) return { chapter, section }
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
      <div
        v-for="chapter in localChapters"
        :key="chapter.chapter_id"
        class="chapter-block"
      >
        <!-- 章节头部 -->
        <div class="chapter-header" @click="toggleChapter(chapter.chapter_id)">
          <el-icon class="expand-icon" :class="{ expanded: expandedChapters.has(chapter.chapter_id) }">
            <Rank />
          </el-icon>

          <!-- 章节标题 -->
          <template v-if="editingChapterId === chapter.chapter_id">
            <el-input
              v-model="editingChapterTitle"
              size="small"
              :class="`chapter-input-${chapter.chapter_id}`"
              style="flex: 1"
              @click.stop
              @blur="saveChapterEdit(chapter)"
              @keyup.enter="saveChapterEdit(chapter)"
              @keyup.esc="editingChapterId = null"
            />
          </template>
          <template v-else>
            <span class="chapter-title" @click.stop="startEditChapter(chapter)">
              {{ chapter.title }}
            </span>
          </template>

          <span class="section-count">{{ chapter.sections.length }} 小节</span>

          <el-button text size="small" :icon="Plus" @click.stop="handleAddSection(chapter)">
            添加小节
          </el-button>
          <el-button text size="small" type="danger" :icon="Delete" @click.stop="handleDeleteChapter(chapter)">
            删除
          </el-button>
        </div>

        <!-- 小节列表 -->
        <div v-show="expandedChapters.has(chapter.chapter_id)" class="section-list">
          <div
            v-for="section in chapter.sections"
            :key="section.section_id"
            class="section-item"
          >
            <el-icon class="drag-icon"><Rank /></el-icon>

            <!-- 小节标题 -->
            <template v-if="editingSectionId === section.section_id">
              <el-input
                v-model="editingSectionTitle"
                size="small"
                :class="`section-input-${section.section_id}`"
                style="flex: 1"
                @blur="saveSectionEdit(chapter.chapter_id, section)"
                @keyup.enter="saveSectionEdit(chapter.chapter_id, section)"
                @keyup.esc="editingSectionId = null"
              />
            </template>
            <template v-else>
              <span class="section-title" @click="startEditSection(chapter.chapter_id, section)">
                {{ section.title }}
              </span>
            </template>

            <span class="resource-count">{{ section.resources?.length || 0 }} 资源</span>

            <el-button text size="small" @click="handleManageResources(section.section_id)">
              管理资源
            </el-button>
            <el-button text size="small" type="danger" :icon="Delete" @click="handleDeleteSection(chapter.chapter_id, section)">
              删除
            </el-button>
          </div>

          <!-- 空小节 -->
          <div v-if="chapter.sections.length === 0" class="empty-section">
            暂无小节，点击上方"添加小节"按钮添加
          </div>
        </div>
      </div>
    </div>

    <!-- 资源管理弹窗 -->
    <el-dialog
      v-if="currentResourceSection"
      :model-value="!!resourceSectionId"
      :title="`${currentResourceSection.section.title} - 资源管理`"
      width="700px"
      @close="closeResourceManager"
    >
      <ResourceManager
        :course-id="courseId"
        :section-id="resourceSectionId!"
        :resources="currentResourceSection.section.resources"
        @update="handleResourcesUpdate"
      />
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>

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
    background: darken($bg-color, 3%);
  }

  .expand-icon {
    transition: transform 0.2s ease;
    color: $text-tertiary;

    &.expanded {
      transform: rotate(90deg);
    }
  }

  .chapter-title {
    flex: 1;
    font-weight: 500;
    color: $text-primary;
    cursor: text;

    &:hover {
      color: $primary-color;
    }
  }

  .section-count {
    font-size: $font-size-xs;
    color: $text-tertiary;
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

  .section-title {
    flex: 1;
    color: $text-primary;
    cursor: text;

    &:hover {
      color: $primary-color;
    }
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