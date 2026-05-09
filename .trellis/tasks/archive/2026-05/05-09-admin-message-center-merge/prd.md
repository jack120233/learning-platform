# fix: admin message center merge

## Goal

Restore `/admin/messages` as an admin-layout page and merge the newer admin message-center design into the existing admin page main/right content.

## Requirements

* `/admin/messages` should render an admin message center page inside `AdminLayout` instead of redirecting to `/profile/messages`.
* Admin sidebar can stay without a visible `消息中心` menu item, per prior requirement, but direct route should work.
* The page should use the newer admin message-center experience/design already present in the repository rather than the old plain version.
* Keep `/profile/messages` as the personal message center.
* Update `UI/operations-log.md`.

## Acceptance Criteria

* [ ] Visiting `/admin/messages` as admin shows the admin message center in the admin layout main content area.
* [ ] `/admin/messages` no longer redirects to `/profile/messages`.
* [ ] Admin sidebar still does not expose a separate `系统消息` menu item unless current code requires active route highlighting.
* [ ] Frontend build passes.
