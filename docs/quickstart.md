# Quickstart

Install from PyPI and run the demo hub:

```bash
pip install ratatui-py
ratatui-py-demos
```

Minimal program:

```python
from ratatui_py import Terminal, Paragraph

with Terminal() as term:
    p = Paragraph.from_text("Hello ratatui-py!\nPress any key to exit.")
    p.set_block_title("Demo", True)
    term.draw_paragraph(p)
    term.next_event(5000)
```

App loop helper:

```python
from ratatui_py import App, Terminal, Paragraph

def render(term: Terminal, state: dict) -> None:
    w, h = term.size()
    p = Paragraph.from_text(state.get("msg", "Hi"))
    p.set_block_title("Demo", True)
    term.draw_paragraph(p, (0, 0, w, h))

def on_event(term: Terminal, evt: dict, state: dict) -> bool:
    if evt.get("kind") == "key" and evt.get("ch") in (ord('q'), ord('Q')):
        return False
    return True

App(render=render, on_event=on_event, tick_ms=250).run({"msg": "Hello from App"})
```
