__all__ = [
    "Seed",
    "resolve_rng",
    "sample_int",
]

import random
from typing import TypeAlias

Seed: TypeAlias = int | random.Random | None


def resolve_rng(seed: Seed | None = None) -> random.Random:
    """Return a random.Random instance from the given seed."""
    global_rng = getattr(random, "_inst", None)

    if seed is None or seed is global_rng:
        return global_rng

    if isinstance(seed, random.Random):
        return seed

    if isinstance(seed, int):
        return random.Random(seed)

    raise ValueError(f"{seed=!r} - invalid seed")


def sample_int(a: int, b: int | None = None, seed: Seed | None = None) -> int:
    """Return a random integer n such that a <= n <= b."""
    rng = resolve_rng(seed)

    if b is None:
        low, high = 0, a
    else:
        low, high = a, b

    if low > high:
        low, high = high, low

    return rng.randint(low, high)
