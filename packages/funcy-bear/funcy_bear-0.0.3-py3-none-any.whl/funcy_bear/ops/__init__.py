"""Operations: functional programming utilities and helpers."""

from funcy_bear.ops.collections_ops.dict_stuffs import key_counts, merge as merge_dicts
from funcy_bear.ops.collections_ops.iter_stuffs import (
    dupes,
    merge,
    merge_lists,
    merge_sets,
    merge_tuples,
    pairwise,
    uniqueify,
    window,
)

__all__ = [
    "dupes",
    "key_counts",
    "merge",
    "merge_dicts",
    "merge_lists",
    "merge_sets",
    "merge_tuples",
    "pairwise",
    "uniqueify",
    "window",
]
