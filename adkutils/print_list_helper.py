from typing import Callable, Any
from rich.table import Table
from rich import box

DEFAULT_KWARGS = {"default_value": "N.A."}


def after_last_slash(v):
    """Extracts the part of a string after the last slash.

    Args:
        v (str): The input string, typically a file path.

    Returns:
        str: The substring after the last occurrence of '/'.
    """
    return v.split("/")[-1]


def after_last_slash_multi(v: list[str]) -> str:
    """Extracts the part of a string after the last slash for multiple strings.

    Args:
        v (list[str]): A list of input strings, typically file paths.

    Returns:
        str: A comma-separated string of substrings after the last occurrence of '/'.
    """
    return ", ".join([elem.split("/")[-1] for elem in v])


def _get_safe(
    object: Any,
    path: str,
    on_found: Callable | None = None,
    default_value: Any | None = None,
):
    """Safely gets a value from a nested object and optionally transforms it.

    Args:
        object: The object to traverse.
        path: The path to the value, separated by dots.
        on_found: A function to call with the value if it's found.
        default_value: The value to return if the path is not found.

    Returns:
        The transformed value if found, otherwise the default_value.
    """
    obj = object
    if path:
        for element in path.split("."):
            if hasattr(obj, element):
                obj = getattr(obj, element)
            elif isinstance(obj, dict) and element in obj:
                obj = obj[element]
            else:
                return default_value
    if on_found:
        return on_found(obj)
    return obj


class col_spec:
    """A helper class to define column specifications for rich.Table.

    Allows passing arbitrary arguments and keywords directly to `table.add_column`.
    """

    def __init__(self, *args: Any, **keywords: Any) -> None:
        """Initializes a new col_spec instance.

        Args:
            *args: Positional arguments to be passed to `table.add_column`.
                   Typically the column header string.
            **keywords: Keyword arguments to be passed to `table.add_column`.
                        E.g., `style="bold magenta"`, `overflow="fold"`.
        """
        self.args = args
        self.keywords = keywords


def get_table_generic(
    data: dict[str, list[Any]],
    data_key: str,
    col_specs: list[str | col_spec],
    row_specs: list[str | tuple[str, Callable | None]],
):
    """Generates a rich.Table object with data formatted according to column and row specifications.

    This function dynamically creates a table based on provided column headers and
    specifications for extracting data for each row from a given data source.

    Args:
        data: The raw data containing a list of items to display.
                     Expected to have a key (`data_key`) that holds a list of
                     dictionaries or objects.
        data_key: The key in the `data` dictionary that points to the list of items
                  to be displayed in the table.
        col_specs: A list of column specifications. Each element can be:
                          - A `str` for a simple column header.
                          - A `col_spec` object for advanced column formatting
                            (e.g., style, overflow).
        row_specs: A list of row data specifications. Each element can be:
                          - A `str` representing a dot-separated path to a value
                            within each item in `data` (e.g., "name", "spec.displayName").
                          - A `tuple` where the first element is the path (`str`)
                            and the second element is an optional `Callable` to
                            transform the found value (e.g., `("name", after_last_slash)`).

    Returns:
        rich.table.Table: A formatted rich Table object ready for printing.
    """

    table = Table(box=box.SQUARE, show_lines=True)
    for cs in col_specs:
        if isinstance(cs, col_spec):
            table.add_column(*cs.args, **cs.keywords)
        else:
            table.add_column(cs)
    # print(col_specs)

    # Iterate through the agents and extract the necessary information for display.
    for item in data.get(data_key, []):
        result = []
        for row_spec in row_specs:
            if isinstance(row_spec, tuple):
                kwargs = {} if len(row_spec) == 3 else DEFAULT_KWARGS
                result.append(_get_safe(item, *row_spec, **kwargs))
            else:
                result.append(
                    _get_safe(item, row_spec, on_found=None, **DEFAULT_KWARGS)
                )

        # print(result)
        table.add_row(*tuple(result))

    return table
