from __future__ import annotations
import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path


def _plat_lib_name() -> str:
    if sys.platform.startswith("win"):
        return "ratatui_ffi.dll"
    elif sys.platform == "darwin":
        return "libratatui_ffi.dylib"
    else:
        return "libratatui_ffi.so"


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _build_from_src(src: Path) -> Path:
    profile = os.getenv("RATATUI_FFI_PROFILE", "release").lower()
    if profile not in ("debug", "release"):
        profile = "release"
    args = ["cargo", "build"] + ([] if profile == "debug" else ["--release"])
    subprocess.check_call(args, cwd=src)
    out = src / "target" / ("debug" if profile == "debug" else "release") / _plat_lib_name()
    if not out.exists():
        raise FileNotFoundError(out)
    return out


def _clone_and_build(url: str, tag: str) -> Path:
    with tempfile.TemporaryDirectory() as td:
        subprocess.check_call(["git", "init"], cwd=td)
        subprocess.check_call(["git", "remote", "add", "origin", url], cwd=td)
        subprocess.check_call(["git", "fetch", "--depth", "1", "origin", tag], cwd=td)
        subprocess.check_call(["git", "checkout", "FETCH_HEAD"], cwd=td)
        return _build_from_src(Path(td))


def ensure_runtime_lib() -> None:
    # Ensure a bundled libratatui_ffi.* exists alongside the package at runtime.
    pkg_dir = Path(__file__).resolve().parent
    bundled = pkg_dir / "_bundled" / _plat_lib_name()
    if bundled.exists():
        return

    # Try env overrides
    env_lib = os.getenv("RATATUI_FFI_LIB")
    env_src = os.getenv("RATATUI_FFI_SRC")
    url = os.getenv("RATATUI_FFI_GIT", "https://github.com/holo-q/ratatui-ffi.git")
    tag = os.getenv("RATATUI_FFI_TAG", "v0.1.5")

    try:
        if env_lib and Path(env_lib).exists():
            _copy(Path(env_lib), bundled)
            return
        if env_src and Path(env_src).exists():
            out = _build_from_src(Path(env_src))
            _copy(out, bundled)
            return
        # Final fallback: clone + build
        out = _clone_and_build(url, tag)
        _copy(out, bundled)
    except Exception:
        # Leave as-is; loader may still find a system lib
        return
