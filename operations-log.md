# UI 操作记录

## 教师端资源上传联调收口与前端留痕约束
时间：2026-04-10

- 变更原因：教师端课程编辑页已经接入课程资料、章节资源、小节资源和分片上传能力，但前端真实校验、接口文档和协作约束还没有完全同步，容易出现“界面提示支持、前端实际拦截”以及“改了 UI 却没有留痕”的问题。
- 涉及文件：
  - `CLAUDE.md`
  - `operations-log.md`
  - `docs/前端接口文档.md`
  - `src/views/teacher/CourseFormPage.vue`
  - `src/views/teacher/components/ResourceManager.vue`
- 核心改动：
  - 在 `UI/CLAUDE.md` 中新增前端硬约束：只要 `UI` 仓库有实际文件变更，必须更新 `UI/operations-log.md`；前端 API 契约、上传流程或开发脚本变化时，必须同步更新前端文档。
  - 新增 `UI/operations-log.md`，作为前端仓库正式留痕入口。
  - 修复教师端资源上传前端校验，补齐 `.mov`、Excel、CSV、Markdown、ZIP、`application/octet-stream` 等当前联调实际需要的格式判断，并在资源列表 props 更新时同步本地视图。
  - 将课程资料上传组件的 `accept` 属性与页面文案统一到当前支持范围。
  - 更新 `docs/前端接口文档.md`，补充章节级资源、课程资料双模式上传、分片上传链路与教师端资源绑定约定。
- 验证结果：
  - 已执行：`npx vue-tsc -b`
  - 结果：通过
  - 已执行：`npm run build`
  - 结果：通过
  - 备注：构建产物提示存在大于 500kB 的 chunk 警告，但不影响本次功能正确性。
