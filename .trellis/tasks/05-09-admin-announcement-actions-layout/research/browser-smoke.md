# Research: Browser smoke for admin announcements actions layout

- **Query**: Browser-smoke the UI change for `/admin/announcements`: verify compact soft/rounded action group, action discoverability, and desktop/mobile horizontal overflow.
- **Scope**: internal/browser smoke
- **Date**: 2026-05-09

## Findings

### Files Found

| File Path | Description |
|---|---|
| N/A | Browser smoke only; no source files were inspected for this report. |

### Code Patterns

N/A — this was a runtime browser smoke check.

### Browser Smoke Result

- **Pass/Fail**: PASS
- **URL tested**: `http://127.0.0.1:3000/admin/announcements`
- **Login**: Login was required; authenticated successfully with `admin1@example.com` / seed admin password.
- **Desktop viewport**: 1280x800. The operation column rendered a compact grouped surface: first row action wrapper class `announcement-row-actions soft-action-surface`; buttons used soft action classes and remained visible as `编辑`, `转草稿`, `删除`.
- **Mobile/narrow viewport**: 390x800. No document-level horizontal overflow detected: `document.documentElement.scrollWidth` was `390` and `window.innerWidth` was `390`. First row actions remained visible/discoverable as `编辑`, `转草稿`, `删除`.
- **Console/network issues related to this change**: No related console errors, request failures, or HTTP 4xx/5xx responses observed during the smoke run. Only normal Vite debug connection messages appeared.

### External References

N/A

### Related Specs

- `.trellis/tasks/05-09-admin-announcement-actions-layout/prd.md` — task PRD present.

## Caveats / Not Found

- Backend root `http://127.0.0.1:8000/api/v1` returned 404 to a HEAD probe, but proxied authenticated page API calls used by the UI succeeded during the browser smoke.
- The current row state showed `转草稿`; the alternate `发布` action was not present in the displayed published rows during this run.
