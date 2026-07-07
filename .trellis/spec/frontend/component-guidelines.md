# Component Guidelines

> How components are built in this project.

---

## Overview

Frontend components use Vue 3 Single File Components with `<script setup lang="ts">`, typed props/emits, Element Plus UI components, and scoped SCSS.

Route-level pages belong under `UI/src/views/`. Shared reusable components belong under `UI/src/components/`. Page/domain-only subcomponents should stay under that domain's local `components/` directory.

---

## Component Structure

Use this order in Vue files:

```vue
<script setup lang="ts">
// imports
// props/emits
// local state/computed
// functions
// lifecycle/watchers
</script>

<template>
  <div class="component-root">
    ...
  </div>
</template>

<style lang="scss" scoped>
/* scoped styles */
</style>
```

Examples:

- `UI/src/components/common/CourseCard.vue`
- `UI/src/components/feedback/FeedbackForm.vue`
- `UI/src/views/profile/MyFeedbacksPage.vue`

---

## Props Conventions

Define a local `Props` interface for component props. Use `withDefaults(...)` when props have defaults.

Simple required props:

```ts
interface Props {
  data: CourseBaseItem
}

const props = defineProps<Props>()
```

Optional props with defaults:

```ts
interface Props {
  mode?: 'inline' | 'dialog'
  defaultType?: 'system' | 'course'
  typeLocked?: boolean
  courseId?: number
  courseName?: string
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'inline',
  defaultType: 'system',
  typeLocked: false,
})
```

Do not use untyped props objects for new components.

---

## Emits Conventions

Use typed `defineEmits` for component events.

```ts
const emit = defineEmits<{
  (e: 'success'): void
  (e: 'cancel'): void
}>()
```

Emit business-level events (`success`, `cancel`, `refresh`) instead of exposing internal implementation details.

---

## State and Behavior

Keep component-local state inside the component when it is not shared across routes.

Example from `FeedbackForm.vue`:

```ts
const form = reactive({
  feedback_type: props.defaultType as 'system' | 'course',
  content: '',
  images: [] as string[],
})

const submitting = ref(false)
const uploadFiles = ref<UploadFile[]>([])
const showCourseSelect = computed(() => form.feedback_type === 'course')
```

Use Pinia only for cross-page state such as authentication, permissions, categories, and learning context.

---

## Routing from Components

Use Vue Router for navigation actions inside components.

Example from `CourseCard.vue`:

```ts
const router = useRouter()

const handleClick = () => {
  const courseId = props.data.course_id || props.data.id
  if (courseId) {
    router.push(`/courses/${courseId}`)
  }
}
```

If missing identifiers indicate a data contract problem, prefer fixing the API mapper/contract rather than adding broad UI fallbacks.

---

## Styling Patterns

Use scoped SCSS for component styles:

```vue
<style lang="scss" scoped>
.course-card {
  background: #fff;
  border-radius: 8px;
}
</style>
```

Project style conventions:

- global variables live in `UI/src/assets/styles/_variables.scss`
- Vite injects SCSS variables through `additionalData`; do not manually import them in every component
- page containers should follow the existing `.page-container` max-width convention when applicable
- text truncation can use existing utility classes or local `line-clamp` styles
- keep PC styles by default and add mobile media queries for small screens

Responsive pattern:

```scss
@media (max-width: 768px) {
  .card-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
```

### Visual Style Convention: Soft Blue Action Surfaces

Use the same polished blue action style established in `UI/src/components/layout/AppHeader.vue` for future pages and shared components.

**Scope**: Apply this to primary page actions, auth actions, submit/cancel groups, toolbar actions, and important navigation CTAs. Keep normal table row actions compact and low-noise unless they are the primary action of the page.

**Style contract**:

| UI role | Contract |
|---------|----------|
| Action group surface | `display: inline-flex` or `flex`; `gap: 8px-10px`; pale blue background `#f4f8ff`; border `1px solid #dbeafe`; rounded pill/card radius |
| Primary CTA | Element Plus `type="primary"` plus local class; blue gradient `#1890ff -> #2563eb`; no hard border; subtle blue shadow |
| Secondary CTA | White or transparent background; blue text `#2563eb`; light blue border on hover/focus |
| Shape | Prefer `border-radius: 999px` for action buttons and pill groups; use `12px-14px` radius for mobile stacked surfaces |
| Text | Use `font-weight: 600` for action buttons; keep labels short and direct |
| Interaction | Define hover/focus states together; do not rely only on Element Plus defaults for custom CTA groups |
| Mobile | Stack action groups vertically in drawers/cards when horizontal space is limited |

**Reference implementation**:

```scss
.action-surface {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px;
  background: #f4f8ff;
  border: 1px solid #dbeafe;
  border-radius: 999px;
}

.action-btn {
  min-width: 68px;
  height: 34px;
  margin-left: 0 !important;
  border-radius: 999px;
  font-weight: 600;
}

.action-btn--secondary {
  border-color: transparent;
  background: transparent;
  color: #2563eb;

  &:hover,
  &:focus {
    border-color: #bfdbfe;
    background: #fff;
    color: #1d4ed8;
  }
}

.action-btn--primary {
  border: none;
  background: linear-gradient(135deg, #1890ff 0%, #2563eb 100%);
  box-shadow: 0 8px 18px rgba(24, 144, 255, 0.25);

  &:hover,
  &:focus {
    background: linear-gradient(135deg, #40a9ff 0%, #1d4ed8 100%);
    box-shadow: 0 10px 22px rgba(24, 144, 255, 0.32);
  }
}
```

**Good / Base / Bad cases**:

- Good: a page's main action group uses a pale-blue rounded surface, a lightweight secondary action, and one gradient primary CTA.
- Base: plain Element Plus buttons are acceptable for dense admin tables, filters, pagination, or low-emphasis inline actions.
- Bad: multiple solid primary buttons side by side with no hierarchy, square default buttons in hero/header CTAs, or custom colors that do not match the blue palette.

**Wrong vs Correct**:

Wrong:

```vue
<el-button type="primary" text>登录</el-button>
<el-button type="primary">注册</el-button>
```

Correct:

```vue
<div class="action-surface">
  <el-button class="action-btn action-btn--secondary">登录</el-button>
  <el-button class="action-btn action-btn--primary" type="primary">注册</el-button>
</div>
```

**Tests / verification required**:

- Run `npm run build` after changing shared styles or layout components.
- For visible UI changes, verify in browser at the target route in both logged-in and logged-out states if auth controls are affected.
- Check mobile or narrow layout when the action group can wrap or stack.

---

## Element Plus Usage

Use Element Plus components for forms, buttons, tags, images, upload, empty states, pagination, and messages where the project already does.

Examples:

- `el-form`, `el-form-item`, `el-input`, `el-select` in `FeedbackForm.vue`
- `el-image` with an error slot in `CourseCard.vue`
- `el-empty`, `el-tag`, `el-pagination` in `MyFeedbacksPage.vue`
- `ElMessage` for user-facing operation feedback

Do not introduce a second UI library for normal product UI.

---

## Accessibility and UX

Minimum expectations:

- clickable cards/buttons must have clear visual affordance such as cursor and hover state
- images should provide graceful placeholders or error slots
- form inputs should have visible labels and validation messages
- long content should wrap or truncate without breaking layout
- loading and submitting states should disable or show loading on actions
- mobile layouts must avoid horizontal overflow

Existing examples:

- `CourseCard.vue` uses image error placeholder and hover state.
- `FeedbackForm.vue` shows upload limits, validates content length, and disables submit while uploading/submitting.
- `MyFeedbacksPage.vue` has empty state and mobile layout adjustments.

---

## Forbidden Patterns

- Do not create untyped props/emits for new components.
- Do not put route pages under `components/`.
- Do not put one-page-only components under global `components/`.
- Do not read `localStorage` directly from components for auth or role checks; use `useUserStore()`.
- Do not create a new Axios instance inside a component.
- Do not use unscoped global styles from component files unless intentionally editing global styles.
- Do not skip mobile media queries for new page-level layouts.
- Do not introduce another UI framework beside Element Plus for normal app UI.

---

## Common Mistakes

- Moving domain-only components into global `components/`, making ownership unclear.
- Duplicating API request logic inside components instead of using `UI/src/api/*.ts`.
- Duplicating permission logic in components instead of relying on router meta and `useUserStore()`.
- Handling backend compatibility fields in templates instead of API mapper functions.
- Forgetting loading states on submit/upload actions.
- Adding PC-only layout that overflows below `768px`.
