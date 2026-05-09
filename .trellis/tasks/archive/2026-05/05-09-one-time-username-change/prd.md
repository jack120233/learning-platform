# feature: one-time username change

## Goal

允许用户在个人信息页自助修改用户名一次，修改前二次确认，后端强制一次性限制并记录原用户名，同时为教师后续再次开放一次修改名额预留能力。

## Requirements

* 用户可在 `/profile` 修改用户名一次。
* 修改用户名前必须二次确认。
* 后端校验用户名唯一性和格式。
* 后端记录原用户名，且第二次自助修改会被拒绝。
* 响应中提供是否还可修改用户名的状态，供前端控制按钮/提示。
* 教师端提供给用户再次开放一次用户名修改机会的完整入口。
* 后端提供教师重置用户改名机会的接口和权限校验。

## Acceptance Criteria

* [ ] 首次修改用户名成功，个人信息和全局 store 同步更新。
* [ ] 第二次自助修改被后端拒绝，前端展示明确提示。
* [ ] 数据库可追溯原用户名。
* [ ] 用户名冲突时返回明确错误。
* [ ] 后端用户测试覆盖首次修改、重复修改、冲突、教师重置改名机会、权限/字段状态。
* [ ] 前端构建/类型检查通过，后端相关 pytest 通过。

## Technical Notes

* Likely backend files: `models/user.py`, `schemas/user.py`, `services/user_service.py`, `api/v1/users.py`, `core/db_schema.py`, `tests/test_users.py`.
* Likely frontend files: `UI/src/api/profile.ts`, `UI/src/views/profile/ProfileInfoPage.vue`, `UI/src/store/user.ts`.
