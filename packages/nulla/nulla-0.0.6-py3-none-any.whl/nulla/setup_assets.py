# nulla/setup_assets.py
from __future__ import annotations
import io, json, os, re, sys, shutil, subprocess, tempfile, textwrap, zipfile, urllib.request
from pathlib import Path

# ====================== tiny utils ======================
def _run(cmd: list[str], check=True, env=None, cwd=None) -> subprocess.CompletedProcess:
    print(">>", " ".join(cmd))
    return subprocess.run(cmd, check=check, env=env, cwd=cwd)

def _py() -> str:
    return sys.executable

def _is_win() -> bool:
    return os.name == "nt"

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def _yesno(prompt: str, assume_yes: bool) -> bool:
    if assume_yes:
        print(prompt + " [Y/n]  -> assuming YES (-y)")
        return True
    ans = input(prompt + " [Y/n] ").strip().lower()
    return ans in ("", "y", "yes")

def _copy_tree(src: Path, dst: Path, skip_existing=True) -> None:
    if not src.exists():
        return
    for root, _, files in os.walk(src):
        rel = Path(root).relative_to(src)
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            s = Path(root) / f
            d = target_dir / f
            if skip_existing and d.exists():
                continue
            shutil.copy2(s, d)

def _venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if _is_win() else "bin/python")

def _pip(python_exe: Path, *args: str, env: dict | None = None) -> None:
    """pip wrapper with optional env override."""
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)
    _run([str(python_exe), "-m", "pip", *args], env=env_vars)

def _ensure_hf_installed() -> None:
    try:
        import huggingface_hub  # noqa: F401
    except Exception:
        _pip(Path(_py()), "install", "--upgrade", "huggingface_hub")

def _canonicalize_root(p: Path) -> Path:
    """If user passed ...\\nulla_source_test, use ...\\nulla_source instead."""
    p = p.expanduser().resolve()
    if p.name == "nulla_source_test":
        target = p.parent / "nulla_source"
        print(f"[canonicalize] Using '{target}' instead of '{p.name}'.")
        return target
    return p

# ====================== tree + templates ======================
def _ensure_tree(root: Path) -> None:
    for d in [
        "assets",
        "bin/ffmpeg",
        "llama.cpp",
        "logs",
        "models",
        "scripts",
        "Whisper",
        "XTTS-v2",
    ]:
        _ensure_dir(root / d)

def _copy_templates_into(root: Path) -> None:
    try:
        import importlib.resources as ir
        tpl = ir.files("nulla") / "templates"
        if tpl.exists():
            _copy_tree(Path(tpl), root, skip_existing=True)
            print(f"Copied templates into: {root}")
        else:
            print("No templates/ in package (skipping).")
    except Exception as e:
        print(f"templates copy skipped: {e!r}")

# ====================== FFmpeg (portable) ======================
def _ensure_ffmpeg(root: Path, assume_yes: bool) -> None:
    from .bootstrap import setup_ffmpeg  # official portable build
    ff = root / "bin" / "ffmpeg" / ("ffmpeg.exe" if _is_win() else "ffmpeg")
    fp = root / "bin" / "ffmpeg" / ("ffprobe.exe" if _is_win() else "ffprobe")
    if ff.exists() and fp.exists():
        print("FFmpeg already present.")
        return
    if _yesno("FFmpeg not found. Download a portable build now?", assume_yes):
        setup_ffmpeg(root)
    else:
        print("Skipping FFmpeg. Whisper may fail to transcode audio without it.")

# ====================== Whisper helper script ======================
EMBEDDED_ACTIVATE_WHISPER_PS1 = r'''. "$PSScriptRoot\.venv\Scripts\Activate.ps1"
# keep everything local to this folder
$env:XDG_CACHE_HOME      = "$PSScriptRoot\.cache"
$env:HF_HOME             = "$PSScriptRoot\.cache\huggingface"
$env:TRANSFORMERS_CACHE  = "$PSScriptRoot\.cache\huggingface\transformers"
$env:PIP_CACHE_DIR       = "$PSScriptRoot\.cache\pip"
$env:TORCH_HOME          = "$PSScriptRoot\.cache\torch"
# if you place a portable ffmpeg at .\ffmpeg\bin\ffmpeg.exe, add it to PATH for this venv only
if (Test-Path "$PSScriptRoot\ffmpeg\bin\ffmpeg.exe") {
  $env:PATH = "$PSScriptRoot\ffmpeg\bin;$env:PATH"
}
'''

def _ensure_activate_whisper(root: Path) -> None:
    """Guarantee Whisper/Activate-Whisper.ps1 exists (template or embedded)."""
    dest = root / "Whisper" / "Activate-Whisper.ps1"
    if dest.exists():
        print("Whisper helper present:", dest)
        return
    try:
        import importlib.resources as ir
        cand = (ir.files("nulla") / "templates" / "Whisper" / "Activate-Whisper.ps1")
        if cand.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(cand, "rb") as r, open(dest, "wb") as w:
                w.write(r.read())
            print("Copied Activate-Whisper.ps1 from package templates.")
            return
    except Exception as e:
        print(f"Package template not available ({e!r}); writing embedded helper.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(EMBEDDED_ACTIVATE_WHISPER_PS1, encoding="utf-8")
    print("Wrote embedded Activate-Whisper.ps1:", dest)

# ====================== Whisper (pinned to your working combo) ======================
# Your working venv shows CPU Torch 2.9.0 stack and webrtcvad present. :contentReference[oaicite:2]{index=2}
_WHISPER_PINS = [
    "numpy==2.3.3",
    "llvmlite==0.45.1",
    "numba==0.62.1",
    "sounddevice==0.5.3",
    "openai-whisper==20250625",
    # --- extras seen in your good env ---
    "webrtcvad-wheels==2.0.14",    # fixes 'No module named webrtcvad'
    "tiktoken==0.12.0",
    "Pillow==11.3.0",
    "regex==2025.10.23",
    "requests==2.32.5",
    "typing_extensions==4.15.0",
]
_WHISPER_TORCH = [
    "torch==2.9.0+cpu",
    "torchaudio==2.9.0+cpu",
    "torchvision==0.24.0+cpu",
]

def _install_torch_cpu(python_exe: Path) -> None:
    _pip(
        python_exe,
        "install", "--upgrade",
        *_WHISPER_TORCH,
        env={
            "PIP_PREFER_BINARY": "1",
            "PIP_ONLY_BINARY": ":all:",
            "PIP_EXTRA_INDEX_URL": "https://download.pytorch.org/whl/cpu",
        },
    )
    _run([str(python_exe), "-c", "import torch, torchaudio, torchvision; print('CPU CUDA?', torch.cuda.is_available())"])

def setup_whisper(*, root: Path, model_size: str = "small", assume_yes: bool = False) -> None:
    root = _canonicalize_root(root)
    _ensure_tree(root)
    _ensure_ffmpeg(root, assume_yes)

    venv_dir = root / "Whisper" / ".venv"
    py_venv = _venv_python(venv_dir)
    if not py_venv.exists():
        print(f"Creating Whisper venv: {venv_dir}")
        _run([_py(), "-m", "venv", str(venv_dir)])

    _ensure_activate_whisper(root)

    # Wheels-first
    _pip(py_venv, "install", "--upgrade", "pip", "setuptools", "wheel", env={"PIP_PREFER_BINARY": "1"})
    _install_torch_cpu(py_venv)
    _pip(py_venv, "install", *_WHISPER_PINS, env={"PIP_PREFER_BINARY": "1"})

    # Sanity check: import webrtcvad + whisper
    _run([str(py_venv), "-c", "import webrtcvad, whisper; print('webrtcvad OK, whisper OK')"])

    if _yesno(f"Prefetch Whisper model '{model_size}' to cache now?", assume_yes):
        code = (
            "import whisper; "
            f"print('Loading {model_size}...'); "
            f"whisper.load_model('{model_size}'); "
            "print('Whisper model ready.')"
        )
        _run([str(py_venv), "-c", code])

# ====================== GGUF model (OpenHermes Q8_0) ======================
def setup_model(*, root: Path, repo_id: str, gguf_filename: str, assume_yes: bool = False) -> None:
    root = _canonicalize_root(root)
    _ensure_tree(root)
    target = root / "models" / gguf_filename
    if target.exists():
        print(f"Model already present: {target}")
        return
    if not _yesno(f"Download GGUF '{gguf_filename}' from '{repo_id}' to: {target} ?", assume_yes):
        print("Skipping GGUF download.")
        return

    _ensure_hf_installed()
    from huggingface_hub import hf_hub_download
    tmp_path = hf_hub_download(repo_id=repo_id, filename=gguf_filename, local_dir=str(root / "models"))
    dst = root / "models" / gguf_filename
    if Path(tmp_path) != dst and Path(tmp_path).exists():
        shutil.move(tmp_path, dst)
    print(f"GGUF downloaded: {dst}")

# ====================== llama.cpp (auto Windows download) ======================
_GH_API = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"

def _gh_latest_assets() -> list[dict]:
    req = urllib.request.Request(_GH_API, headers={"User-Agent": "nulla-setup"})
    with urllib.request.urlopen(req) as r:
        return json.load(r).get("assets", [])

def _find_asset_url(pattern: str) -> str | None:
    rx = re.compile(pattern, re.IGNORECASE)
    for a in _gh_latest_assets():
        name = a.get("name", "")
        if rx.fullmatch(name):
            return a.get("browser_download_url")
    return None

def _download_to_file(url: str, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, open(dst, "wb") as f:
        while True:
            chunk = r.read(1024 * 64)
            if not chunk:
                break
            f.write(chunk)
    return dst

def _extract_zip(zip_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)

def setup_llama_bins(root: str, cuda: str = "12.4") -> Path:
    """
    Downloads & extracts llama.cpp Windows CUDA binaries into <root>/llama.cpp.
    Official source: ggml-org/llama.cpp latest release.
    """
    base_root = _canonicalize_root(Path(root))
    base = base_root / "llama.cpp"
    base.mkdir(parents=True, exist_ok=True)

    pat_llama  = rf"llama-b[\d\.]+-bin-win-cuda-{re.escape(cuda)}-x64\.zip"
    pat_cudart = rf"cudart-llama-bin-win-cuda-{re.escape(cuda)}-x64\.zip"

    url_llama  = _find_asset_url(pat_llama)
    url_cudart = _find_asset_url(pat_cudart)

    if not url_llama or not url_cudart:
        raise RuntimeError(
            "Could not find expected llama.cpp assets on the latest official release. "
            "Open https://github.com/ggml-org/llama.cpp/releases and fetch the two Windows CUDA zips manually."
        )

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        z1 = _download_to_file(url_llama,  td / "llama.zip")
        z2 = _download_to_file(url_cudart, td / "cudart.zip")
        _extract_zip(z1, base)
        _extract_zip(z2, base)

    (base / "NOTICE_llama.txt").write_text(
        "llama.cpp binaries fetched from ggml-org/llama.cpp (MIT).\n"
        "Latest release: https://github.com/ggml-org/llama.cpp/releases\n",
        encoding="utf-8",
    )
    print(f"llama.cpp binaries ready at: {base}")
    return base

def setup_llamacpp(*, root: Path, method: str = "auto", assume_yes: bool = False) -> None:
    root = _canonicalize_root(root)
    _ensure_tree(root)
    ll_dir = root / "llama.cpp"
    _ensure_dir(ll_dir)

    if method == "auto" and _is_win():
        if _yesno("Download official llama.cpp Windows CUDA binaries now?", assume_yes):
            try:
                setup_llama_bins(str(root), cuda="12.4")
                return
            except Exception as e:
                print(f"Auto llama.cpp download failed ({e}). You can drop EXEs manually.")
        # fall through to prompt/manual

    readme = ll_dir / "README_LLAMA_CPP.txt"
    if not readme.exists():
        readme.write_text(textwrap.dedent("""\
            Place your llama.cpp binaries here (Windows):
              - llama-cli.exe (optional)
              - llama-server.exe (recommended)
            Get binaries from the official ggml-org/llama.cpp releases.
            """).strip() + "\n", encoding="utf-8")
    print(f"llama.cpp: expecting you to drop EXEs into: {ll_dir}")

# ====================== XTTS-v2 (match your cu128 + pins) ======================
# Your working venv shows torch/torchaudio/torchvision cu128 and these libs. :contentReference[oaicite:3]{index=3}
_COQUI_PINS = [
    "encodec==0.1.1",
    "gruut==2.4.0",
    "gruut-ipa==0.13.0",
    "gruut_lang_en==2.0.1",
    "gruut_lang_fr==2.0.2",
    "gruut_lang_de==2.0.1",
    "gruut_lang_es==2.0.1",
    "monotonic-alignment-search==0.2.1",
    "librosa==0.11.0",
    "numba==0.62.1",
    "llvmlite==0.45.1",
    "numpy==2.3.3",
    "soundfile==0.13.1",
    "soxr==1.0.0",
    "tokenizers==0.21.4",
    "transformers==4.55.4",
    "huggingface-hub==0.36.0",
    "coqui-tts==0.27.2",
    # Extras observed in your env (safe wheels):
    "Cython==3.1.6",
    "scipy==1.16.2",
    "scikit-learn==1.7.2",
    "matplotlib==3.10.7",
    "protobuf==6.33.0",
    "psutil==7.1.1",
    "typeguard==4.4.4",
    "audioread==3.0.1",
]

def _install_torch_cu128(python_exe: Path) -> None:
    """Install your exact Torch stack (cu128)."""
    _pip(
        python_exe,
        "install", "--upgrade",
        "torch==2.8.0+cu128",
        "torchaudio==2.8.0+cu128",
        "torchvision==0.23.0+cu128",
        "--index-url", "https://download.pytorch.org/whl/cu128",
        env={"PIP_PREFER_BINARY": "1", "PIP_ONLY_BINARY": ":all:"},
    )
    _run([str(python_exe), "-c", "import torch, torchaudio, torchvision; print('Torch', torch.__version__, 'CUDA?', torch.cuda.is_available())"])

def _install_coqui_xtts(python_exe: Path) -> None:
    """Install coqui-tts + deps using pins (wheels-first)."""
    _pip(python_exe, "install", "--upgrade", "pip", "setuptools", "wheel", env={"PIP_PREFER_BINARY": "1"})
    _pip(python_exe, "install", *_COQUI_PINS, env={"PIP_PREFER_BINARY": "1"})
    _run([str(python_exe), "-c", "from TTS.api import TTS; print('coqui-tts OK')"], env={"TRANSFORMERS_NO_TORCHVISION": "1"})

def setup_xtts(*, root: Path, torch_spec: str | None = None, assume_yes: bool = False) -> None:
    root = _canonicalize_root(root)
    _ensure_tree(root)
    venv_dir = root / "XTTS-v2" / ".venv"
    py_venv = _venv_python(venv_dir)
    if not py_venv.exists():
        print(f"Creating XTTS venv: {venv_dir}")
        _run([_py(), "-m", "venv", str(venv_dir)])

    _pip(py_venv, "install", "--upgrade", "pip", "setuptools", "wheel", env={"PIP_PREFER_BINARY": "1"})

    if torch_spec:
        print(f"Installing Torch from provided spec: {torch_spec}")
        _pip(py_venv, "install", *torch_spec.split(), env={"PIP_PREFER_BINARY": "1", "PIP_ONLY_BINARY": ":all:"})
    else:
        _install_torch_cu128(py_venv)

    _install_coqui_xtts(py_venv)

    if _yesno("Prefetch XTTS-v2 model to cache now?", assume_yes):
        code = (
            "from TTS.api import TTS; "
            "print('Loading XTTS-v2...'); "
            "TTS('tts_models/multilingual/multi-dataset/xtts_v2'); "
            "print('XTTS-v2 ready.')"
        )
        _run([str(py_venv), "-c", code], env={"TRANSFORMERS_NO_TORCHVISION": "1"})

# ====================== Orchestrator ======================
def do_setup(*, root: Path, assume_yes: bool = False) -> None:
    root = _canonicalize_root(root)
    print(f"== Nulla setup to: {root} ==")

    _ensure_tree(root)
    _copy_templates_into(root)

    # FFmpeg
    try:
        _ensure_ffmpeg(root, assume_yes)
    except Exception as e:
        print(f"FFmpeg step skipped/failed: {e}")

    # Whisper (CPU, pinned)
    try:
        setup_whisper(root=root, model_size="small", assume_yes=assume_yes)
    except Exception as e:
        print(f"Whisper step skipped/failed: {e}")

    # GGUF (OpenHermes Q8_0)
    try:
        setup_model(
            root=root,
            repo_id="TheBloke/OpenHermes-2.5-Mistral-7B-GGUF",
            gguf_filename="openhermes-2.5-mistral-7b.Q8_0.gguf",
            assume_yes=assume_yes,
        )
    except Exception as e:
        print(f"Model step skipped/failed: {e}")

    # llama.cpp
    try:
        setup_llamacpp(root=root, method="auto", assume_yes=assume_yes)
    except Exception as e:
        print(f"llama.cpp step skipped/failed: {e}")

    # XTTS
    try:
        setup_xtts(root=root, torch_spec=None, assume_yes=assume_yes)
    except Exception as e:
        print(f"XTTS step skipped/failed: {e}")

    # Summary
    print("\n== Setup complete (summary) ==")
    print("Root:        ", root)
    print("FFmpeg:      ", (root / 'bin' / 'ffmpeg').resolve())
    print("Whisper venv:", (root / 'Whisper' / '.venv').resolve())
    print("XTTS venv:   ", (root / 'XTTS-v2' / '.venv').resolve())
    print("Models dir:  ", (root / 'models').resolve())
    print("llama.cpp:   ", (root / 'llama.cpp').resolve())
    print("\nIf llama.cpp EXEs are missing, you can fetch with the function 'setup_llama_bins' or drop EXEs manually.")
