from ratatui_py import Terminal, Paragraph, Style, FFI_COLOR

if __name__ == "__main__":
    with Terminal() as term:
        p = Paragraph.from_text("Hello from Python!\nThis is ratatui.")
        p.set_block_title("Demo", True)
        p.append_line("\nStyled line", Style(fg=FFI_COLOR["LightCyan"]))
        term.draw_paragraph(p)
