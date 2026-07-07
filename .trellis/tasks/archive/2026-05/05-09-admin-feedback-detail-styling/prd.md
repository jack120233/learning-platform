# fix: admin feedback detail styling

## Goal

将管理员“用户反馈详情”侧边栏样式调整为接近教师“学生反馈详情”的对话式展示，提高两端反馈处理体验一致性。

## Requirements

* 管理员反馈详情抽屉采用教师侧反馈详情的结构/视觉语言。
* 展示提交人、反馈对象、状态、提交时间、反馈内容、截图、处理回复。
* 保留管理员处理反馈能力。
* 移动端不出现明显横向溢出。

## Acceptance Criteria

* [ ] 管理员反馈详情视觉与教师反馈详情明显一致。
* [ ] 原有处理反馈流程仍可用。
* [ ] 图片预览、长文本换行正常。
* [ ] 前端构建或类型检查通过。

## Technical Notes

* Compare `UI/src/views/admin/AdminMessagePage.vue` / `FeedbackManagePage.vue` with `UI/src/views/teacher/TeacherMessageCenterPage.vue` feedback drawer styles.
