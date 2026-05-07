# Hook Guidelines

> How composables are used in this project.

---

## Overview

This Vue project uses Composition API composables under `UI/src/composables/`. Composables are named `useXxx.ts` and are used for reusable stateful logic, not for one-off component internals.

Current examples:

- `usePagination.ts` for reusable paginated list state/actions
- `useProgressSync.ts` for learning progress synchronization
- `useBreakpoint.ts` for responsive breakpoint state
- `useCountdown.ts` and `usePasswordStrength.ts` for focused reusable UI logic

---

## When to Create a Composable

Create a composable when:

- two or more components/pages need the same stateful logic
- the logic combines state, computed values, and actions
- the logic is independent of a specific page's template
- the logic can be tested or reasoned about separately from a component

Do not create a composable for:

- a few lines of one-off component state
- purely stateless formatting or validation helpers; use `UI/src/utils/` instead
- global application state; use Pinia stores instead
- API endpoint wrappers; use `UI/src/api/` instead

---

## Composable Structure

Use explicit exported interfaces/types for reusable composable return values.

Example from `usePagination.ts`:

```ts
export interface PaginationState<T> {
  items: Ref<T[]>
  total: Ref<number>
  page: Ref<number>
  pageSize: Ref<number>
  totalPages: ComputedRef<number>
  isLoading: Ref<boolean>
  isEmpty: ComputedRef<boolean>
}

export interface PaginationActions {
  fetchData: (resetPage?: boolean) => Promise<void>
  goToPage: (p: number) => Promise<void>
  setPageSize: (size: number) => Promise<void>
  refresh: () => Promise<void>
}
```

Return refs, computed values, and actions as a plain object.

```ts
return {
  items,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  isEmpty,
  fetchData,
  goToPage,
  setPageSize,
  refresh,
}
```

---

## Data Fetching

The project does not use React Query/SWR-style libraries. Data fetching is done through typed API functions under `UI/src/api/`, then composed with local page state or composables.

Example from `MyFeedbacksPage.vue`:

```ts
const {
  items: feedbacks,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  isEmpty,
  fetchData,
  goToPage,
} = usePagination<FeedbackItem>(fetchMyFeedbacks, 10)
```

`usePagination` accepts a typed fetch function:

```ts
export type FetchFn<T, P = Record<string, unknown>> = (
  params: P & { page?: number; page_size?: number }
) => Promise<PaginatedData<T>>
```

Keep backend response normalization inside the API function, not inside the composable.

---

## Loading and Error Handling

Composable loading state should prevent duplicate requests when appropriate.

```ts
async function fetchData(resetPage: boolean = false) {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const result = await fetchFn(...)
  } catch (error) {
    console.error('分页数据加载失败:', error)
    items.value = []
    total.value = 0
  } finally {
    isLoading.value = false
  }
}
```

User-facing error messages are usually handled by the Axios interceptor in `UI/src/api/index.ts`, so composables should avoid duplicate `ElMessage` noise unless they are handling a user action with specific feedback.

---

## Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| File | `useXxx.ts` | `usePagination.ts` |
| Function | `useXxx` | `usePagination` |
| State interface | `XxxState` | `PaginationState` |
| Actions interface | `XxxActions` | `PaginationActions` |
| Generic item type | `T` | `usePagination<T>` |

Composables should be imported through the alias path:

```ts
import { usePagination } from '@/composables/usePagination'
```

---

## Relationship to Stores and Utils

Use a composable when logic is reusable and stateful but does not need to be global.

Use Pinia store when state must be shared globally or persist across route boundaries.

Use `utils/` when the helper is pure and stateless, such as formatting or validation.

Use `api/` when defining HTTP calls or backend payload types.

---

## Forbidden Patterns

- Do not create composables for one-off page state that is not reused.
- Do not put API endpoint definitions inside composables.
- Do not put global auth/permission state in composables; use `useUserStore()`.
- Do not normalize backend legacy fields inside generic composables; normalize in API modules.
- Do not return untyped `any` structures from composables.
- Do not trigger duplicate user-facing error messages when Axios already handles the request error.

---

## Common Mistakes

- Turning every repeated line into a composable before there is a real reuse boundary.
- Hiding route-specific behavior inside a generic composable.
- Mixing server payload mapping into `usePagination` instead of keeping it in `fetchMyFeedbacks` or similar API functions.
- Forgetting to expose loading and empty state from list composables.
- Forgetting to guard against duplicate fetches while a request is already loading.
