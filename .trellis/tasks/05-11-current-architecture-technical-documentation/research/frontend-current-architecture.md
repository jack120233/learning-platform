# Research: frontend current architecture

- **Query**: Research the current frontend architecture and functionality for this Vue/Vite project. Goal: support a new technical documentation task at `.trellis/tasks/05-11-current-architecture-technical-documentation`. Inspect current code under `UI/` and relevant docs under `UI/docs` and `UI/README.md`. Include: app entry/routing/store/API conventions, major pages/modules, auth/role/permission flow, build/dev commands, notable differences or stale spots in existing docs if obvious.
- **Scope**: internal
- **Date**: 2026-05-11

## Findings

### Files Found

| File Path | Description |
|---|---|
| `UI/package.json` | Frontend scripts, dependencies, and dev dependencies. |
| `UI/vite.config.ts` | Vite configuration: Vue plugin, Element Plus auto-import, alias, SCSS globals, dev server proxy. |
| `UI/src/main.ts` | Vue app entry; installs Pinia, Vue Router, Element Plus Chinese locale, and global Element Plus icons. |
| `UI/src/App.vue` | App shell wrapper; conditionally displays `AppHeader`/`AppFooter` based on route meta `hideAppChrome`. |
| `UI/src/router/index.ts` | Central route definitions and route guard for public/authenticated/permission-code routes. |
| `UI/src/api/index.ts` | Shared Axios instance, response unwrapping, token injection, 401 refresh handling, shared response/pagination types. |
| `UI/src/api/auth.ts` | Login/register/captcha/email-code/reset/refresh/logout API types and wrappers. |
| `UI/src/api/course.ts` | Public homepage/course-list/course-search API types and wrappers. |
| `UI/src/api/category.ts` | Category API wrapper with `id` to `category_id` compatibility mapping. |
| `UI/src/api/learning.ts` | Course detail, learning progress, resource play, feedback, teacher options, upload APIs. |
| `UI/src/api/profile.ts` | Profile, permissions, messages, learning records, user feedback APIs plus backend-to-frontend mappers. |
| `UI/src/api/teacher.ts` | Teacher course management, content/chapter/section/resource/material/upload, tags, teacher feedback APIs. |
| `UI/src/api/admin.ts` | Admin users, teacher audits, admin applications, categories, tags, messages, permissions, announcements, feedback APIs. |
| `UI/src/store/user.ts` | Pinia authentication, user profile normalization, token persistence, permission-code loading, unread count. |
| `UI/src/store/category.ts` | Pinia category cache and helpers. |
| `UI/src/store/learn.ts` | Pinia learning state: current course, active resource, playback/progress state, resource traversal. |
| `UI/src/components/layout/AppHeader.vue` | Main header, search, auth buttons, user dropdown, unread badge, role/permission-based teacher/admin menu entries. |
| `UI/src/components/layout/AppFooter.vue` | Main app footer. |
| `UI/src/layouts/AuthLayout.vue` | Standalone auth-page layout with branded left panel and form slot. |
| `UI/src/components/common/CourseCard.vue` | Shared course card component for course lists. |
| `UI/src/components/common/UnreadLabelBadge.vue` | Shared unread-count label/badge display. |
| `UI/src/components/feedback/FeedbackForm.vue` | Reusable feedback submission form. |
| `UI/src/components/feedback/FeedbackDialog.vue` | Reusable feedback dialog wrapper. |
| `UI/src/composables/usePagination.ts` | Generic pagination composable for pages backed by `PaginatedData`. |
| `UI/src/composables/useProgressSync.ts` | Learning progress synchronization composable with timer, immediate sync, beacon, offline queue hooks. |
| `UI/src/composables/useBreakpoint.ts` | Responsive breakpoint composable aligned with SCSS breakpoints. |
| `UI/src/composables/useCountdown.ts` | Countdown timer composable used by auth verification-code flows. |
| `UI/src/composables/usePasswordStrength.ts` | Password-strength helper composable. |
| `UI/src/utils/format.ts` | Formatting utilities for masked contact info, file size, duration, date, relative time. |
| `UI/src/utils/validators.ts` | Element Plus form validation patterns/rules for auth forms. |
| `UI/src/views/home/HomePage.vue` | Homepage: banner, search/filter, course list, pagination; loads categories and course list/search data. |
| `UI/src/views/home/components/BannerCarousel.vue` | Homepage banner carousel component. |
| `UI/src/views/home/components/SearchFilterBar.vue` | Homepage search/filter UI component. |
| `UI/src/views/home/components/CourseListSection.vue` | Homepage course list display component. |
| `UI/src/views/home/components/PaginationBar.vue` | Homepage pagination component. |
| `UI/src/views/auth/LoginPage.vue` | Login page with email/phone login mode, remember login id, login-state initialization. |
| `UI/src/views/auth/RegisterPage.vue` | Register page with student/teacher role choice, captcha, email code, pending-teacher dialog. |
| `UI/src/views/auth/ForgotPasswordPage.vue` | Password reset page. |
| `UI/src/views/course/CourseDetailPage.vue` | Public course detail page with outline/material preview/download/feedback and start/continue-learning flow. |
| `UI/src/views/learn/LearningPage.vue` | Immersive learning page for video/audio/document/image resources, progress sync, side directory, shortcuts. |
| `UI/src/views/profile/ProfileLayout.vue` | Profile-center nested route layout. |
| `UI/src/views/profile/ProfileInfoPage.vue` | Personal profile page. |
| `UI/src/views/profile/ChangePasswordPage.vue` | Password-change page. |
| `UI/src/views/profile/LearningRecordsPage.vue` | User learning-records page. |
| `UI/src/views/profile/MessagesPage.vue` | User messages center with unread/read/delete handling. |
| `UI/src/views/profile/MyFeedbacksPage.vue` | User feedback history page. |
| `UI/src/views/teacher/TeacherLayout.vue` | Teacher nested route layout. |
| `UI/src/views/teacher/CourseListPage.vue` | Teacher/admin course management list. |
| `UI/src/views/teacher/CourseFormPage.vue` | Course create/edit form. |
| `UI/src/views/teacher/FeedbackManagePage.vue` | Teacher-side course feedback management. |
| `UI/src/views/teacher/components/ChapterManager.vue` | Course-edit chapter/section management component. |
| `UI/src/views/teacher/components/ResourceManager.vue` | Course-edit resource/material upload/management component. |
| `UI/src/views/admin/AdminLayout.vue` | Admin console layout and permission-filtered admin menu. |
| `UI/src/views/admin/UserManagePage.vue` | Admin user management page. |
| `UI/src/views/admin/TeacherAuditPage.vue` | Teacher audit page. |
| `UI/src/views/admin/AdminApplicationPage.vue` | Admin application page exists in source, but no route was found in `UI/src/router/index.ts`. |
| `UI/src/views/admin/AnnouncementPage.vue` | Announcement management page. |
| `UI/src/views/admin/FeedbackManagePage.vue` | Admin feedback management page. |
| `UI/src/views/admin/AdminMessagePage.vue` | Admin system-message page. |
| `UI/src/views/admin/CategoryManagePage.vue` | Admin category management page. |
| `UI/src/views/admin/TagManagePage.vue` | Admin tag management page. |
| `UI/src/views/admin/RolePermissionPage.vue` | Role-permission page exists in source, but no route was found in `UI/src/router/index.ts`. |
| `UI/docs/login-auth-issue-review.md` | Login/auth issue review and formal auth-state/interface alignment conventions. |
| `UI/docs/course-id-mismatch-review.md` | Course ID field mismatch review and compatibility convention. |
| `UI/docs/前端接口文档.md` | Frontend API documentation; partly stale against current source in specific rows noted below. |
| `UI/README.md` | Boilerplate Vue/Vite README, not project-specific architecture documentation. |
| `.trellis/spec/frontend/index.md` | Frontend guideline index. |
| `.trellis/spec/frontend/directory-structure.md` | Current frontend directory and module-organization guidelines. |
| `.trellis/spec/frontend/component-guidelines.md` | Frontend component conventions. |
| `.trellis/spec/frontend/hook-guidelines.md` | Frontend composable/hook conventions. |
| `.trellis/spec/frontend/state-management.md` | Frontend state-management conventions. |
| `.trellis/spec/frontend/quality-guidelines.md` | Frontend quality guidelines. |
| `.trellis/spec/frontend/type-safety.md` | Frontend type-safety guidelines. |

### App Entry, Build, and Vite Conventions

- `UI/package.json` defines the active frontend package and scripts:
  - `dev`: `vite` (`UI/package.json:6`)
  - `dev:force`: `vite --force` (`UI/package.json:7`)
  - `dev:reset`: `node scripts/reset-vite-cache.mjs && vite --force` (`UI/package.json:8`)
  - `build`: `vue-tsc -b && vite build` (`UI/package.json:9`)
  - `preview`: `vite preview` (`UI/package.json:10`)
- Key runtime dependencies include Vue 3, Vue Router 4, Pinia, Axios, Element Plus, `@vue-office/*`, `cropperjs`, `lodash-es`, and `vuedraggable` (`UI/package.json:12-27`).
- `UI/vite.config.ts` uses:
  - Vue plugin (`UI/vite.config.ts:11-12`)
  - `unplugin-auto-import` for Vue, Vue Router, Pinia, and Element Plus resolver with generated `src/auto-imports.d.ts` (`UI/vite.config.ts:13-17`)
  - `unplugin-vue-components` with Element Plus resolver and generated `src/components.d.ts` (`UI/vite.config.ts:18-21`)
  - Alias `@` to `src` (`UI/vite.config.ts:23-26`)
  - SCSS `additionalData` to make `@/assets/styles/variables.scss` available globally (`UI/vite.config.ts:28-33`)
  - Dev server on port `3000` with `/api` proxy to `http://localhost:8000` (`UI/vite.config.ts:35-42`)
- App entry creates and mounts a Vue app, globally registers Element Plus icons, installs Pinia, Router, and Element Plus Chinese locale (`UI/src/main.ts:0-22`).
- `UI/src/App.vue` wraps every route in `el-config-provider`, `AppHeader`, `router-view` transition, and `AppFooter`; route meta `hideAppChrome === true` hides the shell for immersive pages (`UI/src/App.vue:0-23`).

### Routing and Page Modules

- Routes are centralized in `UI/src/router/index.ts` with `createRouter(createWebHistory())` (`UI/src/router/index.ts:203-215`).
- Public routes:
  - `/` → `HomePage.vue` (`UI/src/router/index.ts:13-21`)
  - `/login` → `LoginPage.vue` (`UI/src/router/index.ts:23-30`)
  - `/register` → `RegisterPage.vue` (`UI/src/router/index.ts:32-39`)
  - `/forgot-password` → `ForgotPasswordPage.vue` (`UI/src/router/index.ts:41-48`)
  - `/courses/:courseId` → `CourseDetailPage.vue` (`UI/src/router/index.ts:50-57`)
- Authenticated routes:
  - `/learn/:courseId` → `LearningPage.vue`, `requiresAuth: true`, `hideAppChrome: true` (`UI/src/router/index.ts:59-67`)
  - `/profile` layout with child pages for profile info, password, records, messages, feedbacks (`UI/src/router/index.ts:69-107`)
  - `/teacher` layout with `permissionCode: 'teacher.course'`, child pages for courses, create/edit course, feedbacks (`UI/src/router/index.ts:109-145`)
  - `/admin` layout with parent `permissionCode: 'admin'`, child pages for users, teacher audits, announcements, feedbacks, messages, categories, tags (`UI/src/router/index.ts:147-199`)
- Route guard behavior:
  - Sets document title from route meta (`UI/src/router/index.ts:225-226`).
  - Redirects logged-in users away from login/register/forgot-password to Home (`UI/src/router/index.ts:228-231`).
  - Allows `meta.public` routes directly (`UI/src/router/index.ts:233-236`).
  - Redirects unauthenticated users from `requiresAuth` routes to Login with `redirect` query (`UI/src/router/index.ts:238-240`).
  - Loads current-user permissions before checking `meta.permissionCode` if not already loaded (`UI/src/router/index.ts:243-252`).
  - Resolves `/admin` to the first admin child route whose permission code is present (`UI/src/router/index.ts:217-219`, `254-260`).
  - Redirects to Home when a required permission is missing (`UI/src/router/index.ts:263-265`).

### Store and State Conventions

- Pinia stores use Composition API style (`defineStore(..., () => { ... })`) in current source.
- `useUserStore` is the authentication/permission source of truth:
  - Defines role/status/user info types (`UI/src/store/user.ts:4-15`).
  - Uses localStorage keys `access_token`, `refresh_token`, `user_info`, `permission_codes`, `edu_remember_login_id` (`UI/src/store/user.ts:34-40`).
  - Normalizes user id, strings, roles, status, avatar, and nickname fallback (`UI/src/store/user.ts:78-115`).
  - Computed auth/role/permission entries: `isLoggedIn`, `isTeacher`, `isAdmin`, `isPendingTeacher`, `canAccessTeacherCenter`, `canAccessAdminCenter` (`UI/src/store/user.ts:128-133`).
  - Permission codes are loaded from `fetchMyPermissions()` and cached/persisted (`UI/src/store/user.ts:173-203`).
  - `restoreFromStorage()` restores user info, tokens, permissions, and triggers permission reload when logged in (`UI/src/store/user.ts:226-261`).
  - `setLoginInfo()` normalizes backend login/register data, persists user info, clears permission codes, and stores tokens (`UI/src/store/user.ts:276-289`).
  - Store initialization calls `restoreFromStorage()` immediately (`UI/src/store/user.ts:291`).
- `useCategoryStore` caches categories, maps backend `id` to frontend `category_id`, exposes top-level/category-by-id helpers (`UI/src/store/category.ts:4-49`).
- `useLearnStore` owns current learning context, active resource state, continue-learning info, progress cache, media state, resource traversal, and cleanup (`UI/src/store/learn.ts:75-357`).

### API Layer Conventions

- `UI/src/api/index.ts` defines shared backend response and pagination shapes:
  - `ApiResponse<T> = { code, message, data }` (`UI/src/api/index.ts:15-20`)
  - `PaginatedData<T> = { items, total, page, page_size, total_pages }` (`UI/src/api/index.ts:22-29`)
- Shared Axios instance:
  - `baseURL` is `import.meta.env.VITE_API_BASE_URL || '/api/v1'` (`UI/src/api/index.ts:31-38`).
  - Requests inject `Authorization: Bearer <access_token>` from localStorage (`UI/src/api/index.ts:59-67`).
  - Responses unwrap `data` only when backend `code === 200`; otherwise show Element Plus error and reject (`UI/src/api/index.ts:73-87`).
  - 401 handling refreshes via `POST /api/v1/auth/refresh`, updates `access_token`, retries queued requests, and redirects to `/login` if refresh fails (`UI/src/api/index.ts:91-137`).
  - `skipErrorMessage` is supported on Axios config to suppress generic UI errors (`UI/src/api/index.ts:3-13`, `55-57`, `82-85`, `139-145`).
- API modules import the shared client rather than creating their own. Examples:
  - `auth.ts` calls `/auth/login`, `/auth/register`, `/auth/captcha`, `/auth/send-email-code`, `/auth/reset-password`, `/auth/refresh`, `/auth/logout` (`UI/src/api/auth.ts:98-147`).
  - `course.ts` uses `/courses/homepage`, `/courses`, `/courses/search` (`UI/src/api/course.ts:57-76`).
  - `learning.ts` uses `/courses/:id`, `/learning/courses/:id/continue`, `/learning/resources/:id/play`, `/learning/progress`, `/feedbacks`, `/upload/file`, `/upload/feedback-image` (`UI/src/api/learning.ts:162-243`).
  - `profile.ts` maps backend message/feedback shapes into frontend item types for messages and feedback lists (`UI/src/api/profile.ts:181-341`).
  - `teacher.ts` includes course CRUD, batch actions, feedback processing, chapter/section/resource/material management, and chunk upload endpoints (`UI/src/api/teacher.ts:276-476`).
  - `admin.ts` includes admin users, audits, admin applications, category/tag/announcement mappers, role permissions, messages, feedbacks (`UI/src/api/admin.ts:328-616`).

### Auth, Role, and Permission Flow

- Login page sends `username`, `password`, `remember_me` to `login()` (`UI/src/views/auth/LoginPage.vue:64-69`). The UI can label the login identifier as email or phone, but the request field is `username` (`UI/src/views/auth/LoginPage.vue:18-25`, `64-69`).
- Login response is nested under `response.user`; `LoginPage.vue` maps `response.user.id`, username, email, nickname, avatar, role, status plus tokens into `userStore.setLoginInfo()` (`UI/src/views/auth/LoginPage.vue:71-82`).
- After login, the page validates store state, loads permissions, optionally remembers the login id in `edu_remember_login_id`, and redirects to `redirect`, `/admin`, or `/` depending on permission state (`UI/src/views/auth/LoginPage.vue:84-106`).
- Register page supports `student` and `teacher` roles in the UI (`UI/src/views/auth/RegisterPage.vue:27-37`, `51-55`) and submits username/email/phone/password/captcha/email code/role to `register()` (`UI/src/views/auth/RegisterPage.vue:148-159`).
- Register success writes tokens/user state through `userStore.setLoginInfo()` and loads permissions; pending teacher registrations show a pending dialog instead of immediate teacher-center access (`UI/src/views/auth/RegisterPage.vue:161-180`, `377-403`).
- Header menu items depend on store permissions:
  - Teacher center appears if `userStore.canAccessTeacherCenter` (`UI/src/components/layout/AppHeader.vue:42-44`, `287-290`).
  - Admin center appears if `userStore.canAccessAdminCenter` (`UI/src/components/layout/AppHeader.vue:46-48`, `291-294`).
  - Message unread count is fetched from `/messages/unread-count` and stored in `userStore.unreadMessageCount` (`UI/src/components/layout/AppHeader.vue:82-102`).
- Admin layout filters the side menu by `userStore.hasPermission(item.permissionCode)` (`UI/src/views/admin/AdminLayout.vue:19-28`).
- `ADMIN_ENTRY_PERMISSION_CODES` includes `admin`, specific admin child permissions, and `admin.admin_application` even though the current router/admin menu does not expose an admin-application route/menu item (`UI/src/store/user.ts:52-62`; routes/menu shown at `UI/src/router/index.ts:147-199`, `UI/src/views/admin/AdminLayout.vue:19-28`).

### Major Functionality by Module

#### Home and Public Course Discovery

- `HomePage.vue` loads categories via `categoryStore.loadCategories()` and loads either search results or course list depending on route query (`UI/src/views/home/HomePage.vue:81-87`, `27-65`).
- If `keyword` or normalized sort exists, Home calls `searchCourses`; otherwise it calls paginated `fetchCourseList` rather than the homepage limit endpoint (`UI/src/views/home/HomePage.vue:38-56`).
- Search/sort query mapping converts `popular` → `student_count`, `latest` → `published_at` (`UI/src/views/home/HomePage.vue:20-24`).

#### Course Detail and Learning

- `CourseDetailPage.vue` fetches course detail, handles archived/not-found/network/server states, initializes `learnStore` with course/chapter context, and loads continue-learning info for logged-in users (`UI/src/views/course/CourseDetailPage.vue:94-169`).
- Course detail actions:
  - Login prompt/start/continue learning based on `userStore.isLoggedIn` and `learnStore.hasLearningRecord` (`UI/src/views/course/CourseDetailPage.vue:87-93`, `171-207`).
  - Course outline supports chapter resources and section resources (`UI/src/views/course/CourseDetailPage.vue:312-350`, `497-565`).
  - Materials can be downloaded or previewed using `@vue-office`/image dialog (`UI/src/views/course/CourseDetailPage.vue:241-289`, `656-685`).
  - Course feedback uses shared `FeedbackForm` in inline, course-locked mode (`UI/src/views/course/CourseDetailPage.vue:613-651`).
- `LearningPage.vue` is immersive and hides normal chrome via route meta (`UI/src/router/index.ts:60-67`). It:
  - Loads course detail and rejects non-published courses (`UI/src/views/learn/LearningPage.vue:252-285`).
  - Chooses initial resource from route query, continue-learning info, or first course resource (`UI/src/views/learn/LearningPage.vue:287-347`).
  - Switches resources with current progress save, play URL/progress loading, document rendering mode selection, and autoplay attempt (`UI/src/views/learn/LearningPage.vue:353-455`).
  - Supports video/audio/document/image rendering (`UI/src/views/learn/LearningPage.vue:852-933`).
  - Registers keyboard shortcuts, online/offline hooks, beforeunload beacon, route-leave cleanup (`UI/src/views/learn/LearningPage.vue:570-635`, `643-701`).
- `useProgressSync` implements a three-layer progress model: high-frequency memory updates, periodic reporting, immediate save on key events; also supports beacon-on-unload and offline queue hooks (`UI/src/composables/useProgressSync.ts:13-20`, `37-90`, `93-147`, `150-178`).

#### Profile, Messages, and Feedback

- Profile routes are nested under `/profile` and require auth (`UI/src/router/index.ts:69-107`).
- `profile.ts` handles profile, profile update, avatar upload, password change, email code, learning records, messages, unread count, and my feedback APIs (`UI/src/api/profile.ts:122-256`).
- Messages API wrapper performs a combined fetch of `/messages` and `/messages/unread-count`, maps backend `type` into frontend `message_type`, and exposes `markAsRead`, `markAllRead`, `deleteMessage`, `fetchUnreadCount` (`UI/src/api/profile.ts:181-242`, `298-319`).
- My-feedback API wrapper maps backend feedback ids, status variants, target teacher fields, and images (`UI/src/api/profile.ts:247-256`, `321-341`).

#### Teacher Course Management

- Teacher parent route requires `permissionCode: 'teacher.course'` (`UI/src/router/index.ts:109-115`).
- Teacher pages include course list, create/edit course form, and course feedback management (`UI/src/router/index.ts:116-145`).
- `teacher.ts` supports:
  - course list/manage endpoints (`/courses/my-courses`, `/courses/manage`) (`UI/src/api/teacher.ts:276-295`),
  - course CRUD/publish/archive/delete/batch action (`UI/src/api/teacher.ts:297-330`),
  - course feedback list/detail/process (`UI/src/api/teacher.ts:332-354`),
  - chapter/section CRUD/sort (`UI/src/api/teacher.ts:356-405`),
  - chapter/section resources and materials (`UI/src/api/teacher.ts:410-444`),
  - normal and chunked upload (`UI/src/api/teacher.ts:448-476`).

#### Admin Console

- Admin route requires auth and parent `permissionCode: 'admin'`; child pages require specific permission codes (`UI/src/router/index.ts:147-199`).
- Admin menu is generated from a static list and filtered by `userStore.hasPermission()` (`UI/src/views/admin/AdminLayout.vue:19-28`).
- Admin API wrappers include users, teacher audits, admin applications, categories, tags, admin messages, permissions, announcements, and feedbacks (`UI/src/api/admin.ts:328-616`).
- Source files exist for `AdminApplicationPage.vue` and `RolePermissionPage.vue`, but current router children do not include routes for admin applications or role permissions (`UI/src/router/index.ts:147-199`).

### Components, Composables, Utilities, and Styling Patterns

- Shared layout components are in `UI/src/components/layout`; shared business components are in `UI/src/components/common` and `UI/src/components/feedback`.
- Domain-specific page components are colocated under the domain, e.g. teacher-only `ChapterManager.vue` and `ResourceManager.vue` under `UI/src/views/teacher/components/`.
- `usePagination` standardizes page/page_size loading and tolerates backend `items`, `list`, or array response bodies (`UI/src/composables/usePagination.ts:36-80`).
- `useBreakpoint` centralizes JS breakpoint detection (`xs=480`, `sm=768`, `md=1024`, `lg=1280`, `xl=1440`, `2xl=1920`) and exports `BREAKPOINT_VALUES` for alignment with CSS (`UI/src/composables/useBreakpoint.ts:2-10`, `18-105`, `107-111`).
- `validators.ts` centralizes auth form validation for password, phone, username, email code, captcha, login id type detection (`UI/src/utils/validators.ts:2-130`).
- `format.ts` centralizes email/phone masking, file size, duration, date, relative time (`UI/src/utils/format.ts:0-98`).
- SCSS variables are globally injected by Vite, and many components use scoped SCSS plus media queries using `$breakpoint-*` values (e.g. `AdminLayout.vue:141-143`, `LearningPage.vue:1398-1508`, `CourseDetailPage.vue:1366-1496`).

### Related Specs

| Spec File | Relevant Content |
|---|---|
| `.trellis/spec/frontend/index.md` | Frontend guideline index; states the guideline documents are filled and should document actual conventions (`.trellis/spec/frontend/index.md:12-21`, `25-38`). |
| `.trellis/spec/frontend/directory-structure.md` | Mirrors current source organization under `UI/src`, naming conventions, routing rules, API/store/composable locations, and forbidden patterns (`.trellis/spec/frontend/directory-structure.md:36-61`, `65-183`, `186-217`). |
| `.trellis/spec/frontend/component-guidelines.md` | Component patterns and reuse guidance. |
| `.trellis/spec/frontend/hook-guidelines.md` | Composable/hook and data-fetching patterns. |
| `.trellis/spec/frontend/state-management.md` | State-management conventions, including store/source-of-truth behavior. |
| `.trellis/spec/frontend/quality-guidelines.md` | Frontend quality and forbidden-pattern guidance. |
| `.trellis/spec/frontend/type-safety.md` | Type-safety and validation conventions. |

### Existing Docs and Notable Stale/Different Spots

- `UI/README.md` is still the default Vue 3 + TypeScript + Vite template text and does not document this learning-platform architecture (`UI/README.md:0-4`).
- `UI/CLAUDE.md` broadly matches the current architecture but has some older descriptions:
  - It lists `useUserStore` and `useCategoryStore` under Store, while current code also has `useLearnStore` (`UI/CLAUDE.md:92-98`; current `UI/src/store/learn.ts:75-357`).
  - It describes route meta fields `requiresTeacher` / `requiresAdmin` (`UI/CLAUDE.md:82-90`), while current routing primarily uses `permissionCode` for teacher/admin access (`UI/src/router/index.ts:113-115`, `151-155`, `161-197`).
  - Its structure examples list only `api/index.ts`, `course.ts`, and `category.ts` (`UI/CLAUDE.md:45-50`), while the current API folder includes `admin.ts`, `auth.ts`, `learning.ts`, `profile.ts`, `teacher.ts` as well.
- `UI/docs/前端接口文档.md` has several rows that differ from current source:
  - Login row says request field `login_id`, while current `LoginRequest` uses `username` and `LoginPage.vue` sends `username` (`UI/docs/前端接口文档.md:8-15`; `UI/src/api/auth.ts:31-36`; `UI/src/views/auth/LoginPage.vue:64-69`).
  - Password reset row says `login_id`, while current `ResetPasswordRequest` uses `username` (`UI/docs/前端接口文档.md:14`; `UI/src/api/auth.ts:76-82`).
  - Homepage course list row says `page?`, `page_size?`, while current `fetchHomepageCourses` uses `limit` and Home currently uses `fetchCourseList`/`searchCourses` for the displayed paginated homepage list (`UI/docs/前端接口文档.md:22-27`; `UI/src/api/course.ts:35-61`; `UI/src/views/home/HomePage.vue:38-56`).
  - Course search row says request field `q`, while current `searchCourses` sends `keyword`, `category_id`, `sort_by`, `page`, `page_size` (`UI/docs/前端接口文档.md:26`; `UI/src/api/course.ts:49-55`, `72-76`).
  - Message delete row says `POST /messages/{id}/delete`, while current `deleteMessage()` uses `DELETE /messages/{id}` (`UI/docs/前端接口文档.md:75-80`; `UI/src/api/profile.ts:229-234`).
- `UI/docs/login-auth-issue-review.md` remains relevant for the single-source auth convention and documents the exact historical switch from `login_id` to `username`, nested login response shape, and `useUserStore()` source-of-truth rule (`UI/docs/login-auth-issue-review.md:23-47`, `55-145`, `181-275`, `463-679`).
- `UI/docs/course-id-mismatch-review.md` remains relevant for the `id`/`course_id` compatibility pattern; current `CourseBaseItem` still includes optional `id` and `course_id` (`UI/docs/course-id-mismatch-review.md:32-64`; `UI/src/api/course.ts:2-11`).

### External References

- None. This was an internal codebase/docs research task.

## Caveats / Not Found

- Trellis current-task resolution via `python3 ./.trellis/scripts/task.py current --source` failed in this checkout because `current` is not an available subcommand. The user supplied the target task directory explicitly, so the research file was written under that directory.
- The requested task directory existed in the main repository path (`/Users/jacob/Developer/a3.learn_platform/learning-platform/.trellis/tasks/05-11-current-architecture-technical-documentation`) but not in the current worktree's `.trellis/tasks`; the research output was persisted to the supplied main-repository task path.
- No external web/library research was performed because the query was specifically about current internal architecture and existing docs.
- No code files were modified. Only this research file was created.
