from contextlib import redirect_stderr
from functools import cache
from io import StringIO

from m.utils.path import global_store
from typer import Exit


@cache
def _get_session():
    from prompt_toolkit import PromptSession
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

    return session


def prompt():
    return _get_session().prompt(" > ", prompt_continuation="   ")


def get_user_message():
    print()

    message = prompt()
    if not message:
        print()
        raise Exit

    print()

    return message
