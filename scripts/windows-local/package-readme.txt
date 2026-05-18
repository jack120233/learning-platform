Windows Local Learning Platform
================================

Usage
- Extract the package to a writable folder.
- Double-click `start-windows-local.cmd`.
- Wait for the browser to open `http://127.0.0.1:8000/`.

Default accounts
- admin1 / Admin123456
- teacher1 / Test123456
- student1 / Test123456

Notes
- This package does not require MySQL or Redis.
- User data is stored under `project_code\backend\data`.
- Uploaded files are stored under `project_code\backend\uploads`.
- Logs are stored under `project_code\backend\logs`.

Troubleshooting
- If startup fails, check:
  - `project_code\backend\logs\windows-local-startup.log`
  - `project_code\backend\logs\windows-local-startup-error.log`
