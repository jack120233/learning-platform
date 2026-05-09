# fix: profile and admin cleanup

## Goal

Clean up profile/admin UI details from the post-review feedback.

## Requirements

* In `/profile`, remove standalone rows for `改名机会` and `注册时间` for all roles.
* In `/profile`, username input hint should only show `剩余 N 次修改机会` when the current user has remaining opportunities.
* If a non-teacher user has no remaining username-change opportunities, the username input is disabled and no hint is shown.
* Teachers are not limited by username-change opportunity count.
* In admin feedback detail drawer, move `反馈编号 #...` away from the visual area that conflicts with `用户名#id`.
* In `/admin/users`, remove the `用户昵称` column.
* Update `UI/operations-log.md`.

## Acceptance Criteria

* [ ] `/profile` does not show standalone `改名机会` or `注册时间` rows.
* [ ] `/profile` hint only says `剩余 N 次修改机会` when shown.
* [ ] Teacher profile username field is not disabled due to username-change count.
* [ ] Admin feedback detail no longer places `反馈编号 #...` next to identity in a confusing way.
* [ ] `/admin/users` table has no `用户昵称` column.
* [ ] Frontend build passes.
