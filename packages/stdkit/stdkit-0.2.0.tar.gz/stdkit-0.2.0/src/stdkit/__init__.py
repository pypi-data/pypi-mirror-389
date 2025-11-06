__all__ = [
    "__version__",
    # core.py
    "flatten",
    "max_signed_value",
    # random.py
    "Seed",
    "resolve_rng",
    "sample_int",
]

from importlib import metadata

from stdkit.core import flatten, max_signed_value
from stdkit.random import Seed, resolve_rng, sample_int

__version__ = metadata.version(__name__)
