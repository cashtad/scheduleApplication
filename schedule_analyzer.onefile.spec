block_cipher = None


a = Analysis(
    ["src/main.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "openpyxl",
        "yaml",
        "pandas",
        "PySide6",
        "PySide6.QtWebEngineWidgets",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="schedule_analyzer_onefile",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    runtime_tmpdir=None,
)

