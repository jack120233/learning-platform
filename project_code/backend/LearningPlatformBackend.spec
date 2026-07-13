# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


backend_root = Path(SPECPATH).resolve()
entry_script = backend_root / "scripts" / "windows_runtime_entry.py"

hiddenimports = []
for module_name in (
    "uvicorn",
    "fastapi",
    "aiosqlite",
    "diskcache",
    "jose",
    "passlib.handlers",
    "bcrypt",
    "email_validator",
):
    hiddenimports.extend(collect_submodules(module_name))

a = Analysis(
    [str(entry_script)],
    pathex=[str(backend_root)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="LearningPlatformBackend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LearningPlatformBackend",
)
