#!/usr/bin/env python3
"""Stage-2 ergonomic wrapper generator for ratatui-py.

The Stage-1 emitter (`gen_ffi.py`) turns the typed IR (`bindings.json`) into the
ctypes interop layer. Stage-2 (this script) shrinks the *residue* — FFI fns with
no ergonomic wrapper — by generating idiomatic widget methods from the same
manifest, following the verb taxonomy in `../ratatui-ffi/CODEGEN.md` (Stage 2):

    _set_<prop>          -> fluent setter returning self
    _append_* / _add_*   -> append/add method
    headless_render_<w>  -> module-level render helper
    _free/_reserve/_new* -> NOT generated (disposal / perf / ctor)

Composition (the cleanest non-colliding shape for Python): a generated module
`src/ratatui_py/_wrappers_generated.py` defines, per widget group, the methods
as plain functions, plus an `apply_generated()` that `setattr`s them onto the
hand-written classes ONLY where the hand class lacks the name (hand wins,
collisions skipped + reported). This mirrors the idiom already used at the foot
of `wrappers.py` (`setattr(Terminal, 'draw_list_state', ...)`), so the generated
layer ADDS to the public API without inheritance churn across ten classes.

The marshaling mirrors the hand wrappers exactly: `_build_spans` /
`_build_lines_spans` for span arrays, `Style.to_ffi()` for styles, UTF-8 encode
for char*, out-string decode + `ratatui_string_free` for headless renders.

`LineGauge` is an entirely new widget with no hand class — its full ergonomic
class (ctor/free/setters/render) is generated standalone.

Stdlib only. Deterministic: manifest is emitted in name order; same input → byte
-identical output.
"""
from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass, field
from pathlib import Path


# --- IR model (only what Stage-2 needs) --------------------------------------


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


def load_functions(path: Path) -> list[Function]:
    raw = json.loads(path.read_text())
    return [
        Function(
            name=f["name"],
            params=[Param(p["name"], p["type"]) for p in f["params"]],
            ret=f["ret"],
            cfg_feature=f.get("cfg_feature"),
        )
        for f in raw["functions"]
    ]


# --- IrType shape predicates --------------------------------------------------
# Stage-2 dispatches on the *tail shape* of a function's params (after the
# leading handle). These predicates name the shapes the taxonomy recognises.


def is_prim(t: dict, name: str) -> bool:
    return t["kind"] == "prim" and t["name"] == name


def is_ptr_to_struct(t: dict, struct: str) -> bool:
    return t["kind"] == "ptr" and t["elem"].get("kind") == "struct" and t["elem"].get("name") == struct


def is_ptr_char(t: dict) -> bool:
    return t["kind"] == "ptr" and t["elem"].get("kind") == "char"


def is_value_style(t: dict) -> bool:
    return t["kind"] == "struct" and t.get("name") == "FfiStyle" and not t.get("opaque")


def is_handle(t: dict) -> bool:
    # An opaque widget handle is always crossed as a pointer to an opaque struct.
    return t["kind"] == "ptr" and t["elem"].get("kind") == "struct" and t["elem"].get("opaque", False)


# --- Group → hand class map ---------------------------------------------------
# Every export is ratatui_<group>_<verb...>. The <group> token selects the hand
# wrapper class the generated methods attach to. `linegauge` has no hand class
# (new widget) — generated as a standalone class instead.

GROUP_CLASS = {
    "paragraph": "Paragraph",
    "list_state": "ListState",
    "table_state": "TableState",
    "list": "List",
    "table": "Table",
    "gauge": "Gauge",
    "tabs": "Tabs",
    "barchart": "BarChart",
    "sparkline": "Sparkline",
    "scrollbar": "Scrollbar",
    "chart": "Chart",
    "canvas": "Canvas",
}

# Groups whose token is multi-segment must be matched longest-first so e.g.
# `ratatui_list_state_*` is not mis-split as group `list`.
_GROUP_PREFIXES = sorted(GROUP_CLASS, key=len, reverse=True)

LINEGAUGE_GROUP = "linegauge"

# Verbs we never wrap (disposal / perf / capacity / constructors). Suffix match
# on the verb token after the group. `new`/`new_*` ctors are hand-written;
# `free` is owned by __del__; `reserve_*` is a low-level capacity hint.
RAW_REASONS = {
    "free": "disposal — owned by __del__",
    "reserve": "capacity hint — low-level perf, leave raw",
    "new": "constructor — hand-written",
}


# --- Method codegen -----------------------------------------------------------
# A WrapperMethod is the structured plan for one generated member. The writer
# turns it into Python source. `body` lines are emitted at 8-space indent (inside
# the function), `self`-style for instance methods.


@dataclass
class WrapperMethod:
    fn: Function          # source FFI function
    cls: str              # target hand class (or generated class)
    method: str           # python method name
    sig: str              # python signature after self (e.g. "spans, show_border=True")
    body: list[str]       # function body lines (no leading indent normalization)
    returns_self: bool    # fluent setter?
    is_static: bool = False


@dataclass
class Plan:
    methods: list[WrapperMethod] = field(default_factory=list)
    headless: list[Function] = field(default_factory=list)   # module render helpers
    draw_in: list[Function] = field(default_factory=list)     # Terminal draw_*_in
    linegauge: list[Function] = field(default_factory=list)   # whole LineGauge group
    wrapped_now: list[str] = field(default_factory=list)
    deliberately_raw: list[tuple[str, str]] = field(default_factory=list)
    skipped_collision: list[tuple[str, str]] = field(default_factory=list)
    still_unwrapped: list[str] = field(default_factory=list)


def method_name(fn_name: str, group: str) -> str:
    """ratatui_<group>_<rest> -> <rest> (already snake_case)."""
    return fn_name[len(f"ratatui_{group}_") :]


def split_group(fn_name: str) -> str | None:
    if not fn_name.startswith("ratatui_"):
        return None
    rest = fn_name[len("ratatui_") :]
    if rest.startswith(LINEGAUGE_GROUP + "_") or rest == LINEGAUGE_GROUP:
        return LINEGAUGE_GROUP
    for g in _GROUP_PREFIXES:
        if rest == g or rest.startswith(g + "_"):
            return g
    return None


def raw_reason(verb: str) -> str | None:
    if verb == "free" or verb.startswith("free"):
        return RAW_REASONS["free"]
    if verb.startswith("reserve"):
        return RAW_REASONS["reserve"]
    if verb == "new" or verb.startswith("new"):
        return RAW_REASONS["new"]
    return None


# Tail-shape marshalers. Each takes the params AFTER the handle and, if it
# recognises the shape, returns (python_sig_after_self, body_lines, call_args).
# `h` is the handle expr (`self._handle`); the call passes the marshaled args.


def plan_setter_body(fn: Function, handle_expr: str) -> tuple[str, list[str]] | None:
    """Return (sig_after_handle, body_lines) for a recognised setter/append shape,
    or None if the shape is not in the taxonomy. body uses `self._lib` + handle."""
    ps = fn.params[1:]  # drop the leading handle
    call = f"self._lib.{fn.name}({handle_expr}"

    # --- spans tail: (*FfiSpan, usize[, bool show_border]) ---
    if len(ps) >= 2 and is_ptr_to_struct(ps[0].type, "FfiSpan") and is_prim(ps[1].type, "usize"):
        trailing = ps[2:]
        if not trailing:
            body = [
                "arr, _keep = _build_spans(spans)",
                f"{call}, arr, len(arr))",
            ]
            return "spans", body
        if len(trailing) == 1 and is_prim(trailing[0].type, "bool"):
            body = [
                "arr, _keep = _build_spans(spans)",
                f"{call}, arr, len(arr), bool(show_border))",
            ]
            return "spans, show_border=True", body
        return None

    # --- lines tail: (*FfiLineSpans, usize) ---
    if len(ps) == 2 and is_ptr_to_struct(ps[0].type, "FfiLineSpans") and is_prim(ps[1].type, "usize"):
        body = [
            "arr, _keep = _build_lines_spans(lines)",
            f"{call}, arr, len(arr))",
        ]
        return "lines", body

    # --- block_adv: (u8 borders, u32 border_type, u16 pad_l..pad_b, *FfiSpan, usize) ---
    if (
        len(ps) == 8
        and is_prim(ps[0].type, "u8")
        and is_prim(ps[1].type, "u32")
        and all(is_prim(ps[i].type, "u16") for i in (2, 3, 4, 5))
        and is_ptr_to_struct(ps[6].type, "FfiSpan")
        and is_prim(ps[7].type, "usize")
    ):
        body = [
            "arr, _keep = _build_spans(title_spans)",
            f"{call}, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),",
            "    C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),",
            "    C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),",
            "    arr, len(arr))",
        ]
        sig = (
            "borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, "
            "title_spans=()"
        )
        return sig, body

    # --- single value style: (FfiStyle) ---
    if len(ps) == 1 and is_value_style(ps[0].type):
        body = [f"{call}, style.to_ffi())"]
        return "style", body

    # --- single scalar setters ---
    if len(ps) == 1:
        t = ps[0].type
        nm = ps[0].name
        if is_prim(t, "u32"):
            body = [f"{call}, C.c_uint32(int({nm})))"]
            return nm, body
        if is_prim(t, "u16"):
            body = [f"{call}, C.c_uint16(int({nm})))"]
            return nm, body
        if is_prim(t, "f32"):
            body = [f"{call}, C.c_float(float({nm})))"]
            return nm, body
        if is_prim(t, "f64"):
            body = [f"{call}, C.c_double(float({nm})))"]
            return nm, body
        if is_prim(t, "bool"):
            body = [f"{call}, bool({nm}))"]
            return nm, body
        if is_ptr_char(t):
            body = [
                f"_s = None if {nm} is None else {nm}.encode('utf-8')",
                f"{call}, _s)",
            ]
            return f"{nm}", body

    # --- char* + bool (set_block_title / set_label with show_border) ---
    if len(ps) == 2 and is_ptr_char(ps[0].type) and is_prim(ps[1].type, "bool"):
        nm = ps[0].name
        body = [
            f"_s = None if {nm} is None else {nm}.encode('utf-8')",
            f"{call}, _s, bool({ps[1].name}))",
        ]
        return f"{nm}, {ps[1].name}=True", body

    return None


def build_plan(fns: list[Function], hand_methods: dict[str, set[str]]) -> Plan:
    plan = Plan()
    # The set of fns already surfaced by SOME hand wrapper (referenced anywhere
    # in the hand src) is computed by the residue tool; here we work from the IR
    # and the per-class hand method names to decide collisions. The residue list
    # itself is recomputed by parity_report.py post-gen.

    # Non-widget utility exports the taxonomy leaves raw case-by-case: version /
    # feature introspection, raw color encoders, string disposal. Surfaced (if at
    # all) by hand helpers (`rgb`, `color_indexed`) — recorded here as raw so the
    # triage accounts for them rather than silently dropping them.
    NONWIDGET_RAW = {
        "ratatui_ffi_version": "version introspection (out-params) — not widget-bound",
        "ratatui_ffi_feature_bits": "feature introspection — not widget-bound",
        "ratatui_string_free": "string disposal — owned by the out-string decode helpers",
        "ratatui_color_rgb": "raw color encoder — surfaced by the rgb() helper",
        "ratatui_color_indexed": "raw color encoder — surfaced by the color_indexed() helper",
    }

    for fn in fns:
        if fn.name in NONWIDGET_RAW:
            plan.deliberately_raw.append((fn.name, NONWIDGET_RAW[fn.name]))
            continue
        group = split_group(fn.name)
        if group is None:
            continue

        if group == LINEGAUGE_GROUP:
            plan.linegauge.append(fn)
            continue

        verb = method_name(fn.name, group)

        # headless_render_<group> lives under the literal group token, but its
        # fn name is ratatui_headless_render_<group> — handled separately below.

        rr = raw_reason(verb)
        if rr is not None:
            plan.deliberately_raw.append((fn.name, rr))
            continue

        cls = GROUP_CLASS[group]
        meth = verb

        # collision: hand class already defines this method -> skip, hand wins.
        if meth in hand_methods.get(cls, set()):
            plan.skipped_collision.append((fn.name, f"{cls}.{meth} hand-written"))
            continue

        # complex array-spec verbs: marshaled bespoke (mirror hand idiom).
        bespoke = plan_bespoke(fn, group, cls, meth)
        if bespoke is not None:
            plan.methods.append(bespoke)
            continue

        result = plan_setter_body(fn, "self._handle")
        if result is None:
            plan.still_unwrapped.append(fn.name)
            continue
        sig, body = result
        returns_self = meth.startswith("set_")
        if returns_self:
            body = body + ["return self"]
        plan.methods.append(
            WrapperMethod(fn=fn, cls=cls, method=meth, sig=sig, body=body, returns_self=returns_self)
        )

    # headless_render_<group> helpers (module-level) — only for groups whose
    # hand layer lacks the helper. The residue lists the missing ones.
    for fn in fns:
        if not fn.name.startswith("ratatui_headless_render_"):
            continue
        tail = fn.name[len("ratatui_headless_render_") :]
        # Only generate the ones in the residue families: clear, linegauge,
        # scrollbar. Others (paragraph/list/...) already have hand helpers and
        # are skipped via collision with the module fn name.
        if tail in ("clear", "linegauge", "scrollbar"):
            plan.headless.append(fn)

    # Terminal draw_<group>_in for the residue families (linegauge, scrollbar).
    for fn in fns:
        if fn.name in ("ratatui_terminal_draw_linegauge_in", "ratatui_terminal_draw_scrollbar_in"):
            plan.draw_in.append(fn)

    # wrapped-now = every fn we emitted a wrapper for.
    wrapped = {m.fn.name for m in plan.methods}
    wrapped |= {f.name for f in plan.headless}
    wrapped |= {f.name for f in plan.draw_in}
    wrapped |= {f.name for f in plan.linegauge}
    plan.wrapped_now = sorted(wrapped)
    return plan


def plan_bespoke(fn: Function, group: str, cls: str, meth: str) -> WrapperMethod | None:
    """Bespoke marshalers for the few array-of-struct verbs the generic shape
    matcher cannot express. Each mirrors the existing hand idiom 1:1."""
    h = "self._handle"

    if fn.name == "ratatui_chart_add_dataset_with_type":
        # (name_utf8: char*, points_xy: f64*, len_pairs, style, kind: u32)
        body = [
            "n = name.encode('utf-8')",
            "flat = []",
            "for (x, y) in points:",
            "    flat.extend([float(x), float(y)])",
            "arr = (C.c_double * len(flat))(*flat)",
            f"self._lib.{fn.name}({h}, n, arr, len(points), (style or Style()).to_ffi(), C.c_uint32(int(kind)))",
        ]
        return WrapperMethod(fn, cls, "add_dataset_with_type",
                             "name, points, kind, style=None", body, False)

    if fn.name == "ratatui_table_append_rows_cells_lines":
        # rows: [FfiRowCellsLines] each {cells: FfiCellLines*, len}; mirrors the
        # hand append_row_cells_lines which builds one FfiCellLines array.
        body = [
            "FfiLineSpans = self._lib.FfiLineSpans",
            "FfiCellLines = self._lib.FfiCellLines",
            "FfiRowCellsLines = self._lib.FfiRowCellsLines",
            "keep = []",
            "row_structs = (FfiRowCellsLines * len(rows))()",
            "cell_buffers = []",
            "for ri, row in enumerate(rows):",
            "    cell_arr = (FfiCellLines * len(row))()",
            "    for ci, cell in enumerate(row):",
            "        lines_arr, k = _build_lines_spans(cell)",
            "        keep.append(lines_arr)",
            "        keep.extend(k)",
            "        cell_arr[ci] = FfiCellLines(lines_arr, len(lines_arr))",
            "    cell_buffers.append(cell_arr)",
            "    row_structs[ri] = FfiRowCellsLines(cell_arr, len(cell_arr))",
            f"self._lib.{fn.name}({h}, row_structs, len(row_structs))",
        ]
        return WrapperMethod(fn, cls, "append_rows_cells_lines", "rows", body, False)

    if fn.name == "ratatui_chart_add_datasets":
        # specs: [FfiChartDatasetSpec] {name_utf8, points_xy, len_pairs, style, kind}
        body = [
            "FfiChartDatasetSpec = self._lib.FfiChartDatasetSpec",
            "keep = []",
            "arr = (FfiChartDatasetSpec * len(specs))()",
            "for i, (name, points, kind, style) in enumerate(specs):",
            "    n = name.encode('utf-8')",
            "    keep.append(n)",
            "    flat = []",
            "    for (x, y) in points:",
            "        flat.extend([float(x), float(y)])",
            "    pts = (C.c_double * len(flat))(*flat)",
            "    keep.append(pts)",
            "    st = (style or Style()).to_ffi()",
            "    arr[i] = FfiChartDatasetSpec(n, pts, len(points), st, C.c_uint32(int(kind)))",
            f"self._lib.{fn.name}({h}, arr, len(arr))",
        ]
        return WrapperMethod(fn, cls, "add_datasets", "specs", body, False)

    return None


# --- Writer -------------------------------------------------------------------

HEADER = (
    "# GENERATED from bindings.json by tools/gen_wrappers.py — DO NOT EDIT. "
    "Regenerate with `just gen`."
)

PREAMBLE = '''\
"""Generated ergonomic wrappers (Stage 2 of the codegen pipeline).

Methods here ADD to the hand-written wrapper classes in `wrappers.py`. Call
`apply_generated()` once (done at import time by `wrappers.py`) to attach every
method onto its target class WHERE THE HAND CLASS LACKS THE NAME — hand-written
methods always win (collisions are skipped at generation time and reported in
tools/residue.txt). `LineGauge` is fully generated (no hand class exists).

Marshaling mirrors `wrappers.py` exactly: `_build_spans` / `_build_lines_spans`
for span arrays, `Style.to_ffi()` for styles, UTF-8 encode for char*, out-string
decode + `ratatui_string_free` for headless renders.
"""
from __future__ import annotations
import ctypes as C
from typing import Optional, Sequence, Tuple

from ._ffi import load_library
from .wrappers import (
    Style,
    Terminal,
    Paragraph,
    List,
    Table,
    Gauge,
    Tabs,
    BarChart,
    Sparkline,
    Scrollbar,
    Chart,
    Canvas,
    _build_spans,
    _build_lines_spans,
    _ffi_rect,
)
from .types import RectLike
'''


def emit_method_fn(m: WrapperMethod, fn_prefix: str) -> str:
    """Emit a free function `<prefix>__<cls>__<method>(self, <sig>)` that
    `apply_generated` will bind onto the class. Free functions keep the
    generated module flat and avoid premature class bodies."""
    sig = f"self, {m.sig}" if m.sig else "self"
    lines = [f"def {fn_prefix}_{m.cls}_{m.method}({sig}):"]
    for b in m.body:
        lines.append("    " + b)
    return "\n".join(lines)


def emit_headless(fn: Function) -> str:
    """Module-level headless_render_<x>(width, height[, widget]) -> str."""
    tail = fn.name[len("ratatui_headless_render_") :]
    # signature: width, height, and (if the fn takes a widget handle) the widget.
    has_widget = any(is_handle(p.type) for p in fn.params)
    if has_widget:
        sig = "width: int, height: int, widget"
        handle = "widget._handle"
        libexpr = "widget._lib"
    else:
        sig = "width: int, height: int"
        handle = None
        libexpr = "load_library()"
    name = f"headless_render_{tail}"
    lines = [f"def {name}({sig}) -> str:"]
    lines.append(f"    lib = {libexpr}")
    lines.append(f"    if not hasattr(lib, {fn.name!r}):")
    lines.append('        return ""')
    lines.append("    out = C.c_char_p()")
    if handle:
        lines.append(
            f"    ok = lib.{fn.name}(C.c_uint16(width), C.c_uint16(height), {handle}, C.byref(out))"
        )
    else:
        lines.append(
            f"    ok = lib.{fn.name}(C.c_uint16(width), C.c_uint16(height), C.byref(out))"
        )
    lines.append("    if not ok or not out:")
    lines.append('        return ""')
    lines.append("    try:")
    lines.append("        return C.cast(out, C.c_char_p).value.decode('utf-8', errors='replace')")
    lines.append("    finally:")
    lines.append("        lib.ratatui_string_free(out)")
    return "\n".join(lines)


def emit_draw_in(fn: Function) -> str:
    """Terminal.draw_<group>_in(widget, rect) -> bool, attached via apply."""
    # name: ratatui_terminal_draw_<group>_in
    mid = fn.name[len("ratatui_terminal_draw_") : -len("_in")]
    method = f"draw_{mid}"
    lines = [f"def _gen_Terminal_{method}(self, widget, rect):"]
    lines.append(f"    if not hasattr(self._lib, {fn.name!r}):")
    lines.append("        return False")
    lines.append("    r = _ffi_rect(rect)")
    lines.append(f"    return bool(self._lib.{fn.name}(self._handle, widget._handle, r))")
    return "\n".join(lines), "Terminal", method


def emit_linegauge(fns: list[Function]) -> str:
    """Full standalone LineGauge widget class (no hand class exists)."""
    by_name = {f.name: f for f in fns}
    lines: list[str] = []
    lines.append("class LineGauge:")
    lines.append('    """Generated ergonomic wrapper for the LineGauge widget."""')
    lines.append("")
    lines.append("    def __init__(self):")
    lines.append("        self._lib = load_library()")
    lines.append("        if not hasattr(self._lib, 'ratatui_linegauge_new'):")
    lines.append('            raise RuntimeError("ratatui_ffi lacks LineGauge APIs")')
    lines.append("        ptr = self._lib.ratatui_linegauge_new()")
    lines.append("        if not ptr:")
    lines.append('            raise RuntimeError("ratatui_linegauge_new failed")')
    lines.append("        self._handle = C.c_void_p(ptr)")
    lines.append("")
    # Emit setters (skip new/free) using the same shape matcher.
    for name in sorted(by_name):
        if name in ("ratatui_linegauge_new", "ratatui_linegauge_free"):
            continue
        fn = by_name[name]
        meth = method_name(name, LINEGAUGE_GROUP)
        result = plan_setter_body(fn, "self._handle")
        if result is None:
            continue
        sig, body = result
        returns_self = meth.startswith("set_")
        head = f"    def {meth}(self, {sig}) -> \"LineGauge\":" if returns_self else f"    def {meth}(self, {sig}):"
        lines.append(head)
        for b in body:
            lines.append("        " + b)
        if returns_self:
            lines.append("        return self")
        lines.append("")
    lines.append("    def close(self) -> None:")
    lines.append("        if getattr(self, '_handle', None):")
    lines.append("            self._lib.ratatui_linegauge_free(self._handle)")
    lines.append("            self._handle = None")
    lines.append("")
    lines.append("    def __del__(self):")
    lines.append("        try:")
    lines.append("            self.close()")
    lines.append("        except Exception:")
    lines.append("            pass")
    return "\n".join(lines)


def emit(plan: Plan) -> str:
    out: list[str] = [HEADER, "", PREAMBLE]

    out.append("")
    out.append("# ----- LineGauge (fully generated; no hand class) -----")
    out.append("")
    out.append(emit_linegauge(plan.linegauge))
    out.append("")
    out.append("")

    out.append("# ----- Generated widget methods (bound onto hand classes) -----")
    out.append("")
    for m in plan.methods:
        out.append(emit_method_fn(m, "_gen"))
        out.append("")

    out.append("")
    out.append("# ----- Terminal draw_*_in helpers -----")
    out.append("")
    draw_specs: list[tuple[str, str]] = []
    for fn in plan.draw_in:
        src, cls, method = emit_draw_in(fn)
        out.append(src)
        out.append("")
        draw_specs.append((cls, method))

    out.append("")
    out.append("# ----- Module-level headless render helpers -----")
    out.append("")
    for fn in plan.headless:
        out.append(emit_headless(fn))
        out.append("")

    # apply_generated: setattr each method onto its class IF ABSENT (hand wins).
    out.append("")
    out.append("# ----- Binder: attach generated methods where the hand class lacks them -----")
    out.append("")
    out.append("_GENERATED_METHODS = [")
    for m in plan.methods:
        out.append(f"    ({m.cls}, {m.method!r}, _gen_{m.cls}_{m.method}),")
    for cls, method in draw_specs:
        out.append(f"    ({cls}, {method!r}, _gen_{cls}_{method}),")
    out.append("]")
    out.append("")
    out.append("")
    out.append("def apply_generated() -> None:")
    out.append('    """Attach every generated method onto its target hand class, but only')
    out.append("    where the hand class does not already define the name (hand wins).")
    out.append('    Idempotent."""')
    out.append("    for cls, name, func in _GENERATED_METHODS:")
    out.append("        if name not in cls.__dict__:")
    out.append("            setattr(cls, name, func)")
    out.append("")
    return "\n".join(out)


# --- Hand-method extraction (collision detection) ----------------------------


def hand_methods(wrappers_py: Path) -> dict[str, set[str]]:
    tree = ast.parse(wrappers_py.read_text())
    out: dict[str, set[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out[node.name] = {
                m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return out


def emit_residue(plan: Plan, total: int) -> str:
    """The Stage-2 triage report: every residue fn classified into wrapped-now /
    deliberately-raw / still-unwrapped, plus the collision skips (hand wins). The
    goal is still-unwrapped → 0 with every exclusion justified."""
    lines: list[str] = []
    lines.append("# Stage-2 residue triage — generated by tools/gen_wrappers.py.")
    lines.append("# Each FFI fn with no HAND-written ergonomic wrapper is classified below.")
    lines.append("# Goal: still-unwrapped -> 0, every exclusion justified (see CODEGEN.md Stage 2).")
    lines.append(
        f"# total exports: {total}   wrapped-now: {len(plan.wrapped_now)}   "
        f"deliberately-raw: {len(plan.deliberately_raw)}   "
        f"still-unwrapped: {len(plan.still_unwrapped)}   "
        f"(collisions skipped, hand wins: {len(plan.skipped_collision)})"
    )
    lines.append("")
    lines.append(f"## wrapped-now ({len(plan.wrapped_now)}) — generated this pass")
    lines += plan.wrapped_now or ["(none)"]
    lines.append("")
    lines.append(f"## deliberately-raw ({len(plan.deliberately_raw)}) — free/reserve/ctor, left raw on purpose")
    lines += [f"{n}  # {why}" for n, why in sorted(plan.deliberately_raw)] or ["(none)"]
    lines.append("")
    lines.append(f"## still-unwrapped ({len(plan.still_unwrapped)}) — genuine remaining worklist")
    lines += sorted(plan.still_unwrapped) or ["(none)"]
    lines.append("")
    lines.append(
        f"## collisions-skipped ({len(plan.skipped_collision)}) — hand wrapper already exists; hand wins"
    )
    lines += [f"{n}  # {why}" for n, why in sorted(plan.skipped_collision)] or ["(none)"]
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    repo = here.parent
    ap.add_argument("--manifest", type=Path, default=repo.parent / "ratatui-ffi" / "bindings.json")
    ap.add_argument("--wrappers", type=Path, default=repo / "src" / "ratatui_py" / "wrappers.py")
    ap.add_argument("--out", type=Path, default=repo / "src" / "ratatui_py" / "_wrappers_generated.py")
    ap.add_argument("--report", type=Path, default=here / "residue.txt")
    args = ap.parse_args()

    fns = load_functions(args.manifest)
    hand = hand_methods(args.wrappers)
    plan = build_plan(fns, hand)

    text = emit(plan)
    if not text.endswith("\n"):
        text += "\n"
    args.out.write_text(text)

    report = emit_residue(plan, total=len(fns))
    if not report.endswith("\n"):
        report += "\n"
    args.report.write_text(report)

    print(
        f"wrote {args.out} — "
        f"methods={len(plan.methods)} headless={len(plan.headless)} "
        f"draw_in={len(plan.draw_in)} linegauge={len(plan.linegauge)} "
        f"wrapped_now={len(plan.wrapped_now)} "
        f"raw={len(plan.deliberately_raw)} collisions={len(plan.skipped_collision)} "
        f"still_unwrapped={len(plan.still_unwrapped)}"
    )
    if plan.still_unwrapped:
        for n in plan.still_unwrapped:
            print(f"  still-unwrapped: {n}")


if __name__ == "__main__":
    main()
