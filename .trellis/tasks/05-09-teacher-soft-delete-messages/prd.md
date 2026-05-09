# feature: teacher soft delete messages

## Goal

Add teacher-side single and batch delete management for both `学生反馈` and `平台通知`, with backend database soft-delete semantics.

## Requirements

* In teacher message center `学生反馈` tab:
  * Add single delete action.
  * Add batch selection mode and batch delete action.
  * Deleted feedbacks must be hidden from teacher list/detail through soft delete, not hard-deleted.
* In teacher message center `平台通知` tab:
  * Keep/add single delete action.
  * Keep/add batch selection mode and batch delete action.
  * Delete must be soft delete in the database.
* Add or update backend endpoints/services/tests as needed.
* Update `UI/operations-log.md` and `project_code/operations-log.md`.

## Acceptance Criteria

* [ ] Teacher `学生反馈` tab shows single delete and batch delete controls.
* [ ] Teacher deleting student feedback hides it from future lists but does not physically remove the DB row.
* [ ] Teacher `平台通知` tab shows single delete and batch delete controls.
* [ ] Teacher deleting platform notifications uses existing soft-delete message semantics or adds it if missing.
* [ ] Frontend build passes.
* [ ] Backend tests for affected endpoints pass.
