"""
A program that generates customizable ASCII art pictures with a message.
"""

import enum
import sys
import textwrap
from pathlib import Path

import appdirs
import cli_box
import click


DEFAULT_ASCII_ART = """
        \\   ^__^
         \\  (oo)\\_______
            (__)\\       )\\/\\
                ||----w |
                ||     ||
"""[1:-1]


CONFIG_DIR = Path(appdirs.user_config_dir("ccowsay"))
CONFIG_DIR.mkdir(exist_ok=True)

ASCII_ART_FILE = CONFIG_DIR / "ascii.txt"


class Align(enum.Enum):
    """
    An enum representing align positions
    """

    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"


@click.command()
@click.argument("message", required=False)
@click.option("-a", "--align", default=Align.LEFT, type=click.Choice(Align))
@click.option("-w", "--box-width", default=50, type=int)
def ccowsay(message: str, align: str, box_width: int) -> None:
    """
    ccowsay is a program that generates customizable ASCII art pictures with a message.
    """

    ascii_art = DEFAULT_ASCII_ART

    if ASCII_ART_FILE.is_file():
        ascii_art = ASCII_ART_FILE.read_text()

    if message is None:
        message = sys.stdin.read()

    print(
        "%s\n%s"
        % (
            cli_box.rounded(
                "\n".join(
                    textwrap.wrap(message, replace_whitespace=False, width=box_width)
                ),
                align=align,
            ),
            ascii_art,
        )
    )


if __name__ == "__main__":
    ccowsay()
