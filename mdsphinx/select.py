from collections.abc import Generator
from subprocess import CalledProcessError
from subprocess import PIPE
from subprocess import Popen
from typing import Any

# unicode non-breaking space
NBS = "\u00A0"


def select(
    *candidates: tuple[Any, ...] | Any,
    headers: tuple[str, ...] | None = None,
    matches: int | str | None = None,
    query: str | None = None,
) -> tuple[Any, ...]:
    """
    Use fzf to select a candidate from the given list of candidates.

    Parameters:
        *candidates: The list of candidates to select from.
        headers: The headers to display for the columns.
        matches: The columns to match on.
        query: The initial query to use.

    Returns:
        The selected candidate.
    """
    if not candidates:
        return ()

    command = [
        "fzf",
        "--select-1",
        "--height=~100%",
        "--delimiter",
        NBS,
        "--with-nth",
        "2..",
        *(() if query is None else ("--query", query)),
        *(() if headers is None else ("--header-lines", "1")),
        *(() if matches is None else ("--nth", matches if isinstance(matches, str) else str(matches + 1))),
    ]

    if headers is not None:
        headers = ("", *headers)

    inputs = "\n".join(_as_fixed_width(*_as_tuples(*candidates), headers=headers))
    process = Popen(command, stdin=PIPE, stdout=PIPE, text=True)
    stdout, stderr = process.communicate(input=inputs)

    if process.returncode != 0:
        raise CalledProcessError(process.returncode, command, stdout, stderr)

    return candidates[int(stdout.split(NBS)[0])]


def _as_tuples(*candidates: tuple[Any, ...] | Any) -> Generator[tuple[Any, ...], None, None]:
    """
    Ensure candidates are tuples.
    """
    for i, candidate in enumerate(candidates):
        if not isinstance(candidate, tuple):
            yield i, candidate
        else:
            yield i, *candidate


def _get_max_widths(*candidates: tuple[Any, ...], headers: tuple[str, ...] | None) -> dict[int, int]:
    """
    Get the maximum width of each column.
    """
    widths: dict[int, int] = {}
    for candidate in candidates:
        for i, value in enumerate(candidate):
            widths[i] = max(widths.get(i, 0 if not headers else len(headers[i])), len(str(value)))
    return widths


def _as_fixed_width(*candidates: tuple[Any, ...], headers: tuple[str, ...] | None) -> Generator[str, None, None]:
    """
    Format candidate row using fixed widths.
    """
    widths = _get_max_widths(*candidates, headers=headers)
    if headers is not None:
        yield NBS.join(f"{item:<{widths[i]}}" for i, item in enumerate(headers))
    for candidate in candidates:
        yield NBS.join(f"{item:<{widths[i]}}" for i, item in enumerate(candidate))
