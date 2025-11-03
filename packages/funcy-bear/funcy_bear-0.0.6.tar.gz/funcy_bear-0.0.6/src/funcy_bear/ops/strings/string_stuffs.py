"""String manipulation utilities."""


def cut_prefix(s: str, prefix: str) -> str:
    """Cuts prefix from given string if it's present.

    Args:
        s: The original string.
        prefix: The prefix to cut.

    Returns:
        The string without the prefix if it was present, otherwise the original string.
    """
    return s[len(prefix) :] if s.startswith(prefix) else s


def cut_suffix(s: str, suffix: str) -> str:
    """Cuts suffix from given string if it's present.

    Args:
        s: The original string.
        suffix: The suffix to cut.

    Returns:
        The string without the suffix if it was present, otherwise the original string.
    """
    if not suffix:
        return s
    return s[: -len(suffix)] if s.endswith(suffix) else s
