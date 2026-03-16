# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

django_datas, django_binaries, django_hiddenimports = collect_all("django")
drf_datas, drf_binaries, drf_hiddenimports = collect_all("rest_framework")

hiddenimports = [
    "waitress",
    "fuel_app",
    "fuel_system",
] + collect_submodules("fuel_app") + collect_submodules("fuel_system") + django_hiddenimports + drf_hiddenimports

datas = [
    ("db.sqlite3", "."),
] + django_datas + drf_datas

binaries = django_binaries + drf_binaries

a = Analysis(
    ["run.backend.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="fuel_backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="fuel_backend",
)