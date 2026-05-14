# Windows 单机版实机测试检查清单

## 1. 测试环境记录

请先记录：

- Windows 版本：
- 是否真机 / 虚拟机：
- 项目所在路径：
- 路径是否包含中文或空格：
- Python 虚拟环境是否已准备：`project_code\.venv\Scripts\python.exe`
- Node / npm 是否可用：
- 测试日期：
- 测试人：

建议至少测两种路径：

- 普通路径：`D:\learning-platform`
- 含空格路径：`D:\Test Folder\learning-platform`

## 2. 交付包完整性检查

### 操作

在一个全新的解压目录中检查交付包，优先覆盖普通路径和含空格路径。

必须存在：

- `start-windows-local.cmd`
- `config\windows-local.env`
- `project_code\.venv\Scripts\python.exe` 或等价后端运行环境
- `UI\dist\index.html`，或 `UI\package.json` + 可用 npm 构建环境

### 预期结果

- 不需要用户安装 MySQL。
- 不需要用户安装 Redis。
- 不需要用户手动执行 `init_db.py` 或 `seed_data.py`。
- 如果是 `zip + launcher` 形态，解压后应能直接进入首次启动测试。
- 如果后续改为安装器形态，安装器必须默认保留用户数据，并明确说明卸载/升级行为。

## 3. 首次启动测试

### 操作

1. 确认以下文件存在：
   - `start-windows-local.cmd`
   - `config\windows-local.env`
   - `project_code\.venv\Scripts\python.exe`
   - `UI\package.json`
2. 如果存在旧数据，先备份后删除：
   - `project_code\backend\data\windows-local.db`
   - `project_code\backend\data\cache\`
   - `project_code\backend\logs\`
   - 不要删除 `project_code\backend\uploads\`，除非确认是测试数据。
3. 双击运行 `start-windows-local.cmd`。

### 预期结果

- 命令行窗口没有直接闪退。
- 如果 `UI\dist\index.html` 不存在，会自动执行前端构建。
- 后端成功启动。
- 浏览器自动打开 `http://127.0.0.1:8000/`。
- 页面显示前端应用，而不是纯 JSON API 欢迎信息。
- 自动生成：
  - `project_code\backend\data\windows-local.db`
  - `project_code\backend\data\cache\`
  - `project_code\backend\logs\`

### 如失败，请收集

- 控制台截图
- `project_code\backend\logs\windows-local-startup.log`
- `project_code\backend\logs\windows-local-startup-error.log`

## 3. 登录账号验证

使用种子账号登录。

| 角色 | 用户名 | 密码 | 预期 |
| --- | --- | --- | --- |
| 管理员 | `admin1` | `Admin123456` | 可进入管理员相关页面 |
| 教师 | `teacher1` | `Test123456` | 可进入教师课程管理相关页面 |
| 学生 | `student1` | `Test123456` | 可进入学习相关页面 |

检查点：

- 登录成功后不会白屏。
- 刷新页面后登录态正常。
- 退出登录后不能继续访问受保护页面。
- 不同角色看到的菜单和权限大致正确。

## 4. 核心功能冒烟测试

### 首页 / 课程

1. 打开首页。
2. 查看课程列表是否正常加载。
3. 点击任意课程进入课程详情页。
4. 刷新课程详情页。

预期：

- 页面正常显示。
- 刷新后不 404。
- 没有明显接口错误弹窗。

### 学习页

使用学生账号：

1. 打开课程详情。
2. 进入学习页。
3. 点击章节 / 小节。
4. 刷新页面。
5. 返回首页后再次进入学习页。

预期：

- 学习页能打开。
- 章节、小节信息正常显示。
- 刷新后页面仍可恢复。
- 没有明显白屏或路由错误。

### 教师课程管理

使用教师账号：

1. 进入教师课程列表。
2. 查看已有课程。
3. 尝试进入课程编辑页。
4. 查看章节、资源管理区域。

预期：

- 教师页面可正常访问。
- 课程列表正常加载。
- 编辑页不白屏。

### 管理后台

使用管理员账号：

1. 进入用户管理。
2. 进入分类管理。
3. 进入标签管理。
4. 进入公告管理。
5. 进入反馈管理。

预期：

- 管理页面可访问。
- 表格数据正常加载。
- 新增、编辑、删除按钮显示符合权限。

## 5. 上传与静态文件测试

任选一个支持上传的入口，例如：

- 课程封面上传
- 头像上传
- 反馈图片上传
- 课程资源上传

上传一个小文件。

预期结果：

- 上传接口成功。
- 页面能显示上传后的图片或文件链接。
- 文件落在 `project_code\backend\uploads\`。
- 浏览器中直接访问上传文件 URL 时可以打开。
- 刷新页面后，上传文件仍可访问。

## 6. 路由刷新与 404 测试

### 前端路由刷新

请直接在浏览器地址栏打开或刷新：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/courses`
- `http://127.0.0.1:8000/profile`
- `http://127.0.0.1:8000/teacher/courses`
- `http://127.0.0.1:8000/admin/users`

预期：

- 前端页面正常显示。
- 不应出现后端 404。
- 不应下载文件或显示源码。

### API 404 检查

直接访问：

- `http://127.0.0.1:8000/api/unknown`
- `http://127.0.0.1:8000/api/v1/unknown`
- `http://127.0.0.1:8000/uploads/not-exist.png`

预期：

- 这些地址应该是 404。
- 不应该返回前端首页 HTML。
- 不应该显示完整前端应用。

## 7. 重启与数据保留测试

### 操作

1. 登录并确认系统可用。
2. 关闭启动窗口或关闭后端进程。
3. 再次双击 `start-windows-local.cmd`。
4. 再次登录。
5. 检查课程、用户、上传文件是否仍存在。

### 预期结果

- 第二次启动不会重复导入种子数据导致重复用户。
- 原有数据保留。
- 上传文件仍可访问。
- 日志继续写入。

## 8. 端口占用测试

### 操作

1. 保持第一次启动的后端运行。
2. 再次双击 `start-windows-local.cmd`。

### 预期结果

- 脚本提示端口 `8000` 已被占用。
- 窗口保留，不闪退。
- 提示中包含占用进程 PID。
- 不应启动第二个异常后端。

## 9. 异常场景测试

可选，但建议至少测两个。

### 缺少虚拟环境

临时改名 `project_code\.venv`，然后运行 `start-windows-local.cmd`。

预期：

- 明确提示 Python virtual environment not found。
- 窗口不闪退。
- 写入错误日志。

### 缺少配置文件

临时改名 `config\windows-local.env`，然后运行 `start-windows-local.cmd`。

预期：

- 明确提示 Missing config file。
- 窗口不闪退。
- 写入错误日志。

### 前端 dist 不存在

删除或改名 `UI\dist`，然后运行 `start-windows-local.cmd`。

预期：

- 自动执行 `npm run build`。
- 构建成功后继续启动后端。
- 浏览器打开后能访问前端页面。

## 10. 测试结论模板

```text
测试环境：
- Windows 版本：
- 项目路径：
- 是否含空格/中文：
- 测试人：
- 测试时间：

结论：
- 首次启动：通过 / 不通过
- 前端构建：通过 / 不通过 / 未触发
- 自动建库：通过 / 不通过
- 自动导种子：通过 / 不通过
- 登录验证：通过 / 不通过
- 核心页面：通过 / 不通过
- 上传验证：通过 / 不通过 / 未测
- 重启数据保留：通过 / 不通过
- 端口占用提示：通过 / 不通过 / 未测

问题列表：
1. 问题现象：
   操作步骤：
   预期结果：
   实际结果：
   截图/日志：
   是否可复现：

2. 问题现象：
   操作步骤：
   预期结果：
   实际结果：
   截图/日志：
   是否可复现：
```

请把以下材料随问题反馈一起发回：

- 控制台截图
- `project_code\backend\logs\windows-local-startup.log`
- `project_code\backend\logs\windows-local-startup-error.log`
- 如果页面异常，再附浏览器开发者工具 Console / Network 截图。
