#!/usr/bin/env python3
import sys, csv, pathlib

def main(argv):
    if len(argv) not in (3, 4):
        print(f"Usage: {argv[0]} <index.tsv> <out.md> [readme.md]")
        return 2
    index = pathlib.Path(argv[1])
    out = pathlib.Path(argv[2])
    rows = []
    with index.open('r', encoding='utf-8') as f:
        rdr = csv.reader(f, delimiter='\t')
        for row in rdr:
            if not row or row[0].strip().startswith('#') or row[0] == 'cast':
                continue
            # cast, gif, mp4, theme, speed, scale
            cast, gif, mp4, *_ = row + [None] * (6 - len(row))
            name = pathlib.Path(cast).stem
            rows.append((name, gif, mp4))
    # Simple 3-column grid
    cols = 3
    lines = []
    lines.append("# Screencast Snapshots\n")
    lines.append("A grid of latest screencasts rendered from the casts in docs/assets.\n\n")
    # header separator to render table
    def cell_html(name, gif, mp4):
        # Prefer GIF inline; link to MP4 if present
        gif_rel = gif
        link = mp4 if mp4 else gif
        return f"<a href=\"{link}\"><img src=\"{gif_rel}\" alt=\"{name}\" width=\"320\"/></a>"
    for i in range(0, len(rows), cols):
        chunk = rows[i:i+cols]
        html_row = "<table><tr>" + "".join(f"<td>{cell_html(n,g,m)}</td>" for n,g,m in chunk) + "</tr>\n<tr>" + "".join(f"<td align=\"center\"><code>{n}</code></td>" for n,_,_ in chunk) + "</tr></table>\n\n"
        lines.append(html_row)
    grid_md = "".join(lines)
    out.write_text(grid_md, encoding='utf-8')
    # Optional: inject grid into README between markers
    if len(argv) == 4:
        readme = pathlib.Path(argv[3])
        txt = readme.read_text(encoding='utf-8')
        begin = "<!-- BEGIN: SNAPSHOTS -->"
        end = "<!-- END: SNAPSHOTS -->"
        if begin in txt and end in txt:
            before, rest = txt.split(begin, 1)
            _, after = rest.split(end, 1)
            injected = before + begin + "\n\n" + grid_md + "\n" + end + after
            readme.write_text(injected, encoding='utf-8')
    return 0

if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
