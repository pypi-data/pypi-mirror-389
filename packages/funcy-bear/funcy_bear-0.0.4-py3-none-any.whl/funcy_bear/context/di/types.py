"""Types for the dependency injection system."""

from collections.abc import Callable
from typing import Any, Literal, NamedTuple, ParamSpec, Protocol, TypeVar, runtime_checkable

type CollectionChoice = Literal["list", "set", "dict", "defaultdict"]
type ReturnedCallable = Callable[..., dict | list | set | Callable]

Item = TypeVar("Item", bound=dict | object)
Return = TypeVar("Return")
Params = ParamSpec("Params")


@runtime_checkable
class Bindable(Protocol):
    """A protocol for objects that can bind documents."""

    def bind(self, doc: Any, **kwargs) -> None:
        """Bind a document to the object."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the object with the given arguments."""


class TearDownCallback(NamedTuple):
    """Information about a registered teardown callback."""

    priority: float
    name: str
    callback: Callable[[], None]
