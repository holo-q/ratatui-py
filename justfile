# ratatui-py — codegen verbs.
# The interop layer (src/ratatui_py/_ffi.py) is 100% generated from the FFI's
# typed IR (../ratatui-ffi/bindings.json). See ../ratatui-ffi/CODEGEN.md for the contract.

manifest := "../ratatui-ffi/bindings.json"

# Regenerate the interop layer (_ffi.py) AND the Stage-2 ergonomic wrappers
# (_wrappers_generated.py) from the manifest. One verb, both stages.
gen:
    python3 tools/gen_ffi.py --manifest {{manifest}}
    python3 tools/gen_wrappers.py --manifest {{manifest}}

# Parity (superset proof vs prior hand file, if a tmp/_ffi_old.py snapshot exists)
# + residue (FFI fns with no ergonomic wrapper in src/). Both written under tools/.
report:
    python3 tools/parity_report.py --manifest {{manifest}}

# Import + smoke-load the regenerated bindings against the sibling .so.
build:
    RATATUI_FFI_LIB=../ratatui-ffi/target/release/libratatui_ffi.so uv run python -c "import ratatui_py._ffi as f; print('ratatui_py._ffi OK')"

# Full local loop: regenerate, report drift+residue, then load-check.
all: gen report build
