# Backend Upload and Resource API Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 补齐教师端课程管理页面所需的上传、资料绑定、章节/小节资源绑定与前端兼容接口，形成“上传文件 -> 绑定业务 -> 页面回显 -> 删除资源”的完整闭环。

**Architecture:** 延续现有 FastAPI + Service + Pydantic + pytest 的分层。上传层拆成两类能力：小文件直接写入 `uploads/` 下的正式目录，大文件先写入 `uploads/.chunk-sessions/<upload_id>/` 并用 manifest 管理分片状态，再在 `complete` 阶段合并到正式目录。业务层优先采用“扩展现有路由 + 增加前端兼容别名 + 输出字段兼容转换”的方式补齐能力；章节级资源因为前端真实依赖 `chapter.resources`，单独作为一项模型调整处理。

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy AsyncSession, pytest, httpx, 本地文件系统存储

---

### Task 1: 扩展通用小文件上传接口

**Files:**
- Create: `project_code/backend/tests/test_uploads.py`
- Create: `project_code/backend/app/schemas/upload.py`
- Modify: `project_code/backend/app/config.py`
- Modify: `project_code/backend/app/api/v1/uploads.py`
- Modify: `project_code/backend/app/services/upload_service.py`

**Step 1: Write the failing test**

在 `project_code/backend/tests/test_uploads.py` 先写 3 个失败用例：

```python
async def test_upload_file_supports_course_cover_png(...): ...
async def test_upload_file_supports_material_pdf(...): ...
async def test_upload_file_rejects_unsupported_extension(...): ...
```

重点断言：
- `POST /api/v1/upload/file` 对 `course-cover.png` 仍返回 200
- `POST /api/v1/upload/file` 对 `lesson-outline.pdf` 返回统一字段：`file_name`、`file_url`、`url`、`file_size`、`content_type`
- PDF 文件实际落盘到非 `course-covers` 目录
- 不支持的扩展名返回 422

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_uploads.py -v`
Expected: FAIL，至少出现“只支持 JPG/PNG”或模块/路由不存在的断言错误

**Step 3: Write minimal implementation**

实现要点：
- 在 `project_code/backend/app/config.py` 增加上传子目录与大小配置，例如：
  - `general_upload_subdir`
  - `chunk_upload_tmp_subdir`
  - `general_file_max_size`
- 在 `project_code/backend/app/schemas/upload.py` 定义统一响应模型，供 `/upload/*` 共用
- 将 `project_code/backend/app/services/upload_service.py` 从“仅封面”改为“按扩展名/MIME 分类保存”
- 保留封面上传兼容行为：
  - 图片仍允许存到 `course-covers`
  - 文档/压缩包等进入通用目录
- `/api/v1/upload/file` 继续限制为讲师/管理员可用

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_uploads.py -k "upload_file" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_uploads.py app/config.py app/api/v1/uploads.py app/services/upload_service.py app/schemas/upload.py
git commit -m "feat: extend generic file upload endpoint"
```

### Task 2: 实现分片上传 init/chunk/complete

**Files:**
- Modify: `project_code/backend/tests/test_uploads.py`
- Modify: `project_code/backend/app/schemas/upload.py`
- Modify: `project_code/backend/app/api/v1/uploads.py`
- Modify: `project_code/backend/app/services/upload_service.py`

**Step 1: Write the failing test**

在 `project_code/backend/tests/test_uploads.py` 增加 4 个用例：

```python
async def test_init_chunk_upload_returns_upload_id(...): ...
async def test_upload_chunk_saves_single_part(...): ...
async def test_complete_chunk_upload_merges_parts(...): ...
async def test_complete_chunk_upload_rejects_missing_chunks(...): ...
```

重点断言：
- `POST /api/v1/upload/init` 返回 `upload_id`、`chunk_size`、`total_chunks`
- `POST /api/v1/upload/chunk` 成功写入分片文件
- `POST /api/v1/upload/complete` 合并后返回统一文件信息
- 少片时返回 422

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_uploads.py -k "chunk_upload" -v`
Expected: FAIL，出现 404 或字段缺失

**Step 3: Write minimal implementation**

实现要点：
- schema：
  - `ChunkUploadInitRequest`
  - `ChunkUploadInitResponse`
  - `ChunkUploadCompleteRequest`
- service：
  - `init_chunk_upload()`
  - `save_chunk()`
  - `complete_chunk_upload()`
- 存储策略：
  - manifest 建议保存 `file_name`、`file_size`、`chunk_size`、`total_chunks`、`received_chunks`
  - 分片文件命名为 `<chunk_index>.part`
  - complete 时按序合并，成功后删除临时目录
- 视频时长先不做真实解析，返回结构里允许 `duration=None`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_uploads.py -k "chunk_upload" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_uploads.py app/api/v1/uploads.py app/services/upload_service.py app/schemas/upload.py
git commit -m "feat: add chunk upload lifecycle endpoints"
```

### Task 3: 让课程资料接口同时支持 JSON 绑定与 multipart 直传

**Files:**
- Modify: `project_code/backend/tests/test_courses.py`
- Modify: `project_code/backend/app/api/v1/courses.py`
- Modify: `project_code/backend/app/services/course_service.py`
- Modify: `project_code/backend/app/services/upload_service.py`
- Modify: `project_code/backend/app/schemas/course.py`

**Step 1: Write the failing test**

在 `project_code/backend/tests/test_courses.py` 新增：

```python
async def test_create_material_from_json_payload(...): ...
async def test_create_material_from_multipart_file(...): ...
async def test_delete_material_legacy_post_route(...): ...
```

重点断言：
- 现有 JSON `POST /api/v1/courses/{course_id}/materials` 行为不回归
- `multipart/form-data` 上传文件后自动落盘并创建资料记录
- `POST /api/v1/courses/{course_id}/materials/{material_id}/delete` 返回 200

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_courses.py -k "material" -v`
Expected: FAIL，multipart 目前会 422，legacy delete 目前会 404

**Step 3: Write minimal implementation**

实现要点：
- 在 `project_code/backend/app/api/v1/courses.py` 按 `Content-Type` 分支：
  - `application/json` 继续走原 `MaterialCreate`
  - `multipart/form-data` 直接收 `UploadFile`
- multipart 分支流程：
  1. 调 `upload_service` 保存文件
  2. 构造 `MaterialCreate(name=file_name, file_url=..., file_size=..., file_type=...)`
  3. 调 `material_service.create(...)`
- 增加 legacy 路由：
  - `POST /courses/{course_id}/materials/{material_id}/delete`
- 响应字段增加前端兼容别名：
  - `material_id`
  - `file_name`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_courses.py -k "material" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_courses.py app/api/v1/courses.py app/services/course_service.py app/services/upload_service.py app/schemas/course.py
git commit -m "feat: support direct material upload and legacy delete route"
```

### Task 4: 对齐小节资源接口的请求和响应字段

**Files:**
- Modify: `project_code/backend/tests/test_content.py`
- Modify: `project_code/backend/app/api/v1/content.py`
- Modify: `project_code/backend/app/services/content_service.py`
- Modify: `project_code/backend/app/schemas/content.py`

**Step 1: Write the failing test**

在 `project_code/backend/tests/test_content.py` 新增：

```python
async def test_create_section_resource_accepts_resource_type_payload(...): ...
async def test_delete_section_resource_legacy_post_route(...): ...
```

重点断言：
- 可接受前端当前 payload：
  - `resource_type`
  - `title`
  - `file_name`
  - `file_url`
  - `file_size`
  - `sort_order`
  - `is_free`
- 响应中同时返回：
  - `resource_id`
  - `resource_type`
  - `file_name`
- `POST /courses/{course_id}/sections/{section_id}/resources/{resource_id}/delete` 可删除

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_content.py -k "section_resource" -v`
Expected: FAIL，当前模型只接受 `type` 且 legacy delete 不存在

**Step 3: Write minimal implementation**

实现要点：
- 在 `project_code/backend/app/schemas/content.py` 为创建模型增加兼容输入：
  - `type` 与 `resource_type` 二选一
  - `title` 为空时回退到 `file_name`
- 在响应模型中提供前端兼容字段：
  - `resource_id <- id`
  - `resource_type <- type`
  - `file_name <- title`
- 在 `project_code/backend/app/api/v1/content.py` 增加 section resource legacy delete 路由

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_content.py -k "section_resource" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_content.py app/api/v1/content.py app/services/content_service.py app/schemas/content.py
git commit -m "feat: align section resource api with frontend payload"
```

### Task 5: 支持真正的章节级资源

**Files:**
- Modify: `project_code/backend/tests/test_content.py`
- Modify: `project_code/backend/app/models/content.py`
- Modify: `project_code/backend/app/api/v1/content.py`
- Modify: `project_code/backend/app/services/content_service.py`
- Modify: `project_code/backend/app/schemas/content.py`

**Step 1: Write the failing test**

在 `project_code/backend/tests/test_content.py` 新增：

```python
async def test_create_chapter_resource(...): ...
async def test_delete_chapter_resource_legacy_post_route(...): ...
async def test_chapter_resource_does_not_change_section_counts(...): ...
```

重点断言：
- `POST /api/v1/courses/{course_id}/chapters/{chapter_id}/resources` 返回 200
- 返回数据能直接回填到前端 `chapter.resources`
- 删除接口 `POST /api/v1/courses/{course_id}/chapters/{chapter_id}/resources/{resource_id}/delete` 生效
- 章节资源不会错误修改小节 `resource_count` / `duration`

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_content.py -k "chapter_resource" -v`
Expected: FAIL，当前无路由且 `Resource.section_id` 不允许为空

**Step 3: Write minimal implementation**

实现要点：
- 将 `project_code/backend/app/models/content.py` 中 `Resource.section_id` 改为可空
- `resource_service.create(...)` 拆成两类入口：
  - `create_for_section(...)`
  - `create_for_chapter(...)`
- 数据更新规则：
  - 章节资源只更新 `Chapter.total_duration` / `Course.total_duration`（若为视频）
  - 不更新 `Section.duration` / `Section.resource_count`
- 在 `project_code/backend/app/api/v1/content.py` 新增 chapter resource 创建与删除路由
- 保持学习模块使用 section 资源时不受影响

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_content.py -k "chapter_resource" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_content.py app/models/content.py app/api/v1/content.py app/services/content_service.py app/schemas/content.py
git commit -m "feat: add chapter level resource support"
```

### Task 6: 补齐课程详情返回的 materials / chapter.resources / section.resources

**Files:**
- Modify: `project_code/backend/tests/test_courses.py`
- Modify: `project_code/backend/app/api/v1/courses.py`
- Modify: `project_code/backend/app/services/course_service.py`
- Modify: `project_code/backend/app/schemas/course.py`
- Modify: `project_code/backend/app/schemas/content.py`

**Step 1: Write the failing test**

在 `project_code/backend/tests/test_courses.py` 增加：

```python
async def test_get_course_detail_includes_materials_and_resources(...): ...
```

重点断言：
- `GET /api/v1/courses/{course_id}` 返回：
  - `materials`
  - `chapters[].resources`
  - `chapters[].sections[].resources`
- 字段名兼容前端：
  - `material_id`
  - `resource_id`
  - `resource_type`
  - `file_name`

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_courses.py -k "course_detail_includes_materials_and_resources" -v`
Expected: FAIL，当前详情未加载这些集合

**Step 3: Write minimal implementation**

实现要点：
- `project_code/backend/app/services/course_service.py`
  - 在 `get_chapters_with_sections()` 中同时加载 chapter resources 与 section resources
  - 新增读取课程 materials 的逻辑
- `project_code/backend/app/api/v1/courses.py`
  - 将 `materials` 合并进详情响应
- `project_code/backend/app/schemas/course.py` / `project_code/backend/app/schemas/content.py`
  - 为 teacher 端详情补齐字段模型与兼容别名

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_courses.py -k "course_detail_includes_materials_and_resources" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_courses.py app/api/v1/courses.py app/services/course_service.py app/schemas/course.py app/schemas/content.py
git commit -m "feat: include teacher asset data in course detail response"
```

### Task 7: 整体验证与文档收尾

**Files:**
- Modify: `project_code/docs/api-endpoint-inventory.md`
- Modify: `project_code/docs/api-testing-guide.md`

**Step 1: Run focused backend suites**

Run:

```bash
pytest tests/test_uploads.py -v
pytest tests/test_courses.py -k "upload or material or course_detail_includes_materials_and_resources" -v
pytest tests/test_content.py -k "resource" -v
```

Expected: PASS

**Step 2: Run regression suite around impacted modules**

Run:

```bash
pytest tests/test_courses.py tests/test_content.py tests/test_learning.py -v
```

Expected: PASS，若 `test_learning.py` 因章节资源引入回归，需要先修复再继续

**Step 3: Update docs**

文档至少补充：
- `/api/v1/upload/file`
- `/api/v1/upload/init`
- `/api/v1/upload/chunk`
- `/api/v1/upload/complete`
- `/api/v1/courses/{course_id}/materials` 的双模式行为
- chapter/section resource legacy delete 路由

**Step 4: Smoke test manually**

在本地联调教师端页面，手动验证：
- 上传封面
- 上传课程资料
- 小节上传视频
- 小节上传课件
- 章节整体资源管理
- 删除资源后页面列表即时刷新

**Step 5: Commit**

```bash
git add docs/api-endpoint-inventory.md docs/api-testing-guide.md
git commit -m "docs: document teacher upload and resource api flow"
```

## Notes and Assumptions

- 假设当前项目仍使用 `metadata.create_all()` 或初始化脚本建表；若线上已有持久化数据库，Task 5 需要补一份迁移脚本。
- 假设第一阶段只做本地文件系统存储，不引入 OSS / MinIO / S3。
- 假设视频元数据提取不是本轮 P0；若前端后续强依赖 `duration`，可在 `complete` 后追加 ffprobe 解析。
- 若执行时希望降低模型改动风险，可以先完成 Task 1-4 与 Task 6，再落 Task 5。
