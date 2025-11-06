# nulla/bootstrap.py
from __future__ import annotations
import os, sys, zipfile, io, shutil, tempfile, urllib.request
from pathlib import Path

# Default layout on the user's disk (you can override with --root)
DEFAULT_ROOT = Path.home() / "nulla_source"

def ensure_dirs(root: Path) -> None:
    for p in [
        root / "assets",
        root / "bin" / "ffmpeg",
        root / "llama.cpp",
        root / "logs",
        root / "models",
        root / "scripts",
        root / "Whisper",
        root / "XTTS-v2",
    ]:
        p.mkdir(parents=True, exist_ok=True)

def write_third_party_notice_ffmpeg(root: Path) -> None:
    notices = root / "THIRD_PARTY_NOTICES"
    notices.mkdir(exist_ok=True)
    (notices / "FFmpeg.txt").write_text(
        "This project does not distribute FFmpeg.\n"
        "During setup, FFmpeg is downloaded from an upstream Windows build provider.\n"
        "FFmpeg is licensed under LGPL/GPL; see license files alongside ffmpeg.exe/ffprobe.exe.\n",
        encoding="utf-8",
    )

def _download(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()

def _extract_ffmpeg_zip_and_copy(data: bytes, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members = z.namelist()
        # Find ffmpeg.exe / ffprobe.exe wherever they live in the zip
        exe_map = {}
        for name in members:
            low = name.lower()
            if low.endswith("/"):
                continue
            if low.endswith("ffmpeg.exe"):
                exe_map["ffmpeg.exe"] = name
            elif low.endswith("ffprobe.exe"):
                exe_map["ffprobe.exe"] = name

        if "ffmpeg.exe" not in exe_map or "ffprobe.exe" not in exe_map:
            raise RuntimeError("Could not locate ffmpeg.exe/ffprobe.exe inside the downloaded zip.")

        # Copy binaries
        for out in ("ffmpeg.exe", "ffprobe.exe"):
            with z.open(exe_map[out]) as src, open(dest / out, "wb") as dst:
                shutil.copyfileobj(src, dst)

        # Try to drop any shipped license/readme files nearby (best effort)
        license_dir = dest / "LICENSES"
        license_dir.mkdir(exist_ok=True)
        for name in members:
            low = name.lower()
            if any(key in low for key in ("license", "copying", "readme")) and not low.endswith("/"):
                try:
                    with z.open(name) as src, open(license_dir / Path(name).name, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                except Exception:
                    pass  # non-fatal

def fetch_ffmpeg(root: Path, prefer: str = "btbn") -> None:
    """
    Download a recent Windows 64-bit static/portable build and place:
      <root>/bin/ffmpeg/ffmpeg.exe
      <root>/bin/ffmpeg/ffprobe.exe
      <root>/bin/ffmpeg/LICENSES/* (best effort)
    We try a couple of well-known upstreams; URLs may change over time.
    """
    dest = root / "bin" / "ffmpeg"
    ff, fp = dest / "ffmpeg.exe", dest / "ffprobe.exe"
    if ff.exists() and fp.exists():
        return  # already present

    # Two commonly used upstreams for Windows builds. We'll try one then the other.
    candidates = []
    if prefer == "btbn":
        # GitHub community builds (LGPL/GPL variants). Zip contains bin/ffmpeg.exe etc.
        candidates.append("https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-lgpl.zip")
        candidates.append("https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-gpl.zip")
    # Essentials build (gyan.dev) is another popular option
    candidates.append("https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip")

    last_err = None
    for url in candidates:
        try:
            data = _download(url, timeout=120)
            _extract_ffmpeg_zip_and_copy(data, dest)
            write_third_party_notice_ffmpeg(root)
            return
        except Exception as e:
            last_err = e
    raise RuntimeError(f"FFmpeg download failed. Last error: {last_err}")

def setup_ffmpeg(root: Path) -> None:
    ensure_dirs(root)
    fetch_ffmpeg(root)
