"""Utility module."""

import abc
import asyncio
import collections.abc
import contextlib
import errno
import io
import os
import socket
import threading
import time
import types
import typing
import weakref

from . import protocols


RecvSize = collections.abc.Callable[[io.BytesIO], collections.abc.Iterable[int]] | int
SendPayload = collections.abc.Iterable[protocols.SizedBuffer] | protocols.SizedBuffer


class ClosingContext(abc.ABC):

    @abc.abstractmethod
    def close(self) -> None:
        """Perform close operations (abstract)."""

    def __enter__(self) -> typing.Self:
        """Get self class as context manager."""
        return self

    def __exit__(
            self,
            exc_type: type | None,
            exc_value: BaseException | None,
            exc_traceback: types.TracebackType | None,
            ) -> None:
        """Leave context manager closing the socket."""
        try:
            try:
                self.close()

            except OSError as e:
                if propagate_close_error(e):
                    raise

        except* OSError as g:
            if errors := [e for e in g.exceptions if propagate_close_error(e)]:
                raise ExceptionGroup(g.message, errors) from g


class ContextPair[A: contextlib.AbstractContextManager, B: contextlib.AbstractContextManager](tuple[A, B]):
    """Tuple supporting context manager protocol."""

    def __new__(cls, a: A, b: B) -> typing.Self:
        """Initialize with variadic arguments as items (instead of iterable)."""
        return super().__new__(cls, (a, b))

    def __enter__(self) -> typing.Self:
        """Enter context on all items and return tuple itself."""
        errors = []
        for item in self:
            try:
                item.__enter__()

            except Exception as err:
                errors.append(err)

        if errors:
            message = 'Context manager exceptions'
            raise ExceptionGroup(message, errors)

        return self

    def __exit__(
            self,
            exc_type: type | None,
            exc_value: BaseException | None,
            exc_traceback: types.TracebackType | None,
            ) -> bool | None:
        """Leave context on all items."""
        booleans = 0
        truthies = 0
        errors = []
        for item in self:
            try:
                res = item.__exit__(exc_type, exc_value, exc_traceback)
                booleans += res is not None
                truthies += bool(res)

            except Exception as err:
                errors.append(err)

        if errors:
            message = 'Context manager exceptions'
            raise ExceptionGroup(message, errors)

        return True if truthies else False if booleans else None


class CrossLock:
    """A higher level lock for both sync and async."""

    __slots__: typing.ClassVar = '_aiolocks', '_aiowaits', '_busy', '_lock'

    _aiolocks: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock]
    _aiowaits: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Future]
    _busy: threading.Lock
    _lock: threading.Lock

    def __init__(self) -> None:
        """Initialize lock state."""
        self._lock = threading.Lock()
        self._busy = threading.Lock()
        self._aiolocks = weakref.WeakKeyDictionary()
        self._aiowaits = weakref.WeakKeyDictionary()

    @property
    def locked(self) -> bool:
        return self._lock.locked()

    def acquire(self, *, timeout: float | None = None) -> bool:
        return (
            self._lock.acquire() if timeout in {None, -1} else
            self._lock.acquire(timeout=timeout) if timeout else
            self._lock.acquire(blocking=False)
            )

    def release(self) -> None:
        with self._busy:
            aiowaits = dict(self._aiowaits)
            self._aiowaits.clear()
            self._lock.release()

        try:
            if future := aiowaits.pop(asyncio.get_running_loop(), None):
                future.set_result(None)

        except RuntimeError:
            pass

        for loop, future in aiowaits.items():
            loop.call_soon_threadsafe(future.set_result, None)

    async def acquire_async(self) -> typing.Literal[True]:
        loop = asyncio.get_running_loop()
        aiolock = self._aiolocks.get(loop) or self._aiolocks.setdefault(loop, asyncio.Lock())

        async with aiolock:  # per-loop lock mitigating thundering herd
            while True:
                with self._busy:
                    if self._lock.acquire(blocking=False):
                        return True

                    future = self._aiowaits.get(loop) or self._aiowaits.setdefault(loop, loop.create_future())

                await asyncio.shield(future)  # wait for release notification

    def __await__(self) -> collections.abc.Generator[None, None, None]:
        yield from self.acquire_async().__await__()

    def __enter__(self) -> typing.Self:
        self.acquire()
        return self

    def __exit__(
            self,
            exc_type: type | None,
            exc_value: BaseException | None,
            exc_traceback: types.TracebackType | None,
            ) -> None:
        self.release()

    async def __aenter__(self) -> typing.Self:
        await self.acquire_async()
        return self

    async def __aexit__(
            self,
            exc_type: type | None,
            exc_value: BaseException | None,
            exc_traceback: types.TracebackType | None,
            ) -> None:
        self.release()


def safe_timeout(sock: protocols.SocketLike, timeout: float | None) -> bool:
    """Check if timeout if supported by setting it and handling ValueError."""
    try:
        sock.settimeout(timeout)
    except ValueError:
        return False
    return True


def reader(
        sock: protocols.SocketLike, buffer: io.BytesIO, size: RecvSize, *,
        throttle: bool = False,
        ) -> collections.abc.Iterator[bool]:
    """Fully consume bytes from the socket."""
    buff_write = buffer.write
    sock_recv = sock.recv
    tell = buffer.tell
    seek = buffer.seek
    seek_end = os.SEEK_END
    sizes = (size,) if isinstance(size, int) else size(buffer)
    for sz in sizes:
        if sz > 0:
            pos = tell()
            seek(0, seek_end)
            while True:
                try:
                    if not (data := sock_recv(sz)):
                        raise EOFError

                    if (sz := sz - buff_write(data)) < 1:
                        break

                    if throttle:
                        yield False

                except BlockingIOError:
                    yield True

            seek(pos)


def writer(  # noqa: C901
        sock: protocols.SocketLike, data: SendPayload, *,
        throttle: bool = False,
        ) -> collections.abc.Iterator[bool]:
    """Fully write iterable of buffer into socket as an iterator."""

    def safe_write(data: collections.abc.Buffer) -> int:
        """Write buffer data into socket and return bytes written, if possible."""
        try:
            return sock_send(data)

        except BlockingIOError as e:
            return getattr(e, 'characters_written', 0)  # handle buffered-io-based socket-likes

    sock_send = sock.send
    chunks = (data,) if isinstance(data, protocols.SizedBuffer) else data
    for chunk in chunks:
        if chunk:
            offset = 0
            while (offset := safe_write(chunk)) < 1:  # write first chunk without slicing
                yield True

            if offset < len(chunk):  # finished
                buffer = memoryview(chunk)[offset:]  # turn slicing into zero-copy
                while True:
                    if (offset := safe_write(buffer)) < 1:
                        yield True

                    elif not (buffer := buffer[offset:]):
                        break

                    elif throttle:
                        yield False


@contextlib.contextmanager
def lock_timeout(lock: CrossLock, timeout: float | None = None) -> collections.abc.Generator[float | None, None, None]:
    """Acquire lock and calculate deadline for timeout."""
    timeout = socket.getdefaulttimeout() if timeout is None else timeout
    deadline = time.monotonic() + timeout if timeout else None
    if not lock.acquire(timeout=timeout):
        msg = 'timeout waiting for a concurrent operation'
        raise TimeoutError(msg)

    try:
        yield deadline

    finally:
        lock.release()


def propagate_close_error(error: Exception) -> bool:
    """Get whether or not an fd close OSError should be propagated by __exit__."""
    return getattr(error, 'errno', None) not in {errno.EBADF, errno.EBADFD}


def timeout_checker(deadline: float, error: str | None) -> collections.abc.Callable[[], float]:
    """Get function returning seconds left before monotonic timestamp, optionally raising on timeout."""

    def func() -> float:
        if (seconds := deadline - time.monotonic()) > 0:
            return seconds

        if error:
            raise TimeoutError(error)

        return 0

    return func
