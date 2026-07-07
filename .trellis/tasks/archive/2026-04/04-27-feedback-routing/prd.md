# Feedback Routing Optimization

## Goal

Optimize the feedback submission and handling flow so course/video/learning feedback submitted in a course context can be directed to a selected target teacher, while preserving submitter feedback history and administrator oversight. This reflects the implemented product flow: students choose the target teacher when submitting course feedback, and backend visibility/processing permissions are enforced by `Feedback.target_user_id`.

## What I already know

* The user reported a product logic issue on `http://localhost:3000/profile`.
* Current behavior: feedback submitted by two of the three roles goes to the administrator role.
* Expected scenario: students submit feedback while watching videos or using the platform; the feedback should go to the corresponding responsible person.
* Course/video/learning problems should be submitted with the current `course_id` and a selected target teacher.
* Platform/operation problems remain in the administrator/global queue for MVP because profile/system feedback has no course context and there is no dedicated customer-service/platform-operations role.
* This is a fullstack/cross-layer task because it affects frontend feedback UI/API and backend feedback routing/query/permission behavior.
* `Course` still has `teacher_id`, and the frontend uses it to default the target teacher to the current course teacher; however, routing and processing permissions are based on `Feedback.target_user_id` after submission.
* The implemented feedback payload contains `feedback_type`, optional `course_id`, `target_user_id` for course feedback, `content`, and optional `images`.
* Backend feedback visibility is permission-based: roles with `admin.feedback` see/process all feedback; a target teacher sees/processes feedback assigned to them; submitters still see their own feedback history.
* A teacher feedback workbench now exists at `/teacher/feedbacks` for course feedback handling.
* Tests now cover target-teacher visibility/processing, course-owner non-target denial, invalid target teacher rejection, teacher options, and database compatibility for `target_user_id`.

## Requirements

* Course/video/learning feedback must not be administrator-only by default.
* Course feedback must submit the current `course_id` and a selected `target_user_id`; the backend must validate that the target user exists, is active, and has the teacher role.
* The feedback form should default the target teacher to the current course teacher while still allowing the student to choose another active teacher.
* A target teacher must be able to see and process feedback assigned to them.
* Teachers must not be able to see/process feedback assigned to another teacher unless they also have global `admin.feedback` permission.
* The submitter must continue to see their own submitted feedback in profile feedback history.
* Admin users or roles with `admin.feedback` must retain global oversight and processing access.
* Frontend and backend fields must stay aligned with the existing `{ code, message, data }` response shape and `student`/`teacher`/`admin` roles.
* Profile/system feedback has no course context; for MVP, profile direct submission is hidden and system/platform feedback remains in the admin/global queue.
* Course detail feedback should submit `feedback_type: "course"`, `course_id`, and `target_user_id`, then become visible to the selected target teacher.

## Acceptance Criteria

* [x] A student can submit course-related feedback from a course page with `course_id` and `target_user_id`.
* [x] The selected target teacher can see and process/reply to assigned course feedback.
* [x] A teacher cannot see/process feedback assigned to another teacher without global `admin.feedback` permission.
* [x] The submitter can still see their own submitted feedback in profile.
* [x] Admin/global feedback managers can still see and process all feedback.
* [x] Profile direct feedback submission is hidden; profile feedback history and replies remain available.
* [x] Frontend route/API usage clearly separates global admin feedback management from teacher course-feedback handling.
* [x] Backend pytest covers target-teacher visibility, processing permissions, invalid target teacher rejection, and compatibility behavior.
* [x] Relevant frontend build/typecheck and backend tests were run and recorded in operations logs.

## Definition of Done

* Tests added/updated where appropriate.
* Frontend typecheck/build or relevant verification completed.
* Backend pytest for feedback-related behavior completed.
* `UI/operations-log.md` and/or `project_code/operations-log.md` updated if actual frontend/backend files change.
* Trellis spec guidelines followed.

## Technical Approach

MVP uses explicit target-teacher routing with backend validation:

* `Feedback` stores `target_user_id` for course feedback. Legacy databases are patched by the backend compatibility check to add the column when missing.
* Course feedback creation requires both `course_id` and `target_user_id`; the backend validates that the course exists and that the target user is an active teacher.
* Backend list/detail/process checks treat a user as authorized when any of these is true:
  * the user submitted the feedback;
  * the user's role has `admin.feedback`;
  * the feedback is assigned to the current user through `Feedback.target_user_id`.
* Backend list query supports a teacher filter using `Feedback.target_user_id == current_user.id` for teacher workbench data without exposing unrelated assigned feedback.
* Existing `/api/v1/feedbacks` remains the shared endpoint, but its behavior branches by role/permission/target-teacher assignment.
* `GET /api/v1/users/teachers/options` provides active teacher options for the frontend selector without exposing sensitive contact fields.
* Frontend exposes `/teacher/feedbacks` for teacher-side feedback processing and keeps `/admin/feedbacks` as the global oversight path for `admin.feedback` users.
* Teacher UI copy uses teacher/processing wording instead of fixed “管理员回复” wording.
* The client may send only the selected `target_user_id`; the backend still owns validation and authorization.

## Decision (ADR-lite)

**Context**: Feedback routing needs to match the teaching platform scenario without introducing a new operations/customer-service role or a large notification system. During implementation, the product direction changed from automatic course-owner routing to student-selected target-teacher routing in course feedback context.

**Decision**: Use `target_user_id` for course/video/learning feedback. The course page defaults the selector to the current course teacher, but the student can choose another active teacher. Keep profile/system feedback out of direct submission for MVP and keep administrator/global feedback management for oversight.

**Consequences**: This adds a small schema change but makes routing explicit and reviewable, while still keeping backend validation authoritative. It does not solve arbitrary platform feedback assignment outside course context; that remains a future enhancement if the product needs manual routing or a dedicated support role.

## Out of Scope

* Replacing the entire messaging/notification system.
* Introducing a new customer-service/platform-operator role.
* Adding a manual teacher-picker for profile/system feedback in the MVP.
* Large admin dashboard redesign.
* Real-time notifications to teachers.

## Technical Notes

* Frontend inspected:
  * `UI/src/components/feedback/FeedbackForm.vue` submits `feedback_type`, `course_id`, `target_user_id`, `content`, and `images` through `submitFeedback` when the feedback type is `course`.
  * `UI/src/views/course/CourseDetailPage.vue` embeds `FeedbackForm` with `default-type="course"`, `type-locked`, `courseId`, `courseTeacherId`, and `courseTeacherName`.
  * `UI/src/views/profile/ProfileLayout.vue` no longer exposes direct feedback submission without course context; profile keeps feedback history access.
  * `UI/src/api/learning.ts` defines `SubmitFeedbackRequest.target_user_id` and `fetchTeacherOptions` for `/users/teachers/options`.
  * `UI/src/api/profile.ts` maps submitter feedback history including target teacher fields via `/users/me/feedbacks`.
  * `UI/src/api/admin.ts` exposes feedback list/detail/process APIs and target teacher fields against `/feedbacks`.
  * `UI/src/views/teacher/FeedbackManagePage.vue` provides the teacher workbench for assigned course feedback.
  * `UI/src/views/admin/FeedbackManagePage.vue` remains the admin/global management page and displays target teacher fields.
  * `UI/src/router/index.ts` has `/teacher/feedbacks` and `/admin/feedbacks` as separate feedback management entries.
* Backend inspected:
  * `project_code/backend/app/models/feedback.py` has `target_user_id` in addition to `user_id`, `type`, `course_id`, `status`, `reply`, `replied_at`, and `replied_by`.
  * `project_code/backend/app/core/db_schema.py` includes compatibility logic to add `feedbacks.target_user_id` to old databases.
  * `project_code/backend/app/models/course.py` still has `teacher_id`, which is returned as `course_teacher_id` for context and default frontend selection.
  * `project_code/backend/app/schemas/feedback.py` validates `course` feedback requires both `course_id` and `target_user_id`, and responses include `course_teacher_id`, `target_user_id`, `target_username`, and `target_nickname`.
  * `project_code/backend/app/services/feedback_service.py` joins `Feedback`, submitter `User`, `Course`, and target `User`, and filters teacher workbench data by `Feedback.target_user_id`.
  * `project_code/backend/app/api/v1/feedbacks.py` uses `admin.feedback` for global visibility and `target_user_id == current_user.id` for target teacher visibility/processing.
  * `project_code/backend/app/api/v1/users.py` exposes `/users/teachers/options` and continues to use `feedback_service.get_list(user_id=current_user)` for `/users/me/feedbacks`.
  * `project_code/backend/tests/test_feedbacks.py` covers create/list/detail/process, target-teacher permissions, invalid target teacher rejection, teacher options, and old database compatibility.
