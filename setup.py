from __future__ import annotations
import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
from setuptools import setup
from setuptools.dist import Distribution
try:
    # Mark wheel as non-pure so it gets a platform tag
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel  # type: ignore
except Exception:  # wheel may not be present at import time
    _bdist_wheel = None  # type: ignore
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.develop import develop as _develop

PKG_ROOT = Path(__file__).parent
SRC_DIR = PKG_ROOT / "src" / "ratatui_py"
BUNDLED_DIR = SRC_DIR / "_bundled"

RATATUI_FFI_GIT = os.environ.get("RATATUI_FFI_GIT", "https://github.com/holo-q/ratatui-ffi.git")
RATATUI_FFI_TAG = os.environ.get("RATATUI_FFI_TAG", "v0.2.0")
RATATUI_FFI_SRC = os.environ.get("RATATUI_FFI_SRC")
RATATUI_FFI_LIB = os.environ.get("RATATUI_FFI_LIB")


def plat_lib_name() -> str:
    if sys.platform.startswith("win"):
        return "ratatui_ffi.dll"
    elif sys.platform == "darwin":
        return "libratatui_ffi.dylib"
    else:
        return "libratatui_ffi.so"


def copy_lib_to_bundle(path: Path) -> None:
    BUNDLED_DIR.mkdir(parents=True, exist_ok=True)
    target = BUNDLED_DIR / plat_lib_name()
    shutil.copy2(path, target)
    print(f"Bundled: {target}")


def build_from_src(src_path: Path) -> Path:
    # Build the Rust cdylib via cargo in the provided repository path
    profile = os.environ.get("RATATUI_FFI_PROFILE", "release").lower()
    if profile not in ("release", "debug"):
        profile = "release"
    print(f"Building ratatui_ffi from {src_path} (profile={profile})…")
    args = ["cargo", "build"] + ([] if profile == "debug" else ["--release"])
    subprocess.check_call(args, cwd=src_path)
    target = src_path / "target" / ("debug" if profile == "debug" else "release") / plat_lib_name()
    if not target.exists():
        raise FileNotFoundError(f"Built library not found: {target}")
    return target


def clone_and_build() -> Path:
    print(f"Cloning {RATATUI_FFI_GIT}@{RATATUI_FFI_TAG}...")
    with tempfile.TemporaryDirectory() as td:
        subprocess.check_call(["git", "init"], cwd=td)
        subprocess.check_call(["git", "remote", "add", "origin", RATATUI_FFI_GIT], cwd=td)
        subprocess.check_call(["git", "fetch", "--depth", "1", "origin", RATATUI_FFI_TAG], cwd=td)
        subprocess.check_call(["git", "checkout", "FETCH_HEAD"], cwd=td)
        return build_from_src(Path(td))


def ensure_bundled_lib():
    libname = plat_lib_name()
    bundled = BUNDLED_DIR / libname
    if RATATUI_FFI_LIB and Path(RATATUI_FFI_LIB).exists():
        copy_lib_to_bundle(Path(RATATUI_FFI_LIB))
    elif RATATUI_FFI_SRC and Path(RATATUI_FFI_SRC).exists():
        built = build_from_src(Path(RATATUI_FFI_SRC))
        copy_lib_to_bundle(built)
    elif not bundled.exists():
        try:
            built = clone_and_build()
            copy_lib_to_bundle(built)
        except Exception as e:
            print("Warning: Could not bundle ratatui_ffi automatically:", e)
            print("You can set RATATUI_FFI_LIB to a prebuilt library or RATATUI_FFI_SRC to a local source and rebuild.")


class build_py(_build_py):
    def run(self):
        ensure_bundled_lib()
        super().run()


class develop(_develop):
    def run(self):
        # Ensure the bundled library exists for editable installs too
        ensure_bundled_lib()
        super().run()


class BinaryDistribution(Distribution):
    # Ensure the wheel is treated as having binary components
    def has_ext_modules(self):  # type: ignore[override]
        return True


if _bdist_wheel is not None:
    class bdist_wheel(_bdist_wheel):  # type: ignore[misc,valid-type]
        def finalize_options(self):  # type: ignore[override]
            super().finalize_options()
            # Mark as non-pure so the wheel gets a platform tag
            self.root_is_pure = False
else:
    bdist_wheel = None  # type: ignore


if __name__ == "__main__":
    setup(
        name="ratatui-py",
        cmdclass={k: v for k, v in {"build_py": build_py, "develop": develop, "bdist_wheel": bdist_wheel}.items() if v is not None},
        distclass=BinaryDistribution,
        package_data={"ratatui_py": ["_bundled/*", "py.typed"]},
    )
