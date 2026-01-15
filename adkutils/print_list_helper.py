from typing import Callable, Any
from rich.table import Table
from rich import box


def after_last_slash(v):
    """Extracts the part of a string after the last slash.

    Args:
        v (str): The input string, typically a file path.

    Returns:
        str: The substring after the last occurrence of '/'.
    """
    return v.split("/")[-1]


def after_last_slash_multi(v):
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
    if not path:
        return obj
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
    def __init__(self, *args, **keywords) -> None:
        self.args = args
        self.keywords = keywords


def get_table_generic(data, col_specs, row_specs):
    """Generates a rich.Table object with data formatted according to column and row specifications.

    This function dynamically creates a table based on provided column headers and
    specifications for extracting data for each row from a given data source.

    Args:
        data (dict): The raw data containing a list of items to display.
                     Expected to have a key (e.g., "agents" or "reasoningEngines")
                     that holds a list of dictionaries or objects.
        col_specs (list): A list of column specifications. Each element can be:
                          - A string for a simple column header.
                          - A `col_spec` object for advanced column formatting
                            (e.g., style, overflow).
        row_specs (list): A list of row data specifications. Each element can be:
                          - A string representing a dot-separated path to a value
                            within each item in `data` (e.g., "name", "spec.displayName").
                          - A tuple where the first element is the path and subsequent
                            elements are arguments for the `_get_safe` function (e.g.,
                            `("name", after_last_slash)`).

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
    for agent in data.get("agents", []):
        result = []
        for row_spec in row_specs:
            if isinstance(row_spec, tuple):
                result.append(_get_safe(agent, *row_spec, default_value="N.A."))
            else:
                result.append(_get_safe(agent, row_spec, default_value="N.A."))

        # print(result)
        table.add_row(*tuple(result))

    return table
