"""Keep Playwright's synchronous API on one dedicated thread."""

from concurrent.futures import Future, TimeoutError as FutureTimeout
import queue
import threading
import time
from typing import Callable, TypeVar

from playwright.sync_api import Locator, Page, sync_playwright

from .config import Config

T = TypeVar("T")


class BrowserSession:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._jobs = queue.Queue()
        self._ready = threading.Event()
        self._startup_error: BaseException | None = None
        self._thread = threading.Thread(target=self._loop, name="psauto-playwright", daemon=True)
        self._page: Page | None = None
        self._lifecycle_lock = threading.Lock()
        self._closing = False
        self._poisoned = threading.Event()

    def start(self) -> None:
        self._thread.start()
        if not self._ready.wait(timeout=60):
            with self._lifecycle_lock:
                self._closing = True
                self._jobs.put(None)
            raise TimeoutError("Playwright browser did not start within 60 seconds")
        if self._startup_error is not None:
            raise RuntimeError("Playwright browser failed to start") from self._startup_error

    def call(self, fn: Callable[[Page], T], timeout: float = 30) -> T:
        future: Future[T] = Future()
        with self._lifecycle_lock:
            if self._closing or not self._ready.is_set() or not self._thread.is_alive():
                raise RuntimeError("Playwright session is not running or is closing")
            self._jobs.put((fn, future))
        try:
            return future.result(timeout=timeout)
        except FutureTimeout as exc:
            if future.done():
                return future.result()
            cancelled = future.cancel()
            if not cancelled:
                with self._lifecycle_lock:
                    if future.done():
                        return future.result()
                    self._poisoned.set()
                    if not self._closing:
                        self._closing = True
                        self._jobs.put(None)
            detail = "queued operation cancelled" if cancelled else "operation may still be running"
            raise TimeoutError(f"Playwright operation timed out; {detail}") from exc

    def save_storage_state(self) -> None:
        path = self.cfg.resolve_path(self.cfg.storage_state)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.call(lambda page: page.context.storage_state(path=str(path), indexed_db=True))

    def stop(self) -> None:
        with self._lifecycle_lock:
            if not self._thread.is_alive():
                self._closing = True
                return
            if not self._closing:
                self._closing = True
                self._jobs.put(None)
        self._thread.join(timeout=30)
        if self._thread.is_alive():
            raise TimeoutError("Playwright session did not stop within 30 seconds")

    def _loop(self) -> None:
        pw = browser = context = None
        try:
            pw = sync_playwright().start()
            browser = pw.chromium.launch(headless=self.cfg.headless, channel=self.cfg.browser_channel)
            state_path = self.cfg.resolve_path(self.cfg.storage_state)
            state = str(state_path) if state_path.is_file() else None
            context = browser.new_context(
                viewport={"width": self.cfg.viewport_width, "height": self.cfg.viewport_height},
                device_scale_factor=1,
                ignore_https_errors=self.cfg.ignore_https_errors,
                storage_state=state,
            )
            self._page = context.new_page()
            self._ready.set()
            while True:
                try:
                    item = self._jobs.get(timeout=0.1)
                except queue.Empty:
                    if not self._page.is_closed():
                        self._page.wait_for_timeout(10)
                    continue
                if item is None:
                    break
                fn, future = item
                if not future.set_running_or_notify_cancel():
                    continue
                if self._poisoned.is_set():
                    future.set_exception(RuntimeError("Playwright session was stopped after an operation timed out"))
                    continue
                try:
                    future.set_result(fn(self._page))
                except BaseException as exc:
                    future.set_exception(exc)
        except BaseException as exc:
            if not self._ready.is_set():
                self._startup_error = exc
                self._ready.set()
            else:
                self._fail_queued(exc)
        finally:
            with self._lifecycle_lock:
                self._closing = True
            self._fail_queued(RuntimeError("Playwright session stopped before the operation could run"))
            try:
                if context is not None:
                    context.close()
            finally:
                try:
                    if browser is not None:
                        browser.close()
                finally:
                    if pw is not None:
                        pw.stop()

    def _fail_queued(self, exc: BaseException) -> None:
        while True:
            try:
                item = self._jobs.get_nowait()
            except queue.Empty:
                return
            if item is not None:
                _, future = item
                if future.set_running_or_notify_cancel():
                    future.set_exception(exc)


def display(page: Page, cfg: Config) -> Locator:
    if cfg.display_frame:
        return page.frame_locator(cfg.display_frame).locator(cfg.display_selector).first
    return page.locator(cfg.display_selector).first


def open_remote(session: BrowserSession, cfg: Config) -> None:
    if not cfg.connect_url or not cfg.display_selector:
        raise ValueError("connect_url and display_selector must be configured before connecting")

    def _open(page: Page) -> None:
        context = page.context
        page.goto(cfg.connect_url, timeout=30_000)
        for selector in cfg.pre_connect_clicks:
            step_deadline = time.monotonic() + 30
            while True:
                pages = context.pages
                if not pages:
                    raise RuntimeError("All browser pages were closed during connection")
                target = next((candidate.locator(selector).first for candidate in reversed(pages)
                               if not candidate.is_closed() and candidate.locator(selector).first.is_visible()), None)
                if target is not None:
                    target.click(timeout=10_000)
                    break
                if time.monotonic() >= step_deadline:
                    raise TimeoutError(f"Connection step did not become visible: {selector}")
                pages[0].wait_for_timeout(200)
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            for candidate in reversed(context.pages):
                if not candidate.is_closed() and display(candidate, cfg).is_visible(timeout=200):
                    session._page = candidate
                    return
            if not context.pages:
                raise RuntimeError("All browser pages were closed before the remote display appeared")
            context.pages[0].wait_for_timeout(200)
        raise TimeoutError("Remote display did not become visible within 60 seconds")

    session.call(_open, timeout=100 + 40 * len(cfg.pre_connect_clicks))
