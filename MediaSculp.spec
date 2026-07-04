# PyInstaller spec for the MediaSculp desktop app (one-folder build).
# Build with:  python -m PyInstaller --noconfirm MediaSculp.spec
from PyInstaller.utils.hooks import collect_all

datas = [
    ("templates", "templates"),
    ("static", "static"),
    ("icons", "icons"),
]
binaries = []
hiddenimports = ["waitress", "clr"]

# yt-dlp loads extractors dynamically, moviepy/imageio carry data files, and the
# imageio-ffmpeg binary must ride along so downloads and trims work with no
# separate ffmpeg install. pywebview needs its platform backend + interop DLLs.
for package in ("yt_dlp", "moviepy", "imageio", "imageio_ffmpeg", "webview"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

hiddenimports += [
    "webview.platforms.winforms",
    "webview.platforms.edgechromium",
]

a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MediaSculp",
    console=False,
    icon="icons/mediasculp.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="MediaSculp",
)
