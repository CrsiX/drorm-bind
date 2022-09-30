import ctypes
import asyncio
import contextlib
from typing import Any, Generator


def _counter(start: int = 0) -> Generator[int, Any, Any]:
    n = start
    while True:
        if n.bit_count() >= 64:
            raise RuntimeError(f"Exceeding int64_t range: {n}")
        yield n
        n += 1


def is_null_ptr(ptr: ctypes.POINTER) -> bool:
    try:
        _ = ptr.contents
        return False
    except ValueError:
        return True


async def wait_event(event: asyncio.Event, timeout: float):
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(event.wait(), timeout)
    return event.is_set()
