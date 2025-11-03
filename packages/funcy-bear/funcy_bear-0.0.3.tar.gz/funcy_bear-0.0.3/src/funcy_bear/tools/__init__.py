"""Generally useful tools like data structures, caching, and freezing."""

from funcy_bear.tools.freezing import FrozenDict, freeze
from funcy_bear.tools.lru_cache import LRUCache

__all__ = [
    "FrozenDict",
    "LRUCache",
    "freeze",
]
