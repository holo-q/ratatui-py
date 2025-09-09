from ratatui_py import margin, split_h, split_v


def test_margin_and_splits():
    base = (0, 0, 80, 24)
    inner = margin(base, all=1)
    assert inner == (1, 1, 78, 22)

    rows = split_h(base, 1, 1, gap=2)
    assert len(rows) == 2
    # Total height 24, gap 2 -> 22 to split roughly in half
    assert rows[0][1] == 0 and rows[1][1] == rows[0][3] + 2

    cols = split_v(base, 2, 1, gap=1)
    assert len(cols) == 2
    assert cols[0][0] == 0 and cols[1][0] == cols[0][2] + 1

