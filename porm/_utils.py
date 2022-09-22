from typing import Any, Generator


def _counter(start: int = 0) -> Generator[int, Any, Any]:
    n = start
    while True:
        if n.bit_count() >= 64:
            raise RuntimeError(f"Exceeding int64_t range: {n}")
        yield n
        n += 1
