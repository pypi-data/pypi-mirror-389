__all__ = [
    "flatten",
    "max_signed_value",
]

from collections.abc import Generator, Iterable, Iterator, Sequence
from typing import Any


def flatten(*items: Any | Iterable[Any]) -> Generator:
    """Flatten iterable of items.

    Examples
    --------
    >>> import stdkit
    >>> list(stdkit.flatten([[1, 2], *[3, 4], [5]]))
    [1, 2, 3, 4, 5]

    >>> list(stdkit.flatten([1, (2, 3)], 4, [], [[[5]], 6]))
    [1, 2, 3, 4, 5, 6]

    >>> list(stdkit.flatten(["one", 2], 3, [(4, "five")], [[["six"]]], "seven", []))
    ['one', 2, 3, 4, 'five', 'six', 'seven']
    """

    def _flatten(items):
        for item in items:
            if isinstance(item, (Iterator, Sequence)) and not isinstance(item, str):
                yield from _flatten(item)
            else:
                yield item

    return _flatten(items)


def max_signed_value(n_bits: int) -> int:
    """Return the max value of a signed integer using `n_bits` bits."""
    if not isinstance(n_bits, int):
        raise TypeError(f"type(n_bits)={type(n_bits).__name__!r} - expected integer")

    if n_bits < 2:
        raise ValueError(f"{n_bits=!r} - expected >= 2 for signed range")

    return (1 << (n_bits - 1)) - 1
