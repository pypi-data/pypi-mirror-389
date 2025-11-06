from contextlib import redirect_stderr
from functools import cache
from io import StringIO

from m.utils.path import global_store
from typer import Exit


@cache
def _get_session():
    from prompt_toolkit import PromptSession
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.input import create_input
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.styles import Style

    history = FileHistory(global_store / ".history")
    style = Style([("", "ansiyellow")])

    kb = KeyBindings()

    @kb.add(Keys.ControlJ)
    @kb.add(Keys.Escape, Keys.Enter)
    def _(event):
        event.current_buffer.insert_text("\n")

    with redirect_stderr(io := StringIO()):
        session = PromptSession(history=history, style=style, key_bindings=kb)

    if "Input is not a terminal (fd=0)" in io.getvalue():  # Warning: Input is not a terminal (fd=0).
        return PromptSession(input=create_input(open("/dev/tty")), history=history, style=style, key_bindings=kb)  # noqa: PTH123

    buf = session.default_buffer
    _accept = buf.accept_handler
    assert _accept is not None

    def accept(buf: Buffer):
        buf.text = buf.text.strip()
        return _accept(buf)

    buf.accept_handler = accept

    return session


def prompt():
    try:
        return _get_session().prompt(" > ", prompt_continuation="   ")
    finally:
        print()


def get_user_message():
    print()
    if message := prompt():
        return message
    else:
        raise Exit
