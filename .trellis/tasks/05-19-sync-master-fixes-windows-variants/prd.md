# brainstorm: sync master fixes to Windows variants

## Goal

把 `master` 当前已经修复的 bug 同步到 Windows 单机版分支 `future/windows-local` 和课堂版分支 `future/windows-classroom`，让两个变体分支保留自身原有功能的同时获得相同修复。

## What I already know

* 用户希望同步 master 当前更新后的 bug fixes 到单机版和课堂版。
* 目标分支名来自用户描述和仓库现有分支：`future/windows-local`、`future/windows-classroom`。
* 当前 `master` 已推送到 GitHub，最新提交包含登录/认证相关修复。

## Assumptions (temporary)

* 目标是更新两个长期变体分支，而不是只在本地临时合并。
* 需要保留两个变体分支各自已有功能，不应覆盖或丢弃其差异。
* 同步方式可能是 merge master，也可能是 cherry-pick 特定提交，需先比较分支关系。

## Open Questions

* 需要同步 `master` 当前所有领先于目标分支的提交，还是只同步最近一次登录/认证修复提交？

## Requirements (evolving)

* 保留 `future/windows-local` 和 `future/windows-classroom` 各自已有功能。
* 将用户指定范围内的 master bug fixes 同步到目标分支。

## Acceptance Criteria (evolving)

* [ ] 明确同步范围：全部 master 修复或特定提交。
* [ ] `future/windows-local` 包含指定修复且保留分支特有功能。
* [ ] `future/windows-classroom` 包含指定修复且保留分支特有功能。
* [ ] 必要验证已执行并记录结果。

## Definition of Done (team quality bar)

* Tests added/updated if needed.
* Relevant frontend/backend validation executed where practical.
* Docs/notes updated if behavior changes.
* Rollout/rollback considered if risky.

## Out of Scope (explicit)

* 不主动重构 Windows 单机版或课堂版功能。
* 不删除目标分支已有差异。
* 不在未确认范围前修改分支内容。

## Technical Notes

* 待检查：两个目标分支是否存在、是否跟踪远端、与 `master` 的共同祖先和差异。
