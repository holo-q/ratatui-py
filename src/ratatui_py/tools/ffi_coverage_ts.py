from __future__ import annotations

import argparse
import ctypes as C
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set, Tuple


Ident = re.compile(r"[A-Za-z_][$\w]*")


@dataclass
class Config:
    roots: List[Path]
    ffi_json: Path | None
    run_introspect: bool
    ratatui_ffi_repo: Path | None
    lib_path: Path | None
    ignore_file: Path | None
    strict: bool


def parse_args() -> Config:
    ap = argparse.ArgumentParser(description="Audit TS ffi-napi bindings against ratatui_ffi introspection JSON.")
    ap.add_argument("roots", nargs="*", help="TS files/dirs to scan (default: src)")
    ap.add_argument("--ffi-json", dest="ffi_json", help="Path to ffi_introspect JSON output")
    ap.add_argument("--run-introspect", action="store_true", help="Run cargo ffi_introspect to obtain JSON")
    ap.add_argument("--ratatui-ffi-repo", dest="ffi_repo", help="Path to ratatui-ffi repo (for --run-introspect)")
    ap.add_argument("--lib", dest="lib_path", help="Path or name of libratatui_ffi to dlopen for link-through checks")
    ap.add_argument("--ignore", dest="ignore_file", help="JSON file with {ignore:[...]} of symbol names or /regex/")
    ap.add_argument("--strict", action="store_true", help="Fail with non-zero exit code on any discrepancies")

    a = ap.parse_args()
    roots = [Path(p) for p in (a.roots or ["src"]) if p]
    return Config(
        roots=roots,
        ffi_json=(Path(a.ffi_json) if a.ffi_json else None),
        run_introspect=bool(a.run_introspect),
        ratatui_ffi_repo=(Path(a.ffi_repo) if a.ffi_repo else None),
        lib_path=(Path(a.lib_path) if a.lib_path else None),
        ignore_file=(Path(a.ignore_file) if a.ignore_file else None),
        strict=bool(a.strict),
    )


def run_introspector(repo: Path) -> Set[str]:
    out = subprocess.check_output(
        ["cargo", "run", "--quiet", "--bin", "ffi_introspect", "--", "--json"],
        cwd=str(repo),
    ).decode("utf-8")
    data = json.loads(out)
    return normalize_introspect(data)


def normalize_introspect(data) -> Set[str]:
    # Accept either { functions: [{name:...}, ...] } or a flat array
    fns = data.get("functions") if isinstance(data, dict) else data
    names: Set[str] = set()
    for fn in (fns or []):
        if isinstance(fn, str):
            names.add(fn)
        elif isinstance(fn, dict) and isinstance(fn.get("name"), str):
            names.add(fn["name"])
    return names


def read_introspect(cfg: Config) -> Set[str]:
    if cfg.ffi_json:
        with open(cfg.ffi_json, "r", encoding="utf-8") as f:
            return normalize_introspect(json.load(f))
    if cfg.run_introspect:
        if not cfg.ratatui_ffi_repo:
            raise SystemExit("--ratatui-ffi-repo is required with --run-introspect")
        return run_introspector(cfg.ratatui_ffi_repo)
    env_path = os.getenv("FFI_JSON")
    if env_path:
        with open(env_path, "r", encoding="utf-8") as f:
            return normalize_introspect(json.load(f))
    raise SystemExit("Provide --ffi-json or set FFI_JSON, or use --run-introspect with --ratatui-ffi-repo")


def ts_files(paths: Iterable[Path]) -> Iterable[Path]:
    for p in paths:
        if p.is_dir():
            for sub in p.rglob("*.ts"):
                yield sub
        elif p.suffix == ".ts":
            yield p


def extract_bindings_from_text(src: str) -> Set[str]:
    names: Set[str] = set()
    # Heuristic: find ffi.Library( ..., { ... }) and scrape keys of the object literal
    for m in re.finditer(r"\bLibrary\s*\(\s*[^,]+,\s*\{", src):
        start = m.end() - 1  # at '{'
        obj, end = _read_balanced(src, start, open_char='{', close_char='}')
        names |= _keys_from_object_literal(obj)
    return names


def _read_balanced(s: str, i: int, open_char: str, close_char: str) -> Tuple[str, int]:
    assert s[i] == open_char
    depth = 0
    j = i
    in_str: str | None = None
    esc = False
    while j < len(s):
        ch = s[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
        else:
            if ch in ('"', "'", "`"):
                in_str = ch
            elif ch == open_char:
                depth += 1
            elif ch == close_char:
                depth -= 1
                if depth == 0:
                    return s[i : j + 1], j + 1
        j += 1
    raise ValueError("unbalanced braces while parsing object literal")


def _keys_from_object_literal(obj_text: str) -> Set[str]:
    # Parse top-level keys of an object literal: { key: ..., 'str': ..., "str": ..., [computed]: ... }
    # Ignore computed keys and spreads.
    names: Set[str] = set()
    i = 1  # skip leading '{'
    depth = 0
    in_str: str | None = None
    esc = False
    expecting_key = True
    cur = ""
    while i < len(obj_text) - 1:
        ch = obj_text[i]
        if in_str:
            cur += ch
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
        else:
            if ch in ('"', "'", "`"):
                in_str = ch
                cur = ch
            elif ch in "[{(":
                depth += 1
            elif ch in "]})":
                depth = max(0, depth - 1)
            elif depth == 0 and ch == ',':
                expecting_key = True
            elif depth == 0 and ch == ':':
                # finalize key token in cur
                key = _normalize_key(cur.strip())
                if key:
                    names.add(key)
                cur = ""
                expecting_key = False
            elif expecting_key and depth == 0:
                cur += ch
        i += 1
    # handle last key without trailing ':' (rare) -> ignore
    return names


def _normalize_key(tok: str) -> str | None:
    tok = tok.strip()
    if not tok or tok.startswith("..."):
        return None
    if tok[0] in ('"', "'", "`") and tok[-1] == tok[0]:
        return tok[1:-1]
    m = Ident.fullmatch(tok)
    return m.group(0) if m else None


def extract_bindings(paths: Iterable[Path]) -> Set[str]:
    result: Set[str] = set()
    for f in ts_files(paths):
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        result |= extract_bindings_from_text(text)
    return result


def load_library(lib_hint: Path | None) -> C.CDLL | None:
    cand: List[str] = []
    if lib_hint is not None:
        cand.append(str(lib_hint))
    if os.name == 'nt':
        cand += ['ratatui_ffi.dll', 'ratatui_ffi']
    elif sys_platform() == 'darwin':
        cand += ['libratatui_ffi.dylib', 'ratatui_ffi']
    else:
        cand += ['libratatui_ffi.so', 'ratatui_ffi']
    for name in cand:
        try:
            return C.CDLL(name)
        except OSError:
            continue
    return None


def sys_platform() -> str:
    # Avoid importing sys at module top to keep script self-contained
    import sys as _sys
    return _sys.platform


def get_feature_bits(lib: C.CDLL | None) -> int:
    if not lib:
        return 0
    try:
        lib.ratatui_ffi_feature_bits.restype = C.c_uint32
        return int(lib.ratatui_ffi_feature_bits())
    except Exception:
        return 0


def load_ignore(path: Path | None) -> Tuple[Set[str], List[re.Pattern[str]]]:
    if not path or not path.exists():
        return set(), []
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("ignore", []) if isinstance(data, dict) else []
    exact: Set[str] = set()
    regex: List[re.Pattern[str]] = []
    for s in items:
        if isinstance(s, str) and s.startswith('/') and s.endswith('/'):
            regex.append(re.compile(s[1:-1]))
        elif isinstance(s, str):
            exact.add(s)
    return exact, regex


def is_ignored(name: str, exact: Set[str], regex: List[re.Pattern[str]]) -> bool:
    return name in exact or any(r.search(name) for r in regex)


def main() -> None:
    cfg = parse_args()
    introspect = read_introspect(cfg)
    bindings = extract_bindings(cfg.roots)
    ign_exact, ign_regex = load_ignore(cfg.ignore_file)

    # Link-through
    unresolved: List[str] = []
    lib = load_library(cfg.lib_path)
    if lib is not None:
        for name in sorted(bindings):
            if is_ignored(name, ign_exact, ign_regex):
                continue
            try:
                getattr(lib, name)
            except AttributeError:
                unresolved.append(name)

    missing = sorted(n for n in introspect if n not in bindings and not is_ignored(n, ign_exact, ign_regex))
    extra = sorted(n for n in bindings if n not in introspect and not is_ignored(n, ign_exact, ign_regex))

    exit_code = 0
    def report(label: str, items: List[str]) -> None:
        nonlocal exit_code
        if not items:
            return
        print(f"{label} ({len(items)}):")
        for n in items:
            print(f"  - {n}")
        exit_code = 1

    report("MISSING in bindings", missing)
    report("EXTRA in bindings", extra)
    report("UNRESOLVED (not found in library)", unresolved)

    if cfg.strict and exit_code:
        raise SystemExit(exit_code)
    print("TS FFI coverage audit complete.")


if __name__ == "__main__":
    main()

