from asyncio import Event, Lock
from collections.abc import Callable
from contextlib import contextmanager
from threading import Thread

from prompt_toolkit import ANSI, Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import FormattedTextControl, Layout, Window
from reactivity import async_effect, derived
from rich.console import Console, RenderResult
from rich.containers import Renderables
from rich.markdown import Markdown


class TruncatedMarkdown(Markdown):
    def __rich_console__(self, console, options):
        results = list(super().__rich_console__(console, options))
        height = console.height
        count = 0
        buffer = []
        for segment in reversed(results):
            count += segment.text.count("\n")  # type: ignore
            if count > height:
                break
            buffer.append(segment)

        self.truncated = len(buffer) < len(results)
        self.original = results

        yield from reversed(buffer)


@contextmanager
def streaming_markdown(get_md: Callable[[], str]):
    full_markdown: RenderResult | None = None

    @derived
    def get_ansi():
        segments = Console().render(m := TruncatedMarkdown(get_md()))
        ansi_output = "".join(seg.style.render(seg.text) if seg.style else seg.text for seg in segments)
        if m.truncated:
            nonlocal full_markdown
            full_markdown = m.original
        return ANSI(ansi_output.rstrip())

    event = Event()
    lock = Lock()

    app = Application(
        Layout(Window(FormattedTextControl(get_ansi), always_hide_cursor=True)),
        key_bindings=(kb := KeyBindings()),
        refresh_interval=0,  # disable automatic refresh
        after_render=lambda _: event.set(),
    )

    @async_effect(call_immediately=False, task_factory=lambda func: app.loop.create_task(func()))  # type: ignore
    async def update():
        async with lock:
            app.invalidate()
            await event.wait()
        event.clear()
        get_md()  # track dependency

    # manually connect dependencies and subscribers for the first time
    update.dependencies.add(get_ansi)
    get_ansi.subscribers.add(update)

    @kb.add("c-c")
    def _(_):
        raise KeyboardInterrupt

    thread = Thread(target=lambda: app.run(set_exception_handler=False, handle_sigint=False), daemon=True)
    thread.start()
    try:
        yield
    finally:
        if full_markdown:
            app.erase_when_done = True
        app.exit()
        thread.join()
        if full_markdown:
            Console().print(Renderables(full_markdown))
