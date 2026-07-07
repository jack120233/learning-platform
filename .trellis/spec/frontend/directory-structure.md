# Directory Structure

> How frontend code is organized in this project.

---

## Overview

The frontend project lives under `UI/`. The workspace root is not a frontend package, so frontend commands and file lookups must be performed inside `UI/` unless the task explicitly concerns root-level collaboration files.

The application is a Vue 3 + TypeScript + Vite project. Code is organized by technical layer first (`api`, `store`, `router`, `components`, `views`) and by business domain inside `views`.

---

## Project Root

```text
UI/
├── src/                  # Frontend source code
├── docs/                 # Frontend integration docs and issue reviews
├── vite.config.ts        # Vite config and /api proxy
├── package.json          # Frontend scripts and dependencies
├── CLAUDE.md             # Frontend-specific AI development rules
└── operations-log.md     # Required log for actual UI file changes
```

Run frontend commands from `UI/`:

```bash
npm run dev
npm run build
npx vue-tsc -b
```

---

## Source Layout

```text
UI/src/
├── api/                  # Typed API wrappers and Axios instance
│   ├── index.ts          # Axios instance, interceptors, shared response types
│   ├── auth.ts           # Auth API calls
│   ├── course.ts         # Course API calls
│   ├── learning.ts       # Learning and feedback API calls
│   ├── profile.ts        # Profile, messages, permissions, feedback list
│   ├── teacher.ts        # Teacher-side API calls
│   └── admin.ts          # Admin-side API calls
├── assets/styles/        # Global SCSS entry and variables
├── components/           # Shared reusable components
│   ├── common/           # Shared business components
│   ├── feedback/         # Feedback form/dialog components
│   └── layout/           # App shell components
├── composables/          # Reusable Composition API hooks
├── layouts/              # Standalone layout wrappers
├── router/               # Vue Router config and guards
├── store/                # Pinia stores
├── utils/                # Shared pure utility functions
├── views/                # Route-level pages grouped by business domain
├── App.vue
└── main.ts
```

---

## Module Organization

### Route pages belong in `views/`

Use `views/<domain>/` for route-level pages. Current domains include:

```text
views/
├── admin/       # Admin console pages
├── auth/        # Login, register, forgot password
├── course/      # Course detail page
├── home/        # Home page and home-only sections
├── learn/       # Immersive learning page
├── profile/     # Profile center pages
└── teacher/     # Teacher center pages
```

Examples:

- `UI/src/views/profile/MyFeedbacksPage.vue` renders the user's feedback list.
- `UI/src/views/learn/LearningPage.vue` owns the learning experience.
- `UI/src/views/admin/FeedbackManagePage.vue` owns admin feedback management.

### Shared components belong in `components/`

Use `components/` only for components reused across pages or expected to become shared UI/business building blocks.

Examples:

- `UI/src/components/common/CourseCard.vue` for course cards reused outside one page.
- `UI/src/components/feedback/FeedbackForm.vue` for feedback submission UI reused by profile/learning flows.
- `UI/src/components/layout/AppHeader.vue` and `AppFooter.vue` for app shell UI.

If a component is only used by one page/domain, keep it under that page's local `components/` folder, as in `UI/src/views/teacher/components/ChapterManager.vue`.

### API wrappers belong in `api/`

Each business area gets a typed API module. API modules should call the shared Axios instance from `UI/src/api/index.ts` instead of creating their own client.

Examples:

```ts
// UI/src/api/learning.ts
export function submitFeedback(data: SubmitFeedbackRequest): Promise<SubmitFeedbackResponse> {
  return request.post<unknown, SubmitFeedbackResponse>('/feedbacks', data)
}
```

```ts
// UI/src/api/index.ts
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}
```

### Global state belongs in `store/`

Pinia stores are used for cross-page application state such as authentication, permissions, cached categories, and learning state.

Examples:

- `UI/src/store/user.ts` is the single source of truth for authentication and permissions.
- `UI/src/store/learn.ts` stores learning-page state.
- `UI/src/store/category.ts` caches category data.

Local form state, loading state, and page-only filters should stay inside the page/component unless reused across pages.

### Reusable Composition API logic belongs in `composables/`

Use `composables/` for reusable stateful logic with a `useXxx` naming pattern.

Examples:

- `UI/src/composables/usePagination.ts`
- `UI/src/composables/useProgressSync.ts`
- `UI/src/composables/useBreakpoint.ts`
- `UI/src/composables/useCountdown.ts`

### Utilities belong in `utils/`

Use `utils/` for pure helpers that do not own component state or framework lifecycle.

Examples:

- `UI/src/utils/format.ts`
- `UI/src/utils/validators.ts`

---

## Routing Rules

Routing is centralized in `UI/src/router/index.ts`.

Use route `meta` to describe access requirements:

- `public: true` for public pages.
- `requiresAuth: true` for logged-in pages.
- `requiresTeacher: true` for teacher pages.
- `requiresAdmin: true` for admin pages.
- `permissionCode` when permission-code checks are required.

Do not implement page-local authentication redirects when the route guard can enforce access globally.

---

## Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Route page files | PascalCase + `Page.vue` | `HomePage.vue`, `CourseDetailPage.vue` |
| Shared components | PascalCase `.vue` | `CourseCard.vue`, `FeedbackForm.vue` |
| Layout components | PascalCase `.vue` | `AppHeader.vue`, `AuthLayout.vue` |
| Composables | `useXxx.ts` | `usePagination.ts` |
| Stores | `useXxxStore` export | `useUserStore` |
| API functions | `fetch` / `get` / `post` / verb prefix | `fetchHomepageCourses`, `submitFeedback` |
| API request/response types | `XxxRequest`, `XxxResponse`, `XxxItem`, `XxxParams` | `SubmitFeedbackRequest` |

---

## Required Checks Before Adding Files

Before creating a new frontend file:

1. Check whether the task belongs to `UI/` using the root `CLAUDE.md` routing rules.
2. Search for an existing page/component/API/store/composable with similar responsibility.
3. Prefer extending the existing domain module over creating a parallel structure.
4. If the change modifies API contracts, update the relevant API module and frontend docs together.
5. If an actual `UI/` file is changed, update `UI/operations-log.md`.

---

## Forbidden Patterns

- Do not put frontend source code in the workspace root.
- Do not create a second Axios instance for normal API calls; use `UI/src/api/index.ts`.
- Do not read authentication state directly from `localStorage` in business code; use `useUserStore()` except for the API interceptor.
- Do not place route-level pages under `components/`.
- Do not place one-off page-only components under global `components/`.
- Do not bypass route meta/guards with page-local role checks unless the page also needs conditional rendering.
- Do not create new top-level source folders when an existing layer already fits the responsibility.

---

## Good Examples

- `UI/src/api/index.ts` centralizes Axios, response typing, token injection, refresh handling, and user-facing request errors.
- `UI/src/store/user.ts` centralizes authentication, user info normalization, permissions, and persisted login state.
- `UI/src/views/profile/MyFeedbacksPage.vue` keeps route-page state local while reusing `usePagination` and `fetchMyFeedbacks`.
- `UI/src/components/feedback/FeedbackForm.vue` is reusable because the same feedback form can appear in profile and learning contexts.
- `UI/src/views/teacher/components/ChapterManager.vue` is correctly scoped to teacher course editing instead of global components.
