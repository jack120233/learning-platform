# Browser Smoke Validation

- **Date**: 2026-05-09
- **Scope**: read-only browser smoke against current working tree
- **Servers**: frontend `http://127.0.0.1:3000`, backend `http://127.0.0.1:8000`

## Result

PASS with caveat.

- Admin login used `admin1@example.com / Admin123456` because the login form validates email/phone input; login landed on `/admin/users`, then `/profile/messages` was opened.
- `/profile/messages`: one user feedback row was available. Opening `详情` showed drawer title `用户反馈详情`; drawer text did not contain `删除反馈`.
- Row delete control remained visible as `删除` in the feedback row. `批量删除` was not visible in the current one-row/no-selection state, so batch delete presence could not be confirmed without interacting with selection controls.
- `/profile` as admin showed `当前用户名` and editable fields; `原用户名` count was 0.
- Teacher login used `teacher1@example.com / Test123456`; `/profile` showed `当前用户名`; `原用户名` count was 0.

## Console / Request Errors

Only external placeholder banner image loads failed:

- `GET https://via.placeholder.com/1200x400/... net::ERR_CONNECTION_CLOSED` (3 requests)
- Matching browser console `Failed to load resource: net::ERR_CONNECTION_CLOSED` messages.

No app JavaScript page errors were observed.