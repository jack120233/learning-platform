# Worktree 开发指南

本文档介绍如何在在线学习平台项目中使用 Git Worktree 进行多模块并行开发。

## 什么是 Git Worktree

Git Worktree 允许你在同一个仓库中同时检出多个分支到不同的目录，而不需要克隆多个仓库副本。这对于同时开发多个功能模块非常有用。

## Worktree 核心优势

1. **并行开发**：在不同目录中同时开发不同功能
2. **节省空间**：共享 .git 目录，无需重复克隆
3. **快速切换**：无需 stash 或 commit 即可切换上下文
4. **独立环境**：每个 worktree 可以有独立的虚拟环境

## 项目 Worktree 规范

### 目录结构

```
E:\video_project\
├── project_code/          # 主工作目录（master 分支）
│   ├── backend/
│   ├── .venv/
│   └── .env
├── .zcf/
│   └── project_code/      # Worktree 存放目录
│       ├── feature-auth/  # 认证模块开发
│       ├── course-api/    # 课程 API 开发
│       └── user-module/   # 用户模块开发
```

### 创建 Worktree

```bash
# 方式一：创建新分支的 worktree
git worktree add ../.zcf/project_code/feature-auth -b feature/auth

# 方式二：基于现有分支创建
git worktree add ../.zcf/project_code/course-api feature/course-api

# 方式三：使用 zcf:git-worktree 技能（推荐）
# 该技能会自动处理目录创建、环境初始化等
```

### Worktree 开发流程

1. **初始化 Worktree**
   ```bash
   cd ../.zcf/project_code/feature-auth
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. **复制环境配置**
   ```bash
   # 从主目录复制 .env 文件
   copy ..\..\project_code\.env .
   ```

4. **安装依赖**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

5. **开始开发**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

6. **完成后合并**
   ```bash
   # 回到主目录
   cd ../../../project_code
   git merge feature/auth
   git worktree remove ../.zcf/project_code/feature-auth
   ```

### Worktree 管理命令

```bash
# 列出所有 worktree
git worktree list

# 移除 worktree（分支合并后）
git worktree remove <path>

# 清理已删除分支的 worktree
git worktree prune

# 锁定 worktree（防止误删）
git worktree lock <path>

# 解锁 worktree
git worktree unlock <path>
```

## 开发规范

### 分支命名规范

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| 功能 | feature/模块名 | feature/auth |
| 修复 | fix/问题描述 | fix/login-validation |
| 重构 | refactor/模块名 | refactor/user-service |
| 文档 | docs/描述 | docs/api-spec |

### Worktree 命名规范

与分支名对应，使用分支名的最后一段：
- 分支 `feature/auth` → 目录 `feature-auth`
- 分支 `fix/login-validation` → 目录 `fix-login-validation`

### 端口分配

不同 worktree 使用不同端口避免冲突：
- 主目录：8000
- Worktree 1：8001
- Worktree 2：8002
- 以此类推

## 常见问题

### Q: 如何在 Worktree 间共享代码？

A: Worktree 共享 .git 目录，所有分支的提交都可见。可以：
1. 频繁提交到当前分支
2. 在另一个 worktree 中 merge 或 cherry-pick

### Q: 虚拟环境如何处理？

A: 每个 worktree 应有独立的虚拟环境：
1. 在 worktree 根目录创建 .venv
2. 独立安装依赖
3. 避免环境污染

### Q: 如何处理 .env 文件？

A: .env 文件在 .gitignore 中，需要手动复制：
1. 从主目录复制 .env 到新 worktree
2. 根据需要调整配置（如端口号）

## 使用 zcf:git-worktree 技能

项目配置了 `zcf:git-worktree` 技能，可自动化大部分工作：

```bash
# 在 Claude Code 中使用
/skill zcf:git-worktree
```

该技能会：
1. 自动创建 worktree 目录
2. 初始化虚拟环境
3. 复制 .env 配置
4. 安装项目依赖
5. 配置 IDE 设置