from sys import stdin

from promplate.prompt.chat import Message, assistant, system, user
from reactivity import signal
from typer import Argument, Option, Typer

from .impl import default_model, get_client
from .markdown import streaming_markdown
from .utils import get_user_message

app = Typer()


@app.command()
def ask(message: str = Argument(""), model: str = Option(default_model, "--model", "-m")):
    if not message:
        message = get_user_message()

    messages: list[Message] = [user > message]
    if not stdin.isatty():
        messages.insert(0, system > stdin.read())

    while True:
        out = signal("")
        with streaming_markdown(out.get):
            for i in get_client().generate(messages, model=model):
                out.update(lambda last: last + i)

        messages.append(assistant > out.get())

        messages.append(user > get_user_message())
