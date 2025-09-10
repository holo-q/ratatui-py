from ratatui_py import Terminal, Canvas, Style, rgb


def main() -> None:
    term = Terminal()
    try:
        w, h = term.size()
        rect = (0, 0, w, h)

        # Draw a simple canvas: a cyan rectangle and a diagonal line
        cv = Canvas(0.0, 100.0, 0.0, 100.0)
        cv.set_block_title("Canvas", show_border=True)
        cv.add_rect(10, 10, 80, 60, Style(fg=rgb(0, 255, 255)))
        cv.add_line(10, 10, 90, 70, Style(fg=rgb(255, 128, 0)))
        term.draw_canvas(cv, rect)

        # Draw the Ratatui logo below if space allows
        if h >= 16:
            term.draw_logo((0, h - 12, w, 12))
    finally:
        term.close()


if __name__ == "__main__":
    main()

