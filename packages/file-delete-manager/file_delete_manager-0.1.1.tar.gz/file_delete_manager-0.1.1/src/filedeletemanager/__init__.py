from .core import DeleteOptions, delete_by_age, delete_by_count
from .rules import delete_if_over_size, move_to_trash

__all__ = [
    "DeleteOptions",
    "delete_by_age",
    "delete_by_count",
    "delete_if_over_size",
    "move_to_trash",
]
