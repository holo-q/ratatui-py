#!/usr/bin/env python3
"""Generate `src/ratatui_py/_ffi.py` from the frozen FFI manifest.

This is the Python emitter of the ratatui bindings codegen pipeline (see
`../ratatui-ffi/CODEGEN.md`). The Rust FFI is the ABI truth; `bindings.json`
is the typed IR emitted from it; this script turns that IR into the ctypes
interop layer so hand-drift becomes structurally impossible.

The generated `_ffi.py` keeps the exact public surface the ergonomic layer
(`wrappers.py`, `layout.py`, `__init__.py`) already imports:
  - `load_library()` and the existing resolver/loader mechanism (unchanged).
  - Value-struct `ctypes.Structure` subclasses in C layout order.
  - `FFI_*` int-constant dicts derived from manifest enums/bitflags.
  - Every export bound with `.argtypes` / `.restype` per the CODEGEN.md
    Python column.

Stdlib only. Deterministic: same manifest in, byte-identical file out.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

# --- IR model ----------------------------------------------------------------
# Small typed views over the JSON so the emitter is structured, not string soup.
# IrType is left as the raw tagged-union dict (it is recursive and total-mapped
# by `ctype_for` below); the named records wrap the rest.


@dataclass(frozen=True)
class Field:
    name: str
    type: dict


@dataclass(frozen=True)
class Param:
    name: str
    type: dict


@dataclass(frozen=True)
class Function:
    name: str
    params: list[Param]
    ret: dict
    cfg_feature: str | None


@dataclass(frozen=True)
class ValueStruct:
    name: str
    fields: list[Field]


@dataclass(frozen=True)
class EnumDef:
    name: str
    repr: str
    variants: list[tuple[str, int]]


@dataclass(frozen=True)
class Manifest:
    ffi_version: str
    ratatui_version: str
    functions: list[Function]
    value_structs: list[ValueStruct]
    opaque_structs: list[str]
    enums: list[EnumDef]
    bitflags: list[EnumDef]


def load_manifest(path: Path) -> Manifest:
    raw = json.loads(path.read_text())
    return Manifest(
        ffi_version=raw["ffi_version"],
        ratatui_version=raw["ratatui_version"],
        functions=[
            Function(
                name=f["name"],
                params=[Param(p["name"], p["type"]) for p in f["params"]],
                ret=f["ret"],
                cfg_feature=f.get("cfg_feature"),
            )
            for f in raw["functions"]
        ],
        value_structs=[
            ValueStruct(vs["name"], [Field(fl["name"], fl["type"]) for fl in vs["fields"]])
            for vs in raw["value_structs"]
        ],
        opaque_structs=list(raw["opaque_structs"]),
        enums=[
            EnumDef(e["name"], e["repr"], [(v["name"], v["value"]) for v in e["variants"]])
            for e in raw["enums"]
        ],
        bitflags=[
            EnumDef(e["name"], e["repr"], [(v["name"], v["value"]) for v in e["variants"]])
            for e in raw["bitflags"]
        ],
    )


# --- Type mapping (TOTAL) -----------------------------------------------------
# Per the CODEGEN.md Python column. Unknown kinds raise — never guess.

_PRIM_CTYPE = {
    "u8": "C.c_uint8",
    "u16": "C.c_uint16",
    "u32": "C.c_uint32",
    "u64": "C.c_uint64",
    "usize": "C.c_size_t",
    "i8": "C.c_int8",
    "i16": "C.c_int16",
    "i32": "C.c_int32",
    "i64": "C.c_int64",
    "f32": "C.c_float",
    "f64": "C.c_double",
    "bool": "C.c_bool",
}


def ctype_for(t: dict) -> str:
    """Map an IrType to a ctypes expression string. Total — raises on unknown.

    Pointer policy (matches the existing hand-written interop, which is uniform
    across every binding): a `ptr->char` is `c_char_p` (UTF-8 in/out); every
    other pointer collapses to `c_void_p`. Typed `POINTER(...)` is NOT used for
    arbitrary pointers — the old file used `c_void_p` for handles and only typed
    pointers for out-params/arrays of known structs. We follow the simpler,
    ABI-correct rule from the table: ptr->char => c_char_p, ptr->* => c_void_p.
    By-value `struct(opaque=false)` becomes the generated Structure type.
    """
    kind = t["kind"]
    if kind == "prim":
        name = t["name"]
        ct = _PRIM_CTYPE.get(name)
        if ct is None:
            raise ValueError(f"unknown prim type: {name!r} in {t!r}")
        return ct
    if kind == "char":
        # c_char only ever appears under a ptr in this ABI; a bare char would be
        # c_char, but the manifest never emits one. Handle defensively.
        return "C.c_char"
    if kind == "void":
        # void as a pointee or unit; bare void return is handled by the caller.
        return "None"
    if kind == "ptr":
        elem = t["elem"]
        if elem["kind"] == "char":
            return "C.c_char_p"
        return "C.c_void_p"
    if kind == "struct":
        if t.get("opaque"):
            # An opaque struct can only be crossed by pointer; by-value opaque is
            # not a valid ABI and the manifest never emits it. Defensive guard.
            raise ValueError(f"opaque struct by value is not representable: {t!r}")
        # value-struct passed by value => the generated Structure subclass.
        return t["name"]
    raise ValueError(f"unknown IrType kind: {kind!r} in {t!r}")


def restype_for(ret: dict) -> str | None:
    """ctypes restype expression, or None for a void return (no restype set)."""
    if ret["kind"] == "void":
        return None
    return ctype_for(ret)


# --- Struct dependency ordering ----------------------------------------------
# Value-structs reference each other by value (e.g. FfiCellLines -> FfiLineSpans
# -> FfiSpan -> FfiStyle). ctypes Structure subclasses must be DEFINED before
# referenced as a `_fields_` type. The manifest order is alphabetical, not
# dependency order, so we topologically sort by value-struct references.
# A struct under a ptr is NOT a hard dependency (it becomes c_void_p), so only
# by-value struct fields create edges.


def struct_value_deps(vs: ValueStruct) -> set[str]:
    deps: set[str] = set()

    def walk(t: dict, under_ptr: bool) -> None:
        kind = t["kind"]
        if kind == "ptr":
            walk(t["elem"], under_ptr=True)
        elif kind == "struct" and not t.get("opaque") and not under_ptr:
            deps.add(t["name"])

    for f in vs.fields:
        walk(f.type, under_ptr=False)
    return deps


def topo_order_structs(structs: list[ValueStruct]) -> list[ValueStruct]:
    by_name = {s.name: s for s in structs}
    ordered: list[ValueStruct] = []
    seen: set[str] = set()

    def visit(name: str, stack: tuple[str, ...]) -> None:
        if name in seen:
            return
        if name in stack:
            raise ValueError(f"cyclic value-struct dependency: {' -> '.join((*stack, name))}")
        vs = by_name.get(name)
        if vs is None:
            return  # ptr-only / external reference; nothing to define here
        for dep in sorted(struct_value_deps(vs)):
            visit(dep, (*stack, name))
        seen.add(name)
        ordered.append(vs)

    # Visit in manifest (alphabetical) order for determinism; deps pulled first.
    for s in structs:
        visit(s.name, ())
    return ordered


# --- Name derivation ----------------------------------------------------------
# Consumers import `FFI_EVENT_KIND` etc. Manifest enum names are `FfiEventKind`.
# Strip the `Ffi` prefix, insert underscores at camel boundaries, uppercase,
# prefix `FFI_`. This reproduces every name the ergonomic layer imports.


def enum_const_name(enum_name: str) -> str:
    base = enum_name[3:] if enum_name.startswith("Ffi") else enum_name
    out: list[str] = []
    for i, ch in enumerate(base):
        if ch.isupper() and i > 0:
            out.append("_")
        out.append(ch.upper())
    return "FFI_" + "".join(out)


# --- Emitter ------------------------------------------------------------------

HEADER = (
    "# GENERATED from bindings.json by tools/gen_ffi.py — DO NOT EDIT. "
    "Regenerate with `just gen`. ffi={ffi} ratatui={ratatui}"
)

# The library loader/resolver is ABI-stable infrastructure, not derived from the
# manifest — it is carried verbatim so `load_library()` keeps working exactly as
# the prior hand-written file did (RATATUI_FFI_LIB env, bundled .so, auto-build).
LOADER_PREAMBLE = '''\
import os
import sys
import ctypes as C
from typing import Optional
from ctypes.util import find_library
from pathlib import Path
import shutil
import tempfile
import subprocess
'''

# Non-manifest ABI constants: layout direction is passed as a raw c_uint to the
# split functions and is not modelled as an enum in the IR, but `layout.py`
# imports FFI_LAYOUT_DIR. Kept here as a hand-stable ABI fact.
NONMANIFEST_CONSTS = '''\
# Layout direction is passed as a raw c_uint to ratatui_layout_split*; the IR
# does not model it as an enum, but the ergonomic layer (layout.py) imports it.
FFI_LAYOUT_DIR = {"Vertical": 0, "Horizontal": 1}
'''

LOADER_BODY = '''\
def _default_names():
    if sys.platform.startswith("win"):
        return ["ratatui_ffi.dll"]
    elif sys.platform == "darwin":
        return ["libratatui_ffi.dylib"]
    else:
        return ["libratatui_ffi.so", "ratatui_ffi"]


_cached_lib = None


def _resolve_library(explicit: Optional[str] = None) -> C.CDLL:
    path = explicit or os.getenv("RATATUI_FFI_LIB")
    if path and os.path.exists(path):
        return C.CDLL(path)
    pkg_dir = Path(__file__).resolve().parent
    bundled = pkg_dir / "_bundled"
    plat = (
        "ratatui_ffi.dll"
        if sys.platform.startswith("win")
        else ("libratatui_ffi.dylib" if sys.platform == "darwin" else "libratatui_ffi.so")
    )
    candidate = bundled / plat
    if candidate.exists():
        try:
            return C.CDLL(str(candidate))
        except OSError:
            pass
    libname = find_library("ratatui_ffi")
    if libname:
        try:
            return C.CDLL(libname)
        except OSError:
            pass
    last_err = None
    for name in _default_names():
        try:
            return C.CDLL(name)
        except OSError as e:
            last_err = e
    auto = os.getenv("RATATUI_FFI_AUTO_BUILD", "1")
    if auto != "0" and shutil.which("cargo"):
        try:
            git_url = os.getenv("RATATUI_FFI_GIT", "https://github.com/holo-q/ratatui-ffi.git")
            tag = os.getenv("RATATUI_FFI_TAG", "v0.2.1")
            cache_dir = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "ratatui-py" / "ffi" / tag
            cache_dir.mkdir(parents=True, exist_ok=True)
            dst = cache_dir / plat
            if not dst.exists():
                if os.getenv("RATATUI_FFI_PROGRESS", "1") not in ("0", "false", "False", ""):
                    sys.stderr.write(f"ratatui-py: building ratatui_ffi {tag} (first run) ...\\n")
                    sys.stderr.flush()
                with tempfile.TemporaryDirectory() as td:
                    subprocess.check_call(["git", "init"], cwd=td)
                    subprocess.check_call(["git", "remote", "add", "origin", git_url], cwd=td)
                    subprocess.check_call(["git", "fetch", "--depth", "1", "origin", tag], cwd=td)
                    subprocess.check_call(["git", "checkout", "FETCH_HEAD"], cwd=td)
                    subprocess.check_call(["cargo", "build", "--release"], cwd=td)
                    built = Path(td) / "target" / "release" / dst.name
                    if not built.exists():
                        raise FileNotFoundError(str(built))
                    shutil.copy2(built, dst)
            return C.CDLL(str(dst))
        except Exception as e:
            raise RuntimeError(
                "Failed to auto-build ratatui_ffi; install Rust/cargo, set RATATUI_FFI_LIB "
                "to a prebuilt library, or disable auto-build with RATATUI_FFI_AUTO_BUILD=0."
            ) from e
    raise RuntimeError(
        "No bundled or system ratatui_ffi found. Set RATATUI_FFI_LIB to a prebuilt "
        ".so/.dylib/.dll, or install Rust (cargo) and enable auto-build via RATATUI_FFI_AUTO_BUILD=1."
    ) from last_err


def load_library(explicit: Optional[str] = None) -> C.CDLL:
    global _cached_lib
    if _cached_lib is not None:
        return _cached_lib
    lib = _resolve_library(explicit)
    _bind_prototypes(lib)
    _cached_lib = lib
    return lib
'''


def emit_struct(vs: ValueStruct) -> str:
    lines = [f"class {vs.name}(C.Structure):", "    _fields_ = ["]
    for f in vs.fields:
        lines.append(f'        ("{f.name}", {ctype_for(f.type)}),')
    lines.append("    ]")
    return "\n".join(lines)


def emit_enum(e: EnumDef) -> str:
    const = enum_const_name(e.name)
    lines = [f"{const} = {{"]
    for name, value in e.variants:
        lines.append(f'    "{name}": {value},')
    lines.append("}")
    return "\n".join(lines)


def emit_prototype(fn: Function) -> str:
    argtypes = ", ".join(ctype_for(p.type) for p in fn.params)
    rest = restype_for(fn.ret)
    lines = [f"    lib.{fn.name}.argtypes = [{argtypes}]"]
    if rest is not None:
        lines.append(f"    lib.{fn.name}.restype = {rest}")
    return "\n".join(lines)


def emit(manifest: Manifest) -> str:
    out: list[str] = []
    out.append(HEADER.format(ffi=manifest.ffi_version, ratatui=manifest.ratatui_version))
    out.append("")
    out.append(LOADER_PREAMBLE)
    out.append("# ----- Value-struct layouts (C ABI, dependency-ordered) -----")
    out.append("")
    for vs in topo_order_structs(manifest.value_structs):
        out.append(emit_struct(vs))
        out.append("")

    out.append("# ----- Enums (named int constants) -----")
    out.append("")
    for e in manifest.enums:
        out.append(emit_enum(e))
        out.append("")
    out.append("# ----- Bitflags (named int constants) -----")
    out.append("")
    for e in manifest.bitflags:
        out.append(emit_enum(e))
        out.append("")
    out.append(NONMANIFEST_CONSTS)

    out.append("# ----- Library loader / resolver -----")
    out.append("")
    out.append(LOADER_BODY)
    out.append("")

    # Prototype binder: sets argtypes/restype for every export, then exposes the
    # value-struct types as attributes on the lib object (the ergonomic layer
    # reaches them as `load_library().FfiSpan` etc.).
    out.append("def _bind_prototypes(lib: C.CDLL) -> None:")
    out.append(f"    # All {len(manifest.functions)} exports — argtypes/restype per the FFI ABI manifest.")
    for fn in manifest.functions:
        if fn.cfg_feature:
            # cfg-gated exports may be absent if the loaded lib lacks the feature.
            out.append(f"    if hasattr(lib, {fn.name!r}):  # cfg_feature={fn.cfg_feature}")
            body = emit_prototype(fn)
            for ln in body.splitlines():
                out.append("    " + ln)
        else:
            out.append(emit_prototype(fn))
    out.append("")
    out.append("    # Expose value-struct types on the lib object for the ergonomic layer.")
    for vs in manifest.value_structs:
        out.append(f"    lib.{vs.name} = {vs.name}")
    out.append("")

    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    ap.add_argument(
        "--manifest",
        type=Path,
        default=here.parent.parent / "ratatui-ffi" / "bindings.json",
        help="path to bindings.json (default: ../ratatui-ffi/bindings.json)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=here.parent / "src" / "ratatui_py" / "_ffi.py",
        help="output path for the generated _ffi.py",
    )
    args = ap.parse_args()
    manifest = load_manifest(args.manifest)
    text = emit(manifest)
    if not text.endswith("\n"):
        text += "\n"
    args.out.write_text(text)
    print(
        f"wrote {args.out} — {len(manifest.functions)} fns, "
        f"{len(manifest.value_structs)} structs, "
        f"{len(manifest.enums)} enums, {len(manifest.bitflags)} bitflags "
        f"(ffi={manifest.ffi_version} ratatui={manifest.ratatui_version})"
    )


if __name__ == "__main__":
    main()
