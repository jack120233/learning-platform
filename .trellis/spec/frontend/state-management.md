# State Management

> How state is managed in this project.

---

## Overview

The frontend uses Pinia with Vue 3 Composition API stores. Global state is reserved for cross-page application state such as authentication, permissions, categories, and learning-session context.

Most page state should stay local inside the route page or component. Do not promote form inputs, modal visibility, one-page filters, or one-off loading flags into Pinia unless another route/component genuinely needs them.

---

## State Categories

### Local component/page state

Use `ref`, `reactive`, and `computed` inside `.vue` files for state that only belongs to one page or one component.

Examples:

- `UI/src/components/feedback/FeedbackForm.vue` keeps form data, upload list, upload count, and submit loading state locally.
- `UI/src/views/profile/MyFeedbacksPage.vue` keeps route-page list state through `usePagination` instead of a global feedback store.

Typical local pattern:

```ts
const form = reactive({
  feedback_type: props.defaultType as 'system' | 'course',
  content: '',
  images: [] as string[],
})

const submitting = ref(false)
const showCourseSelect = computed(() => form.feedback_type === 'course')
```

### Global application state

Use Pinia stores for state shared across routes or needed by routing/permission logic.

Current stores:

- `UI/src/store/user.ts` for authentication, tokens, current user, permissions, and unread message count.
- `UI/src/store/learn.ts` for learning-page course context, active resource state, continue-learning info, and progress cache.
- `UI/src/store/category.ts` for category data caching.

### Server state

Server data is usually fetched through typed API modules under `UI/src/api/` and held locally in pages/composables.

Examples:

- `UI/src/views/profile/MyFeedbacksPage.vue` calls `usePagination(fetchMyFeedbacks, 10)`.
- `UI/src/api/profile.ts` maps backend feedback/message payloads into frontend-facing types before pages consume them.

### URL state

Route and query state should come from Vue Router, not from Pinia.

Example:

```ts
const route = useRoute()

watch(() => route.query.refresh, () => {
  fetchData()
})
```

---

## When to Use Global State

Use Pinia when at least one of these is true:

- The state controls routing or access checks.
- The state must survive route changes.
- Multiple distant pages/components consume or update the same state.
- The state represents the current authenticated user or permissions.
- The state is a long-lived learning session context.
- The state is intentionally cached across pages, such as categories.

Do not use Pinia when:

- The state is only needed by one form.
- The state is only a table/list loading flag.
- The state can be recomputed from route params or API response.
- The state is only used to avoid prop drilling inside a small local subtree.

---

## User Store Rules

`UI/src/store/user.ts` is the single source of truth for authentication and permission state.

Use these computed values instead of reading persisted storage or duplicating role logic:

- `isLoggedIn`
- `isTeacher`
- `isAdmin`
- `isPendingTeacher`
- `canAccessTeacherCenter`
- `canAccessAdminCenter`

Correct pattern:

```ts
const userStore = useUserStore()

if (userStore.isLoggedIn) {
  // authenticated behavior
}

if (userStore.canAccessAdminCenter) {
  // admin-entry behavior
}
```

Forbidden pattern:

```ts
const token = localStorage.getItem('access_token')
const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
```

The only normal exception is `UI/src/api/index.ts`, where the Axios request interceptor reads `access_token` to attach the `Authorization` header.

---

## Learning Store Rules

`UI/src/store/learn.ts` owns the active learning-session state:

- current course id/title/cover/chapters/status
- active resource id/type/section/chapter
- media load/play state
- playback time and progress
- continue-learning info
- in-memory progress cache

Use the store's actions to mutate learning state:

- `initCourseContext`
- `setContinueInfo`
- `setActiveResource`
- `setResourceLoadState`
- `updatePlayProgress`
- `setPlayState`
- `restoreProgress`
- `markResourceCompleted`
- `updateProgressCache`
- `cleanup`

Do not mutate nested learning state from unrelated pages if a store action already exists.

---

## Derived State

Prefer `computed` for derived state.

Examples:

```ts
const isLoggedIn = computed(() => !!accessToken.value && !!userInfo.value.userId)
const hasActiveResource = computed(() => activeResource.value.resourceId !== null)
```

Do not store both a source value and a derived value unless there is a clear reason. For example, role should be stored once in `userInfo.role`, then `isTeacher` and `isAdmin` should be computed from it.

---

## Persistence

Persistence is manually handled in stores that need it.

Current pattern in `UI/src/store/user.ts`:

- token/user/permission storage keys are centralized in `STORAGE_KEYS`
- store state is normalized before persisting
- `restoreFromStorage()` restores persisted state on store creation
- `logout()` clears both in-memory and persisted state

Do not write scattered `localStorage` keys from pages/components.

---

## Server State Mapping

When backend payloads do not exactly match frontend UI needs, normalize them in the API module rather than spreading compatibility logic across pages.

Example from `UI/src/api/profile.ts`:

```ts
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
    reply: item.reply ?? null,
    replied_at: item.replied_at ?? null,
    created_at: item.created_at,
    title: item.title,
    content: item.content,
  }
}
```

---

## Common Mistakes

- Reading `localStorage` directly from business pages instead of using `useUserStore()`.
- Duplicating role checks in components instead of using store computed properties or router meta.
- Creating global stores for one-page forms or one-off lists.
- Mutating global store state directly from many places instead of using store actions for complex state transitions.
- Keeping backend compatibility transformations inside pages instead of API modules.
- Forgetting to clear global state in logout or `cleanup()` actions.
- Caching server data globally without a clear invalidation strategy.
