#!/usr/bin/env python3
import sys
from pathlib import Path

TEMPLATE_BEGIN = "<!-- BEGIN: SNAPSHOTS -->"
TEMPLATE_END = "<!-- END: SNAPSHOTS -->"


def render_widgets_section() -> str:
    try:
        from ratatui_py import List, Table, Gauge
        from ratatui_py import headless_render_list, headless_render_table, headless_render_gauge
        lst = List()
        for i in range(1, 6):
            lst.append_item(f"Item {i}")
        lst.set_selected(2)
        tl = headless_render_list(30, 7, lst)

        tbl = Table()
        tbl.set_headers(["A", "B", "C"])
        tbl.append_row(["1", "2", "3"])
        tt = headless_render_table(30, 7, tbl)

        g = Gauge().ratio(0.42).label("42%")
        tg = headless_render_gauge(30, 3, g)

        return (
            "<table><tr>"
            f"<td><pre><code>{escape_html(tl)}</code></pre></td>"
            f"<td><pre><code>{escape_html(tt)}</code></pre></td>"
            f"<td><pre><code>{escape_html(tg)}</code></pre></td>"
            "</tr><tr>"
            "<td align=\"center\"><code>List</code></td>"
            "<td align=\"center\"><code>Table</code></td>"
            "<td align=\"center\"><code>Gauge</code></td>"
            "</tr></table>\n\n"
        )
    except Exception as e:
        return f"<p>Snapshot generation failed: {e}</p>\n\n"


def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def generate_snapshots_md() -> str:
    md = ["# Screencast Snapshots\n", "A grid of text snapshots rendered in CI.\n\n"]
    md.append(render_widgets_section())
    return "".join(md)


def inject_into_readme(readme_path: Path, content: str) -> None:
    txt = readme_path.read_text(encoding="utf-8")
    if TEMPLATE_BEGIN in txt and TEMPLATE_END in txt:
        before, rest = txt.split(TEMPLATE_BEGIN, 1)
        _, after = rest.split(TEMPLATE_END, 1)
        new = before + TEMPLATE_BEGIN + "\n\n" + content + "\n" + TEMPLATE_END + after
        readme_path.write_text(new, encoding="utf-8")


def main(argv):
    if len(argv) not in (2, 3):
        print(f"Usage: {argv[0]} <out.md> [readme.md]", file=sys.stderr)
        return 2
    out_md = Path(argv[1])
    content = generate_snapshots_md()
    out_md.write_text(content, encoding="utf-8")
    if len(argv) == 3:
        inject_into_readme(Path(argv[2]), content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

