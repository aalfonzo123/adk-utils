from pathlib import Path
from typing import Callable
from rich.prompt import Prompt


def resource_write_after_confirm(
    content_generator: Callable[[], str], path: Path, ask: bool
):
    if path.exists() and ask:
        choice = Prompt.ask(
            f"File {path} exists, overwrite? [Y]es,[N]o,[A]ll",
            choices=["y", "n", "a"],
            default="n",
        )
        if choice == "n":
            return True
        elif choice == "a":
            ask = False
    path.write_text(content_generator())
    print(f"Wrote {path}")
    return ask
