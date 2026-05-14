# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller .spec para gerar PDV_Supermercado.exe
Uso:  pyinstaller pdv_supermercado.spec
"""

block_cipher = None

a = Analysis(
    ['pdv_supermercado.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Adicione aqui arquivos extras se houver (imagens, fontes, etc.)
        # ('assets/logo.png', 'assets'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'qrcode',
        'qrcode.image.pil',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas',
        'pytest', 'unittest', 'test',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    name='PDV_Supermercado',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False = janela GUI sem console preto
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icone.ico',  # coloque um icone.ico na mesma pasta (256x256 recomendado)
    version='version_info.txt',
)
