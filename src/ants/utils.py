from queue import Queue, ShutDown
from typing import Iterator, TypeVar

T = TypeVar("T")


def consume(q: Queue[T]) -> Iterator[T]:
    try:
        while True:
            yield q.get()
    except ShutDown:
        return
