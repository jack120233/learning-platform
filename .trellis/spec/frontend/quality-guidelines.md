# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

Frontend changes must preserve the Vue 3 + TypeScript + Vite + Pinia + Vue Router + Element Plus architecture. The frontend project lives in `UI/`; run frontend commands from that directory.

The most important project rule is that authentication and permission state must flow through `useUserStore()`. API calls must use the shared Axios instance in `UI/src/api/index.ts` and continue to target `/api/v1` through the Vite proxy/dev environment.

---

## Required Patterns

### API calls

Use typed API wrapper functions under `UI/src/api/`.

```ts
export function submitFeedback(data: SubmitFeedbackRequest): Promise<SubmitFeedbackResponse> {
  return request.post<unknown, SubmitFeedbackResponse>('/feedbacks', data)
}
```

Do not call `axios` directly from pages/components for normal backend APIs.

### Authentication and permissions

Use `useUserStore()` for login, role, and permission state.

```ts
const userStore = useUserStore()

if (userStore.isLoggedIn) {
  // authenticated behavior
}
```

Route access should be controlled with route `meta` and the central guard in `UI/src/router/index.ts`.

### Pages and components

Use `<script setup lang="ts">`, typed props/emits, local state for page-only behavior, and scoped SCSS.

### Responsive layout

New pages/components must support PC and mobile. Keep PC styles as the default and add media queries for small screens, usually `@media (max-width: 768px)`.

---

## Router and Access Control

Route config is centralized in `UI/src/router/index.ts`.

Use these meta fields:

- `public: true`
- `requiresAuth: true`
- `permissionCode: '...'`
- `hideAppChrome: true` for immersive pages such as learning

The route guard handles:

- document title
- logged-in users visiting login/register/forgot-password
- public routes
- unauthenticated redirect to login with `redirect`
- permission loading
- admin landing route resolution
- permission-code denial redirect

Do not implement separate page-level redirects for standard route protection.

---

## Type and Contract Quality

- API request/response types should live with their API functions.
- Components should consume frontend-stable types, not raw backend compatibility payloads.
- Backend legacy fields should be normalized in API modules.
- Use string-literal unions for known enums such as role, feedback type, status, resource type, and media state.
- Avoid `any`; replace it with explicit backend/internal interfaces or normalizers when practical.

---

## Styling Quality

- Use scoped SCSS in components.
- Use existing global SCSS variables and utility classes.
- Avoid global style leakage from page/component files.
- Use Element Plus components consistently.
- Ensure loading, empty, error, hover, and mobile states are considered for user-facing pages.

---

## Testing and Verification Requirements

For frontend-only changes, run from `UI/`:

```bash
npm run build
```

When type contracts are involved, also run:

```bash
npx vue-tsc -b
```

For page or interaction changes, start the dev server and manually check the affected page in the browser when possible:

```bash
npm run dev
```

Manual UI checks should cover:

- golden path
- loading/empty/error states when relevant
- permission/role access when relevant
- PC and mobile layout
- no obvious console errors

If verification cannot be run, state the reason clearly in the final report.

---

## Documentation and Operations Log

If any actual file under `UI/` changes, update `UI/operations-log.md`.

If frontend API contracts, upload flows, page integration behavior, or scripts change, update `UI/docs/前端接口文档.md` or the relevant review/integration document.

For `.trellis/spec/` documentation-only changes, update the relevant Trellis spec files and indexes; no UI operations log is required unless `UI/` files changed.

---

## Forbidden Patterns

- Do not read auth state directly from `localStorage` in business code.
- Do not create a second Axios instance for normal API requests.
- Do not bypass the shared route guard for standard auth/permission checks.
- Do not place route pages under global `components/`.
- Do not add untyped API calls or untyped component props/emits.
- Do not scatter backend compatibility logic across templates/pages.
- Do not introduce another UI framework for normal product UI.
- Do not make PC-only layouts that overflow on mobile.
- Do not modify `UI/` files without updating `UI/operations-log.md`.

---

## Code Review Checklist

Before considering frontend work complete, check:

- files are in the correct `UI/src` layer/domain
- API calls use `UI/src/api/index.ts`
- auth/permission state uses `useUserStore()`
- route access uses router meta when applicable
- TypeScript types are explicit and stable
- backend payload compatibility is handled in API mappers
- Element Plus usage is consistent with existing UI
- scoped SCSS and mobile media queries are present where needed
- `npm run build` or `npx vue-tsc -b` was run, or not run with a clear reason
- `UI/operations-log.md` was updated if `UI/` files changed

---

## Common Mistakes

- Fixing a frontend API issue only in the template instead of the API mapper.
- Checking roles with stale local storage instead of the Pinia store.
- Adding admin/teacher pages without matching route meta permission codes.
- Forgetting mobile layout checks after desktop UI changes.
- Treating `npm run build` as a substitute for manual browser testing of interactions.
- Updating frontend fields without checking backend schemas and response examples.
