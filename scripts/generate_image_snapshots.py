#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List, Tuple

# Ensure local src is importable in CI and local runs
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from PIL import Image, ImageDraw, ImageFont  # type: ignore


def font_path() -> str:
    # Prefer env-provided path
    import os
    p = os.getenv('SNAPSHOT_FONT')
    if p and Path(p).exists():
        return p
    # Common system path on Ubuntu
    for c in [
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
        '/usr/share/fonts/TTF/DejaVuSansMono.ttf',
    ]:
        if Path(c).exists():
            return c
    raise FileNotFoundError('Could not find a monospaced TTF font; set SNAPSHOT_FONT to a .ttf')


def draw_text_image(lines: List[str], out: Path, *, pad: int = 10, bg=(248, 250, 252), fg=(20, 20, 20), size: int = 16) -> None:
    fp = font_path()
    font = ImageFont.truetype(fp, size)
    # Measure
    max_len = max((len(l) for l in lines), default=0)
    # getbbox returns (l,t,r,b)
    w_char = int(font.getlength('M'))
    h_char = font.getbbox('Mg')[3] - font.getbbox('Mg')[1]
    W = max(1, max_len) * w_char + pad * 2
    H = max(1, len(lines)) * h_char + pad * 2
    img = Image.new('RGB', (W, H), color=bg)
    draw = ImageDraw.Draw(img)
    y = pad
    for ln in lines:
        draw.text((pad, y), ln, font=font, fill=fg)
        y += h_char
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def render_snapshots() -> Tuple[str, list[Path]]:
    # Import after sys.path tweak
    from ratatui_py import List, Table, Gauge
    from ratatui_py import headless_render_list, headless_render_table, headless_render_gauge

    assets = []
    lines = []
    lines.append('# UI Snapshots\n')
    lines.append('A grid of image snapshots rendered in CI.\n\n')

    # Render a few widgets into text buffers
    lst = List()
    for i in range(1, 6):
        lst.append_item(f'Item {i}')
    lst.set_selected(2)
    tl = headless_render_list(30, 7, lst)
    p_lst = Path('docs/assets/snapshots/list.png')
    draw_text_image(tl.splitlines(), p_lst)
    assets.append(p_lst)

    tbl = Table()
    tbl.set_headers(['A', 'B', 'C'])
    tbl.append_row(['1', '2', '3'])
    tt = headless_render_table(30, 7, tbl)
    p_tbl = Path('docs/assets/snapshots/table.png')
    draw_text_image(tt.splitlines(), p_tbl)
    assets.append(p_tbl)

    g = Gauge().ratio(0.42).label('42%')
    tg = headless_render_gauge(30, 3, g)
    p_g = Path('docs/assets/snapshots/gauge.png')
    draw_text_image(tg.splitlines(), p_g)
    assets.append(p_g)

    # Build simple HTML table grid 3 columns
    def cell_img(p: Path, label: str) -> str:
        return f'<td><img src="{p.as_posix()}" alt="{label}" width="320"/></td>'

    row = '<table><tr>' + cell_img(p_lst, 'List') + cell_img(p_tbl, 'Table') + cell_img(p_g, 'Gauge') + '</tr>\n'
    row += '<tr><td align="center"><code>List</code></td><td align="center"><code>Table</code></td><td align="center"><code>Gauge</code></td></tr></table>\n\n'
    lines.append(row)
    return (''.join(lines), assets)


def inject_into_readme(readme_path: Path, content: str) -> None:
    begin = '<!-- BEGIN: SNAPSHOTS -->'
    end = '<!-- END: SNAPSHOTS -->'
    txt = readme_path.read_text(encoding='utf-8')
    if begin in txt and end in txt:
        before, rest = txt.split(begin, 1)
        _, after = rest.split(end, 1)
        new = before + begin + '\n\n' + content + '\n' + end + after
        readme_path.write_text(new, encoding='utf-8')


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print(f'Usage: {argv[0]} <out.md> [readme.md]')
        return 2
    out = Path(argv[1])
    content, assets = render_snapshots()
    out.write_text(content, encoding='utf-8')
    if len(argv) == 3:
        inject_into_readme(Path(argv[2]), content)
    # Print assets for CI logs
    for p in assets:
        print('Wrote', p)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
