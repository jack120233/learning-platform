## 项目上下文摘要（backend-runbat-fix）
生成时间：2026-04-17

### 1. 相似实现分析
- **实现1**: backend/run.bat:1-28
  - 模式：批处理脚本内定位虚拟环境并直接启动 uvicorn。
  - 可复用：`%~dp0` 用于回到脚本目录。
  - 需注意：原实现夹杂 `start powershell`，导致错误展示链路被打断。

- **实现2**: backend/app/main.py:16-17
  - 模式：应用入口依赖 `app.main:app` 这种包导入方式。
  - 可复用：沿用 `uvicorn app.main:app` 作为唯一启动入口。
  - 需注意：必须保证工作目录或 `PYTHONPATH` 指向 `backend/`，否则会报 `No module named 'app'`。

- **实现3**: docs/api-testing-guide.md:37-45
  - 模式：文档约定先进入 `backend` 目录，再执行 `uvicorn app.main:app --reload --port 8000`。
  - 可复用：保持已有启动命令不变。
  - 需注意：脚本也要复用同一目录约定，不能引入额外窗口行为。

### 2. 项目约定
- **命名约定**: 后端入口包名固定为 `app`，启动脚本文件名为 `run.bat`。
- **文件组织**: 启动脚本位于 `backend/`，虚拟环境优先查找 `project_code/.venv`，其次查找工作区根级 `.venv`。
- **代码风格**: 批处理输出使用简短中文提示，错误后保留 `pause` 便于查看。

### 3. 可复用组件清单
- `backend/run.bat`：现有虚拟环境探测逻辑。
- `backend/app/main.py`：FastAPI 应用真实入口。
- `docs/api-testing-guide.md`：已有后端手动启动方式。

### 4. 测试策略
- **验证方式**: 直接执行 `backend/run.bat`。
- **参考命令**: `..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000`
- **覆盖要求**: 至少验证能显示真实错误，且修复后能正常进入 uvicorn 启动日志。

### 5. 依赖和集成点
- **外部依赖**: `uvicorn`。
- **内部依赖**: `backend/app/main.py`。
- **集成方式**: 批处理脚本设置 Python 解释器与 `PYTHONPATH` 后调用模块启动。

### 6. 技术选型理由
- **为什么用这个方案**: 保持现有 `uvicorn app.main:app` 入口不变，只修正脚本工作目录和错误输出链路。
- **优势**: 改动小，兼容原有手工启动方式，方便直接看到报错。
- **劣势和风险**: `--reload` 仍会启动重载子进程，若目录异常依旧会暴露真实 Python 报错。

### 7. 关键风险点
- **边界条件**: 两个候选虚拟环境路径都不存在时必须明确提示。
- **性能瓶颈**: 无。
- **安全考虑**: 无额外处理，本次仅修复启动脚本可观测性。
