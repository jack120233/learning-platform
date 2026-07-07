# brainstorm: improve admin announcement actions layout

## Goal

Improve the visual polish and usability of the admin announcement management page by redesigning the rightmost operation/actions area in the announcement table or adjacent page layout so it better matches the project's current soft-card/admin UI style.

## What I already know

* Target page: `/admin/announcements`.
* User specifically called out the rightmost operation column for each announcement row as visually poor.
* The solution should reference the current project style rather than introduce a new visual language.
* This is likely a frontend-only UI polish task under `UI/src/views/admin/AnnouncementPage.vue` or nearby admin components/API types.

## Assumptions (temporary)

* No backend behavior changes are needed.
* Existing announcement actions and permissions should remain unchanged.
* The preferred MVP is to improve layout/styling without redesigning the full announcement management workflow.

## Open Questions

* None; inspect current implementation and apply a style-consistent UI improvement.

## Requirements

* Improve the rightmost operation/actions column layout for each announcement row on `/admin/announcements`.
* Keep existing actions functionally available.
* Match existing project visual style: soft surfaces, rounded buttons/cards, compact admin controls, and responsive behavior.
* Avoid changing announcement API behavior or permissions.

## Acceptance Criteria

* [ ] Announcement operation column looks orderly and visually consistent with current admin pages.
* [ ] Existing row actions still work and remain discoverable.
* [ ] Table/page layout does not overflow awkwardly on normal desktop widths.
* [ ] Mobile/narrow viewport behavior remains usable.
* [ ] Frontend validation/build passes.
* [ ] `UI/operations-log.md` is updated.

## Definition of Done

* Frontend code changed minimally and safely.
* Frontend build/typecheck passes or any skipped validation is clearly recorded.
* Browser smoke check is performed if local services are available.
* No backend changes unless inspection reveals they are necessary.

## Out of Scope

* Changing announcement CRUD semantics.
* Adding new announcement statuses or permission logic.
* Redesigning the entire admin backend layout beyond what is needed for this page polish.

## Technical Notes

* Must inspect `UI/CLAUDE.md` before editing frontend files.
* Likely file: `UI/src/views/admin/AnnouncementPage.vue`.
* Compare style patterns in nearby admin/profile pages before implementing.
