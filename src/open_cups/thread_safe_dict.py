from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from collections.abc import ItemsView, Iterator, ValuesView


class ThreadSafeDict[T]:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        self._lock = threading.RLock()
        self._data: dict[str, T] = dict(*args, **kwargs)

    def __getitem__(self, key: str) -> T:
        with self._lock:
            return self._data[key]

    def __setitem__(self, key: str, value: T) -> None:
        with self._lock:
            self._data[key] = value

    def __delitem__(self, key: str) -> None:
        with self._lock:
            del self._data[key]

    def __iter__(self) -> Iterator[str]:
        with self._lock:
            return iter(list(self._data))  # safe copy, in contrast to normal dict

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._data

    def __enter__(self) -> Self:
        self._lock.acquire()
        return self

    def __exit__(self, *args: object) -> None:
        self._lock.release()

    def copy(self) -> ThreadSafeDict[T]:
        """Return a shallow copy as a ThreadSafeDict instance."""
        with self._lock:
            return ThreadSafeDict(self._data.copy())

    def items(self) -> ItemsView[str, T]:
        with self._lock:
            return self._data.copy().items()

    def values(self) -> ValuesView[T]:
        with self._lock:
            return self._data.copy().values()
