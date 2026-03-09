block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        # Бандлим конфиг в архив .exe, но runtime читает из папки рядом с .exe
        ('src/config/rules_config.yaml', 'config'),
    ],
    hiddenimports=[
        'openpyxl',
        'yaml',
        'pandas',
        'PySide6',
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
    name='schedule_analyzer',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    runtime_tmpdir=None,
)