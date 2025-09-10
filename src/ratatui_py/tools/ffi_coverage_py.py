from __future__ import annotations

import argparse
import ctypes as C
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set, Tuple


@dataclass
class Config:
    ffi_py: Path
    lib: str | None
    ignore_file: Path | None
    strict: bool


def parse_args() -> Config:
    ap = argparse.ArgumentParser(description="Audit Python (_ffi.py) coverage against libratatui_ffi exports.")
    ap.add_argument("--ffi-py", default=str(Path("src/ratatui_py/_ffi.py")), help="Path to _ffi.py")
    ap.add_argument("--lib", help="Path or name of libratatui_ffi to dlopen and enumerate (defaults to bundled)")
    ap.add_argument("--ignore", dest="ignore_file", help="JSON with ignore: [names or /regex/]")
    ap.add_argument("--strict", action="store_true", help="Fail on any discrepancies")
    a = ap.parse_args()
    return Config(
        ffi_py=Path(a.ffi_py),
        lib=a.lib,
        ignore_file=(Path(a.ignore_file) if a.ignore_file else None),
        strict=bool(a.strict),
    )


def resolve_library(user_hint: str | None) -> str:
    if user_hint:
        return user_hint
    # Try env var
    env = os.getenv("RATATUI_FFI_LIB")
    if env:
        return env
    # Try packaged bundle
    pkg = Path(__file__).resolve().parents[1] / "_bundled"
    names = (
        ["ratatui_ffi.dll"] if os.name == "nt" else (["libratatui_ffi.dylib"] if os.uname().sysname == "Darwin" else ["libratatui_ffi.so"])
    )
    for n in names:
        p = pkg / n
        if p.exists():
            return str(p)
    # Fallback to default names for search path
    return names[0]


def nm_exports(libpath: str) -> Set[str]:
    cmds: List[List[str]] = [
        ["nm", "-D", "--defined-only", libpath],
        ["readelf", "-Ws", libpath],
        ["objdump", "-T", libpath],
    ]
    for cmd in cmds:
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        except Exception:
            continue
        names: Set[str] = set()
        for line in out.splitlines():
            # nm: 0000000000002b30 T ratatui_init_terminal
            # readelf/objdump: ...  FUNC    GLOBAL DEFAULT  UND/..  ratatui_init_terminal
            parts = line.strip().split()
            if not parts:
                continue
            name = parts[-1]
            if not name.startswith("ratatui_"):
                continue
            # skip data symbols sometimes emitted for GOT/PLT
            if name.endswith("@Base"):
                name = name.split("@", 1)[0]
            names.add(name)
        if names:
            return names
    return set()


def parse_python_bound_symbols(ffi_py: Path) -> Set[str]:
    text = ffi_py.read_text(encoding="utf-8")
    names: Set[str] = set()
    # find lib.ratatui_foo_bar occurrences being assigned with .argtypes/.restype or accessed in hasattr
    for m in re.finditer(r"lib\.\s*(ratatui_[A-Za-z0-9_]+)", text):
        names.add(m.group(1))
    return names


def load_ignore(path: Path | None) -> Tuple[Set[str], List[re.Pattern[str]]]:
    if not path or not path.exists():
        return set(), []
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    exact: Set[str] = set()
    regex: List[re.Pattern[str]] = []
    for s in data.get("ignore", []):
        if isinstance(s, str) and s.startswith("/") and s.endswith("/"):
            regex.append(re.compile(s[1:-1]))
        elif isinstance(s, str):
            exact.add(s)
    return exact, regex


def is_ignored(name: str, exact: Set[str], regex: List[re.Pattern[str]]) -> bool:
    return name in exact or any(r.search(name) for r in regex)


def link_through_check(libname: str, names: Iterable[str]) -> List[str]:
    unresolved: List[str] = []
    try:
        lib = C.CDLL(libname)
    except OSError as e:
        # If we cannot load, skip link-through and report nothing here; nm will still catch missing symbols
        return unresolved
    for n in names:
        try:
            getattr(lib, n)
        except AttributeError:
            unresolved.append(n)
    return unresolved


def main() -> None:
    cfg = parse_args()
    libname = resolve_library(cfg.lib)
    exports = nm_exports(libname)
    py_syms = parse_python_bound_symbols(cfg.ffi_py)
    ign_exact, ign_regex = load_ignore(cfg.ignore_file)

    missing = sorted(n for n in exports if n not in py_syms and not is_ignored(n, ign_exact, ign_regex))
    extra = sorted(n for n in py_syms if (exports and n not in exports) and not is_ignored(n, ign_exact, ign_regex))
    unresolved = link_through_check(libname, [n for n in py_syms if not is_ignored(n, ign_exact, ign_regex)])

    exit_code = 0
    def report(label: str, items: List[str]) -> None:
        nonlocal exit_code
        if not items:
            return
        print(f"{label} ({len(items)}):")
        for n in items:
            print(f"  - {n}")
        exit_code = 1

    report("MISSING in _ffi.py (present in library)", missing)
    report("EXTRA in _ffi.py (not found in library)", extra)
    report("UNRESOLVED via ctypes (getattr failed)", unresolved)

    coverage = 0.0
    if exports:
        bound = len([n for n in py_syms if n in exports])
        coverage = 100.0 * bound / max(1, len(exports))
        print(f"Coverage: {bound}/{len(exports)} = {coverage:.1f}%")

    if cfg.strict and exit_code:
        raise SystemExit(exit_code)
    print("Python FFI coverage audit complete.")


if __name__ == "__main__":
    main()

