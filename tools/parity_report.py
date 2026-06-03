#!/usr/bin/env python3
"""Parity + residue reports for the Python FFI emitter.

Two reports, both written under tools/:

  parity-report.txt  — generated (manifest) symbol set vs the prior hand-written
                       _ffi.py. Three lists:
                         added    manifest fns the old file lacked (drift closed)
                         removed  old file had, manifest lacks (investigate)
                         changed  argtypes/restype differs (investigate ABI)
                       Old prototypes are parsed textually from the snapshot
                       (`tmp/_ffi_old.py`) since the prior file gated most
                       prototypes behind hasattr() and is not fully loadable
                       without the .so.

  residue.txt        — every FFI fn that appears ONLY in the generated _ffi.py
                       and is referenced nowhere else under src/ratatui_py/ (no
                       ergonomic wrapper). The manual-work worklist.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


# --- manifest-side prototype model -------------------------------------------

_PRIM_CTYPE = {
    "u8": "C.c_uint8", "u16": "C.c_uint16", "u32": "C.c_uint32", "u64": "C.c_uint64",
    "usize": "C.c_size_t", "i8": "C.c_int8", "i16": "C.c_int16", "i32": "C.c_int32",
    "i64": "C.c_int64", "f32": "C.c_float", "f64": "C.c_double", "bool": "C.c_bool",
}


def ctype_for(t: dict) -> str:
    k = t["kind"]
    if k == "prim":
        return _PRIM_CTYPE[t["name"]]
    if k == "char":
        return "C.c_char"
    if k == "void":
        return "None"
    if k == "ptr":
        return "C.c_char_p" if t["elem"]["kind"] == "char" else "C.c_void_p"
    if k == "struct":
        return t["name"]
    raise ValueError(t)


def manifest_proto(fn: dict) -> tuple[tuple[str, ...], str | None]:
    args = tuple(ctype_for(p["type"]) for p in fn["params"])
    rest = None if fn["ret"]["kind"] == "void" else ctype_for(fn["ret"])
    return args, rest


# --- old-file prototype parsing (textual) ------------------------------------
# The old _ffi.py set prototypes as `lib.<fn>.argtypes = [...]` and
# `lib.<fn>.restype = ...`, frequently inside hasattr() guards. We collect those
# assignments by regex. Normalization folds the cosmetic differences (whitespace,
# POINTER(Struct) vs c_void_p) that are NOT real ABI differences, so `changed`
# reports only genuine signature divergence.

_ARG_RE = re.compile(r"lib\.([A-Za-z0-9_]+)\.argtypes\s*=\s*\[", re.M)
_REST_RE = re.compile(r"lib\.([A-Za-z0-9_]+)\.restype\s*=\s*([A-Za-z0-9_.()\[\] *]+)")
# An old-file export is a symbol the old file intends to bind on the lib object.
# The old file expressed that two ways: `lib.<name>` attribute access (direct
# prototype set / hasattr touch) AND quoted `'ratatui_...'` string entries fed
# through the `for name in [...]: getattr(lib, name)` binder loops. We accept
# both. Loader-infrastructure mentions of "ratatui_ffi" (find_library(...),
# default .so/.dll names) are excluded because they end in a file extension or
# are not function-shaped — handled by requiring the lib./quote context and the
# explicit name shape. A bare `"ratatui_ffi"` default-name literal is filtered
# out below since it is not a real export name.
_NAME_RE = re.compile(
    r"""(?:lib\.|['"])(ratatui_[A-Za-z0-9_]+|FfiCellInfo|FfiDrawCmd)\b"""
)
# Loader string literals that are NOT exports (library file names, base name).
_NOT_EXPORTS = {"ratatui_ffi"}


def _balanced_list(text: str, start: int) -> str:
    """Return the bracketed [...] slice starting at index `start` (at '[')."""
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
        i += 1
    return text[start:]


def _norm_ctype(tok: str) -> str:
    tok = tok.strip()
    # POINTER(X) and c_char_p/c_void_p all collapse to the pointer policy: any
    # pointer is a pointer at the ABI level. The generated file uses c_void_p for
    # non-char pointers and c_char_p for char pointers; the old file sometimes
    # used POINTER(Struct)/POINTER(c_uint16) etc. Treat every pointer-ish token
    # as the opaque pointer class so we don't flag policy-equivalent forms.
    if tok.startswith("C.POINTER") or tok in ("C.c_void_p",):
        return "PTR"
    if tok == "C.c_char_p":
        return "PTR"  # char* is still a pointer; both bindings pass strings here
    # primitive width aliases the old file used: c_uint == c_uint32, c_int == c_int32
    alias = {
        "C.c_uint": "C.c_uint32",
        "C.c_int": "C.c_int32",
        "C.c_ulonglong": "C.c_uint64",
        "C.c_longlong": "C.c_int64",
        "C.c_ubyte": "C.c_uint8",
        "C.c_byte": "C.c_int8",
    }
    return alias.get(tok, tok)


def _norm_args(arglist_src: str) -> tuple[str, ...]:
    inner = arglist_src.strip()[1:-1]  # strip [ ]
    # Strip inline comments FIRST, per source line — the old file's multi-line
    # argtype lists carried `# w, h, dir`-style comments whose commas would
    # otherwise be mistaken for argument separators at depth 0.
    inner = "\n".join(ln.split("#", 1)[0] for ln in inner.splitlines())
    # split on top-level commas
    parts: list[str] = []
    depth = 0
    cur = ""
    for ch in inner:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    out: list[str] = []
    for p in parts:
        # strip inline comments
        p = p.split("#", 1)[0].strip()
        if p:
            out.append(_norm_ctype(p))
    return tuple(out)


def parse_old_protos(text: str) -> dict[str, dict]:
    """name -> {'args': (...)|None, 'rest': str|None}. Presence = name seen at all."""
    protos: dict[str, dict] = {}
    # presence: every ratatui_/Ffi symbol the old file intends to bind
    for m in _NAME_RE.finditer(text):
        name = m.group(1)
        if name in _NOT_EXPORTS:
            continue
        protos.setdefault(name, {"args": None, "rest": None})
    for m in _ARG_RE.finditer(text):
        name = m.group(1)
        lst = _balanced_list(text, m.end() - 1)
        protos.setdefault(name, {"args": None, "rest": None})
        protos[name]["args"] = _norm_args(lst)
    for m in _REST_RE.finditer(text):
        name, rest = m.group(1), m.group(2).strip()
        protos.setdefault(name, {"args": None, "rest": None})
        protos[name]["rest"] = _norm_ctype(rest)
    return protos


def _norm_manifest_args(args: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_norm_ctype(a) for a in args)


def _norm_manifest_rest(rest: str | None) -> str | None:
    return None if rest is None else _norm_ctype(rest)


# --- residue (no ergonomic wrapper) ------------------------------------------


def referenced_outside_ffi(src_dir: Path, fn_names: set[str]) -> set[str]:
    referenced: set[str] = set()
    for py in src_dir.rglob("*.py"):
        if py.name == "_ffi.py":
            continue
        txt = py.read_text(errors="replace")
        for name in fn_names:
            if name in txt:
                referenced.add(name)
    return referenced


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    repo = here.parent
    ap.add_argument("--manifest", type=Path, default=repo.parent / "ratatui-ffi" / "bindings.json")
    ap.add_argument("--old", type=Path, default=repo / "tmp" / "_ffi_old.py")
    ap.add_argument("--src", type=Path, default=repo / "src" / "ratatui_py")
    ap.add_argument("--parity-out", type=Path, default=here / "parity-report.txt")
    # residue.txt is owned by the Stage-2 generator (gen_wrappers.py), which
    # writes the wrapped-now / deliberately-raw / still-unwrapped triage from its
    # structured plan. This tool's text-scan residue is kept as an independent
    # cross-check under a distinct name so the two can be diffed if they drift.
    ap.add_argument("--residue-out", type=Path, default=here / "residue-scan.txt")
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    fns = {f["name"]: f for f in manifest["functions"]}
    manifest_names = set(fns)

    old_text = args.old.read_text()
    old_protos = parse_old_protos(old_text)
    old_fn_names = {n for n in old_protos if n.startswith("ratatui_")}

    added = sorted(manifest_names - old_fn_names)
    removed = sorted(old_fn_names - manifest_names)

    changed: list[str] = []
    for name in sorted(manifest_names & old_fn_names):
        old = old_protos[name]
        m_args, m_rest = manifest_proto(fns[name])
        m_args = _norm_manifest_args(m_args)
        m_rest = _norm_manifest_rest(m_rest)
        # Only compare where the old file actually declared the prototype; a
        # name present but with no argtypes/restype set means the old file left
        # it at ctypes defaults (int/int) — not a real ABI claim to diff.
        diffs = []
        if old["args"] is not None and old["args"] != m_args:
            diffs.append(f"args old={list(old['args'])} new={list(m_args)}")
        if old["rest"] is not None and old["rest"] != m_rest:
            diffs.append(f"rest old={old['rest']} new={m_rest}")
        if diffs:
            changed.append(f"{name}: " + "; ".join(diffs))

    lines = []
    lines.append("# Parity report: generated (manifest) vs prior hand-written _ffi.py")
    lines.append(f"# manifest fns: {len(manifest_names)}   old fns: {len(old_fn_names)}")
    lines.append("")
    lines.append(f"## added ({len(added)}) — manifest has, old lacked (drift gap closed)")
    lines += added or ["(none)"]
    lines.append("")
    lines.append(f"## removed ({len(removed)}) — old had, manifest lacks (investigate)")
    lines += removed or ["(none)"]
    lines.append("")
    lines.append(f"## changed ({len(changed)}) — argtypes/restype differs (investigate)")
    lines += changed or ["(none)"]
    lines.append("")
    args.parity_out.write_text("\n".join(lines))

    # residue
    referenced = referenced_outside_ffi(args.src, manifest_names)
    residue = sorted(manifest_names - referenced)
    rlines = [
        "# Residue: FFI fns with NO ergonomic wrapper (only in generated _ffi.py).",
        "# These are the manual-work worklist — exports the OO layer does not surface yet.",
        f"# total exports: {len(manifest_names)}   wrapped: {len(referenced)}   residue: {len(residue)}",
        "",
    ]
    rlines += residue or ["(none)"]
    args.residue_out.write_text("\n".join(rlines) + "\n")

    print(f"parity: added={len(added)} removed={len(removed)} changed={len(changed)}")
    print(f"residue: {len(residue)} of {len(manifest_names)} exports unwrapped")
    print(f"wrote {args.parity_out}")
    print(f"wrote {args.residue_out}")


if __name__ == "__main__":
    main()
