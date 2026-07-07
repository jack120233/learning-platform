# Type Safety

> Type safety patterns in this project.

---

## Overview

The frontend uses TypeScript with Vue 3 `<script setup>`. API contracts, component props/emits, Pinia stores, composables, and backend-to-frontend mapping functions should be typed explicitly.

The project does not currently use a runtime validation library such as Zod. Runtime validation is handled by UI form rules, explicit normalization helpers, backend Pydantic validation, and API-layer mapping functions.

---

## Type Organization

### API types live with API functions

Define request/response/item types in the same `UI/src/api/*.ts` file as the API functions that use them.

Examples:

- `UI/src/api/profile.ts` defines `UserProfile`, `UpdateProfileRequest`, `FeedbackItem`, `BackendFeedbackItem`, and `fetchMyFeedbacks` together.
- `UI/src/api/learning.ts` defines `CourseDetail`, `SubmitFeedbackRequest`, `SubmitFeedbackResponse`, and learning API functions together.
- `UI/src/api/index.ts` defines shared response wrappers `ApiResponse<T>` and `PaginatedData<T>`.

Preferred naming:

```ts
export interface SubmitFeedbackRequest {
  feedback_type: 'system' | 'course'
  course_id?: number
  content: string
  images?: string[]
}

export interface SubmitFeedbackResponse {
  feedback_id: number
  created_at: string
}
```

### Store types live with stores

Types only used by a store should live in that store file.

Examples:

- `UI/src/store/user.ts` defines `UserRole`, `UserStatus`, `UserInfo`, and internal `LoginInfo`.
- `UI/src/store/learn.ts` defines `ResourceLoadState`, `MediaPlayState`, `ActiveResourceState`, and internal cache/locator types.

### Component props and emits live in the component

Use local interfaces for component-specific props and typed `defineEmits`.

Example from `UI/src/components/feedback/FeedbackForm.vue`:

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

const emit = defineEmits<{
  (e: 'success'): void
  (e: 'cancel'): void
}>()
```

---

## Shared Response Types

Use the shared types from `UI/src/api/index.ts` for common backend response shapes.

```ts
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
```

API wrapper functions should expose the unwrapped `data` type because the Axios response interceptor returns `data` when `code === 200`.

Correct pattern:

```ts
export function fetchProfile(): Promise<UserProfile> {
  return request.get<unknown, UserProfile>('/users/me')
}

export function fetchLearningRecords(params: LearningRecordsParams): Promise<PaginatedData<LearningRecordItem>> {
  return request.get<unknown, PaginatedData<LearningRecordItem>>('/users/me/learning-records', {
    params: { page: 1, page_size: 10, ...params },
  })
}
```

---

## Backend Compatibility Types

When backend payloads need compatibility handling, define backend-facing internal interfaces and map them into frontend-facing exported interfaces.

Example from `UI/src/api/profile.ts`:

```ts
interface BackendFeedbackItem {
  id: number
  feedback_id?: number
  type: string
  feedback_type?: 'system' | 'course'
  images?: string[] | null
  status: string
  course_id?: number | null
  course_title?: string | null
  replied_at?: string | null
  created_at: string
}

function mapFeedbackItem(item: BackendFeedbackItem): FeedbackItem {
  const normalizedStatus = ['processed', 'resolved', 'closed'].includes(item.status) ? 'processed' : 'pending'
  const feedbackType = item.feedback_type ?? (item.type === 'course' ? 'course' : 'system')

  return {
    feedback_id: item.feedback_id ?? item.id,
    feedback_type: feedbackType,
    images: item.images ?? [],
    status: normalizedStatus,
    course_id: item.course_id ?? undefined,
    course_title: item.course_title ?? undefined,
    replied_at: item.replied_at ?? null,
    created_at: item.created_at,
    title: item.title,
    content: item.content,
    reply: item.reply ?? null,
  }
}
```

Keep this mapping in the API layer so pages render stable frontend types.

---

## Union Types

Use string-literal unions for known project enums instead of plain `string`.

Examples:

```ts
export type UserRole = 'student' | 'teacher' | 'admin' | null
export type UserStatus = 'active' | 'disabled' | 'pending' | null
export type ResourceLoadState = 'idle' | 'loading' | 'ready' | 'error'
export type MediaPlayState = 'stopped' | 'playing' | 'paused' | 'completed'
```

For backend fields that may contain legacy or broader values, accept `string` in internal backend types and normalize to a narrower frontend union.

---

## Type Guards and Normalizers

Use small normalization helpers when reading unknown or persisted values.

Examples from `UI/src/store/user.ts`:

```ts
function normalizeRole(value: unknown): UserRole {
  return value === 'student' || value === 'teacher' || value === 'admin' ? value : null
}

function normalizeUserId(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }

  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }

  return null
}
```

Use type predicates when narrowing complex values.

Example from `UI/src/store/learn.ts`:

```ts
function hasContinueProgress(info: ContinueLearningInfo | null): info is ContinueLearningInfo {
  if (!info) return false
  return info.last_resource_id !== null || info.resource_id !== null || info.position > 0
}
```

---

## Validation

### UI validation

Use Element Plus form rules for user-facing form validation.

Example from `FeedbackForm.vue`:

```ts
const rules = {
  feedback_type: [
    { required: true, message: '请选择反馈类型', trigger: 'change' },
  ],
  content: [
    { required: true, message: '请输入反馈内容', trigger: 'blur' },
    { min: 10, message: '反馈内容至少 10 个字符', trigger: 'blur' },
    { max: 500, message: '反馈内容最多 500 个字符', trigger: 'blur' },
  ],
}
```

### File validation

Validate file type, size, and count before upload at the UI boundary.

```ts
const validTypes = ['image/jpeg', 'image/png']
if (!validTypes.includes(file.type)) {
  ElMessage.warning('仅支持 JPG/PNG 格式')
  return false
}
```

### API validation

Backend validation is done by Pydantic. Frontend should still type request payloads, but do not duplicate the full backend schema when the UI only needs user-friendly checks.

---

## Forbidden Patterns

- Do not use untyped API functions that return `Promise<any>`.
- Do not expose backend compatibility fields directly to pages when an API-layer mapper can normalize them.
- Do not use plain `string` for known enums such as role, status, feedback type, resource type, or media state.
- Do not parse persisted `localStorage` values without normalization.
- Do not scatter identical backend-to-frontend mapping logic across multiple pages.
- Avoid `as any`; if unavoidable, keep it local and prefer replacing it with a typed interface or normalizer.
- Do not create global shared type files for types used by only one API module, store, or component.

---

## Common Mistakes

- Forgetting that Axios interceptors unwrap `{ code, message, data }`, causing API functions to type the whole response instead of `data`.
- Treating backend legacy fields and frontend stable fields as the same type instead of mapping them.
- Allowing `null` backend values to leak into component props that expect `undefined` for optional values.
- Duplicating role/status unions in multiple files instead of importing the type from the owning module when it is shared.
- Using type assertions to silence errors before checking whether the backend contract or mapper is wrong.
