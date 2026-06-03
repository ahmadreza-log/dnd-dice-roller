# PyInstaller spec for the D&D Dice Roller desktop app.

from PyInstaller.utils.hooks import collect_all

block_cipher = None

ttkbootstrap_datas, ttkbootstrap_binaries, ttkbootstrap_hiddenimports = collect_all(
    "ttkbootstrap"
)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=ttkbootstrap_binaries,
    datas=ttkbootstrap_datas,
    hiddenimports=ttkbootstrap_hiddenimports + ["PIL._tkinter_finder"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="DND-Dice-Roller",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
