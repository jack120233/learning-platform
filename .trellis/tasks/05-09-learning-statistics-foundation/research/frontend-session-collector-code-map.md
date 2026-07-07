# Research: Frontend session collector code map

- **Query**: Research the frontend codebase for implementing learning session collection in the learning statistics foundation. Focus on LearningPage.vue, useProgressSync.ts, learn store, learning API types, profile learning records, lifecycle hooks, beforeunload/sendBeacon/offline queue patterns, route/user role guards, and operations-log requirements.
- **Scope**: internal
- **Date**: 2026-05-09

## Findings

### Files Found

| File Path | Description |
|---|---|
| `UI/src/views/learn/LearningPage.vue` | Main immersive learning page; loads course/resource data, manages media/document/image lifecycle, starts progress sync, handles route leave/unmount and browser/network events. |
| `UI/src/composables/useProgressSync.ts` | Reusable progress-sync composable with timeupdate memory updates, periodic save, immediate save, beforeunload `sendBeacon`, and in-memory offline retry queue. |
| `UI/src/store/learn.ts` | Pinia learning-session context for current course, active resource, playback/progress state, continue-learning info, and in-memory progress cache. |
| `UI/src/api/learning.ts` | Typed learning API wrappers for course details, continue info, start learning, resource play URL, get/save progress; no learning-session API wrapper currently exists. |
| `UI/src/api/index.ts` | Shared Axios instance with `/api/v1` base URL, `{ code, message, data }` response unwrapping, Authorization injection, and refresh handling. |
| `UI/src/api/profile.ts` | Profile API types/wrappers including current learning-record display item and `/users/me/learning-records` fetch. |
| `UI/src/views/profile/LearningRecordsPage.vue` | Personal learning-record list page; fetches records via `usePagination`, filters by time range, and continues to `/learn/{course_id}`. |
| `UI/src/router/index.ts` | Route declarations and global auth/permission guard; `/learn/:courseId` requires auth and hides app chrome, profile learning records are under authenticated `/profile`. |
| `UI/src/store/user.ts` | User/auth Pinia store; single source for `isLoggedIn`, role/permission computed state, and permissions loading. |
| `UI/docs/前端接口文档.md` | Current documented frontend learning/profile API contract; documents progress endpoints and learning-record endpoint only. |
| `UI/CLAUDE.md` | Frontend implementation rules, including single-source auth store and mandatory `UI/operations-log.md` updates for actual UI file changes. |
| `.trellis/spec/frontend/hook-guidelines.md` | Composable conventions; explicitly lists `useProgressSync.ts` as the learning progress synchronization composable. |
| `.trellis/spec/frontend/state-management.md` | Pinia/global state guidance; defines `learn.ts` ownership of active learning-session state. |
| `.trellis/spec/frontend/quality-guidelines.md` | Frontend quality/logging checklist; requires `UI/operations-log.md` when actual `UI/` files change. |
| `.trellis/tasks/05-09-learning-statistics-foundation/prd.md` | Foundation task PRD; describes optional frontend session collector integration and requirement to keep `/learning/sessions` separate from `/learning/progress`. |

### Code Patterns

#### Learning page initialization and current progress lifecycle

- `UI/src/views/learn/LearningPage.vue:43-47` instantiates `useProgressSync({ intervalMs: 30000, minDeltaSeconds: 5 })` once for the page.
- `UI/src/views/learn/LearningPage.vue:252-285` loads course detail through `fetchCourseDetail(courseId)`, rejects non-`published` courses, and initializes `learnStore.initCourseContext(...)`.
- `UI/src/views/learn/LearningPage.vue:287-347` determines the initial resource from route query first, then `fetchContinueInfo(courseId)`, then the first course resource.
- `UI/src/views/learn/LearningPage.vue:666-673` calls `startLearning(courseId)` only when `learnStore.hasLearningRecord` is false.
- `UI/src/views/learn/LearningPage.vue:676-685` loads the initial resource, starts periodic progress sync, and registers `beforeunload`, `online`, `offline`, and `keydown` listeners.

#### Resource switching and progress snapshot saving

- `UI/src/views/learn/LearningPage.vue:353-363` aborts previous switch work and calls `await progressSync.immediateSync()` before switching away from the current resource.
- `UI/src/views/learn/LearningPage.vue:378-381` loads play info and saved progress in parallel with `getResourcePlayUrl(resourceId)` and `getProgress(sectionId, resourceId)`.
- `UI/src/views/learn/LearningPage.vue:389-398` sets the active resource using API play info (`resource_id`, `resource_type`, `file_url`, optional `duration`) plus the local `sectionId`/resolved `chapterId`.
- `UI/src/views/learn/LearningPage.vue:405-407` restores saved progress via `learnStore.restoreProgress(progressRes.value.current_time, progressRes.value.is_completed)`.
- `UI/src/views/learn/LearningPage.vue:432-436` marks document/image resources complete immediately and triggers `progressSync.immediateSync()`.

#### Media event hooks

- `UI/src/views/learn/LearningPage.vue:458-461` handles video `timeupdate` by passing `videoRef.currentTime` and `videoRef.duration` to `progressSync.onTimeUpdate(...)`; audio uses the same handler at `UI/src/views/learn/LearningPage.vue:881`.
- `UI/src/views/learn/LearningPage.vue:463-466` pauses set play state to `paused` and immediately sync progress.
- `UI/src/views/learn/LearningPage.vue:468-470` play events set play state to `playing`.
- `UI/src/views/learn/LearningPage.vue:472-476` ended events mark the resource completed, immediately sync progress, and start auto-next behavior.
- `UI/src/views/learn/LearningPage.vue:482-488` `loadedmetadata` restores the media element `currentTime` from store state.

#### Route leave, unmount, and browser/network lifecycle hooks

- `UI/src/views/learn/LearningPage.vue:625-635` `onBeforeRouteLeave` awaits `progressSync.immediateSync()`, stops periodic sync, calls `learnStore.cleanup()`, removes window/document event listeners, then calls `next()`.
- `UI/src/views/learn/LearningPage.vue:693-701` `onUnmounted` stops periodic sync, removes the same listeners, and cancels the auto-next timer.
- `UI/src/views/learn/LearningPage.vue:614-623` maps browser `online`/`offline` events to user messages and `progressSync.handleOnline()` / `progressSync.handleOffline()`.
- `UI/src/views/learn/LearningPage.vue:682-684` registers `beforeunload`, `online`, and `offline`; `UI/src/views/learn/LearningPage.vue:696-698` removes them on unmount.

#### Current `useProgressSync` behavior

- `UI/src/composables/useProgressSync.ts:13-19` documents a three-layer architecture: high-frequency `timeupdate` only updates memory, periodic 30s reporting, and immediate saves on pause/switch/leave.
- `UI/src/composables/useProgressSync.ts:40-42` `onTimeUpdate` only calls `learnStore.updatePlayProgress(currentTime, totalTime)`.
- `UI/src/composables/useProgressSync.ts:47-91` `doSync(force)` builds a `SaveProgressRequest` from `learnStore.activeResource`, posts it through `saveProgress(request)`, updates `lastReportedTime`, and updates `learnStore.progressCache` on success.
- `UI/src/composables/useProgressSync.ts:57-64` includes `section_id` only when present, includes `chapter_id` even though the exported `SaveProgressRequest` type does not currently declare it, and always sends `resource_id`, floored `current_time`, floored `total_time`, and `is_completed`.
- `UI/src/composables/useProgressSync.ts:75-87` catches save errors and pushes a request into `offlineQueue` only when `!navigator.onLine`; the queue is an in-memory `ref<OfflineQueueItem[]>([])`.
- `UI/src/composables/useProgressSync.ts:96-108` starts a `setInterval` that only syncs when an active resource exists, `playState === 'playing'`, and the delta from `lastReportedTime` is at least `minDeltaSeconds`.
- `UI/src/composables/useProgressSync.ts:123-125` exposes `immediateSync()` as `doSync(true)`.
- `UI/src/composables/useProgressSync.ts:129-147` sends a `navigator.sendBeacon('/api/v1/learning/progress', Blob(JSON))` payload on `beforeunload` with `section_id`, `chapter_id`, `resource_id`, `current_time`, `total_time`, and `is_completed`.
- `UI/src/composables/useProgressSync.ts:152-163` flushes the in-memory offline queue FIFO on reconnect, unshifting a failed item back to the front and breaking.
- `UI/src/composables/useProgressSync.ts:168-178` stops periodic sync when offline and flushes/restarts periodic sync when online.
- `UI/src/composables/useProgressSync.ts:180-183` stops periodic sync on composable unmount.

#### Learning store state shape

- `UI/src/store/learn.ts:13-37` defines `ActiveResourceState` with resource/chapter/section identifiers, load/play state, playback fields (`currentTime`, `totalTime`, `playbackRate`, `volume`, `isMuted`), progress fields, file URL, and error message.
- `UI/src/store/learn.ts:75-108` stores current course context, `activeResource`, `continueInfo`, `hasLearningRecord`, and `progressCache` in Pinia refs.
- `UI/src/store/learn.ts:117-123` `initCourseContext(...)` records course id/title/cover/chapters/status.
- `UI/src/store/learn.ts:128-132` `setContinueInfo(...)` normalizes backend empty continue responses into `null` and derives `hasLearningRecord`.
- `UI/src/store/learn.ts:137-162` `setActiveResource(...)` resets the active resource on each resource switch while preserving playback rate/volume/mute.
- `UI/src/store/learn.ts:177-185` `updatePlayProgress(...)` writes current/total time and percent.
- `UI/src/store/learn.ts:197-203` `restoreProgress(...)` restores current time/completion and percent.
- `UI/src/store/learn.ts:208-220` `markResourceCompleted()` sets `isCompleted`, `progressPercent = 100`, `playState = 'completed'`, and writes the current resource to `progressCache`.
- `UI/src/store/learn.ts:271-294` `flattenCourseResources()` enumerates chapter-level resources and section resources in course order.
- `UI/src/store/learn.ts:299-325` `cleanup()` clears course context, active resource state, continue info, learning-record flag, and progress cache.

#### Existing learning API contracts

- `UI/src/api/learning.ts:111-118` defines `SaveProgressRequest` with `section_id?: number`, `resource_id`, `current_time`, `total_time`, and `is_completed`.
- `UI/src/api/learning.ts:121-128` defines `LearningProgress` with `section_id`, `resource_id`, `current_time`, `total_time`, `is_completed`, and `last_learn_at`.
- `UI/src/api/learning.ts:172-180` wraps continue/start endpoints: `GET /learning/courses/{courseId}/continue` and `POST /learning/courses/{courseId}/start`.
- `UI/src/api/learning.ts:186-207` wraps resource play URL, progress get, and progress save: `GET /learning/resources/{resourceId}/play`, `GET /learning/progress`, and `POST /learning/progress`.
- No `LearningSession` / `saveLearningSession` / `/learning/sessions` wrapper was found in `UI/src/api/learning.ts` or broader frontend searches.
- `UI/src/api/index.ts:31-38` configures the shared Axios instance with `baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1'`, JSON content type, and 15s timeout.
- `UI/src/api/index.ts:59-67` injects `Authorization: Bearer <access_token>` from local storage in the request interceptor.
- `UI/src/api/index.ts:73-87` unwraps response `data` when `code === 200` and rejects business errors.

#### Profile learning records

- `UI/src/api/profile.ts:49-58` defines `LearningRecordItem` with `course_id`, `course_title`, `course_cover`, `last_section_id`, `last_section_title`, `last_learn_at`, and `course_status`.
- `UI/src/api/profile.ts:60-65` defines `LearningRecordsParams` with `time_range: 'recent_7' | 'recent_30' | 'all'`, `page`, and `page_size`.
- `UI/src/api/profile.ts:171-176` fetches records with `GET /users/me/learning-records`, defaulting `page: 1` and `page_size: 10`.
- `UI/src/views/profile/LearningRecordsPage.vue:17-23` wraps `fetchLearningRecords` to always include the selected `timeRange`.
- `UI/src/views/profile/LearningRecordsPage.vue:25-39` uses `usePagination<LearningRecordItem, LearningRecordsParams>(fetchRecords, 10)`.
- `UI/src/views/profile/LearningRecordsPage.vue:53-56` continues learning with `router.push(`/learn/${record.course_id}`)` and does not pass section/resource query parameters.
- `UI/src/views/profile/LearningRecordsPage.vue:69-72` loads records in `onMounted`.

#### Route and role/auth guards

- `UI/src/router/index.ts:59-68` defines `/learn/:courseId` as `name: 'Learning'`, `requiresAuth: true`, and `hideAppChrome: true`; it has no `permissionCode` or role-specific requirement.
- `UI/src/router/index.ts:70-108` places profile pages, including `/profile/records`, under parent `/profile` with `requiresAuth: true`.
- `UI/src/router/index.ts:221-268` global guard sets page title, redirects logged-in users away from auth pages, allows public routes, sends unauthenticated users to login with `redirect`, loads permissions only when `meta.permissionCode` exists, handles admin landing, and blocks missing permissions.
- `UI/src/store/user.ts:128-133` exposes computed `isLoggedIn`, `isTeacher`, `isAdmin`, `isPendingTeacher`, `canAccessTeacherCenter`, and `canAccessAdminCenter`.
- `UI/src/store/user.ts:173-203` loads permission codes from `fetchMyPermissions()` when required.
- `UI/src/views/learn/LearningPage.vue:649-653` also performs a local login check in `onMounted` and redirects to login if `!userStore.isLoggedIn`.

#### Operations-log and frontend documentation requirements

- `UI/CLAUDE.md:193-197` says any actual `UI` repository file change must append `UI/operations-log.md`; records must include change time, reason, files, core change, and validation result.
- `UI/CLAUDE.md:195-196` says frontend API contract, upload flow, page integration behavior, or script changes must also update `UI/docs/前端接口文档.md` or the relevant document.
- `.trellis/spec/frontend/quality-guidelines.md:130-136` repeats that actual `UI/` file changes require `UI/operations-log.md`, and Trellis spec-only documentation changes do not require UI operations log unless `UI/` files changed.
- `.trellis/spec/frontend/quality-guidelines.md:156-167` checklist includes correct layer/domain, shared Axios usage, `useUserStore()` auth/permission state, explicit types, build/typecheck, and operations-log update when `UI/` changes.

### External References

No external references were used; this research is internal code/spec mapping only.

### Related Specs

- `.trellis/spec/frontend/hook-guidelines.md` — composable naming/structure and current `useProgressSync.ts` ownership.
- `.trellis/spec/frontend/state-management.md` — Pinia learning-session context ownership and user-store single-source auth rules.
- `.trellis/spec/frontend/quality-guidelines.md` — frontend validation, API/client, auth, and operations-log requirements.
- `.trellis/spec/frontend/directory-structure.md` — frontend layer/domain placement and `UI/operations-log.md` mention.
- `.trellis/tasks/05-09-learning-statistics-foundation/prd.md` — foundation task requirements and optional frontend collector scope; explicitly separates `/learning/sessions` analytics facts from `/learning/progress` snapshots.

## Caveats / Not Found

- `.trellis/scripts/task.py current --source` is not supported in this checkout; the script reported no `current` subcommand. The requested task directory path was used explicitly.
- The active worktree at `.claude/worktrees/agent-ab173e8434c8ac774` did not contain `.trellis/tasks/05-09-learning-statistics-foundation`; the task directory exists in the main repo at `/Users/jacob/Developer/a3.learn_platform/learning-platform/.trellis/tasks/05-09-learning-statistics-foundation`.
- No existing frontend `/learning/sessions` API wrapper or session collector was found.
- Current offline queue in `useProgressSync.ts` is memory-only; no persisted retry queue pattern was found in the frontend search.
- Current `beforeunload` beacon targets `/api/v1/learning/progress`, not a session endpoint.
- `useProgressSync.ts` includes `chapter_id` in payloads, but `UI/src/api/learning.ts` `SaveProgressRequest` does not declare `chapter_id`.
- This research file is documentation-only under `.trellis/tasks/.../research/`; no `UI/` code or `UI/operations-log.md` was modified.
