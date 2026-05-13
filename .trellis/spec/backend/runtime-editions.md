# Runtime Editions and Branch Routing

> Executable contracts for Windows local, Windows classroom, and shared runtime-edition work.

---

## Scenario: Windows Edition Branch Routing

### 1. Scope / Trigger

- Trigger: Any change related to Windows packaging, local SQLite runtime, diskcache, classroom LAN behavior, startup scripts, static/video delivery, or `APP_EDITION` environment wiring.
- Goal: Prevent Windows single-machine and classroom changes from being mixed on the wrong branch.

### 2. Signatures

Branch commands:

```bash
git branch --show-current
git switch future/windows-base
git switch future/windows-local
git switch future/windows-classroom
```

Runtime environment key:

```env
APP_EDITION=development
APP_EDITION=windows_local
APP_EDITION=windows_classroom
APP_EDITION=server
```

Backend settings contract:

```py
app_edition: Literal["development", "windows_local", "windows_classroom", "server"]
```

### 3. Contracts

| Branch | Allowed scope | Required `APP_EDITION` focus | Forbidden scope |
|--------|---------------|------------------------------|-----------------|
| `future/windows-base` | Shared foundation used by both Windows editions: config, cache abstraction, SQLite runtime helpers, tests that apply to both editions | `windows_local` and `windows_classroom` shared behavior | Single-machine-only launcher UX, classroom-only LAN/video tuning |
| `future/windows-local` | Windows single-machine install/startup flow, local data directory UX, first-run local initialization, browser auto-open | `windows_local` | LAN classroom capacity claims, classroom-only progress throttling, classroom-only video serving assumptions |
| `future/windows-classroom` | Windows LAN classroom flow, host/LAN address display, SQLite WAL behavior, progress write throttling, static/video delivery for 10-50 LAN users | `windows_classroom` | Single-user installer-only assumptions, features that only work on localhost |

Before editing edition-specific code, run `git branch --show-current` and confirm the branch matches the target edition.

If a change is shared by both Windows editions, implement it on `future/windows-base` first, then merge or rebase it into the edition branches.

### 4. Validation & Error Matrix

| Condition | Required handling |
|-----------|-------------------|
| Current branch is `master` and task is Windows edition work | Stop and switch to the correct `future/windows-*` branch before editing. |
| Current branch is `future/windows-base` and task is local-only | Stop and switch to `future/windows-local`. |
| Current branch is `future/windows-base` and task is classroom-only | Stop and switch to `future/windows-classroom`. |
| Current branch is `future/windows-local` and task changes classroom LAN/video/progress behavior | Stop and switch to `future/windows-classroom`. |
| Current branch is `future/windows-classroom` and task changes single-machine installer/local-only UX | Stop and switch to `future/windows-local`. |
| Uncommitted work exists on the wrong branch | Do not discard it; ask before moving, stashing, or committing. |
| A shared base change is needed after edition branches diverged | Land it on `future/windows-base`, then explicitly merge/rebase both edition branches. |

### 5. Good/Base/Bad Cases

- Good: `git branch --show-current` returns `future/windows-classroom`; implement LAN address display and progress write throttling there.
- Base: `git branch --show-current` returns `future/windows-base`; implement only shared `Settings.app_edition` and cache/backend abstractions there.
- Bad: Implement classroom video delivery optimization directly on `future/windows-local` because it is also a Windows branch.

### 6. Tests Required

For shared `future/windows-base` changes:

- Assert `Settings(app_edition="windows_local")` and `Settings(app_edition="windows_classroom")` both resolve the intended shared defaults.
- Assert `Settings(app_edition="server")` continues to preserve server defaults.
- Run targeted backend tests for runtime config and any touched module.

For `future/windows-local` changes:

- Assert `APP_EDITION=windows_local` uses local SQLite file paths and local cache directories.
- Assert first-run initialization is idempotent.
- Validate startup scripts do not require users to manually run database commands.

For `future/windows-classroom` changes:

- Assert `APP_EDITION=windows_classroom` enables classroom-only runtime behavior such as WAL where applicable.
- Assert progress synchronization is throttled when implemented.
- Assert static/video delivery supports classroom constraints without reading large files into business cache.

### 7. Wrong vs Correct

#### Wrong

```text
git branch --show-current
# future/windows-base

Implement LAN classroom video optimization and 50-user progress throttling here.
```

#### Correct

```text
git branch --show-current
# future/windows-base

git switch future/windows-classroom

Implement LAN classroom video optimization and 50-user progress throttling on the classroom branch.
```

---

## Design Decision: Keep Windows Editions Split After Shared Foundation

**Context**: Windows single-machine and classroom editions share runtime foundations but diverge in startup UX, network assumptions, and performance work.

**Decision**: Use `future/windows-base` only for shared foundation work, then use `future/windows-local` and `future/windows-classroom` for edition-specific implementation.

**Consequences**:

- Shared runtime contracts stay reusable.
- Local installer UX cannot accidentally inherit classroom-only assumptions.
- Classroom LAN/video/progress work cannot accidentally change the single-machine edition behavior.
