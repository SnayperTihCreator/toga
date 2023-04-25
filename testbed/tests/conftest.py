import asyncio
import inspect
from dataclasses import dataclass
from importlib import import_module

from pytest import fixture, register_assert_rewrite, skip

import toga

# Ideally, we'd register rewrites for "tests" and get all the submodules
# recursively; however we've already imported "tests", so that raises a warning.
register_assert_rewrite("tests.assertions")
register_assert_rewrite("tests.widgets")
register_assert_rewrite("tests_backend")


def skip_on_platforms(*platforms):
    current_platform = toga.platform.current_platform
    if current_platform in platforms:
        skip(f"not applicable on {current_platform}")


@fixture(scope="session")
def app():
    return toga.App.app


@fixture(scope="session")
def main_window(app):
    return app.main_window


# Controls the event loop used by pytest-asyncio.
@fixture(scope="session")
def event_loop(app):
    return ProxyEventLoop(app._impl.loop)


# Identical to widgets/probe, but usable by all tests.
# Should replace generic "probe" fixture when window_probe and others are added
@fixture
async def widget_probe(main_window, widget):
    box = toga.Box(children=[widget])
    main_window.content = box

    probe = get_widget_probe(widget)
    await probe.redraw()
    probe.assert_container(box)

    yield probe

    main_window.content = toga.Box()


def get_widget_probe(widget):
    name = type(widget).__name__
    module = import_module(f"tests_backend.widgets.{name.lower()}")
    return getattr(module, f"{name}Probe")(widget)


# Proxy which forwards all tasks to another event loop in a thread-safe manner. It
# implements only the methods used by pytest-asyncio.
@dataclass
class ProxyEventLoop(asyncio.AbstractEventLoop):
    loop: object

    # Used by ensure_future.
    def create_task(self, coro):
        return ProxyTask(coro)

    def run_until_complete(self, future):
        if inspect.iscoroutine(future):
            coro = future
        elif isinstance(future, ProxyTask):
            coro = future.coro
        else:
            raise TypeError(f"Future type {type(future)} is not currently supported")
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def close(self):
        pass


@dataclass
class ProxyTask:
    coro: object

    # Used by ensure_future.
    _source_traceback = None

    def done(self):
        return False
