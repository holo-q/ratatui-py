#!/usr/bin/env python3
import json, sys, io, tempfile, os

def convert(in_path: str, out_path: str) -> None:
    with open(in_path, 'r', encoding='utf-8') as f_in, open(out_path, 'w', encoding='utf-8') as f_out:
        first = f_in.readline()
        if not first:
            raise SystemExit('empty cast file')
        hdr = json.loads(first)
        if hdr.get('version') == 2:
            # pass-through
            f_out.write(first)
            for line in f_in:
                f_out.write(line)
            return
        if hdr.get('version') != 3:
            raise SystemExit(f"unsupported cast version: {hdr.get('version')}")
        term = hdr.get('term', {})
        cols = int(term.get('cols') or 80)
        rows = int(term.get('rows') or 24)
        out_hdr = {
            "version": 2,
            "width": cols,
            "height": rows,
        }
        # Preserve timestamp/env if present
        if 'timestamp' in hdr:
            out_hdr['timestamp'] = hdr['timestamp']
        if 'env' in hdr:
            out_hdr['env'] = hdr['env']
        f_out.write(json.dumps(out_hdr, separators=(',', ':')) + "\n")
        for line in f_in:
            f_out.write(line)

def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"Usage: {argv[0]} <input.cast> <output.cast>", file=sys.stderr)
        return 2
    convert(argv[1], argv[2])
    return 0

if __name__ == '__main__':
    raise SystemExit(main(sys.argv))

