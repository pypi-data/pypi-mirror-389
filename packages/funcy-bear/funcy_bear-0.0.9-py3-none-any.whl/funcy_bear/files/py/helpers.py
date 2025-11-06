"""Functions for File Builder operations related to strings."""

from funcy_bear.constants.characters import PIPE, TRIPLE_QUOTE

from .parts import Arg, Decorator


def _type_name(t: type | str) -> str:
    """Get the name of the type or return the string as is.

    Args:
        t: The type or string.

    Returns:
        The name of the type or the string itself.
    """
    return t if isinstance(t, str) else t.__name__


def get_returns(ret: str | type | tuple[type, ...], prefix: str = "", suffix: str = "") -> str:
    """Set or update the return type annotation.

    Args:
        ret: The return type annotation as a string or type.
        prefix: Optional prefix to add before the return type.
        suffix: Optional suffix to add after the return type.

    Returns:
        string representing the return type annotation.
    """
    ret_str: str = _type_name(ret) if isinstance(ret, (str, type)) else PIPE.join(_type_name(t) for t in ret)
    return f"{prefix}{ret_str}{suffix}"


def get_docstring(docstring: str) -> str:
    """Wrap the given docstring content in triple quotes.

    Args:
        docstring: The docstring content (without triple quotes).

    Returns:
        String representing the docstring with triple quotes.
    """
    return f"{TRIPLE_QUOTE}{docstring}{TRIPLE_QUOTE}"


def render_args(args: str | Arg | list[Arg]) -> str:
    """Render function arguments to a string.

    Args:
        args: Function arguments (string, Arg, or list of Args).

    Returns:
        The rendered arguments as a string.
    """
    return (
        args.render()
        if isinstance(args, Arg)
        else ", ".join(arg.render() for arg in args)
        if isinstance(args, list)
        else args
    )


def get_decorators(decorators: list[str] | list[Decorator]) -> str:
    """Render function decorators to a string.

    Args:
        decorators: Function decorators (list of strings or Decorators).

    Returns:
        The rendered decorators as a string.
    """
    return "\n".join(decorator.render() if isinstance(decorator, Decorator) else decorator for decorator in decorators)
